#!/usr/bin/env bash
# tick_lock.sh — at-most-one execution via flock. Borrowed from
# Hermes-Agent's cron/.tick.lock pattern.
#
#   tick_lock.sh /tmp/cc-sketchybar.lock 30 -- screenpipe-restart
#
# Args:
#   $1  lockfile path
#   $2  timeout in seconds (0 = nonblocking, fail fast if locked)
#   --  separator (optional)
#   $@  command to run
#
# If macOS lacks `flock`, fall back to `mkdir`-based locking with cleanup.

set -uo pipefail

if [[ $# -lt 3 ]]; then
    echo "usage: tick_lock.sh <lockfile> <timeout-sec> -- <cmd> [args...]" >&2
    exit 64
fi

lockfile=$1
timeout=$2
shift 2
[[ "${1:-}" == "--" ]] && shift

if command -v flock >/dev/null 2>&1; then
    exec flock --timeout="$timeout" "$lockfile" -c "$(printf ' %q' "$@")"
fi

# macOS fallback: directory-based lock (atomic mkdir).
lockdir="${lockfile%.lock}.lockdir"
deadline=$(( $(date +%s) + timeout ))
while ! mkdir "$lockdir" 2>/dev/null; do
    if (( $(date +%s) >= deadline )); then
        echo "tick_lock: timed out after ${timeout}s waiting on $lockdir" >&2
        exit 1
    fi
    sleep 1
done
trap 'rmdir "$lockdir" 2>/dev/null' EXIT INT TERM
"$@"
