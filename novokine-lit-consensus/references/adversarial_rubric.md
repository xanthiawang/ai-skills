# Adversarial Novokine Literature Rubric

Schema: `novokine-adversarial-rubric-v1`

Rubric designed by a 10-agent adversarial design panel for Paperclip-derived novokine literature consensus. The rubric prevents association evidence from being mistaken for activation direction or novokine targetability, then defines a separate 10-agent runtime review panel for target and pair consensus outputs.

## Rubric Design Process

Method: 10 independent adversarial design agents plus synthesis into a machine-validated rubric

Design agents: 10

Design goal: Design a transparent Paperclip-first rubric for activation direction and high/mid/small novokine likelihood without using Open Targets, DE, GWAS, expression, or co-expression as direction evidence.

Synthesis rule: Each design agent owns one failure class. The synthesized rubric keeps hard caps, required fields, and failure tests from every agent; unresolved conflicts default to conservative manual_review and lower likelihood.

## 10 Adversarial Design Agents

### 1. Modality Skeptic (design-modality-skeptic)

Activation direction is a causal intervention-translation problem, not a target-relevance problem. Association, expression, genetics, co-expression, and Open Targets are contextual only; absent perturbation evidence defaults to unknown.

Required fields:
- evidence_modality
- activity_delta
- phenotype_delta
- direction_translation
- association_quarantined
- bivalent_activation_plausible

Decision rules:
- Set favor_activation only when verified activation, agonism, ligand stimulation, clustering, gain-of-function, or reverse loss-of-function evidence indicates benefit.
- Set warn_activation when activation worsens the phenotype or inhibition, blockade, knockout, or loss-of-function improves it.
- Set unknown when evidence is association-only, expression-only, genetics-only, co-expression-only, review-only, or lacks a clear activity change.
- Do not let Open Targets, DE, GWAS, or expression decide direction even when they strongly support disease relevance.

Failure tests:
- Favor_activation is assigned from associated, enriched, expressed, implicated, or Open Targets evidence.
- A paper changes disease phenotype but the target activity polarity is missing.
- A ligand-binding or receptor-presence paper is treated as proof that forced clustering is beneficial.
- Beneficial inhibition is counted as support without inversion.

Acceptance standard: Every non-unknown direction call must show activity polarity, phenotype polarity, and explicit translation into support or contra for activation.

Rubric contribution: Creates the modality gate and the rule that relevance evidence cannot substitute for activation-direction evidence.

### 2. Topology Hardliner (design-topology-hardliner)

A novokine is a secreted extracellular bivalent binder; surface annotation alone is not enough. The target must expose an extracellular binding site and have plausible productive activation or clustering biology.

Required fields:
- surface_accessible
- plasma_membrane_evidence
- extracellular_domain_evidence
- membrane_anchor_type
- target_class
- binding_mode_plausible_for_secreted_binder
- activation_or_clustering_plausible
- topology_cap
- topology_failure_reason

Decision rules:
- Cap likelihood at small for intracellular, organelle, secreted-only, or otherwise inaccessible proteins.
- Require plasma-membrane and extracellular-domain evidence before high likelihood.
- Cap atypical topologies at mid unless a verified extracellular binding and activation mechanism is shown.
- For pairs, inherit the stricter topology cap from either partner.

Failure tests:
- High likelihood is assigned to a protein without extracellular-domain evidence.
- A cytosolic, nuclear, mitochondrial, lysosomal, ER, or sarcoplasmic reticulum protein passes as a target.
- Transporters, enzymes, adhesion proteins, or secreted ligands are assumed agonizable without mechanism.
- Pair likelihood ignores one partner's topology failure.

Acceptance standard: High or mid likelihood is allowed only when a secreted binder can physically engage the target and plausibly create productive activation or clustering.

Rubric contribution: Defines topology hard caps and the physical-access gate for target and pair likelihood.

### 3. Context Transfer Critic (design-context-transfer-critic)

Evidence transfer must be justified claim by claim. AD and sarcopenia are separate disease contexts, and developmental, cancer, injury, immune, species, cell-type, or disease-stage evidence cannot create favor_activation or high likelihood by itself.

