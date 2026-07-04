# Paperclip Prompt Templates

## Search Queries

Run multiple targeted searches instead of one broad search.

Topology:

```bash
paperclip search -s pmc "<GENE> receptor extracellular domain transmembrane surface ectodomain" -n 20
paperclip search -s pmc "<GENE> localization plasma membrane extracellular" -n 20
```

Direction, supportive and contradictory:

```bash
paperclip search -s pmc "<GENE> <DISEASE_CONTEXT> agonist ligand activation overexpression protective" -n 20
paperclip search -s pmc "<GENE> <DISEASE_CONTEXT> antagonist blockade knockout inhibition protective" -n 20
paperclip search -s pmc "<GENE> <CELL_CONTEXT> differentiation regeneration activation inhibition" -n 20
```

Use abstracts only as fallback when PMC full text is sparse:

```bash
paperclip search -s abstracts "<GENE> <DISEASE_CONTEXT> agonist antagonist knockout overexpression" -n 20
```

## Map Prompt

Use this with `paperclip map --from <SEARCH_ID>`.

```text
For each paper, extract evidence relevant to a secreted bivalent novokine that activates/clusters <GENE> in <DISEASE_CONTEXT>.

Return JSON-like bullets with:
- doc_id
- target_gene
- paper_context: disease, tissue/cell, species/model
- topology: surface_accessible yes/no/unclear and evidence
- intervention: agonist, ligand, activation, clustering, overexpression, antagonist, blockade, knockout, inhibition, expression_only, review
- phenotype
- direction_for_activation: support, contra, neutral, unclear
- directness: matched_perturbation, adjacent_perturbation, expression_association, review, unrelated
- exact quote or concise claim with line references if available
- caveats

Do not infer direction from association alone. Beneficial inhibition means activation is a warning.
```

## Reduce Prompt

Use this with `paperclip reduce --from <MAP_ID> --strategy consensus`.

```text
Synthesize a literature consensus for <GENE> as a novokine activation target in <DISEASE_CONTEXT>.

Decide:
1. activation_direction: favor_activation, warn_activation, mixed_context_dependent, or unknown
2. direction_confidence: high, medium, low, or none
3. novokine_likelihood: high, mid, or small
4. manual_review: true/false

Explain the intervention translation. Separate matched-context perturbation evidence from expression-only or review evidence. Identify contradictions. Use high/mid/small novokine likelihood only for direct novokine plausibility, not general biology.
```

## Verification Claims

Add short, verifiable claims to the Paperclip repo:

```bash
paperclip git add <DOC_ID> "<GENE>: <intervention> <improved/worsened> <phenotype> in <model>, implying activation is <support/contra> for novokine use."
paperclip git commit -m "Verify <GENE> novokine literature claims"
paperclip git status
```

Only include claims marked OK in the final JSON.
