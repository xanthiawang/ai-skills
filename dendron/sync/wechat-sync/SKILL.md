---
name: wechat-sync
description: "Sync WeChat chat history into vault manifest. Pulls deltas from WeFlow API, identifies pending user-note refreshes, emits manifest. Runs at session start in parallel with calendar/email/screenpipe."
---

# WeChat Sync Adapter

Pulls fresh WeChat deltas from the WeFlow local HTTP API, identifies which `user.*.md` notes have unprocessed new content, and emits a manifest of vault note updates.

## Architecture

Two-stage system, coordinated through state files in `~/Documents/WechatHistory/_extracted/`:

| Stage | What | When |
|-------|------|------|
| **Pull** (`_weflow_pull.py`) | Fetch deltas from WeFlow → write `_extracted/*.txt` + update `_weflow_state.json` | Every 6h via `com.dendron.weflow-sync.plist` + every session start (this skill) |
| **Note refresh** | Read new messages from extracts → rewrite `## Recent (synced …)` in `user.*.md` | Daily 5am via `com.dendron.weflow-notes.plist` (subagent fanout) + every session start (this skill, capped) |

Coordination is through `_weflow_state.json` (per-talker `last_create_time`) and `_weflow_note_state.json` (per-talker `last_note_update_ts`, `messages_at_last_note`). A chat needs note refresh iff `last_create_time > last_note_update_ts` and `messages_now - messages_at_last_note >= min_msgs`. The session-start path processes the top N most-active pending chats inline; the daily cron mops up the rest.

## When to Use

- **Session start** (called by `/sync` router in parallel with calendar/email/screenpipe) — pull deltas + process top N pending notes
- **Manual** (`/sync wechat`) — same flow, no cap on processed notes
- **`/sync wechat --dry-run`** — pull + identify pending, but no manifest emission

## Prerequisites

- WeChat desktop client signed in (account `wxid_w9lx96qu5st022_85bc`)
- `WeFlow.app` running with HTTP API enabled (port 5031)
- Plaintext token at `~/.config/weflow/token` (mode 600). If absent or stale, the pull script exits with `ERROR: no WeFlow token`.

If the pull fails (WeFlow not running, token rejected, etc.), the skill emits an empty manifest and surfaces the error in the delta briefing rather than blocking session start.

## Process

### 1. Pull Deltas

```bash
python3 ~/Documents/WechatHistory/_weflow_pull.py --silent-when-idle
```

Cheap idempotent call. If the 6h cron ran recently and no chat has new activity, returns `[SILENT]` in <1s. Otherwise pulls deltas (typically <1 min for active days). The `--silent-when-idle` flag suppresses output when nothing changed, keeping cron logs clean.

Failure modes:
- `WeFlow not running` (HTTP 502 / connection refused) → log warning, skip remaining steps, emit empty manifest with `error` field
- `Unauthorized` → token expired; surface "Reset WeFlow token (Settings → HTTP API), mirror to ~/.config/weflow/token", emit empty manifest
- `Another _weflow_pull.py is already running` → cron is mid-run; skip pull but continue to step 2 (extracts may already be fresh enough)

### 2. Identify Pending Note Refreshes

```bash
python3 notes/.scripts/dispatch_note_updates.py --dry-run --min-msgs 5
```

Prints (to stderr) the count and a JSON dump of the work list. The skill reads the JSON to get the candidate chats. Each entry has:

```json
{
  "talker": "wxid_xxx",
  "display": "Per Greisen",
  "extract_path": "/Users/A.Y/Documents/WechatHistory/_extracted/Per Greisen.txt",
  "type": "1-on-1",
  "messages_now": 312,
  "messages_at_last_note": 265,
  "new_since_note": 47,
  "last_msg_ts": 1714329600,
  "last_note_ts": 1713984000,
  "first_note_pass": false
}
```

The script orders chats by `new_since_note` descending. Higher = more new messages = higher priority.

If `total_candidates == 0`: emit empty manifest, surface `[SILENT]`, return. This is the steady-state case after the daily cron has run.

### 3. Cap Per-Session Work

Session-start mode caps inline processing at `WECHAT_SYNC_SESSION_CAP` (default **8** chats), to bound session-start latency.

`/sync wechat` (manual mode) sets cap to ∞ (process all pending).

`/sync wechat --dry-run` skips processing entirely; manifest contains only metadata.

Skipped chats remain pending and will be picked up by the next session or the 5am cron.

### 4. Match Chats to Vault Notes

Load `.cache/sync-state/vault-index.json`. For each capped pending chat:

1. Try slug match: chat's slug (from filename, e.g. `Per Greisen.txt` → `per-greisen`) → `user.per-greisen.md`
2. Try Chinese-name fuzzy match against vault notes' `title` field for non-English chats
3. If no match found and `new_since_note >= 20`: emit a `create_note` manifest entry (suggested path `user.<slug>.md`, confidence 0.7 — vault-updater will flag for review)
4. If no match and `new_since_note < 20`: skip (don't auto-create for thin chats)

### 5. Read New Messages and Draft Section Update

For each matched chat:

1. **Read the matched user.*.md FIRST.** Grep for an existing `## Recent` heading. The convention used by the daily cron is `## Recent (synced YYYY-MM-DD via WeFlow)`. Capture the exact heading line — vault-updater uses literal heading matching, so the `section` field must match byte-for-byte. If no heading found, the chat is first-pass and a new section will be created.
2. Read the extract `.txt` file from `extract_path`
3. Slice the trailing `new_since_note` messages (or last 50, whichever smaller — to keep prompts bounded)
4. Identify topic/relationship signals: shared projects, decisions made, plans, sentiment shifts
5. Draft 3–8 dated bullet points. Format:

```markdown
## Recent (synced 2026-04-28 via WeFlow)

- 2026-04-25: Per shared updated AlphaFold3 binder ranking; he flagged top 3 designs for ordering
- 2026-04-22: Discussed shifting tau-binder Round 2 to single-domain antibodies; Per to circulate cost estimate
- 2026-04-19: Catch-up on Janelia visit; Per met with Wyss-Coray briefly, no concrete follow-up
```

Bullet style: `YYYY-MM-DD: short factual statement (sender's perspective if relevant)`. No verbose paraphrase, no quoted strings of Chinese, no emoji-loaded text dumps.

**No em-dashes** (per vault preference `feedback_no_em_dash`). Use colons or semicolons in their place. This applies to bullet text and any prose. Apply the writing-voice skill's terse register.

### 6. Emit Manifest Entries

For each processed chat:

```json
{
  "note": "user.per-greisen.md",
  "action": "rewrite_section",
  "section": "## Recent (synced 2026-04-27 via WeFlow)",
  "content": "## Recent (synced 2026-04-28 via WeFlow)\n\n- 2026-04-25 — Per shared...\n- ...\n",
  "confidence": 0.9,
  "evidence": [
    { "type": "wechat", "subject": "Per Greisen", "date": "2026-04-25" },
    { "type": "wechat", "subject": "Per Greisen", "date": "2026-04-22" }
  ]
}
```

Important: the `section` field is the EXACT existing heading line read from the user.*.md note in step 5.1. Vault-updater matches literally and replaces from the heading line up to the next `##` heading with `content`. Because `content` starts with the new heading line (today's date), the date in the heading rolls forward. If no existing `## Recent` heading was found, set `section` to the new heading text — vault-updater's "heading doesn't exist" path inserts the section at end (before `## Chat History` / `## Stats` if present).

For `create_note` entries:

```json
{
  "note": null,
  "action": "create_note",
  "suggested_path": "user.zhang-wei.md",
  "frontmatter": {
    "title": "Zhang Wei",
    "desc": "WeChat contact, ${context_one_liner}"
  },
  "content": "## Background\n\n${profile_paragraph}\n\n## Recent (synced 2026-04-28)\n\n- ...\n",
  "confidence": 0.7,
  "evidence": [{ "type": "wechat", "subject": "Zhang Wei", "date": "2026-04-25" }]
}
```

### 7. Save Manifest

Write to `.cache/sync-state/wechat-manifest-<UTC-timestamp>.json` with shape:

```json
{
  "source": "wechat",
  "generated_at": "2026-04-28T21:42:00Z",
  "stats": {
    "pull_mode": "merge",
    "pull_appended_msgs": 47,
    "pull_skipped_unchanged": 1042,
    "candidates_total": 12,
    "processed_inline": 8,
    "deferred_to_cron": 4,
    "weflow_error": null
  },
  "changes": [ ... ]
}
```

### 8. Mark Processed

After the manifest is written (and before vault-updater runs), update `_weflow_note_state.json` for the inline-processed talkers so the next session and the 5am cron skip them:

```python
note_state[wxid] = {
    "last_note_update_ts": sync_state[wxid]["last_create_time"],
    "messages_at_last_note": sync_state[wxid]["messages"],
    "last_action": "rewrite_section",  # or "create_note"
    "noted_at": datetime.now(timezone.utc).isoformat(),
}
```

If the vault-updater later fails to apply a particular change, the next session will see no diff (state already advanced) — that's acceptable; manual `/sync wechat` can force re-process.

### 9. Output

Print to stdout:

```
WeChat sync: pulled 47 new msgs from 3 chats. 12 candidates, processed 8 inline, 4 deferred.
Manifest: notes/.cache/sync-state/wechat-manifest-2026-04-28T214200Z.json
```

If pull failed but identification still succeeded:
```
WeChat sync: pull failed (WeFlow not running). Using cached extracts. 4 candidates, processed 4 inline.
```

If everything is idle:
```
[SILENT]
```

## Configuration

Environment overrides:
- `WECHAT_SYNC_SESSION_CAP` — max chats processed inline at session start (default 8)
- `WECHAT_SYNC_MIN_MSGS` — min new messages to consider for note refresh (default 5)
- `WECHAT_SYNC_SKIP_PULL=1` — skip the pull step (e.g. when cron just ran and you want pure note refresh)

## Related Files

- Pull script: `~/Documents/WechatHistory/_weflow_pull.py`
- Dispatch script: `notes/.scripts/dispatch_note_updates.py`
- State (sync): `~/Documents/WechatHistory/_extracted/_weflow_state.json`
- State (notes): `~/Documents/WechatHistory/_extracted/_weflow_note_state.json`
- Last-run summary: `~/Documents/WechatHistory/_extracted/_weflow_lastrun.json`
- Vault doc: `notes/tool.weflow.md`
- Cron logs: `notes/.cache/weflow-cron.log`, `notes/.cache/weflow-notes-cron.log`

## Output

The manifest JSON file path, printed to stdout. Vault-updater consumes the manifest next.
