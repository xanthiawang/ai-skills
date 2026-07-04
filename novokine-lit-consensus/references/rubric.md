# Novokine Literature Consensus Rubric

## Core Assumption

A novokine is a secreted bivalent minibinder that activates or clusters two cell-surface targets. Literature evidence must therefore be interpreted through activation modality, not generic disease association.

## Direction Labels

Use exactly one:

- `favor_activation`: agonism, ligand stimulation, receptor activation, clustering, overexpression, or loss-of-function harm supports activation as protective in the disease-relevant context.
- `warn_activation`: agonism/activation worsens phenotype, or antagonist/blockade/knockout/inhibition improves phenotype.
- `mixed_context_dependent`: credible direct evidence supports both directions after stratifying by disease, cell type, model, or modality.
- `unknown`: no interpretable perturbation evidence.

Do not infer direction from expression up/down, Open Targets association, GWAS, co-expression, or pathway membership alone.

## Direction Confidence

Use exactly one:

- `high`: two or more independent matched-context perturbation papers agree, with no strong matched-context contradiction.
- `medium`: one matched-context perturbation paper, or multiple adjacent-context perturbation papers agree.
- `low`: indirect perturbation, expression, tissue association, review synthesis, or sparse adjacent-context evidence.
- `none`: no usable evidence.

Matched context means the disease program, relevant cell type/tissue, and intervention modality are close enough that the direction can plausibly transfer to a novokine activation signal.

## Intervention Translation

Translate each paper through this table:

| Paper finding | Direction for novokine activation |
|---|---|
| agonist/ligand/receptor activation improves phenotype | support |
| agonist/ligand/receptor activation worsens phenotype | contra |
| antagonist/blockade/knockout/inhibition improves phenotype | contra |
| antagonist/blockade/knockout/inhibition worsens phenotype | support |
| overexpression improves phenotype | support if the protein is surface-accessible and overexpression plausibly increases target activity |
| overexpression worsens phenotype | contra |
| expression higher/lower in disease only | neutral/context |
| review statement without primary data | neutral or weak support only |

## Novokine Likelihood Tiers

Use exactly one:

### `high`

Assign when all are true:

- Target has a surface-accessible extracellular domain or extracellular binding mode.
- Activation/clustering is mechanistically plausible for a secreted bivalent binder.
- Direction is `favor_activation` with medium or high confidence, or direct novokine-like agonism evidence exists.
- No hard matched-context contradiction dominates.

### `mid`

Assign when surface access is plausible but one or more is true:

- Direction is unknown, low-confidence favorable, or mixed without a strong harmful matched-context signal.
- Evidence is adjacent-context rather than matched-context.
- Target is a transporter, adhesion molecule, sheddase, ligand complex, or atypical receptor where clustering could matter but mechanism is not clean.
- Pair-level biology is plausible but not directly tested.

### `small`

Assign when any hard failure is present:

- Intracellular, nuclear, organelle, cytosolic, or no accessible extracellular target for a secreted binder.
- Beneficial evidence is mainly antagonist/blockade/knockout, so activation is likely harmful.
- Matched-context activation evidence is harmful.
- Only generic association evidence exists and no plausible activation mechanism is available.
- Secreted ligand or soluble protein has no clear receptor-clustering target logic.

`small` means small chance as a direct novokine activation target, not biologically unimportant.

## Conflict Rules

- Matched disease/cell perturbation beats adjacent disease association.
- Direct agonism/antagonism beats expression correlation.
- Primary papers beat reviews unless the review identifies primary data that can be verified.
- If direct matched-context papers conflict, use `mixed_context_dependent`, set `manual_review: true`, and do not assign `high`.
- If no paper exists, use `unknown`, `direction_confidence: none`, and usually `mid` only if topology/mechanism is independently compelling; otherwise `small`.

## Pair-Level Rules

Evaluate pair novokine likelihood after per-target calls:

- `high`: both targets are individually high or strong mid, both surface-accessible, no warning direction, same-cell context is credible, and clustering both has plausible pathway logic.
- `mid`: at least one target is mid or unknown but no hard failure; pair is worth follow-up.
- `small`: either target is small due to topology or harmful activation direction, or pair biology has no plausible activation mechanism.

Pair direction is the most cautious target-level direction:

- any `warn_activation` -> pair warning
- any `mixed_context_dependent` -> pair mixed/manual review unless the other target is a strong warning
- both favorable or unknown without warning -> no warning, but keep confidence explicit