Required fields:
- disease_context_match
- cell_context_match
- species_context
- model_context
- disease_stage_or_aging_context
- endpoint_match
- overall_context_match
- transfer_rationale
- context_transfer_penalty

Decision rules:
- Classify each claim as matched, adjacent, weak_transfer, mismatch, or unclear.
- Matched-context perturbation evidence can support high confidence; adjacent evidence can support medium only with explicit rationale.
- Weak_transfer or mismatch evidence cannot create favor_activation and cannot lift likelihood to high.
- Use mixed_context_dependent or manual_review when direction changes by cell type, disease stage, model, or species.

Failure tests:
- Cancer, developmental, acute-injury, or generic inflammation evidence is treated as aging AD or sarcopenia treatment evidence.
- A non-target cell type dominates the rationale without a transfer argument.
- Cross-program evidence from AD to muscle, or muscle to AD, determines final direction.
- A beneficial effect in one disease stage is assumed beneficial in another.

Acceptance standard: The final call explicitly states what transfers, what does not transfer, and which confidence or likelihood cap follows from context mismatch.

Rubric contribution: Adds context-match labels and transfer penalties that prevent unsupported cross-context promotion.

### 4. Intervention Inversion Auditor (design-intervention-inversion-auditor)

The rubric must translate intervention polarity and phenotype polarity before deciding activation direction. Reverse inference is allowed only when mechanism, context, endpoint, and target are close enough to acute novokine activation or clustering.

Required fields:
- intervention_type
- intervention_polarity
- phenotype_effect
- mechanism_directness
- reverse_inference_used
- reverse_inference_limit
- direction_translation
- inversion_error

Decision rules:
- Activation, agonism, ligand stimulation, clustering, or gain-of-function that improves phenotype supports activation.
- Activation, agonism, ligand stimulation, clustering, or gain-of-function that worsens phenotype warns against activation.
- Inhibition, blockade, knockout, knockdown, or loss-of-function that improves phenotype warns against activation.
- Inhibition, blockade, knockout, knockdown, or loss-of-function that worsens phenotype supports activation only with reverse-inference caps.
- Cap reverse-only support at medium or low when compensation, chronic adaptation, off-target effects, or endpoint mismatch is plausible.

Failure tests:
- A protective inhibitor or knockout is summarized as target validation for activation.
- A harmful knockout is not recognized as possible support for activation.
- Drug modality, blocking antibody, deletion, knockdown, or antagonist language appears without inversion.
- Reverse inference from chronic genetic loss is treated as equivalent to acute extracellular activation.

Acceptance standard: Every inhibitory or loss-of-function claim is directionally inverted, capped when needed, and marked when reverse inference is invalid.

Rubric contribution: Creates the intervention-translation table and prevents antagonist biology from being read in the wrong direction.

### 5. Evidence Hierarchy Prosecutor (design-evidence-hierarchy-prosecutor)

Strength is capped by the strongest verified primary perturbation evidence, not by paper count. Weak support cannot override stronger matched contradictory evidence.

Required fields:
- evidence_class
- context_match
- intervention_type
- direction_for_activation
- primary_paper
- verified_paperclip_claim
- independent_study_id
- strongest_support_class
- strongest_contra_class
- confidence_cap_reason

Decision rules:
- High confidence requires at least two independent matched H1-H3 primary perturbation claims and no matched direct contradiction.
- Medium confidence can come from one matched H1-H3 claim or at least two adjacent H1-H4 claims.
- Low is the maximum for single adjacent, indirect, patient-tissue, or mechanistic-only support.
- Review, expression, association, and generic pathway claims cannot determine activation direction.
- The strongest matched contra claim caps or overrides accumulated weak support.

Failure tests:
- A review statement outranks primary perturbation evidence.
- Patient tissue association is treated as an intervention.
- A single weak adjacent paper yields high confidence.
- Support counts are used without evidence quality or independence.

Acceptance standard: Direction confidence follows an explicit evidence hierarchy and reports strongest support and strongest contra evidence separately.

Rubric contribution: Defines confidence caps, primary-evidence requirements, and the rule that evidence quality beats volume.

### 6. Contradiction Hunter (design-contradiction-hunter)

