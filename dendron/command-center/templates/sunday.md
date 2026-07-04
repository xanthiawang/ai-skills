# Sunday Planning — Live State

_Generated ${NOW_UTC} · ${TODAY}_

## This week's calendar (next 7 days)
!`grep -A 60 '^## Upcoming Week' "${VAULT_DIR}/_working-memory.md" 2>/dev/null | head -80`

## Command-center health
!`python3 "${SKILL_DIR}/scripts/healthcheck.py" --quiet 2>/dev/null || true`

## Proactive decision queue
!`python3 "${SKILL_DIR}/scripts/proactive_queue.py" --limit 8 2>/dev/null | head -45 || true`

## Active projects (status snapshot)
!`grep -A 30 '^## Active Tasks' "${VAULT_DIR}/_working-memory.md" 2>/dev/null | head -40`

## Inbox active items (Needs Action HIGH)
!`grep -A 15 '^### Needs Action (HIGH)' "${VAULT_DIR}/_working-memory.md" 2>/dev/null | head -20`

## Currently parked threads
!`awk '/^## Active$/,/^## /{print}' "${VAULT_DIR}/tool.claude-parked-convos.md" 2>/dev/null | grep -E '^\| 2026' | head -10`

## Stale follow-ups (>7 days)
!`grep -B 1 -A 5 '^### High Priority' "${MEMORY_DIR}/command-center.md" 2>/dev/null | head -25`

## Memory hygiene + cold skills
!`python3 "${SKILL_DIR}/scripts/memory_gc.py" 2>/dev/null | head -25`

!`test -f "${MEMORY_DIR}/skill-insights.json" && python3 -c "import json; d=json.load(open('${MEMORY_DIR}/skill-insights.json')); cold=d.get('cold_30d',{}); print('## Cold skills (>30d unused)'); [print(f'  {k}: {v} days') for k,v in list(cold.items())[:5]] if cold else print('  (none — all skills in active rotation)')"`

## Recurring Sunday events

| Time (PT) | Event |
|---|---|
| 08:00 | Norn Longevity Nexus (recurring) |
| 23:00 | Compound weekly 康胖周会 🧪🧬 |

## Suggested workflow

1. Triage HIGH inbox items first
2. Review parked threads — any blockers resolved?
3. Run `python3 "${SKILL_DIR}/scripts/skill_insights.py" --since 7 --print` for the week
4. Lock down Mon-Wed deliverables before they become urgent
