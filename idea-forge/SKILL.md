---
name: idea-forge
description: >
  Evaluate, refine, and evolve a research idea toward Nature/Science-level potential. Use when
  Zixin asks "is this idea Nature-worthy", to score/critique/kill a research idea, to push an
  idea toward a top journal, to refine or evolve an idea in his sci.ideas inbox, or invokes
  /idea-forge. Runs a retrieval-grounded, cross-model (Claude + Codex) judge with a grounded
  adversary and outcome-calibrated anchors; keeps only ideas that can plausibly hit the top tier.
---

# idea-forge

Interactive fitness function for research ideas. One idea at a time: ground it in the
literature, judge it on three orthogonal axes with two independent models, attack it with a
grounded adversary, place it against a calibrated set of known-outcome anchors, and — if it is
promising but short of the bar — evolve it. The goal is not "publishable somewhere"; it is
**Nature/Science-level potential**. Field-journal-level is refine-or-kill.

The plumbing is a tested Python package (`idea_forge/`). **This file is the substance: the
prompts and the decision rules.** Keep the plumbing boring; put the judgment here.

## Core principles (do not violate)

1. **Three axes, never summed.** Novelty, feasibility, impact are kept separate (Pareto).
   A weighted sum silently optimizes for safe increments — the exact thing to avoid.
2. **Calibrate, don't flatter.** Never ask "is this Nature-worthy?" in the abstract. Score
   against known-outcome anchors, and only trust forward verdicts if the judge can retrodict
   the past (leave-one-out). Below the min-n gate, run advisory-only and say so.
3. **Anti-sycophancy is structural.** A grounded adversary must fail to kill the idea. Two
   model families (Claude + Codex) judge independently; disagreement is surfaced, not averaged.
4. **Ground every claim.** Novelty/feasibility/scoop claims cite retrieved papers. No citation
   or concrete mechanism → it does not count as a kill and it lowers grounding confidence.
5. **Honesty over a fake bar.** If grounding is low-confidence or calibration is advisory, the
   system will not certify a "survivor". It says what it could not check.

## Zixin machine overrides (2026-07-06)

This machine has no Codex MCP, no cursor-agent, no Paperclip, and no Dendron vault.
Use these substitutions (all tested working):

- **Second judge + adversary**: `python3 scripts/second_judge.py` (GPT-4o via the OpenAI key in
  `~/Desktop/StudyChat_Project/scripts/system/.env`; add `--adversary` for the kill pass).
  Pipe `{"idea":..., "neighbors":[...], "rubric":...}` JSON on stdin; returns strict JSON.
- **Retrieval**: `idea_forge.openalex.search_with_s2_fallback(query)` — tries Semantic Scholar,
  falls back to keyless OpenAlex (anonymous S2 429s frequently here). PubMed MCP available
  in-session for bio routes; WebSearch for the rest.
- **Notes vault**: `~/Documents/sci-ideas/notes/` (sci.ideas.*.md, free-form headers).
  Use this as `--notes-dir` everywhere the doc says the Dendron path.
- **Python**: `/usr/bin/python3` (3.9) with user-site PyYAML + requests installed.
- **Anchors**: shared `anchors/anchors.yaml` (12 live, missing failed:3 incremental:1) —
  calibration stays ADVISORY-ONLY; candidate real failed anchor to add: AIED 2026 rejection.
- Wherever this file says "Zixin", read "Zixin" (per global overrides).

## Prerequisites

- Python env with the package importable: `cd ~/programs/ai-skills/idea-forge` and use `python3`
  (PyYAML + requests already present). Call helpers via `python3 -c "..."` or the scripts.
- Retrieval tools available in-session: Paperclip CLI (`paperclip`), PubMed MCP, WebSearch, and
  `idea_forge.semantic_scholar`. Codex second judge via `mcp__codex__codex`.
- Anchor set at `anchors/anchors.yaml`. It currently contains real publication-derived anchors
  with `label_status: proposed_from_venue`, so labels are useful but not Zixin-validated. The
  gate stays advisory until `scripts/audit_anchors.py` reports >=12 anchors and >=3 per tier,
  including real failed and incremental examples.

## Lifecycle & ingestion (organic — woven into the vault idea pipeline)

idea-forge is NOT a separate tool with its own idea list; it rides Zixin's existing `sci.ideas`
pipeline. Ideas enter via `dendron-add`, JPR voice capture, or a hand-written note, landing in
`sci.ideas.*` at stage `inbox`. idea-forge attaches to that lifecycle:

