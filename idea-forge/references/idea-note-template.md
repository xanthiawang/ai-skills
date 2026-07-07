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
