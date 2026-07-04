---
name: email-sync
description: "Sync Gmail messages into vault manifest. Runs at session start. Replaces command center Step 1.5."
---

# Email Sync Adapter

Pulls recent emails from Gmail, diffs against snapshot, produces a manifest
of vault note updates. Replaces the inline email sync in command-center Step 1.5.

## When to Use

Called by the `/sync` router. Not invoked directly.

## Process

### 1. Pull Emails

Two queries — **BOTH ARE MANDATORY**:
1. `gmail_search_threads(query="in:inbox -category:promotions -category:social", pageSize=30)` — active inbox
2. `gmail_search_threads(query="in:sent newer_than:14d", pageSize=50)` — recent sent

**CRITICAL — sent folder is not optional:**
- If the sent query fails (502, timeout, etc.), **RETRY at least twice** with backoff.
- If it still fails, widen to `from:me newer_than:14d` as a fallback.
- If all sent-query variants fail, **FAIL LOUDLY** in the manifest with `status: "sent_query_failed"` and flag that the inbox triage is unverified. Do NOT silently emit an inbox-only manifest — Albert has explicitly called this out as a repeated error mode.
- Alternative path: if `gmail_search_threads` returns inbox threads, they already contain Albert's sent replies within the thread. Use `gmail_get_thread` per thread to parse full message history and determine the true latest-sender per thread.

For high-signal threads (starred, from known collaborators, with action items), call
`gmail_get_thread` to get full thread content.

### 1b. Compute Latest-Sender Per Thread

For every inbox thread, determine the sender of the **most recent message in the thread**:
- If `sender == albert.k.ying@gmail.com` or `sender == keying@stanford.edu` or `sender == kying@g.harvard.edu`: thread is **NOT stale on Albert's side** → do not flag as "needs reply" regardless of recency.
- If latest sender is someone else AND the thread has an implicit ask (question, attached file, action item): flag as "awaiting Albert's reply."
- If latest sender is someone else but message is purely FYI/thanks/confirmation: flag as "tracking" not "needs reply."

This latest-sender computation replaces any inbox-only heuristic. Albert's corrections supersede inbox view.

### 2. Load Snapshot

Read `.cache/sync-state/email-snapshot.json`. If missing, treat all emails as new.

Snapshot format:
```json
{
  "synced_at": "2026-03-12T10:00:00Z",
  "threads": {
    "<thread_id>": {
      "subject": "...",
      "last_message_id": "...",
      "participants": ["..."],
      "summary": "...",
      "starred": false
    }
  }
}
```

### 3. Diff

- **New threads**: thread ID not in snapshot
- **Updated threads**: thread ID exists but last_message_id differs (new replies)
- **Newly starred**: starred status changed

### 4. Match Against Vault Index

Load `.cache/sync-state/vault-index.json`.

For each new/updated thread:
1. Extract keywords from: subject line, sender name, recipient names, email body
2. Match against vault index using keyword overlap
3. For person names (From/To/CC), check `type: "person"` matches
4. Read full content of top candidate notes
5. Determine which notes need updating

### 5. Generate Manifest

**Person notes** (`user.*.md`):
- Action: `rewrite_section`, section: `## Current Status`
- Content: Latest interaction context from email thread
- Evidence: subject, date, direction (sent/received)
- Confidence: 0.9+ for known contacts, 0.75 for ambiguous name matches

**Project notes** (`proj.*.md`, `personal.grant.*.md`, etc.):
- Action: `rewrite_section` on status/progress sections
- Content: Status updates derived from email content
- Confidence: 0.85+ if subject/body clearly references the project

**Working memory** (`_working-memory.md`):
- Action: `rewrite_section`, section: `## Email Inbox — Active Items (synced YYYY-MM-DD)`
- Content: Triaged inbox — "### Needs Action", "### Scheduled", "### Tracking"
- Each item: checkbox, subject summary, sender, priority, vault link if person exists
- Confidence: 1.0

**Context model follow-ups**:
- For emails with detected action items or deadlines, emit changes targeting
  the relevant notes rather than command-center.md directly (the vault-updater
  handles cross-note synthesis)

### 6. Save Manifest and Update Snapshot

Write manifest to `.cache/sync-state/email-manifest-<timestamp>.json`.
Update snapshot with current thread state.

## Triage Logic

**Gate:** a thread can only be labeled "needs reply" / "awaiting Albert" if the latest-sender check from §1b confirmed Albert is NOT the last sender. No exceptions — not even for stale-looking threads.

**Also trust Albert:** if Albert says a thread is already addressed (verbal correction during session), honor it immediately. Remove from follow-ups and note the correction; do not re-surface it. Record the source channel if he mentions one (text, WeChat, in-person) so future syncs can widen their check.

Priority assignment for inbox items where Albert is NOT the latest sender:
- **HIGH**: Starred emails, deadlines within 7 days, emails from T1/T2 contacts awaiting response
- **MEDIUM**: Project-related emails, invitations, requests from known contacts
- **LOW**: FYI, newsletters that made it to inbox, tracking items

Use the vault index `tier` field to identify T1/T2 contacts.

## Output

The manifest JSON file path, printed to stdout.