- **inbox (on ingest) → quick triage.** A cheap single-model rubric pass (no full retrieval or
  cross-model adversary): score the three axes from `content_for_judge()`, write a light
  `## idea-forge` block, and suggest whether it's worth a full evaluation. Keeps capture frictionless.
- **paper-idea (on promotion) → full evaluation.** The complete Pipeline below (retrieval +
  cross-model judge + grounded adversary + verdict card + write-back). `disposition` may advance
  the stage (→ pilot) or route to evolution.
- **refine / evolve.** Operators (Step 7); lineage recorded in the note.
- **outcome stages → anchors, automatically.** When an idea reaches `published` / `active-paper`
  (worked) or `rejected` / `dormant` (didn't), it becomes a **calibration anchor** with no manual
  bookkeeping: `harvest_anchors(notes_dir)` maps stage → tier. The calibration set is thus a *view
  over Zixin's own notes* + his publication record (the `top` successes), and **grows as the
  pipeline runs** — the anchor YAML is a cache, not a hand-maintained source of truth.
- **command-center.** Surface newly-ingested ideas awaiting triage and stale high-potential ideas
  in briefings, so evaluation happens as part of the normal vault sweep, not a special errand.

At session start, run `python3 scripts/audit_anchors.py --notes-dir <notes_dir>`, refresh anchors =
`harvest_anchors(notes_dir)` (pipeline outcomes) merged with the publication-record anchors, then
run Step 0. Today the harvest is near-empty (ideas are still active); calibration stays advisory
until outcomes accumulate or the grant-impact RCR engine (`sci.ideas.grant-impact-metascience`)
supplies labels at scale.

## Pipeline

### Step 0 — Session-start calibration check

Before judging anything, establish whether forward verdicts can be trusted.

1. Audit anchors: `python3 scripts/audit_anchors.py --notes-dir ~/Documents/sci-ideas/notes`.
2. If ≥12 anchors with ≥3 per tier: score each anchor **blinded and leave-one-out** (Step 4's
   judge prompt on `anchor.blinded_card()`, with that anchor excluded from any exemplars). Never
   expose anchor `title`, `known_tier`, `tier_ordinal`, `notes`, `label_status`, DOI, or source path
   to the judge; those are provenance for the audit layer only. Collect `{anchor_id:
   tier_potential_score}`, and run
   `echo '<json>' | python3 scripts/retrodiction_check.py`. Show the correlation + CI.
3. If the report is `advisory` (n below the gate) or `passed: false`, print this banner and
   carry it into every verdict this session:

   > ⚠️ Calibration is ADVISORY-ONLY (retrodiction {reason}). Scores are shown but idea-forge
   > will not certify a "survivor" verdict automatically — treat rankings as a prompt for your
   > judgment, not a decision.

### Step 1 — Intake

Resolve the target idea:
- a `sci.ideas.*` note path or Dendron wikilink → `parse_idea(path)`. It handles both the strict
  9-section template AND the free-form structures most notes actually use (Concept / Approach /
  Expected Outcomes / etc.) via header synonyms, and always fills `raw_body`. **Feed the judge
  `idea.content_for_judge()`** — structured sections when present, else the whole body. Never
  proceed on empty sections just because a note didn't use the exact template headers.
- pasted free text → judge it directly as `raw_body`; fill the template slots only if a slot is
  genuinely missing and you can't infer it (then ask Zixin).

Echo back the parsed claim/mechanism/method/gap so Zixin can catch a misread before compute.

### Step 2 — Route + retrieve (with leakage control)

1. `route(idea)` → `bio` or `cs`; note `GROUNDING_CONFIDENCE[route]`.
2. Retrieve the k≈8 nearest prior works:
   - `bio`: Paperclip full text + PubMed. `cs`: `semantic_scholar.search`/`related` + arXiv/WebSearch.
3. **If the target is an anchor (calibration), apply leakage control:** restrict retrieval to
   before `anchor.cutoff_date` and exclude the anchor paper itself and its downstream
   derivatives. Otherwise the judge "discovers" the very paper and novelty collapses to zero for
   exactly the ideas that were most novel at the time.
4. Record every query, corpus, retrieved id, and the evidence snippet used → provenance.

### Step 3 — Judge panel (run TWICE: Claude inline, then Codex)

**You MUST score by the rubric in `references/scoring-rubric.md` (0–10, grounded in the real NIH
9-point scoring scale), not by gut.** Read it first. For each axis, match the descriptor band
whose test the evidence satisfies, then report the 0–10 score **in traceable form**:
`score (band descriptor) — <cited evidence>` (e.g. `Novelty 3 (Fair / decorative) — nearest:
McLain 2018, delta = same question new tool`). A bare number with no band + evidence is invalid.
A score with no cited evidence cannot exceed the middle of its band and forces
`grounding_confidence: low`. Run this once yourself (Claude), then again via `mcp__codex__codex`
with the SAME idea + neighbors + rubric, so the two model families judge independently. Validate
each output with `validate_judge_output`.

> **Judge prompt.** You are a hard-nosed program officer deciding whether an idea can reach a top
> journal. You are given a research idea, its k nearest prior works, and the 0–10 rubric (Novelty
> ≈ NIH Innovation, Impact ≈ Significance, Feasibility ≈ Approach). Score each of the three
> INDEPENDENT axes 0–10 by matching the rubric descriptor to the retrieved evidence — do not let
> one axis bleed into another, and do NOT let low feasibility drag down novelty or impact.
>
> - **Novelty (0–10)** — judged against the nearest retrieved paper. State novelty type, whether
>   the novel axis is substantive or decorative, the nearest paper, the one-line delta. Score 0–1
>   sets `scooped: true`.
> - **Feasibility (0–10)** — decompose into building blocks; label each de-risked / plausible /
>   speculative / **invalid** (used outside its validated domain). Name the single worst risk.
>   This axis is a RISK read; it does not gate merit.
> - **Impact (0–10)** — reason COUNTERFACTUALLY (assume the result is true). Enumerate what it
>   unlocks/overturns/enables/reframes; an empty list caps you at 4.
> - **fundable** — boolean: `Feasibility ≥ 6 AND no grounded kill`. Report it; it does NOT decide
>   disposition.
> - **disposition** — apply the rubric rule: `top-shot` (N≥6, I≥7, F≥4, no kill) / `moonshot`
>   (N≥6, I≥7, F≤3 → pursue anyway) / `solid` / `incremental` / `dead` (grounded kill).
> - **grounding_confidence** — `high` only if the corpus genuinely covers this area.
>
> Return strict JSON:
> `{"novelty":{"score":0-10,"type":"...","substantive":bool,"nearest_paper":"...","delta":"...","scooped":bool,"rationale":"..."},`
> `"feasibility":{"score":0-10,"blocks":[{"name":"...","status":"de-risked|plausible|speculative|invalid"}],"worst_risk":"...","rationale":"..."},`
> `"impact":{"score":0-10,"unlocks":["..."],"overturns":["..."],"rationale":"..."},`
> `"fundable":bool,"disposition":"top-shot|moonshot|solid|incremental|dead","tier_potential":"top|field|failed|incremental","grounding_confidence":"high|low"}`
>
> When two judges land in different descriptor BANDS (not just different integers in the same
> band), that is a real disagreement — surface and arbitrate it, never average.

### Step 4 — Grounded adversary (cross-model)

Run once per model (or at least once on the model that did NOT look most favorable). Its only
job is to kill the idea. Decide kills with `adversary_kills`.

> **Adversary prompt.** Your only job is to kill this idea. Be specific and cite. Find: the
> paper that already scoops it; the single fatal flaw; the confound that explains the result
> away; the one sentence a Nature reviewer uses to reject it. Classify your strongest attack:
> `genuine_scoop` (name the paper), `decisive_confound` (name the mechanism), `feasibility_blocker`
> (name the block with no path), or `speculative_concern` (a worry you cannot ground). Do not
> inflate a speculation into a scoop.
>
> Return strict JSON:
> `{"flaw_type":"genuine_scoop|decisive_confound|feasibility_blocker|speculative_concern",`
> `"citation":"...","mechanism":"...","nature_reviewer_reject_sentence":"...","rationale":"..."}`

Only a killing flaw type WITH a citation or concrete mechanism kills. Speculative concerns are
recorded, never fatal.

### Step 5 — Aggregate + surface disagreement

- Keep the per-axis interval `[claude_score, codex_score]` (0–10). Do NOT average.
- If the two models land in different rubric BANDS on any axis, flag it to Zixin with BOTH
  rationales verbatim and run an arbitration pass (a third scoring that sees both rationales, or
  Zixin's call).
- The vector handed to Pareto is the **per-axis min** of the two models (conservative).
- **Disposition** (from the rubric rule, using the min vector + adversary):
  - `top-shot` — both models N≥6, I≥7, F≥4, no grounded kill, grounding not low-unreviewed,
    calibration not advisory → pursue now.
  - `moonshot` — N≥6, I≥7 but F≤3 → **PURSUE anyway** (high-risk/high-reward; the block is
    feasibility, not merit). Do NOT kill.
  - `solid` / `incremental` → refine or park.
  - `dead` — a grounded adversary kill (`genuine_scoop`/`decisive_confound`) → kill regardless of
    ambition.

### Step 6 — Verdict card + branch

Render (Canvas per Zixin's display rule if output is rich):
- per-axis interval (0–10) + grounding confidence; band-disagreement flags; `fundable`;
- Pareto position vs the current `sci.ideas` population: `pop = load_population(notes_dir)` (reads
  every scored sibling's `## idea-forge` block → `{id: (nov, feas, imp)}`), add this idea's min
  vector, and report whether it's on `pareto_front(pop)` and which siblings dominate it;
- nearest prior paper; the adversary's typed best shot;
- disposition + retrodiction confidence (or the advisory banner).

Then branch:
- **top-shot** → `upsert_forge_block`; advance `stage` (inbox→paper-idea, or paper-idea→pilot).
- **moonshot** → `upsert_forge_block`; tag as high-risk to pursue; advance stage but note the
  feasibility unlock needed. Never `rejected`.
- **solid / incremental** → offer evolution operators (Step 7).
- **dead** → `upsert_forge_block` with the typed kill reason; `set_stage(path, "rejected")`.

### Step 7 — Evolution operators (interactive)

When close but short, propose these and let Zixin pick (or auto-try the one targeting the
weakest axis). After applying, re-run Steps 2–6 on the variant; record lineage.

- **sharpen-claim** — collapse a topic into one precise take-home message.
- **swap-method** — replace the method with a more novel one that clears the nearest-paper.
- **raise-ambition** — push the target up (e.g. healthspan → 2–3× maximum-lifespan).
- **relocate** — move the idea to a more central gap in the graph (higher impact leverage).
- **recombine** — take the mechanism from this idea and the method from another population idea
  (load a second `sci.ideas` note); test the hybrid.

Log which operator moved which axis (before/after) so the system learns what "better" means.

### Step 8 — Write-back schema

`render_forge_block(data)` where `data` is:

```yaml
scored_at: <ISO datetime>
verdict: survivor | close | killed
tier_potential: top | field | failed | incremental
novelty:      {claude: N, codex: N, type: "...", grounding_confidence: high|low}
feasibility:  {claude: N, codex: N, worst_risk: "..."}
impact:       {claude: N, codex: N}
disagreements: ["novelty: 40 vs 80 — <both rationales>"]
nearest_paper: "<title / id>"
adversary: {flaw_type: "...", citation: "...", kills: bool, reject_sentence: "..."}
retrodiction: {correlation: X, ci: [lo, hi], advisory: bool}
lineage: {parents: [<idea ids>], operator: "<op or 'seed'>", moved: "impact 62->78"}
provenance:
  queries: ["..."]
  corpora: ["paperclip", "pubmed", ...]
  retrieved_ids: ["..."]
  snippets: ["..."]
  prompt_version: "v1"
  models: ["claude", "codex"]
  date: "<ISO date>"
```

Then `upsert_forge_block(path, block_md)` (idempotent — replaces any prior block).

## Reference: Python helpers

```
from idea_forge.notes_io import (parse_idea, render_forge_block, upsert_forge_block, set_stage,
                                 read_forge_block, load_population)
from idea_forge.corpus_router import route, CORPUS_BY_ROUTE, GROUNDING_CONFIDENCE
from idea_forge.anchors import load_anchors, save_anchors, blinded_cards, tier_counts
from idea_forge.harvest import harvest_anchors   # organic anchors from the sci.ideas pipeline
from idea_forge.models import validate_judge_output, adversary_kills, Anchor
from idea_forge.pareto import dominates, pareto_front
from idea_forge.retrodiction import retrodiction_report
from idea_forge import semantic_scholar
```

## Failure modes to refuse

- Do NOT invent papers, citations, venues, or outcomes (data-integrity rule). If retrieval
  fails, say so and lower grounding confidence — never fabricate a neighbor.
- Do NOT certify a survivor while calibration is advisory or grounding is low-and-unreviewed.
- Do NOT average away a hard cross-model disagreement — escalate it.
