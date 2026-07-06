#!/bin/bash
# Codex CLI second judge for idea-forge (Zixin machine; replaces Codex MCP).
# Usage: second_judge_codex.sh payload.json [--adversary]
#   payload.json: {"idea": "...", "neighbors": ["..."], "rubric": "..."}
# Prints the model's strict-JSON verdict (last JSON line of codex output).
set -euo pipefail
export PATH=/opt/homebrew/bin:$PATH
ENV_FILE="${IDEA_FORGE_ENV:-$HOME/Desktop/StudyChat_Project/scripts/system/.env}"
if [ -z "${OPENAI_API_KEY:-}" ] && [ -f "$ENV_FILE" ]; then
  export OPENAI_API_KEY=$(grep '^OPENAI_API_KEY=' "$ENV_FILE" | cut -d= -f2- | tr -d '"' | tr -d "'")
fi
PAYLOAD="$1"; MODE="${2:-judge}"
PROMPT=$(/usr/bin/python3 - "$PAYLOAD" "$MODE" <<'PYEOF'
import json, sys
p = json.load(open(sys.argv[1]))
adversary = (len(sys.argv) > 2 and sys.argv[2] == "--adversary")
if adversary:
    head = ('Your only job is to kill this research idea. Be specific and cite. Find: the paper that already scoops it; '
            'the single fatal flaw; the confound that explains the result away; the one sentence a Nature reviewer uses to reject it. '
            'Classify your strongest attack as genuine_scoop / decisive_confound / feasibility_blocker / speculative_concern. '
            'Do not inflate a speculation into a scoop. Return ONLY strict JSON: '
            '{"flaw_type":"...","citation":"...","mechanism":"...","nature_reviewer_reject_sentence":"...","rationale":"..."}')
else:
    head = ('You are a hard-nosed program officer deciding whether an idea can reach a top journal. '
            'Score three INDEPENDENT axes 0-10 against the rubric bands (Novelty~NIH Innovation, Impact~Significance, Feasibility~Approach); '
            'do not let axes bleed; low feasibility must not drag novelty or impact. Novelty scored against the nearest prior work given. '
            'Return ONLY strict JSON: {"novelty":{"score":0,"type":"","substantive":true,"nearest_paper":"","delta":"","scooped":false,"rationale":""},'
            '"feasibility":{"score":0,"blocks":[{"name":"","status":"plausible"}],"worst_risk":"","rationale":""},'
            '"impact":{"score":0,"unlocks":[],"overturns":[],"rationale":""},'
            '"fundable":false,"disposition":"solid","tier_potential":"field","grounding_confidence":"low"}')
body = "\n\n## Idea\n" + p["idea"] + "\n\n## Nearest prior works\n" + \
       ("\n".join("- " + n for n in p.get("neighbors", [])) or "(none retrieved)") + \
       "\n\n## Rubric\n" + p.get("rubric", "(use NIH-style 0-10 bands)")
print(head + body)
PYEOF
)
cd /tmp
codex exec --skip-git-repo-check -s read-only -c model_reasoning_effort=low "$PROMPT" 2>/dev/null | grep -E '^\{' | tail -1
