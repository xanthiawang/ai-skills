---
name: sync
description: "Vault sync router — orchestrates source adapters and vault updater. Use: /sync [source] [--dry-run]"
---

# Vault Sync

Orchestrates the vault sync pipeline: dispatches source adapters, collects manifests,
invokes the vault-updater.

## Usage

- `/sync` or `/sync all` — run calendar + email + screenpipe + wechat + agent-session adapters in parallel, run JPR ingest, include a read-only file-intake summary, then updater
- `/sync calendar` — run only calendar adapter, then updater
- `/sync email` — run only email adapter, then updater
- `/sync screenpipe` — run only screenpipe adapter, then updater
- `/sync wechat` — run only wechat adapter (no per-session cap), then updater
- `/sync agent-session` or `/sync sessions` — scan new completed Claude Code/Codex transcripts for important capture-worthy signals, then updater
- `/sync jpr` — pull + transcribe any new Just Press Record audio (`notes/.scripts/jpr_ingest.sh`), writes to daily journal / meet notes directly, then commit
- `/sync superwhisper` — detect uncaptured meeting recordings, then updater
- `/sync <source> --dry-run` — generate manifest, print summary, don't apply

## Session-Start Mode

When invoked by the command center at session start:

1. **Prune old manifests**: Delete `*-manifest-*.json` files older than 7 days from `.cache/sync-state/`
2. **Rebuild vault index**: Run `python3 notes/.scripts/build_vault_index.py`, then `python3 notes/.scripts/rebuild_md_indexes.py` (idempotently appends any new person/project notes to the curated `_index.by-person.md` / `_index.by-project.md` so they don't drift; preserves the hand-curated sections)
3. **Wait for vault index**: Block until `.cache/sync-state/vault-index.json` exists and is fresh (built_at within last 60s)
4. **Run file-intake summary (read-only)**: Inventory recent `~/Downloads` and loose `~/Desktop` files so sync catches new filesystem clutter without moving anything:
   ```bash
   mkdir -p .cache/sync-state
   python3 /Users/A.Y/programs/ai-skills/file-organizer/scripts/file_intake_scan.py \
     --days 30 \
     --format json \
     --out .cache/sync-state/file-intake-$(date -u +%Y-%m-%dT%H%M%SZ).json
   python3 /Users/A.Y/programs/ai-skills/file-organizer/scripts/file_intake_scan.py \
     --days 30 \
     --format markdown \
     --max 20
   ```
   Surface only counts and the top high-signal candidates in the sync briefing. Do **not** move, rename, delete, or apply cleanup during `/sync` unless Albert explicitly asks for cleanup in the same turn. Broad cleanup remains the existing `fs_drift_scan.py` -> reviewed checklist -> `fs_drift_apply.py` workflow.
5. **Dispatch adapters in parallel** using the Agent tool:
   - Calendar sync agent (foreground — fast, ~5s)
   - Email sync agent (foreground — moderate, ~15s)
   - Screenpipe sync agent (background — slow, ~60s)
   - WeChat sync agent (background — moderate, ~10–30s; capped at `WECHAT_SYNC_SESSION_CAP=8` chats inline)
   - Agent-session sync agent (foreground — fast, ~2-10s):
     ```bash
     python3 /Users/A.Y/programs/ai-skills/dendron/sync/session-sync/scripts/session_sync.py \
       --manifest ".cache/sync-state/agent-session-manifest-$(date -u +%Y-%m-%dT%H%M%SZ).json"
     ```
     This scans completed Claude Code sessions for this vault and Codex rollouts whose `cwd` is inside this vault. It emits only evidence-backed, high-signal snippets: explicit capture requests, user corrections/preferences, decisions about agent/sync/memory behavior, and managed agent-skill or instruction file touches. It advances `.cache/sync-state/session-sync-state.json` after writing the manifest, so future syncs are incremental. If no signal is found, the manifest has `changes: []`.
   - **JPR ingest** (background — variable, seconds to minutes per recording; transcription via SuperWhisper):
     ```bash
     bash notes/.scripts/jpr_ingest.sh
     ```
     `jpr_ingest.sh` `brctl download`s the iCloud Just Press Record folder, waits for sync, transcribes each new `.m4a` (Super mode <5min → daily journal `## Voice Captures`; Meeting mode ≥5min → `meet.YYYY.MM.DD.md`), archives the source, and updates `.cache/sync-state/jpr-manifest.json`. **It writes vault notes directly — there is no manifest / vault-updater step for JPR.** After it finishes, `git add` the new/changed `meet.*.md` and `daily.journal.*.md` files. If a recording is still an iCloud placeholder at run time it is skipped and retried next run (this is the common reason a fresh recording isn't picked up immediately — iCloud upload from the phone can lag hours).
     If `jpr_ingest.sh` may run more than once concurrently it self-locks via `/tmp/jpr-lock.d`; a second invocation exits cleanly.
   - SuperWhisper recording ingest (background — fast scan ~2s, plus 5–30s per meeting to import):
     ```bash
     python3 notes/.scripts/superwhisper_sync.py --since $(date -v-30d +%Y-%m-%d) --manifest .cache/sync-state/superwhisper-manifest-$(date -u +%Y-%m-%dT%H%M%SZ).json
     ```
     If the manifest has uncaptured meetings (`changes[*].action == "create"`, `note_type == "meeting"`), **auto-import** them: for each, read the `source_path` `meta.json`, pull the `llmResult` body, write `meet.YYYY.MM.DD.md` (with a separator `## Meeting N — <title>` if multiple recordings collide on the same date), correct obvious Whisper mistranscriptions of known people inline (e.g. `Tony Curry` → `Tony Wyss-Coray`), and add Dendron frontmatter (id, title, desc, updated, created, date, attendees, topics, source: superwhisper, source_path). Mark the manifest change applied. Surface count in briefing: "SuperWhisper: imported N meeting recordings → meet.YYYY.MM.DD.md".
     Skip auto-import if the target meet note already has substantive content (>200 lines or `source != superwhisper`) — fall back to alert-only in that case so the human-written note isn't overwritten.

     **Speaker-attribution guard (mandatory).** SuperWhisper's LLM summary frequently hallucinates a name for the dominant unlabeled voice (real example 2026-05-14: it labeled Albert's own speech as "Yitong / 奕彤" in a Valhalla TDD call). On every import, run these two checks before trusting any "Interviewee / Host / Speaker N" name the LLM produced:

     1. **Screenpipe cross-check.** Query `.cache/cc-screenpipe-YYYY-MM-DD-HH.json` for every UTC hour overlapping `[meta.datetime, meta.datetime + meta.duration_ms]`. Look for any of these meeting-client apps in foreground: `zoom.us`, `Zoom`, `Google Chrome` window titles containing `meet.google.com` / `teams.microsoft.com` / `webex.com` / `tencent meeting` / `Lark` / `Feishu`, `FaceTime`, `WeChat` window title `Voice Call` or `Video Call`. If **none** are present, the recording was almost certainly a phone call captured via the laptop mic — meaning the dominant speaker is **Albert**, full stop. In that case, set `attendees: [user.albert-ying, "<counterparty unknown — phone, no screenpipe trace>"]`, swap any `**Speaker / Interviewee / Host / 主讲人:** <Name>` line in the body to `**Speaker:** Albert (LLM mislabel: "<original name>")`, and replace `<Name>'s …` body references with `Albert's …`.

     2. **Vault-name verification.** For every personal name the LLM summary attaches to a speaker (look for `**Interviewee:**`, `**Host:**`, `**Speaker N:**`, `**主讲人:**`, `**讲者:**`), match it against `_index.by-person.md` slugs + `user.*.md` `title:` fields (case-insensitive, also try Chinese name variants). If the name doesn't resolve **and** the screenpipe check above didn't already remap to Albert, set frontmatter `needs_human_review: true`, add a banner `> **NEEDS REVIEW.** SuperWhisper LLM named "<X>" as a speaker but the name does not resolve to any vault user. Verify before trusting attribution.`, and leave the body unchanged.

     If the recording is sensitive (mentions Stanford TT track, equity stakes, NIH study sections, salary, confidential client names from `feedback_*confidential*` rules), also set `confidential: true` and add the matching CONFIDENTIAL banner.
     Note: this scans SuperWhisper's *own* recordings folder. JPR recordings only show up here *after* `jpr_ingest.sh` has handed them to SuperWhisper, so a "0 uncaptured" result does not mean there are no un-ingested JPR `.m4a` files — those are handled by the JPR ingest step above, not here.
6. **Invoke vault-updater** as each manifest arrives:
   - After calendar manifest → vault-updater
   - After email manifest → vault-updater
   - After wechat manifest → vault-updater
   - After agent-session manifest → vault-updater
   - After screenpipe manifest → vault-updater (background notification)
   - JPR ingest produces no manifest — commit its note changes alongside the next vault-updater commit (or its own `daily-journal:` / `meet:` commit).
7. **Surface delta briefing** after each updater run — include any JPR-ingested recordings (meet notes created, voice captures appended) and a compact file-intake summary if the scan found candidates.
8. **Break out Needs Attention** on every manual `/sync` / `/sync all` result. After the source delta, add a separate `Needs Attention` section with the 3-7 highest-priority actionable items surfaced by the sync. Build it from the refreshed `_working-memory.md`, `proactive_queue.py --limit 5`, new Gmail latest-sender items, upcoming Calendar deadlines/`needsAction` invites, and source-health blockers. Each item must include the concrete next action and source. Keep tracking-only/no-reply items out of this section. If there is nothing actionable, say `Needs Attention: none found`.

## Single-Source Mode

When invoked as `/sync <source>`:

1. Rebuild vault index (if older than 1 hour)
2. Run the specified adapter
3. If not `--dry-run`: invoke vault-updater with the manifest
4. If `--dry-run`: print manifest summary (N changes, affected notes, confidence levels)

`/sync jpr` is the exception: it runs `bash notes/.scripts/jpr_ingest.sh` (no cap), which writes notes directly — there is no adapter/manifest/vault-updater step. After it finishes, `git add` + commit the new/changed `meet.*.md` / `daily.journal.*.md` and report which recordings were ingested.

File intake is included by default only for `/sync` and `/sync all`. For
source-specific sync (`/sync calendar`, `/sync email`, etc.), skip file-intake
unless Albert asks for it.

After source-specific syncs, include a `Needs Attention` breakout only for that
source unless Albert asked for a full command-center sweep.

## Adapter Dispatch

Each adapter is a separate skill invoked as a subagent:

| Source | Skill | Trigger |
|--------|-------|---------|
| Calendar | `dendron/sync/calendar-sync` | Session start (foreground) |
| Email | `dendron/sync/email-sync` | Session start (foreground) |
| Screenpipe | `dendron/sync/screenpipe-sync` | Session start (background) |
| WeChat | `dendron/sync/wechat-sync` | Session start (background, capped) — also has independent 6h pull cron + 5am notes cron |
| Agent sessions | `dendron/sync/session-sync` | Session start + daily-sync cron — emits transcript-capture manifest |
| JPR (Just Press Record audio) | `notes/.scripts/jpr_ingest.sh` → `jpr_post.py` | Session start (background) + daily-sync cron — writes notes directly, no manifest |
| SuperWhisper | `notes/.scripts/superwhisper_sync.py` | Session start (background) — scans SW's own recordings, not the JPR queue |
| File intake | `file-organizer/scripts/file_intake_scan.py` | Session start (foreground, read-only summary; no moves) |

## Vault Updater Dispatch

After each adapter produces a manifest:
1. Invoke `dendron/sync/vault-updater` skill as a subagent
2. Pass the manifest file path(s)
3. Collect the delta report
4. Surface to user: "Sync delta: Updated N notes from <source>. [details]"

## Error Handling

- If an adapter fails: log the error, skip that source, continue with others
- If file-intake scan fails: log the error, continue sync, and report "File intake scan failed: [error]. No files moved."
- Surface failures in the delta briefing: "Email sync failed: [error]. Using cached state."
- If vault-updater fails: log error, preserve manifest for retry on next session

## Manifest Pruning

At session start, before dispatching adapters:
```bash
find .cache/sync-state/ -name "*-manifest-*.json" -mtime +7 -delete
```