The workflow must try to falsify its own direction call. Decision-changing contradictions must be surfaced, searched for, and allowed to force mixed_context_dependent, warn_activation, manual_review, or lower likelihood.

Required fields:
- negative_search_lanes
- strongest_support_claim
- strongest_contra_claim
- contra_evidence
- contradiction_status
- mixed_direction_basis
- caveats_affecting_call
- manual_review_reason
- likelihood_cap

Decision rules:
- Favor_activation is not final until negative-direction lanes have been searched or reproducibly fail.
- Direct matched support plus direct matched contra sets mixed_context_dependent and manual_review unless resolved.
- Unresolved matched harmful activation sets warn_activation or manual_review and prevents high likelihood.
- Dose, ligand, disease stage, cell type, chronicity, and model reversals must affect the final call.

Failure tests:
- No antagonist, knockout, harmful activation, toxicity, or worsening search terms were used.
- Contradictory papers are labeled as caveats but do not change direction or likelihood.
- No contradictions are listed for a heavily studied target.
- The conclusion says no contradictions without a recorded negative search lane.

Acceptance standard: Every consensus includes strongest-opposing-evidence handling, and unresolved direct contradiction prevents high confidence.

Rubric contribution: Adds falsification lanes and contradiction-driven caps to the final decision protocol.

### 7. Pair Biology Skeptic (design-pair-biology-skeptic)

Pair biology is a separate hypothesis. Two plausible single targets do not imply a plausible bivalent novokine pair; the pair is capped by the weaker partner unless verified pair-specific biology supports co-engagement in the intended direction.

Required fields:
- target_a_direction
- target_b_direction
- target_a_likelihood
- target_b_likelihood
- weaker_target_cap
- pair_specific_evidence
- pair_mechanism_class
- pair_geometry
- direction_conflict
- pair_likelihood_cap_reason

Decision rules:
- If either target is small for topology or accessibility, the pair is small.
- If either target is warn_activation, pair direction is warn_activation, likelihood is small, and manual_review is true.
- If either target is mixed_context_dependent, pair likelihood is capped at mid.
- Pair likelihood cannot exceed the weaker target unless verified pair-specific evidence justifies lifting the cap.
- High requires both targets surface accessible, no warning direction, credible geometry, and direct pair, co-receptor, complex, ligand-receptor, or same-pathway mechanism.

Failure tests:
- Pair rationale only repeats two single-target rationales.
- Pair_specific_evidence is empty but pair is called high.
- Pair exceeds weaker partner without explicit cap-lift justification.
- Any warning partner is present but pair is not warn_activation or small.
- Co-expression, Open Targets, GWAS, or DE is used to infer pair activation direction.

Acceptance standard: High pair likelihood requires independent pair plausibility; mid is used when both targets are plausible but pair biology is untested or indirect; small is used when either partner fails hard or pair logic is absent.

Rubric contribution: Adds weaker-partner caps, pair-specific evidence requirements, and geometry/mechanism classes for bivalent target pairs.

### 8. Safety and Pathology Sentinel (design-safety-pathology-sentinel)

Safety is not a footnote. Verified evidence that activation, agonism, clustering, ligand excess, gain-of-function, or pathway amplification worsens disease biology must change activation_direction, manual_review, and likelihood even when efficacy evidence exists.

Required fields:
- safety_search_performed
- safety_search_terms
- safety_flags
- strongest_safety_contra_claim
- harm_context_match
- harm_intervention_type
- harm_severity
- therapeutic_window_concern
- systemic_exposure_concern
- likelihood_safety_cap

Decision rules:
- Matched-context activation, agonism, or clustering that worsens disease phenotype sets warn_activation and caps likelihood at small.
- Credible matched support plus credible matched activation harm sets mixed_context_dependent, manual_review, and a mid or small cap.
- Do not assign high when intended-tissue evidence indicates inflammation, degeneration, fibrosis, proliferation, pain, or cell death.
- Beneficial antagonism or pathway inhibition in the same disease is activation-contra evidence.
- If required safety search is missing for immune, cytokine, growth-factor, fibrosis, pain, developmental, or proliferation-linked targets, force manual_review and disallow high.

