# Weekly Review — Live State

_Generated ${NOW_UTC} · ${TODAY}_

## Skill insights (last 7 days)
!`python3 "${SKILL_DIR}/scripts/skill_insights.py" --since 7 --print 2>/dev/null | head -40`

## Command-center health
!`python3 "${SKILL_DIR}/scripts/healthcheck.py" --quiet 2>/dev/null || true`

## Proactive decision queue
!`python3 "${SKILL_DIR}/scripts/proactive_queue.py" --limit 8 2>/dev/null | head -45 || true`

## Vault commits this week
!`cd "${VAULT_DIR}" && git log --since='7 days ago' --pretty=format:'  %ad  %s' --date=short 2>/dev/null | head -25`

## Auto-memory diffs this week
!`cd "${MEMORY_DIR}" && find . -name '*.md' -newer /tmp/_review_marker_7d 2>/dev/null | head -15 | sed 's|^./|  |' || (touch -d '7 days ago' /tmp/_review_marker_7d 2>/dev/null && find "${MEMORY_DIR}" -name '*.md' -mtime -7 | head -15 | sed 's|.*/||')`

## Memory hygiene
!`python3 "${SKILL_DIR}/scripts/memory_gc.py" 2>/dev/null | head -50`

## Stale tasks (>14 days)
!`grep -rEh '^- \[ \]' "${VAULT_DIR}/daily.journal.2026."*.md "${VAULT_DIR}/meet.2026."*.md 2>/dev/null | head -20`

## Project momentum
!`grep -A 30 '^## Project Momentum' "${MEMORY_DIR}/command-center.md" 2>/dev/null | head -35`

## Cold skills (>30 days unused)
!`test -f "${MEMORY_DIR}/skill-insights.json" && python3 -c "import json; d=json.load(open('${MEMORY_DIR}/skill-insights.json')); cold=d.get('cold_30d',{}); [print(f'  {k}: {v} days') for k,v in list(cold.items())[:10]] if cold else print('  (none)')"`

## Suggested follow-ups

Run after review:
- `dendron improve` — weekly synthesizer over score files (see SKILL.md)
- Clean any orphans/broken-links surfaced by memory_gc above
- Update `_working-memory.md` Current Focus if priorities shifted
