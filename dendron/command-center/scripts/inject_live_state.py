#!/usr/bin/env python3
"""
Inject live state for command-center skill at session start.

Borrowed from Hermes-Agent's skill_preprocessing.py: expands `${TOKEN}` references
and `!`shell snippet`` inline-shell snippets in a template, returning a single
markdown blob the agent can read in one go instead of running 5+ Bash calls.

Usage:
    python3 inject_live_state.py                    # write to stdout
    python3 inject_live_state.py --template path    # use custom template
    python3 inject_live_state.py --output /tmp/x.md # write to file

Tokens supported:
    ${VAULT_DIR}    Dendron vault path
    ${SKILL_DIR}    Command-center skill directory
    ${SESSION_ID}   Current Claude Code session id (latest jsonl mtime)
    ${SESSION_DIR}  ~/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron-notes/
    ${TODAY}        YYYY-MM-DD in local TZ
    ${NOW_UTC}      ISO 8601 UTC timestamp
    ${MEMORY_DIR}   ~/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron/memory

Inline shell:
    !`cmd`          Substituted with stdout (4KB cap, 30s timeout, cwd=VAULT_DIR)

Without a template path, prints a default state-injection bundle covering
health, proactive queue, sync status, last screenpipe cache, recent jsonl,
and pending feedback memos.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

VAULT_DIR = Path("/Users/A.Y/Documents/Manual Library/Dendron/notes")
SKILL_DIR = Path(__file__).resolve().parent.parent
MEMORY_DIR = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron/memory"
)
SESSION_DIR = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron-notes"
)

TOKEN_RE = re.compile(
    r"\$\{(VAULT_DIR|SKILL_DIR|SESSION_ID|SESSION_DIR|TODAY|NOW_UTC|MEMORY_DIR)\}"
)
INLINE_SHELL_RE = re.compile(r"!`([^`\n]+)`")
INLINE_MAX_OUTPUT = 4000
INLINE_TIMEOUT = 30


def latest_session_id() -> str:
    if not SESSION_DIR.exists():
        return "unknown"
    files = sorted(
        SESSION_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not files:
        return "unknown"
    return files[0].stem


def substitute_tokens(content: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    values = {
        "VAULT_DIR": str(VAULT_DIR),
        "SKILL_DIR": str(SKILL_DIR),
        "SESSION_ID": latest_session_id(),
        "SESSION_DIR": str(SESSION_DIR),
        "TODAY": today,
        "NOW_UTC": now_utc,
        "MEMORY_DIR": str(MEMORY_DIR),
    }
    return TOKEN_RE.sub(lambda m: values.get(m.group(1), m.group(0)), content)


def run_inline_shell(cmd: str) -> str:
    try:
        result = subprocess.run(
            ["bash", "-c", cmd],
            cwd=str(VAULT_DIR),
            capture_output=True,
            text=True,
            timeout=INLINE_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"[inline-shell timeout after {INLINE_TIMEOUT}s: {cmd}]"
    except Exception as exc:
        return f"[inline-shell error: {exc}]"
    out = (result.stdout or result.stderr or "").rstrip("\n")
    if len(out) > INLINE_MAX_OUTPUT:
        out = out[:INLINE_MAX_OUTPUT] + "...[truncated]"
    return out


def expand_inline_shell(content: str) -> str:
    if "!`" not in content:
        return content
    return INLINE_SHELL_RE.sub(lambda m: run_inline_shell(m.group(1).strip()), content)


def expand(content: str) -> str:
    return expand_inline_shell(substitute_tokens(content))


DEFAULT_TEMPLATE = """\
# Command Center Live State (auto-injected)

_Generated ${NOW_UTC} for session `${SESSION_ID}` — local date ${TODAY}._

## Paths
- Vault: ${VAULT_DIR}
- Memory: ${MEMORY_DIR}
- Skill: ${SKILL_DIR}

## Command Center Health
!`python3 "${SKILL_DIR}/scripts/healthcheck.py" --quiet 2>/dev/null || true`

## Proactive Decision Queue
!`python3 "${SKILL_DIR}/scripts/proactive_queue.py" --limit 5 2>/dev/null | head -30 || true`

## Sync Cache Freshness
!`ls -1t "${VAULT_DIR}/.cache/sync-state/"*.json 2>/dev/null | head -10 | sed 's|.*/||' || echo '(no sync-state dir)'`

## Latest Screenpipe Cache
!`ls -1t "${VAULT_DIR}/.cache/cc-screenpipe-"*.json 2>/dev/null | head -3 | sed 's|.*/||' || echo '(no cache)'`

## Most Recent Daily Journal
!`ls -1t "${VAULT_DIR}/daily.journal."*.md 2>/dev/null | head -1 | sed 's|.*/||'`

## Recent Jsonl Sessions (top 5 by mtime)
!`ls -1t "${SESSION_DIR}/"*.jsonl 2>/dev/null | head -5 | xargs -I{} basename {} .jsonl`

## Pending Feedback Memos (last 10 modified)
!`ls -1t "${MEMORY_DIR}/feedback_"*.md 2>/dev/null | head -10 | sed 's|.*/||'`

## Working Memory Sync Header
!`grep -A 8 '^## Sync Status' "${VAULT_DIR}/_working-memory.md" 2>/dev/null | head -10 || echo '(no sync header)'`

## Parked Conversations Top
!`grep -A 1 '^|' "${VAULT_DIR}/tool.claude-parked-convos.md" 2>/dev/null | head -20 || echo '(no parked convos file)'`

## Skill Insights Snapshot (most-fired skills, last 7 days)
!`test -f "${MEMORY_DIR}/skill-insights.json" && python3 -c "import json; d=json.load(open('${MEMORY_DIR}/skill-insights.json')); [print(f'  {k}: {v}') for k,v in sorted(d.get('last_7d',{}).items(), key=lambda x:-x[1])[:8]]" || echo '(skill_insights.py not yet run)'`

## Cold Skills (>30 days unused — candidates for review or removal)
!`test -f "${MEMORY_DIR}/skill-insights.json" && python3 -c "import json; d=json.load(open('${MEMORY_DIR}/skill-insights.json')); cold=d.get('cold_30d',{}); [print(f'  {k}: {v} days') for k,v in list(cold.items())[:8]] if cold else print('  (none — all skills used recently)')" || echo '(run skill_insights.py first)'`

## Skill Changes Since Last Session
!`python3 "${SKILL_DIR}/scripts/skill_diff.py" --since-session 2>/dev/null | tail -n +3 | head -10 || echo '  (no snapshot yet — run skill_diff.py --snapshot)'`

## Recent Skill Commits (last 7 days)
!`python3 "${SKILL_DIR}/scripts/skill_diff.py" --since-days 7 2>/dev/null | tail -n +3 | head -15 || echo '  (skill_diff.py failed)'`
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--template", help="Path to custom template file")
    ap.add_argument("--output", help="Write to file instead of stdout")
    args = ap.parse_args()

    if args.template:
        content = Path(args.template).read_text()
    else:
        content = DEFAULT_TEMPLATE

    expanded = expand(content)

    if args.output:
        Path(args.output).write_text(expanded)
        print(f"Wrote {len(expanded)} chars to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(expanded)
    return 0


if __name__ == "__main__":
    sys.exit(main())