Failure tests:
- A target is promoted while verified harmful activation, inflammation, degeneration, fibrosis, proliferation, or pain evidence is ignored.
- Favor_activation is assigned when the same disease pathway is treated by inhibiting the target.
- Local efficacy is treated as sufficient despite systemic ligand or broad on-target toxicity risk.
- Dose, chronicity, disease stage, or cell-type reversal is ignored.
- A safety claim lacks Paperclip doc_id, verified status, or line refs.

Acceptance standard: The record must include an explicit safety search, strongest harmful activation evidence, verified safety claims, and safety-driven changes to warning, mixed status, manual review, or likelihood cap.

Rubric contribution: Adds safety/pathology flags, harmful-activation direction rules, and safety-driven likelihood caps.

### 9. Retrieval Bias Auditor (design-retrieval-bias-auditor)

Retrieval quality is a gate and confidence cap, not biological evidence. The workflow must prove that it searched supportive and contrary activation-direction evidence across canonical symbols, aliases, and protein names before claiming support, no contradiction, or no hits.

Required fields:
- retrieval_audit
- search_quality_confidence
- search_lanes
- alias_coverage
- retrieval_limitations
- confidence_caps
- no_hit_status

Decision rules:
- Required lanes include topology, activation_benefit, activation_harm, inhibition_benefit, inhibition_harm, disease_context, and safety_pathology.
- Pair calls require a pair_context lane.
- No no-literature or no-contradiction claim is valid unless required lanes ran with alias coverage.
- If the search log is absent, search_quality_confidence is failed, manual_review is required, and high confidence is blocked.
- Sparse Paperclip full-text coverage must be recorded as no_fulltext_hits rather than converted into supportive unknown.

Failure tests:
- Support-only query uses gene plus disease plus agonist terms with no antagonist, knockout, or harm lanes.
- Short or renamed gene symbols are searched without aliases or protein names and then called no-hit.
- Review-only retrieval produces a direction assignment.
- High confidence is assigned from many association papers but no matched perturbation papers.
- Search strings, aliases, result counts, screened doc IDs, or no-hit status are missing.

Acceptance standard: Every target or pair must have a reproducible balanced search log, alias handling, explicit limitations, and confidence caps applied before final labels.

Rubric contribution: Adds the retrieval_audit block and search-quality caps for direction confidence and novokine likelihood.

### 10. Provenance and Schema Enforcer (design-provenance-schema-enforcer)

Fail closed. A literature claim can influence activation_direction, direction_confidence, or novokine_likelihood only if it resolves to an existing Paperclip document, a specific claim string, non-empty line refs, and verified true.

Required fields:
- schema_version
- program
- disease_context
- paperclip_workspace
- validation
- doc_id
- claim
- verified
- line_refs
- missing_data_semantics_errors

Decision rules:
- Document IDs must resolve inside the declared Paperclip workspace; syntactically plausible IDs are not enough.
- Line refs must be non-empty and Paperclip-resolvable; evidence without line refs is rejected.
- Accepted evidence requires verified exactly true, not missing, false, or string true.
- Any non-unknown activation_direction requires at least one verified perturbation or mechanistic evidence item with source_role direction.
- Use unknown for a reviewed decision label, null only for explicitly nullable fields, and 0 only for computed zero values.

Failure tests:
- JSON has trailing commas, duplicate keys, wrong types, missing required fields, or non-enum labels.
- Doc_id cannot be opened in the Paperclip workspace.
- The cited lines do not support the claim.
- Evidence has empty line_refs, verified false, or no claim.
- Favor_activation or warn_activation is derived only from Open Targets, DE, GWAS, expression, co-expression, review-only, or pathway association.
- Zero is used as a stand-in for missing search, topology, or direction evidence.

Acceptance standard: The artifact passes JSON validation, every accepted claim resolves to a Paperclip document and line span, unverified_claim_count is zero, provenance errors are empty, missing-data semantics are explicit, and every non-unknown direction call has verified full-text support.

Rubric contribution: Adds fail-closed validation, Paperclip provenance requirements, and null/zero/unknown semantics.

## Non-Negotiables

