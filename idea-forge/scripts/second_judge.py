#!/usr/bin/env python3
"""Cross-family second judge for idea-forge via the OpenAI API (GPT-4o).

Replaces the Codex-MCP second judge on machines without Codex/cursor-agent.
Reads OPENAI_API_KEY from the environment, or from an --env-file containing
an `OPENAI_API_KEY=...` line (never printed).

Usage:
  python3 scripts/second_judge.py --env-file ~/path/.env < payload.json
  payload.json: {"idea": "<content_for_judge text>",
                 "neighbors": ["<title (year): abstract snippet>", ...],
                 "rubric": "<contents of references/scoring-rubric.md>"}

Prints the judge's strict-JSON verdict on stdout (validate with
idea_forge.models.validate_judge_output).
"""
import argparse
import json
import os
import sys

import requests

MODEL = os.environ.get("SECOND_JUDGE_MODEL", "gpt-4o")

JUDGE_PROMPT = """You are a hard-nosed program officer deciding whether an idea can reach a top journal. You are given a research idea, its k nearest prior works, and a 0-10 scoring rubric (Novelty ~ NIH Innovation, Impact ~ Significance, Feasibility ~ Approach). Score each of the three INDEPENDENT axes 0-10 by matching the rubric descriptor to the retrieved evidence. Do not let one axis bleed into another; do NOT let low feasibility drag down novelty or impact.

- Novelty (0-10): judged against the nearest retrieved paper. State novelty type, whether the novel axis is substantive or decorative, the nearest paper, the one-line delta. Score 0-1 sets scooped: true.
- Feasibility (0-10): decompose into building blocks; label each de-risked / plausible / speculative / invalid. Name the single worst risk.
- Impact (0-10): reason counterfactually (assume the result is true); enumerate what it unlocks/overturns; an empty list caps the score at 4.
- fundable: boolean = Feasibility >= 6 AND no grounded kill.
- disposition: top-shot (N>=6, I>=7, F>=4, no kill) / moonshot (N>=6, I>=7, F<=3) / solid / incremental / dead.
- grounding_confidence: high only if the supplied neighbors genuinely cover the area.

Return ONLY strict JSON:
{"novelty":{"score":0,"type":"","substantive":true,"nearest_paper":"","delta":"","scooped":false,"rationale":""},"feasibility":{"score":0,"blocks":[{"name":"","status":"plausible"}],"worst_risk":"","rationale":""},"impact":{"score":0,"unlocks":[],"overturns":[],"rationale":""},"fundable":false,"disposition":"solid","tier_potential":"field","grounding_confidence":"low"}"""


def load_key(env_file):
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"]
    if env_file and os.path.exists(env_file):
        for line in open(env_file):
            if line.startswith("OPENAI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("OPENAI_API_KEY not found in environment or --env-file")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env-file", default=os.path.expanduser(
        "~/Desktop/StudyChat_Project/scripts/system/.env"))
    ap.add_argument("--adversary", action="store_true",
                    help="run the grounded-adversary prompt instead of the judge")
    args = ap.parse_args()
    key = load_key(args.env_file)
    payload = json.load(sys.stdin)

    if args.adversary:
        system = ("Your only job is to kill this research idea. Be specific and cite. Find: the paper that already scoops it; the single fatal flaw; the confound that explains the result away; the one sentence a Nature reviewer uses to reject it. Classify your strongest attack as genuine_scoop / decisive_confound / feasibility_blocker / speculative_concern. Do not inflate a speculation into a scoop. Return ONLY strict JSON: "
                  '{"flaw_type":"speculative_concern","citation":"","mechanism":"","nature_reviewer_reject_sentence":"","rationale":""}')
    else:
        system = JUDGE_PROMPT

    user = "## Idea\n{}\n\n## Nearest prior works\n{}\n\n## Rubric\n{}".format(
        payload["idea"],
        "\n".join(f"- {n}" for n in payload.get("neighbors", [])) or "(none retrieved)",
        payload.get("rubric", "(rubric omitted; use NIH-style 0-10 bands)"))

    r = requests.post("https://api.openai.com/v1/chat/completions",
                      headers={"Authorization": f"Bearer {key}"},
                      json={"model": MODEL, "temperature": 0,
                            "response_format": {"type": "json_object"},
                            "messages": [{"role": "system", "content": system},
                                         {"role": "user", "content": user}]},
                      timeout=120)
    r.raise_for_status()
    print(r.json()["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()
