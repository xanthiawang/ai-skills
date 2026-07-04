---
name: session-sync
description: "Sync important Claude Code and Codex transcript signals into vault manifests. Runs during /sync and daily sync."
---

# Agent Session Sync

Promotes high-signal Claude Code and Codex session transcript events into the
Dendron vault during sync. This makes capture audit-based instead of relying on
the live assistant to remember session-end reflection perfectly.

## When to Use

Called by the `/sync` router as source `agent-session`, and by the twice-daily
command-center sync. It should not be used for raw transcript dumps.

## What It Does

1. Updates the cross-session FTS index with `session_index.py update`.
2. Scans completed Claude Code sessions for this vault and Codex rollouts whose
   `cwd` is inside this vault.
3. Ignores sessions modified in the last 5 minutes so the current live turn is
   not processed mid-stream.
4. Applies deterministic, evidence-only heuristics for:
   - explicit "record/remember/update working memory" requests,
   - user corrections or preference changes,
   - decisions about agent/sync/memory/tool behavior,
   - notable touched files in the managed agent-skill or instruction files.
5. Writes a standard sync manifest at
   `.cache/sync-state/agent-session-manifest-<timestamp>.json`.
6. Updates `.cache/sync-state/session-sync-state.json` after a manifest is
   written so later syncs only consider new or changed session files.

## Command

```bash
python3 /Users/A.Y/programs/ai-skills/dendron/sync/session-sync/scripts/session_sync.py \
  --manifest ".cache/sync-state/agent-session-manifest-$(date -u +%Y-%m-%dT%H%M%SZ).json"
```

Use `--dry-run --json` to inspect candidates without writing a manifest or
advancing state.

## Routing

- Agent-system decisions, transcript-capture rules, sync behavior, and touched
  files under `~/programs/ai-skills` route to `tool.agent-session-capture.md`.
- Explicit carry-forward, remember, or working-memory requests append to
  `_working-memory.md` under `## Agent Session Capture`.
- Low-confidence or ambiguous findings stay in the manifest as flagged changes;
  the vault-updater surfaces them instead of silently treating them as facts.

## Safety

- Never summarize raw transcripts wholesale.
- Never infer decisions from assistant text alone.
- Never process arbitrary Codex rollouts outside this vault unless explicitly
  invoked with a different `--cwd-prefix`.
- Preserve source evidence in each manifest change: source type, session ID,
  timestamp, and snippet.