- differential expression as activation direction
- Open Targets as activation direction
- GWAS or genetic association as activation direction
- expression up/down as activation direction
- co-expression as activation direction
- review-only claims without primary-paper verification
- unverified Paperclip claims
- fabricated or non-Paperclip document identifiers

## Decision Lanes

### activation_direction

Does activation, agonism, clustering, ligand stimulation, gain-of-function, or reverse loss-of-function evidence imply that a novokine-like activation signal is protective, harmful, mixed, or unknown?
Allowed values: `favor_activation`, `warn_activation`, `mixed_context_dependent`, `unknown`
Minimum evidence: At least one verified perturbation or mechanistic paper is required for favor_activation or warn_activation. Association-only evidence yields unknown.

### direction_confidence

How strong is the literature support after context matching, intervention translation, and contradiction handling?
Allowed values: `high`, `medium`, `low`, `none`
Minimum evidence: High requires at least two independent matched-context perturbation papers with no strong matched-context contradiction.

### novokine_likelihood

How likely is this target or pair to be a direct novokine activation target?
Allowed values: `high`, `mid`, `small`
Minimum evidence: High requires surface access, plausible bivalent activation or clustering, favorable or non-warning direction, and verified mechanistic support.

### evidence_provenance

Can every claim used in the consensus be traced to a verified Paperclip document, claim, and line reference?
Allowed values: `verified`, `partial`, `failed`
Minimum evidence: Every evidence item used for direction or likelihood must have verified=true and a Paperclip document id.

### manual_review

Does the target require human review before use because of contradiction, context transfer, safety, topology uncertainty, or weak provenance?
Allowed values: `true`, `false`
Minimum evidence: Set true when any adversarial agent finds an unresolved major issue.

## 10 Adversarial Agents

### 1. Modality Purist (modality-purist)

Question: Is the evidence actually about activation, agonism, clustering, ligand stimulation, or gain-of-function, rather than generic target involvement?

Failure modes:
- Disease association is treated as activation evidence.
- Expression change is interpreted as desired intervention direction.
- A paper about inhibition is summarized without translating it through novokine activation modality.
- A ligand-binding paper is treated as proof that forced clustering is beneficial.

Required checks:
- Identify the intervention type for every supporting paper.
- Classify each evidence item as direct activation, reverse inhibition, association-only, or topology-only.
- Reject favor_activation if no verified perturbation or mechanistic activation paper exists.
- Explain how each intervention maps to support, contra, neutral, or unclear.

Red flags:
- The rationale uses words like associated, enriched, expressed, or implicated without perturbation.
- The evidence never states whether activity was increased or decreased.
- Activation is inferred from Open Targets, GWAS, or DE.

Pass standard: Every direction call has explicit intervention translation and no association-only evidence drives direction.

Output fields: `intervention_translation_ok`, `modality_failure_reason`, `direction_basis`

### 2. Topology Gatekeeper (topology-gatekeeper)

Question: Can a secreted bivalent minibinder physically reach and productively engage the target?

Failure modes:
- Intracellular or organelle proteins are treated as surface targets.
- Secreted ligands are treated as targets without receptor-clustering logic.
- Transporters, enzymes, and adhesion proteins are assumed to be agonizable without mechanism.
- Surface annotation is accepted without verified ectodomain or extracellular evidence.

Required checks:
- Find verified topology or localization evidence when topology is uncertain.
- Record surface_accessible as true, false, or null.
- If surface_accessible is false, cap novokine_likelihood at small.
- For atypical targets, explain the proposed bivalent engagement mechanism.

Red flags:
- Cytosolic, nuclear, mitochondrial, lysosomal, ER, or sarcoplasmic reticulum localization.
- No extracellular domain or extracellular binding mode.
- Only intracellular gain-of-function evidence supports the target.

Pass standard: High or mid likelihood is impossible unless a secreted binder can plausibly engage the target.

Output fields: `surface_accessible`, `topology_evidence`, `topology_failure_reason`

### 3. Context Transfer Critic (context-transfer-critic)

Question: Does the paper context match the disease, tissue, cell state, and intended therapeutic endpoint closely enough?

Failure modes:
- Cancer or immune evidence is transferred to AD or sarcopenia without justification.
- Developmental biology is treated as aging disease biology.
- A non-target cell type dominates the consensus.
- A beneficial effect in one disease stage is assumed beneficial in another.

