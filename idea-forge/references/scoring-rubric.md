# idea-forge scoring rubric (0–10, grounded in the NIH peer-review scoring system)

Every numeric score idea-forge emits MUST trace back to a named descriptor band with cited
evidence — no free-floating numbers. This rubric is anchored on the **real NIH scoring system**
(source: NIH *Scoring System and Procedure*, grants.nih.gov, rev. 2015-03-18) so the scale means
something specific and defensible.

## The NIH scale idea-forge is built on (verbatim anchors)

NIH scores overall impact and each criterion on a **9-point scale, 1 = best, 9 = worst**:

| Group | NIH score | NIH descriptor |
|---|---|---|
| **High** | 1 / 2 / 3 | Exceptional / Outstanding / Excellent |
| **Medium** | 4 / 5 / 6 | Very Good / Good / Satisfactory |
| **Low** | 7 / 8 / 9 | Fair / Marginal / Poor |

NIH principles idea-forge inherits (their exact stances):
- **Overall impact = "the project's likelihood to have a sustained, powerful influence on the
  research field(s) involved."** This is idea-forge's north-star and maps to the *Impact* axis /
  disposition — and it matches "Nature/Science-level," not "publishable."
- **"The impact score … is not intended to be an average of criterion scores."** → idea-forge
  never sums the axes; selection is Pareto.
- **"An application does not need to be strong in all categories to be judged likely to have major
  impact, e.g., a project that by its nature is not innovative may be essential to advance a
  field."** → this is NIH's own justification for **decoupling fundability from merit** and for the
  **moonshot** bucket. One critically-important criterion can carry the verdict.
- **"5 is a good, medium-impact application"; the full 1–9 range should always be used; 1 and 9
  used less often.** → calibrate away from grade inflation; spread scores.

**idea-forge uses 0–10 (10 = best) for intuitiveness; here is the crosswalk to the NIH scale so
every band traces back:**

| idea-forge 0–10 | NIH score | NIH descriptor / group |
|---|---|---|
| 9–10 | 1–2 | Exceptional / Outstanding (High) |
| 7–8 | 3–4 | Excellent / Very Good (High–Medium) |
| 5–6 | 5–6 | Good / Satisfactory (Medium) |
| 3–4 | 7 | Fair (Low) |
| 1–2 | 8 | Marginal (Low) |
| 0 | 9 | Poor (Low) |

## The three axes = the three scored NIH criteria that judge the IDEA

idea-forge scores the *idea*, so it uses NIH's three idea-facing criteria (NIH's Investigator and
Environment criteria judge the team/resources and are out of scope). Definitions are NIH's
standard review-criteria language:

- **Impact ≈ NIH Significance** — "Does the project address an important problem or a critical
  barrier to progress? If the aims are achieved, how will scientific knowledge, technical
  capability, and/or clinical practice be improved? How will successful completion change the
  concepts, methods, technologies, or interventions that drive the field?"
- **Novelty ≈ NIH Innovation** — "Does the application challenge and seek to shift current
  paradigms by using novel concepts, approaches, methodologies, or interventions? Are they novel
  to one field or in a broad sense? Is it a refinement, improvement, or new application?"
- **Feasibility ≈ NIH Approach** — "Are the overall strategy, methodology, and analyses
  well-reasoned and appropriate? Are potential problems, alternative strategies, and benchmarks
  for success presented? For early-stage projects, are feasibility-establishing strategies
  addressed?" **This axis is a risk read; per NIH it does not gate merit.**

Each score MUST cite: (a) its band descriptor from the table below, and (b) the retrieved
paper(s) the judgment rests on. A score with no cited evidence cannot exceed the middle of its
band and forces `grounding_confidence: low`. Prose confidence never raises a score.

---

## Novelty (0–10) — NIH Innovation, judged against the nearest retrieved prior work

