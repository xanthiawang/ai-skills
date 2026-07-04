# Park Live State

_Generated ${NOW_UTC} · session `${SESSION_ID}` · about to park_

## Phase C reflection on this session
!`python3 "${SKILL_DIR}/scripts/reflect.py" "${SESSION_ID}" 2>/dev/null | head -80 || echo '(reflect.py failed — session may not exist yet)'`

## Recent jsonl sessions (for cross-reference)
!`ls -1t "${SESSION_DIR}/"*.jsonl 2>/dev/null | head -5 | xargs -I{} basename {} .jsonl`

## Currently parked (active threads)
!`grep -A 1 '^| 2026' "${VAULT_DIR}/tool.claude-parked-convos.md" 2>/dev/null | head -15`

## Memory hygiene quick-check
!`python3 "${SKILL_DIR}/scripts/memory_gc.py" 2>/dev/null | head -30 || echo '(memory_gc.py failed)'`

## Park protocol checklist

When parking, the agent must:
1. Save full context to `memory/project_<topic>.md` (or update existing) — findings, decisions, blockers, next steps
2. Get session ID: `ls -t "${SESSION_DIR}/"*.jsonl | head -1 | xargs -I{} basename {} .jsonl`
3. Add row to `${VAULT_DIR}/tool.claude-parked-convos.md` (Active or Tool dev section as appropriate)
4. Update `${MEMORY_DIR}/MEMORY.md` Active Projects section with a one-line pointer
5. Run `python3 "${SKILL_DIR}/scripts/session_index.py" update` to keep FTS5 current

If the work warrants vault capture (per the Vault Capture Rule in SKILL.md), the appropriate `tool.*`/`proj.*`/`meet.*`/`sci.*` note must exist before parking — auto-memory carries pointers only.