Required checks:
- Assign context_match as matched, adjacent, mismatch, or unclear for every claim.
- Separate matched-context and adjacent-context support counts.
- Downgrade confidence when the best evidence is adjacent-context.
- Use mixed_context_dependent when direction changes by cell type or stage.

Red flags:
- The only evidence is from cancer, embryogenesis, acute injury, or generic inflammation.
- The target cell type differs from the intended novokine cell context.
- A mouse developmental phenotype is used as direct disease-treatment evidence.

Pass standard: The rationale explicitly states why evidence transfers, or refuses to transfer it.

Output fields: `context_match_summary`, `context_transfer_penalty`, `manual_review`

### 4. Antagonist Inversion Auditor (antagonist-inversion-auditor)

Question: Was beneficial inhibition, blockade, antagonist treatment, knockout, or loss-of-function correctly inverted into an activation warning?

Failure modes:
- A protective antagonist is counted as support for target selection without warning.
- Knockout benefit is summarized as target validation for activation.
- Loss-of-function harm is not recognized as support for activation.
- Drug class or antibody modality is ignored.

Required checks:
- Mark each inhibitory intervention as beneficial, harmful, or neutral.
- Translate beneficial inhibition into contra for novokine activation.
- Translate harmful loss-of-function into support for novokine activation.
- Flag ambiguous inhibition mechanisms for manual review.

Red flags:
- Words like inhibitor, antagonist, blocking antibody, knockout, deletion, knockdown, or loss-of-function appear in a support claim without inversion.
- A target is high likelihood because blocking it helps.
- The direction_basis omits reverse_inference when using knockout or inhibition.

Pass standard: All inhibition and loss-of-function evidence is directionally translated before consensus.

Output fields: `inversion_checked`, `reverse_inference_count`, `inversion_errors`

### 5. Evidence Hierarchy Prosecutor (evidence-hierarchy-prosecutor)

Question: Is the strongest evidence really strong enough for the assigned direction and likelihood?

Failure modes:
- Review statements outrank primary perturbation evidence.
- Patient tissue association is treated as a perturbation.
- A single weak adjacent paper yields high confidence.
- Conflicting high-quality evidence is buried under many weak supportive papers.

Required checks:
- Assign evidence_class to every claim.
- Report the strongest support and strongest contra evidence separately.
- Require high confidence to have at least two independent matched perturbation papers.
- Prevent volume of weak evidence from overpowering direct contradictory evidence.

Red flags:
- High confidence with only review, expression, or association evidence.
- No independent replication for high confidence.
- The rationale cites support counts without describing evidence quality.

Pass standard: Direction confidence follows evidence hierarchy, not paper count.

Output fields: `strongest_support_class`, `strongest_contra_class`, `confidence_adjustment`

### 6. Contradiction Hunter (contradiction-hunter)

Question: What is the strongest evidence against the proposed direction or likelihood?

Failure modes:
- Searches only retrieve supportive papers.
- Contradictory papers are labeled caveats but do not affect the call.
- Dose, ligand, disease stage, or cell type reversals are ignored.
- Known safety or pathology signals are excluded from consensus.

Required checks:
- Run or require negative-direction search lanes.
- List strongest contra claims even when final direction is favorable.
- Set mixed_context_dependent when support and contra are both direct and credible.
- Set manual_review when contradictions are not resolvable.

Red flags:
- No contra search terms were used.
- No contradictions are listed for a heavily studied target.
- The conclusion says no contradictions without verifying negative search lanes.

Pass standard: Consensus includes an explicit strongest-opposing-evidence paragraph.

Output fields: `strongest_opposing_claim`, `contradiction_status`, `manual_review`

### 7. Pair Biology Skeptic (pair-biology-skeptic)

Question: Does evidence for two single targets justify a bivalent pair, or is pair biology untested?

Failure modes:
- Two individually plausible targets are assumed to be synergistic.
- Pair geometry, pathway relationship, or co-receptor logic is absent.
- One target has harmful activation but the pair is still promoted.
- Pair-level evidence is claimed when only separate single-target evidence exists.

