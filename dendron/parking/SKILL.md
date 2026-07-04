---
name: parking
description: Park and restore Claude/Codex conversations. Triggers on "park this", "save this for later", "park the codex chat about X", "restore the Y chat", "reopen X", "go back to the previous chat about Z", "open the previous chat on Z". Spawns iTerm tabs in YOLO mode by default. Backed by tool.parked-convos.md + session_index.db FTS5 fallback.
---

# Parking — Claude + Codex Session Resume

Albert parks conversations to come back to later, and restores them by topic. The skill owns both ends so the parked-convos table stays accurate and a restore spawns a fully-configured iTerm tab without any copy-paste.

## When to invoke

**Park triggers** (user wants to set this conversation aside):
- "park this", "park this conversation"
- "save this for later", "close this thread"
- "I'll come back to this", "let me park"
- "park the codex chat/session about <topic>"

**Restore triggers** (user wants to reopen a past conversation):
- "restore the <topic> chat"
- "resume <topic>", "reopen <topic>"
- "go back to the previous chat about <topic>"
- "open the previous chat on <topic>"
- "open the codex session for <topic>"

## How to handle "park this"

1. Infer a kebab-case `slug` from the conversation topic. If ambiguous, ask Albert ("what slug — `viktoria-enrichment` or `april-genes`?").
2. Draft `notes` summarizing: what was decided, what's blocking, what to do on resume, and pointers to vault notes / project memory files. Keep it under 400 characters.
3. Run:
   ```bash
   python3 ~/programs/ai-skills/dendron/parking/scripts/park_save.py \
       --source claude --slug <slug> --notes "<draft>"
   ```
4. If the script exits non-zero, surface the error to Albert. Exit code 3 = stale session jsonl (refuse-to-park) — explain and ask whether to override.
5. If exit 0, echo the new row to Albert.

For Codex sessions (Albert was working in Codex separately): use `--source codex`. The script greps recent Codex rollouts for the slug. If exit code 4 (multiple candidates), surface the JSON, ask Albert to pick by recency/excerpt.

## How to handle "restore the X chat"

1. Run:
   ```bash
   python3 ~/programs/ai-skills/dendron/parking/scripts/park_restore.py "<query>"
   ```
2. Exit 0: tab spawned, confirm to Albert with the slug + session ID.
3. Exit 4: JSON list of candidates. Show Albert with slug, source, date, and excerpt; ask which one.
4. Exit 2: nothing matched. Tell Albert and offer to search session jsonls directly with grep.
5. `--safe` opt-out: if Albert says "restore safely" / "restore without yolo", add the flag.

## How to handle "audit the parking table"

Run:
```bash
python3 ~/programs/ai-skills/dendron/parking/scripts/park_audit.py
```

Surface the report. Walk Albert through fixes row by row.

## What this skill does NOT do

- Does not park automatically. Only triggered by Albert's explicit verb.
- Does not modify other vault notes (project memory files are written, but other notes are untouched).
- Does not write to Codex from inside a Claude session beyond reading rollout jsonls.
