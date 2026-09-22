# idea-forge capture template (human-facing)

Use this when a new idea lands in `sci.ideas.*` and you want the note in
paper-proposal shape BEFORE the machine `## idea-forge` block gets written.
This is the human-readable front matter; Step 8's YAML block is the
machine-readable verdict that `upsert_forge_block` maintains alongside it.

Rule: every idea must become a **thesis (precise claim), not a topic.** If you
cannot state a Minimum Publishable Package, it is not yet a paper-idea — leave it
at `inbox`.

```markdown
# <Idea Title>

## Stage
inbox / paper-idea / pilot / active-paper / dormant / rejected / submitted / published

## Paper Thesis
One precise claim this paper would prove. A claim, not a topic.

## Refined Verdict
Worth pursuing? What tier could it hit? Biggest weakness right now?

## Contribution Shape
1.
2.
3.

## Prior-Work Boundary
How far does existing work go, and what is the exact delta? Name the nearest papers.
(Do NOT anchor this idea on your own prior papers — it must stand as an
independent paper once your own work is excluded. See SKILL.md principle 6.)

## Minimum Publishable Package
The smallest set of data / experiments / figures / comparisons / analyses that
constitutes a submittable paper. No MPP → not active-paper.

## Core Empirical Claim
The single most important empirical proposition. What result makes the paper stand?

## Experiments / Evidence Needed
What data / experiments / benchmark / proof / case study does the Core Empirical Claim
require — and can you actually get it? This is where **evidence accessibility** is judged:
list each evidence block and mark it accessible-now / obtainable-with-effort / gated
(needs data you can't reach, hardware you don't have, or a cohort you can't recruit).
A claim whose evidence is gated stays at `inbox` until the gate is named and a path exists.

## Best Anchor
Which successful paper is it most like, and why?

## Failure Anchor
Which class of failed idea is it most like? What must it avoid?

## Reviewer Kill Pass
Where will a reviewer attack? (too small / claim too big / scooped / method just a
combination / no clinical or field meaning / no ablation / no annotator agreement / …)

## One Fix
The single move that raises it one tier.

## Next Action
A concrete action doable in 24–72h — not "keep surveying the literature".

## Verdict
top-shot / moonshot / field-solid / solid+fix / near-miss / dormant / rejected
```

Concept background for the whole funnel: `references/idea-evolve-system.md`.

**How the 7 Pareto dimensions map onto the scored machine** (only 3 are numeric axes; the
other 4 are folded in as signals/gates so the panel never collapses into a weighted sum):
`novelty` / `feasibility` / `impact` = the three scored 0–10 axes; **evidence accessibility**
= the *Experiments / Evidence Needed* section + `feasibility` blocks + `grounding_confidence`;
**mechanistic sharpness** = `novelty` 6–7 band + the adversary's concrete-mechanism requirement
+ the *Core Empirical Claim*; **field-level surprise** = `impact` top bands + `tier_potential`;
**reviewer defensibility** = the *Reviewer Kill Pass* + Step 4 grounded adversary (a gate, not a
score). Keep `moonshot` in the Verdict enum: high-novelty × high-impact × low-feasibility ideas
are pursued, not killed.