Required checks:
- Distinguish single-target evidence from pair-specific evidence.
- Assign pair_novokine_likelihood no higher than the weaker target unless pair-specific evidence justifies it.
- Flag pairs where either target has warn_activation.
- Explain whether the pair has co-receptor, ligand-receptor, same-pathway, or independent clustering logic.

Red flags:
- Pair rationale only repeats two single-target rationales.
- No mechanism links target A and target B.
- The pair is high likelihood despite one target being small.

Pass standard: Pair calls are conservative and explicit about whether pair-level biology exists.

Output fields: `pair_specific_evidence`, `pair_mechanism_class`, `pair_likelihood_cap`

### 8. Safety and Pathology Sentinel (safety-pathology-sentinel)

Question: Could activation plausibly worsen disease, inflammation, proliferation, degeneration, fibrosis, pain, or systemic safety?

Failure modes:
- Known pro-inflammatory activation is ignored.
- Cancer or fibrosis activation risks are not surfaced.
- Systemic ligand biology conflicts with local therapeutic intent.
- Activation of immune checkpoints, cytokine receptors, or growth-factor axes is treated as benign.

Required checks:
- Search for pathology, toxicity, inflammation, fibrosis, proliferation, and adverse activation evidence.
- Record safety_or_pathology_flags when found.
- Set warn_activation or manual_review when matched harmful activation exists.
- Prevent high likelihood when severe matched safety concerns remain unresolved.

Red flags:
- Activation is associated with neuroinflammation, muscle wasting, fibrosis, tumor growth, or cell death.
- The same pathway is therapeutically inhibited in the disease.
- No safety search was performed for an immune or growth-factor target.

Pass standard: Safety-relevant activation liabilities are visible and affect likelihood.

Output fields: `safety_flags`, `pathology_flags`, `likelihood_safety_cap`

### 9. Retrieval Bias Auditor (retrieval-bias-auditor)

Question: Did the search strategy retrieve a balanced, reproducible set of papers rather than a supportive narrative?

Failure modes:
- Only supportive query terms are used.
- Aliases are missing, causing false no-hit calls.
- PMC-only search misses important abstracts or preprints when full text is sparse.
- Highly studied targets receive inflated certainty because they have more papers.

Required checks:
- Record search lanes and query strings.
- Use aliases and protein names when gene symbols are ambiguous.
- Include antagonist, knockout, inhibition, and harmful terms.
- Use no_fulltext_hits rather than unknown support when search coverage is sparse.

Red flags:
- Search log is absent.
- No alias resolution for short or ambiguous symbols.
- All retrieved papers are reviews or irrelevant contexts.

Pass standard: Consensus is reproducible from recorded balanced search lanes.

Output fields: `search_lanes`, `alias_coverage`, `retrieval_limitations`

### 10. Schema and Provenance Enforcer (provenance-enforcer)

Question: Is every output machine-valid, citation-backed, and honest about uncertainty?

Failure modes:
- Doc ids are fabricated, malformed, or not from Paperclip.
- Evidence is included without verified=true.
- Required schema fields are missing.
- Null, unknown, and zero are conflated.

Required checks:
- Run validate_consensus_json.py before accepting outputs.
- Require verified=true for evidence used in the consensus.
- Preserve null for no evidence rather than converting to zero support.
- Require rationale and likelihood_rationale for every target.

Red flags:
- A citation cannot be opened as a Paperclip document.
- Evidence lacks line references or a verifiable claim.
- The output passes prose review but fails JSON validation.

Pass standard: The final JSON validates and every evidence claim is traceable.

Output fields: `schema_valid`, `provenance_errors`, `unverified_claim_count`

## Final Decision Protocol

- Run all 10 adversarial agents against each target or pair consensus.
- Any topology hard failure caps novokine_likelihood at small.
- Any unresolved beneficial-inhibition or harmful-activation finding sets activation_direction to warn_activation unless stronger matched evidence resolves it.
- Any direct matched-context support and direct matched-context contra conflict sets activation_direction to mixed_context_dependent and manual_review to true.
- High novokine_likelihood requires passing modality, topology, context, evidence hierarchy, contradiction, safety, retrieval, and provenance checks.
- The final reducer must report which agents changed the call or forced manual review.