| Score | Band (NIH descriptor) | Assign iff... | Evidence |
|---|---|---|---|
| **0–1** | Poor/Marginal | **Scooped** — a retrieved paper already establishes essentially this claim + approach. | Cite it → `scooped: true`, `dead`. |
| **2–3** | Fair | **Decorative** — delta from nearest work = new dataset / scale / tool on an established question with a known answer-shape ("X but with Y"). | Nearest paper + one-line delta. |
| **4–5** | Satisfactory/Good | **Substantive, in-paradigm** — real increment (a method that measurably beats prior, a new regime/population, a new measurable); paradigm unchanged. | Nearest paper + what's better. |
| **6–7** | Very Good/Excellent | **New claim / mechanism** — a mechanism or claim absent from all near neighbors and non-obvious. | Show the gap across neighbors. |
| **8–9** | Outstanding | **Paradigm-relevant** — attacks a question the field is stuck on; challenges a standing assumption or unifies disparate results. | Name the stuck question. |
| **10** | Exceptional | **Field-defining** — opens a new question or dissolves a controversy. | Justify hard. |

## Feasibility (0–10) — NIH Approach (decoupled: never lowers Novelty/Impact, never auto-kills)

Decompose into building blocks (data, assay, method, model, analysis); label each `de-risked /
plausible / speculative / invalid`.

| Score | Band | Assign iff... |
|---|---|---|
| **0–1** | Poor/Marginal | **Invalid / blocked** — a load-bearing block is invalid (tool used outside its validated domain) or has no credible path. |
| **2–3** | Fair | **Speculative core** — worst risk severe + unmitigated, or ≥2 load-bearing blocks speculative. |
| **4–5** | Satisfactory/Good | **Mixed** — core plausible; 1–2 speculative with a stated mitigation. |
| **6–7** | Very Good/Excellent | **Mostly de-risked** — residual risk is execution, not validity. |
| **8–9** | Outstanding | **De-risked** — every block has prior-work precedent; effort, not gamble. |
| **10** | Exceptional | **Turnkey.** |

## Impact (0–10) — NIH Significance / "sustained, powerful influence on the field" (counterfactual)

Assume the result is TRUE; enumerate the downstream nodes that change (unlocks / overturns /
enables / reframes). An empty list caps the score at **4**.

| Score | Band | Assign iff... |
|---|---|---|
| **0–2** | Poor/Marginal | **Additive** — adds a datapoint/resource; nothing downstream changes. |
| **3–4** | Fair | **Incremental** — confirms/extends a known effect; few citations; no assumption/method changes. |
| **5–6** | Satisfactory/Good | **Enabling** — creates a capability/resource/answer others build on; resolves a specific subfield question. |
| **7–8** | Very Good/Excellent | **Reframing** — overturns a common assumption, or supplies a mechanism/tool that redirects a subfield. |
| **9–10** | Outstanding/Exceptional | **Field-shifting** — changes the questions a field asks; a "sustained, powerful influence" — the top-journal bar. |

---

## Fundability flag (derived, reported — NOT a filter)

`fundable = (Feasibility ≥ 6) AND (no grounded adversary kill)`. NIH folds this into the overall
score; idea-forge reports it but **does not use it to decide** — following NIH's own rule that an
idea "need not be strong in all categories" to have major impact.

## Disposition (Pareto over Novelty × Impact + adversary; feasibility is a risk read, not a gate)

- **top-shot** — Novelty ≥ 6 AND Impact ≥ 7 AND Feasibility ≥ 4 AND no grounded kill → pursue now; top-journal ceiling.
- **moonshot** — Novelty ≥ 6 AND Impact ≥ 7 but Feasibility ≤ 3 → **PURSUE (high-risk/high-reward).** The NIH "not innovative may still be essential" clause, inverted: brilliant-but-unfundable is kept, not killed.
- **solid** — Impact 5–6 or Novelty 4–5, not scooped → refine or park.
- **incremental** — Novelty ≤ 3 AND Impact ≤ 4 → drop unless refined.
- **dead** — the adversary lands a grounded kill (`genuine_scoop`/`decisive_confound`) → kill regardless of ambition.

## Traceability (mandatory)

Every axis score in a verdict MUST render as: `score (band descriptor) — <evidence citation>`,
e.g. `Novelty 3 (Fair / decorative) — nearest: McLain 2018; delta = same question, new tool.`
A verdict with any bare number and no band+evidence is invalid and must be re-scored.

## Why a rubric AND calibration anchors

The rubric makes scoring reproducible and evidence-grounded (kills "confident number from the
air"). The anchors map scores → real outcomes and check the judge retrodicts known results
(leave-one-out). The large-scale calibration engine is the sibling meta-science project
(`sci.ideas.grant-impact-metascience`): real grant text → downstream RCR impact, which replaces
the hand-built anchors with thousands of real known-outcome pairs.
