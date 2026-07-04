#!/usr/bin/env bash
# silent_wrap.sh — wrap a command. If its output's last non-blank line is
# `[SILENT]`, drop the entire output (exit 0). Otherwise print as usual.
# Borrowed from Hermes-Agent's cron `[SILENT]` convention.
#
# Use for cron jobs that should only emit output when something happened:
#
#   silent_wrap.sh -- claude "/dendron-screenpipe-journal" \
#                       "If nothing notable happened in the last 24h, reply with [SILENT]."
#
# Exit code mirrors the wrapped command unless we suppress output, in which
# case we still exit with the wrapped command's code (so cron doesn't think
# the job failed silently).

set -uo pipefail

# Skip optional `--` separator.
[[ "${1:-}" == "--" ]] && shift

if [[ $# -eq 0 ]]; then
    echo "usage: silent_wrap.sh -- <cmd> [args...]" >&2
    exit 64
fi

# Capture stdout+stderr together so `[SILENT]` works even if emitted on stderr.
output=$("$@" 2>&1)
rc=$?

# Strip trailing blank lines, look at the last remaining one.
last_line=$(printf '%s' "$output" | awk 'NF{l=$0} END{print l}')

if [[ "$last_line" == "[SILENT]" ]]; then
    exit "$rc"
fi

printf '%s\n' "$output"
exit "$rc"
