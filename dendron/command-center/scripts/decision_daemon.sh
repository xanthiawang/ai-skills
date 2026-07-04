#!/bin/bash
# Dynamic command-center decision packet refresher.
# Runs under launchd, writes/updates the decision-packet cache, and notifies
# Albert only when the packet changed enough to require review.

set -euo pipefail

HOME_DIR="$HOME"
VAULT="$HOME_DIR/Documents/Manual Library/Dendron/notes"
PACKETS="$HOME_DIR/programs/ai-skills/dendron/command-center/scripts/decision_packets.py"
PREPARED_ACTIONS="$HOME_DIR/programs/ai-skills/dendron/command-center/scripts/prepared_actions.py"
PREP_WORKER="$HOME_DIR/programs/ai-skills/dendron/command-center/scripts/prep_worker.py"
TICK_LOCK="$HOME_DIR/programs/ai-skills/dendron/command-center/scripts/tick_lock.sh"
LOG="$VAULT/.cache/command-center-decisions-cron.log"
ERR="$VAULT/.cache/command-center-decisions-launchd-err.log"
TMP="$(mktemp /tmp/command-center-decisions.XXXXXX)"
PREP_TMP="$(mktemp /tmp/command-center-prepared.XXXXXX)"
NOTIFY_MODE="${COMMAND_CENTER_NOTIFY_MODE:-notification}"
POPUP_TIMEOUT="${COMMAND_CENTER_POPUP_TIMEOUT:-20}"
PREP_WORKER_WAIT_SECONDS="${COMMAND_CENTER_PREP_WORKER_WAIT_SECONDS:-300}"

cleanup() {
  rm -f "$TMP" "$PREP_TMP"
}
trap cleanup EXIT

mkdir -p "$VAULT/.cache"
echo "=== $(date) - command-center decisions ===" >> "$LOG"

if ! "$TICK_LOCK" /tmp/command-center-decisions.lock 0 -- python3 "$PACKETS" --silent-if-unchanged --limit 8 > "$TMP" 2>> "$ERR"; then
  echo "ERROR: decision packet refresh failed at $(date)" >> "$LOG"
  /usr/bin/osascript \
    -e 'display notification "Decision packet refresh failed. Check command-center-decisions logs." with title "Command Center"' \
    >/dev/null 2>&1 || true
  exit 1
fi

if python3 "$PREPARED_ACTIONS" --json > "$PREP_TMP" 2>> "$ERR"; then
  echo "prepared-actions: refreshed" >> "$LOG"
else
  echo "WARN: prepared action refresh failed at $(date)" >> "$LOG"
  echo '{"notification_events":[]}' > "$PREP_TMP"
fi

if python3 "$PREP_WORKER" --limit 1 --wait-seconds "$PREP_WORKER_WAIT_SECONDS" --quiet 2>> "$ERR"; then
  echo "prep-worker: ticked" >> "$LOG"
  if python3 "$PREPARED_ACTIONS" --json > "$PREP_TMP" 2>> "$ERR"; then
    echo "prepared-actions: refreshed after prep-worker" >> "$LOG"
  else
    echo "WARN: prepared action post-worker refresh failed at $(date)" >> "$LOG"
  fi
else
  echo "WARN: prep worker tick failed at $(date)" >> "$LOG"
fi

PREP_EVENT_COUNT="$(
  python3 - "$PREP_TMP" <<'PY'
import json
import sys
from pathlib import Path

try:
    packet = json.loads(Path(sys.argv[1]).read_text())
except Exception:
    packet = {}
print(len(packet.get("notification_events") or []))
PY
)"

if grep -qx '\[SILENT\]' "$TMP" && [[ "$PREP_EVENT_COUNT" = "0" ]]; then
  echo "[SILENT]" >> "$LOG"
  exit 0
fi

if grep -qx '\[SILENT\]' "$TMP"; then
  echo "prepared-action event: $PREP_EVENT_COUNT" >> "$LOG"
else
  cat "$TMP" >> "$LOG"
fi

IFS=$'\t' read -r TITLE SUBTITLE MESSAGE < <(
  python3 - "$TMP" "$PREP_TMP" <<'PY'
import json
import sys
from pathlib import Path

packet_output = Path(sys.argv[1]).read_text().strip()
prep_packet = json.loads(Path(sys.argv[2]).read_text())
events = prep_packet.get("notification_events") or []
if packet_output == "[SILENT]" and events:
    event = events[0]
    title = "Command Center"
    status = str(event.get("status") or "update")
    subtitle = f"{len(events)} prepared action {status}"
    message = str(event.get("title") or event.get("message") or "Prepared action ready")[:120]
    print(title, subtitle, message, sep="\t")
    raise SystemExit

packet_path = Path.home() / "Documents/Manual Library/Dendron/notes/.cache/command-center/decision-packets.json"
packet = json.loads(packet_path.read_text())
items = packet.get("items", [])
status = packet.get("status", "needs_decision")
approval = packet.get("approval_required_count", 0)
first = items[0].get("title", "Review decision packet") if items else "Review decision packet"
title = "Command Center"
subtitle = f"{len(items)} queued / {approval} approval / {status}"
message = first[:120]
print(title, subtitle, message, sep="\t")
PY
)

if [[ "$NOTIFY_MODE" == "both" || "$NOTIFY_MODE" == "banner" || "$NOTIFY_MODE" == "notification" ]]; then
  /usr/bin/osascript \
    -e 'on run argv' \
    -e 'display notification (item 3 of argv) with title (item 1 of argv) subtitle (item 2 of argv) sound name "Glass"' \
    -e 'end run' \
    "$TITLE" "$SUBTITLE" "$MESSAGE" \
    >/dev/null 2>&1 || echo "WARN: notification banner failed" >> "$LOG"
fi

if [[ "$NOTIFY_MODE" == "both" || "$NOTIFY_MODE" == "alert" || "$NOTIFY_MODE" == "popup" ]]; then
  /usr/bin/osascript \
    -e 'on run argv' \
    -e 'set timeoutSeconds to (item 4 of argv) as integer' \
    -e 'display alert (item 1 of argv) message ((item 2 of argv) & return & return & (item 3 of argv)) buttons {"OK"} giving up after timeoutSeconds' \
    -e 'end run' \
    "$TITLE" "$SUBTITLE" "$MESSAGE" "$POPUP_TIMEOUT" \
    >/dev/null 2>&1 || echo "WARN: notification popup failed" >> "$LOG"
fi

echo "notified: $SUBTITLE / mode=$NOTIFY_MODE" >> "$LOG"
