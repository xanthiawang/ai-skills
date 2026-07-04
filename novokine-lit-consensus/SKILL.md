---
name: novokine-lit-consensus
description: Build auditable Paperclip literature consensus for novokine target candidates. Use when assessing whether activating, clustering, or agonizing a cell-surface protein is protective or harmful in a disease context, and when assigning high/mid/small novokine likelihood from full-text papers.
---

# Novokine Literature Consensus

## Purpose

Use Paperclip to produce a reproducible, citation-backed literature consensus for novokine candidates.

The skill answers two questions for each target, and optionally each pair:

1. **Activation direction**: would a novokine-like activation/clustering signal likely be protective, harmful, mixed, or unknown?
2. **Novokine likelihood**: is the target a `high`, `mid`, or `small` chance novokine target?

Do not use Open Targets, DE, or expression direction to decide activation direction. Those can be displayed elsewhere. This skill is for full-text literature consensus only.

## Required First Step

Before any Paperclip work, run:

```bash
paperclip skill
```

Then check that no unrelated Paperclip repo is active. If the task needs citations or reusable outputs, create a fresh workspace repo:

```bash
paperclip git init /workspace/novokine-lit-<program>-<YYYYMMDD>
```

Use a fresh repo for each disease program or target batch. Never add novokine claims to an unrelated active Paperclip repo.

## Workflow

1. **Define the task table**
   - Required: `gene`, `program`, `disease_context`.
   - Useful: aliases, intended cell type, pair partner, receptor/topology annotation, Open Targets score for display only.
   - Keep AD and muscle/sarcopenia as separate disease contexts.

2. **Search independently for topology and direction**
   - Topology query: surface localization, extracellular domain, receptor, ligand, ectodomain, membrane topology.
   - Direction query: disease plus agonist/activation/ligand/overexpression versus antagonist/blockade/knockout/inhibition.
   - Include negative-direction terms intentionally; do not search only for supportive evidence.

3. **Map papers into structured evidence**
   - Use `paperclip map` over filtered results.
   - Extract intervention, phenotype, disease/cell context, direction implied for activation, directness, and exact quoted support.
   - Treat expression-only, GWAS-only, pathway-only, and review-only papers as weak or contextual evidence, not direction proof.

4. **Verify claims before using them**
   - Add each claim that will appear in the output:

```bash
paperclip git add <DOC_ID> "Claim to verify"
paperclip git commit -m "Verify <GENE> novokine direction claims"
paperclip git status
```

   - Use only claims marked OK. Revise or drop failed claims.

5. **Assign consensus**
   - Use the rules in `references/rubric.md`.
   - Direction labels are `favor_activation`, `warn_activation`, `mixed_context_dependent`, or `unknown`.
   - Novokine likelihood tiers are `high`, `mid`, or `small`.
   - Store the rationale and all verified evidence spans.

6. **Validate the output**

```bash
python3 <skill>/scripts/validate_consensus_json.py path/to/ad_literature_consensus.json
```

## Output Contract

Write one JSON file per program or batch. Prefer this path pattern in a project repo:

```text
<program>/data/<program>_literature_consensus.json
```

The JSON must follow `references/schema.md`. Required top-level keys:

- `schema_version`: `novokine-lit-consensus-v1`
- `program`: short program id such as `ad` or `muscle`
- `disease_context`: human-readable disease context
- `targets`: object keyed by gene symbol

Optional top-level keys:

- `paperclip_workspace`
- `generated_at`
- `pairs`

## Integration Guidance

For a downstream novokine browser:

- Rank score should stay separate from this skill unless the user explicitly asks otherwise.
- Use `activation_direction == "warn_activation"` as an activation warning.
- Use `activation_direction == "mixed_context_dependent"` as a weaker warning or manual-review flag.
- Display `novokine_likelihood` and `likelihood_rationale` in the target detail panel.
- Keep all cited Paperclip document IDs and claims visible for audit.

## Adversarial Rubric

Use `references/adversarial_rubric.json` when the literature consensus needs adversarial rubric guidance. The rubric has two explicit layers:

- `rubric_design_agents`: the 10-agent adversarial design panel that created the rubric itself.
- `adversarial_agents`: the runtime review panel for checking each target or pair consensus.

The design panel covers modality, topology, context transfer, antagonist inversion, evidence hierarchy, contradictions, pair biology, safety, retrieval bias, and provenance. Treat these design-agent outputs as the source of the rubric requirements, not as optional commentary.

Validate it without Claude:

```bash
node <skill>/scripts/claude_adversarial_rubric.mjs --dry-run
```

Regenerate it with Claude Agent SDK when the rubric itself needs redesign:

```bash
cd <skill> && npm install
npm run rubric:write
```

`rubric:write` instructs Claude Agent SDK to run or simulate the 10 adversarial design agents first, then synthesize both the design-panel record and the runtime review rubric.

## References

- `references/rubric.md`: direction and high/mid/small novokine-likelihood rules.
- `references/adversarial_rubric.json`: machine-readable adversarial design-panel record and runtime review rubric.
- `references/adversarial_rubric.md`: human-readable rendering of the adversarial rubric.
- `references/prompts.md`: Paperclip search/map/reduce prompt templates.
- `references/schema.md`: canonical JSON schema and example record.
