# Consensus JSON Schema

Canonical file name:

```text
<program>_literature_consensus.json
```

Top-level shape:

```json
{
  "schema_version": "novokine-lit-consensus-v1",
  "program": "ad",
  "disease_context": "Alzheimer's disease",
  "paperclip_workspace": "/workspace/novokine-lit-ad-20260621",
  "generated_at": "2026-06-21T00:00:00Z",
  "targets": {},
  "pairs": {}
}
```

## Target Record

```json
{
  "gene": "ADAM10",
  "aliases": ["ADAM 10"],
  "disease_context": "Alzheimer's disease",
  "cell_context": "neuron / glial / microglial / endothelial",
  "activation_direction": "favor_activation",
  "direction_confidence": "high",
  "direction_score": 0.72,
  "novokine_likelihood": "high",
  "manual_review": false,
  "surface_accessible": true,
  "novokine_mechanism": "ectodomain-accessible receptor/enzyme; activation or clustering plausibly increases protective activity",
  "evidence_counts": {
    "support": 2,
    "contra": 0,
    "neutral": 1
  },
  "evidence": [
    {
      "doc_id": "PMC2647556",
      "claim": "ADAM10 overexpression increased non-amyloidogenic APP processing and improved AD-model phenotypes.",
      "direction_for_activation": "support",
      "intervention": "overexpression",
      "phenotype": "amyloid and cognitive phenotypes",
      "context_match": "matched",
      "evidence_class": "animal_perturbation",
      "verified": true,
      "line_refs": ["L100-L110"]
    }
  ],
  "rationale": "Short paragraph explaining why activation is favored, warned, mixed, or unknown.",
  "likelihood_rationale": "Short paragraph explaining high/mid/small novokine likelihood."
}
```

## Pair Record

```json
{
  "pair_id": "ADAM10+TREM2",
  "anchor": "ADAM10",
  "specifier": "TREM2",
  "activation_warning": false,
  "pair_novokine_likelihood": "mid",
  "pair_direction": "favor_activation",
  "manual_review": false,
  "pair_rationale": "Both targets are surface-accessible; direction is favorable/unknown; pair clustering mechanism remains indirect."
}
```

## Enumerations

- `activation_direction`: `favor_activation`, `warn_activation`, `mixed_context_dependent`, `unknown`
- `direction_confidence`: `high`, `medium`, `low`, `none`
- `novokine_likelihood`: `high`, `mid`, `small`
- `direction_for_activation`: `support`, `contra`, `neutral`, `unclear`
- `context_match`: `matched`, `adjacent`, `mismatch`, `unclear`
- `evidence_class`: `human_perturbation`, `animal_perturbation`, `cell_perturbation`, `patient_tissue`, `expression_association`, `review`, `association`, `topology`, `other`

## Compatibility Field

`direction_score` is optional and only for browser color compatibility. It must be in `[-1, 1]`:

- positive means literature favors activation
- negative means literature warns against activation
- zero means unknown, neutral, or disqualified

Do not rank candidates by `direction_score` unless the user explicitly asks for literature-ranked outputs.
