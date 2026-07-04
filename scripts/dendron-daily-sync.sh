#!/bin/bash
# Twice-daily Dendron command-center sync via Claude Code.
# Pulls agent-session, Gmail, and Google Calendar signals, refreshes
# _working-memory.md and command-center.md, touches user.*.md for new
# interactions, commits + pushes. Wrapped with silent_wrap.sh so quiet runs
# leave no log noise / commit.

set -euo pipefail

VAULT="$HOME/Documents/Manual Library/Dendron/notes"
LOG="$VAULT/.cache/daily-sync-cron.log"
SILENT_WRAP="$HOME/programs/ai-skills/dendron/command-center/scripts/silent_wrap.sh"
JPR_INGEST="$VAULT/.scripts/jpr_ingest.sh"
SESSION_SYNC="$HOME/programs/ai-skills/dendron/sync/session-sync/scripts/session_sync.py"

echo "=== $(date) - Dendron daily sync ===" >> "$LOG"

# JPR ingest is deterministic and writes notes directly. Failures do not block
# the rest of sync.
if [ -x "$JPR_INGEST" ]; then
    echo "[daily-sync] running jpr_ingest" >> "$LOG"
    "$JPR_INGEST" >> "$LOG" 2>&1 || echo "[daily-sync] jpr_ingest exit=$?" >> "$LOG"
fi

# Agent-session sync emits a manifest. Claude applies it below through the
# normal vault-updater semantics so transcript capture uses the same path as
# other sources.
if [ -f "$SESSION_SYNC" ]; then
    echo "[daily-sync] running agent-session sync" >> "$LOG"
    python3 "$SESSION_SYNC" \
      --manifest "$VAULT/.cache/sync-state/agent-session-manifest-$(date -u +%Y-%m-%dT%H%M%SZ).json" \
      >> "$LOG" 2>&1 || echo "[daily-sync] agent-session sync exit=$?" >> "$LOG"
fi

cd "$VAULT"

"$SILENT_WRAP" -- claude --print --model opus \
  --allowedTools 'Bash,Read,Write,Edit,Glob,Grep,Skill,Agent,mcp__claude_ai_Gmail,mcp__claude_ai_Google_Calendar' \
  -- \
  "Run the dendron command-center session-start sync.

Steps:
1. Inspect the latest .cache/sync-state/agent-session-manifest-*.json from today. If changes is non-empty, apply it using the dendron/sync/vault-updater semantics. Do not dump raw transcripts; only apply the manifest's evidence-backed note changes.
2. Pull Gmail inbox state. Cross-check sent folder per feedback_email_sent_crosscheck before flagging anything as needs-reply.
3. Pull Google Calendar — today + next 7 days.
4. Refresh notes/_working-memory.md Calendar and Email sections with '(synced YYYY-MM-DD HH:MM)' headers, plus Agent Session status if an agent-session manifest was applied.
5. Update memory/command-center.md follow-ups based on new email/calendar/session signals (overdue, deadlines, stale threads, capture requests).
6. Refresh a clearly separated Needs Attention breakout in _working-memory.md and command-center.md when new actionable items are found. Use proactive_queue.py --limit 5, latest-sender Gmail items, upcoming Calendar deadlines/needsAction invites, and source-health blockers. Include only actionable items with concrete next actions; keep tracking-only/no-reply items out.
7. Touch any user.*.md notes for new interactions per feedback_people_notes.
8. If meaningful changes landed (not just timestamp bumps), commit as 'vault-sync: cron daily-sync $(date +%Y-%m-%d-%H%M)' and push to origin/main.

If nothing meaningful changed since last sync (no agent-session manifest changes, no new email worth tracking, no calendar deltas, no follow-up state changes, no Needs Attention changes), respond with exactly the single line [SILENT] and exit without writing, committing, or pushing." \
  >> "$LOG" 2>&1

echo "=== Done ===" >> "$LOG"
