#!/usr/bin/env bash
# Bland AI phone-call agent driver.
# Places real outbound calls with an AI voice agent, then pulls the transcript.
# See SKILL.md for usage, the task-script guide, and safety rules.
#
# Key resolution order: $BLAND_API_KEY env var, then $BLAND_KEY_FILE,
# then ~/.config/bland/api_key. The key is never stored in this repo.

set -euo pipefail

API_BASE="${BLAND_API_BASE:-https://api.bland.ai/v1}"
KEY_FILE="${BLAND_KEY_FILE:-$HOME/.config/bland/api_key}"
STATE_DIR="${BLAND_STATE_DIR:-$HOME/.config/bland}"
DEFAULT_VOICE="${BLAND_DEFAULT_VOICE:-60974bf8-151e-44e2-812e-4dc958aac5f3}"  # "Esteban"; Albert clone = fe8bd7bf-4bed-474e-9a4b-7faed121bc96

err() { echo "error: $*" >&2; exit 1; }

get_key() {
  if [ -n "${BLAND_API_KEY:-}" ]; then printf '%s' "$BLAND_API_KEY"; return; fi
  [ -f "$KEY_FILE" ] || err "no API key: set \$BLAND_API_KEY or write $KEY_FILE"
  tr -d '\r\n' < "$KEY_FILE"
}
KEY="$(get_key)"
mkdir -p "$STATE_DIR"

# List the voices you own (cloned / custom), id<TAB>name.
cmd_voices() {
  curl -fsS -H "authorization: $KEY" "$API_BASE/voices" | python3 -c '
import sys,json
d=json.load(sys.stdin)
own=[v for v in d.get("voices",[]) if v.get("user_id")]
for v in own: print(v["id"], "\t", v.get("name"))
sys.stderr.write("\n(%d owned, %d total)\n" % (len(own), len(d.get("voices",[]))))'
}

# Clone a voice from an audio sample. Auto-converts to mp3 via ffmpeg.
cmd_clone() {
  local name="${1:?usage: clone <name> <audio_file>}" audio="${2:?usage: clone <name> <audio_file>}"
  [ -f "$audio" ] || err "audio file not found: $audio"
  local mp3="$audio"
  case "$audio" in
    *.mp3) ;;
    *) mp3="${audio%.*}.mp3"
       command -v ffmpeg >/dev/null || err "ffmpeg needed to convert $audio to mp3"
       ffmpeg -y -i "$audio" -codec:a libmp3lame -q:a 2 "$mp3" >/dev/null 2>&1 || err "ffmpeg convert failed"
       echo "converted -> $mp3" >&2 ;;
  esac
  curl -fsS -X POST "$API_BASE/voices/clone" \
    -H "authorization: $KEY" \
    -F "name=$name" \
    -F "audio_samples.items=@$mp3" | python3 -m json.tool
}

# Place a call. task may be an inline string or a path to a script file.
cmd_call() {
  local phone="${1:?usage: call <e164_phone> <task|file> [voice_id]}"
  local task="${2:?usage: call <e164_phone> <task|file> [voice_id]}"
  local voice="${3:-$DEFAULT_VOICE}"
  [ -f "$task" ] && task="$(cat "$task")"
  local body resp call_id
  body="$(python3 - "$phone" "$task" "$voice" <<'PY'
import json,sys
phone,task,voice=sys.argv[1],sys.argv[2],sys.argv[3]
print(json.dumps({
  "phone_number": phone,
  "task": task,
  "voice": voice,
  "wait_for_greeting": True,
  "record": True,
  "model": "base",
  "answered_by_enabled": True,
  "voicemail_action": "hangup",
  "max_duration": 15,
}))
PY
)"
  resp="$(curl -fsS -X POST "$API_BASE/calls" -H "authorization: $KEY" \
            -H "Content-Type: application/json" -d "$body")"
  echo "$resp" | python3 -m json.tool
  call_id="$(echo "$resp" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("call_id",""))')"
  if [ -n "$call_id" ]; then echo "$call_id" > "$STATE_DIR/last_call_id"; echo "saved call_id: $call_id" >&2; fi
}

_fetch() { curl -fsS -H "authorization: $KEY" "$API_BASE/calls/${1:?}"; }

# Show status + transcript for a call (defaults to the last placed call).
cmd_status() {
  local id="${1:-$(cat "$STATE_DIR/last_call_id" 2>/dev/null || true)}"
  [ -n "$id" ] || err "no call_id (pass one or place a call first)"
  _fetch "$id" | python3 -c '
import sys,json
d=json.load(sys.stdin)
for k in ("status","completed","queue_status","answered_by","call_length","error_message"):
    if d.get(k) is not None: print("%s: %s" % (k, d[k]))
t=d.get("concatenated_transcript")
if not t and isinstance(d.get("transcripts"),list):
    t="\n".join("%s: %s" % (x.get("user","?"), x.get("text","")) for x in d["transcripts"])
if t: print("--- transcript ---\n"+t)'
}

# Poll until the call completes, then print the transcript.
cmd_watch() {
  local id="${1:-$(cat "$STATE_DIR/last_call_id" 2>/dev/null || true)}"
  [ -n "$id" ] || err "no call_id"
  local i
  for i in $(seq 1 90); do
    if [ "$(_fetch "$id" | python3 -c 'import sys,json;print(1 if json.load(sys.stdin).get("completed") else 0)')" = "1" ]; then
      cmd_status "$id"; return
    fi
    sleep 10
  done
  echo "timed out; check later: $0 status $id" >&2
}

usage() {
cat <<EOF
Bland phone-call agent. Key from \$BLAND_API_KEY or $KEY_FILE.

  $0 voices                                  list your owned/cloned voices
  $0 clone  <name> <audio>                   clone a voice (auto mp3 convert)
  $0 call   <e164_phone> <task|file> [voice] place a call (default voice: Albert clone)
  $0 status [call_id]                        status + transcript (default: last call)
  $0 watch  [call_id]                        poll to completion, print transcript

Examples:
  $0 call +18007435000 ./tasks/pge.txt
  $0 watch
EOF
}

case "${1:-}" in
  voices) shift; cmd_voices "$@";;
  clone)  shift; cmd_clone  "$@";;
  call)   shift; cmd_call   "$@";;
  status) shift; cmd_status "$@";;
  watch)  shift; cmd_watch  "$@";;
  *) usage;;
esac
