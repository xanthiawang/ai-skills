# Meeting Prep — Live State

_Generated ${NOW_UTC} · ${TODAY} · session `${SESSION_ID}`_

## Today's calendar
!`grep -A 20 '^## Today.*Calendar' "${VAULT_DIR}/_working-memory.md" 2>/dev/null | head -25 || echo '(no working memory)'`

## Recent meeting notes (last 7 days)
!`ls -1t "${VAULT_DIR}/meet."*.md 2>/dev/null | head -7 | sed 's|.*/||'`

## Pending action items from past meetings
!`grep -l '^- \[ \]' "${VAULT_DIR}/meet."*.md 2>/dev/null | head -5 | xargs -I{} sh -c 'echo "### $(basename {} .md)"; grep -E "^- \[ \]" "{}" | head -5; echo'`

## People with stale interactions (last contact >14 days)
!`python3 -c "
import os, re, time
from pathlib import Path
vault = Path('${VAULT_DIR}')
cutoff = time.time() - 14*86400
stale = []
for fp in vault.glob('user.*.md'):
    if fp.stat().st_mtime < cutoff:
        continue
    text = fp.read_text(errors='ignore')
    m = re.search(r'(?i)last (?:contact|met|interaction)[^\n]*?(\d{4}[-./]\d{2}[-./]\d{2})', text)
    if m:
        stale.append((m.group(1), fp.name))
stale.sort(reverse=True)
for d, n in stale[:8]:
    print(f'  {d}  {n}')
" 2>/dev/null || echo '(scan failed)'`

## Open Gmail drafts (top 5 by recency)
!`grep -E '^\| (\d{4}-\d{2}-\d{2})' "${VAULT_DIR}/tool.claude-parked-convos.md" 2>/dev/null | head -5`

## Suggested next step

Once attendees are known, run:
```
dendron-query Find everything about <attendee>
```
or for a deeper prep, dispatch parallel agents per attendee following the **Meeting Context Prep** section of the command-center SKILL.md.
