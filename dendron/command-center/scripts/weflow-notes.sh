#!/bin/bash
# Daily WeChat note-update pass.
# 1. Build a work list of chats whose extracts have new content since their
#    user.*.md note was last touched.
# 2. If there's anything to do, claude --print headlessly dispatches subagents
#    to verify identity and update / create / skip per chat.
# 3. dispatch_note_updates.py persists per-chat last_note_update_ts so the
#    next run only sees fresh deltas.
#
# Wrapped with silent_wrap.sh so quiet days produce no log noise.

set -uo pipefail

VAULT="$HOME/Documents/Manual Library/Dendron/notes"
LOG="$VAULT/.cache/weflow-notes-cron.log"
SILENT_WRAP="$HOME/programs/ai-skills/dendron/command-center/scripts/silent_wrap.sh"
TICK_LOCK="$HOME/programs/ai-skills/dendron/command-center/scripts/tick_lock.sh"
WORKLIST="/tmp/weflow-notes-worklist.json"

cd "$VAULT"

echo "=== $(date) - Building work list ===" >> "$LOG"
python3 .scripts/dispatch_note_updates.py >> "$LOG" 2>&1
RC=$?

if [ ! -s "$WORKLIST" ]; then
    echo "[SILENT]"
    exit 0
fi

# Quick check: is the work list empty?
COUNT=$(python3 -c "import json; d=json.load(open('$WORKLIST')); print(d.get('total_candidates', 0))")
if [ "$COUNT" -eq 0 ]; then
    echo "[SILENT]"
    exit 0
fi

echo "=== $(date) - Dispatching claude for $COUNT chats ===" >> "$LOG"

# Single claude session: it reads the work list and dispatches its own subagents.
# Allowed tools cover everything subagents need: vault inspection, file edits,
# subagent dispatch via Agent.
#
# NOTE: claude's `--allowedTools <tools...>` is a variadic flag (commander.js).
# Passing the prompt as a trailing positional gets greedily consumed as another
# tool name, producing "Input must be provided either through stdin or as a
# prompt argument". Fix: pipe the prompt via stdin from a temp file.
PROMPT_FILE="/tmp/weflow-notes-prompt-$$.txt"
trap 'rm -f "$PROMPT_FILE"' EXIT

cat > "$PROMPT_FILE" <<EOF
Update Albert's Dendron user.*.md profile notes from the new WeChat content listed in $WORKLIST.

The work list is JSON: {generated_at, sync_lastrun, total_candidates, work: [{talker, display, extract_path, messages_now, new_since_note, first_note_pass, ...}, ...]}.

Process the chats by dispatching subagents in parallel. Split the work list into ~8 batches of similar total volume, dispatch one Agent per batch (subagent_type general-purpose), and have each subagent process its batch sequentially.

Per chat, each subagent must:
1. Grep the vault to find candidate user.*.md notes by display name (English + Chinese parts). Verify identity from the candidate's frontmatter + intro paragraph. If multiple plausible, pick the best match by content overlap. If no good match, decide create-or-skip.
2. Read the new portion of the extract. Last \`new_since_note\` lines of the file (or \`tail -n <new_since_note+5> <extract_path>\` if first_note_pass=false; for first_note_pass=true, skim the most-recent ~150 lines).
3. SKIP for: services / bots (微信ClawBot, 华住会, etc.), system-msgs only, ambiguous identity, low-signal trivia (<10 substantive new msgs).
4. UPDATE existing note: append (or prepend within an existing) '## Recent (synced YYYY-MM-DD via WeFlow)' section with 3-8 dated bullets capturing the most signal-rich threads, decisions, life events, plans. Newest first.
5. CREATE a new user.<slug>.md (style: user.hanna-liu.md) only if it's clearly a real person with substantive content (>30 meaningful msgs) and no existing match.

Constraints:
- Albert's voice rules: no em-dashes anywhere; for Chinese never use '不是X，而是Y' rhetorical inversion; brief.
- Do NOT touch anything in /Users/A.Y/Documents/WechatHistory/_extracted/. Those are source files.
- Do NOT modify _weflow_state.json or _weflow_lastrun.json. Sync owns those.

After all batches return, aggregate the results: per chat (talker, action, note_path, bullets_added). Write the aggregated results to /tmp/weflow-notes-results.json as a JSON array, then run:
  python3 -c "import sys; sys.path.insert(0, '.scripts'); import dispatch_note_updates as d; import json; d.mark_processed(json.load(open('/tmp/weflow-notes-results.json')))"

That marks the per-chat last_note_update_ts so the next daily run only sees fresh deltas.

Final output to stdout: a one-paragraph summary (chats updated, created, skipped) plus any high-signal threads worth flagging. If the entire work list ended up trivial (all skipped), reply with exactly the single line [SILENT] so cron suppresses noise.
EOF

"$TICK_LOCK" /tmp/cc-weflow-notes.lock 0 -- \
"$SILENT_WRAP" -- bash -c "claude --print --allowedTools 'Bash,Read,Edit,Write,Glob,Grep,Agent' < '$PROMPT_FILE'" \
    >> "$LOG" 2>&1

echo "=== $(date) - Done ===" >> "$LOG"
