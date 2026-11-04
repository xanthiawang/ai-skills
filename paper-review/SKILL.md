---
name: paper-review
description: "Review an academic manuscript as a paper: assess contribution, argument, framing, structure, literature dialogue, writing, figures, and venue fit. Use for requests such as paper review, review this manuscript, or 像审稿人一样评价. Do not audit coding, search, screening, raw data, scripts, or project execution unless the user explicitly asks for a methods or analysis audit."
---

# Paper Review

Review the manuscript that a reader or venue reviewer will see. The default task is a paper-facing critique, not a forensic audit of the project that produced it.

## Default boundary

Treat the study's existing data, coding, screening, search, and analysis pipeline as fixed project inputs. Do not inspect or criticize raw data, codebooks, coder files, screening logs, scripts, execution traces, provenance records, repository history, or internal QA unless the user explicitly requests an audit of those materials.

Methods may still be reviewed as prose in the manuscript. Comment on whether the paper explains its design clearly enough for a reader, whether the stated method matches the stated research question, and whether the claims exceed what the manuscript itself says was done. Do not turn missing access to internal evidence into a finding. Do not recalculate statistics or infer pipeline defects from project files in the default mode.

If the user says to ignore coding, search, screening, implementation, engineering, or process issues, treat that as a hard scope boundary. Do not reintroduce those issues indirectly under reproducibility, rigor, limitations, or submission readiness.

Use a separate analysis-review or audit skill only when the user explicitly asks to validate data, statistics, code, screening, coding reliability, provenance, reproducibility, or the execution process.

## What to review

Read the latest manuscript source and its rendered submission PDF when available. Assess:

- the paper's central contribution and whether a reviewer can state it precisely;
- the fit between title, abstract, research questions, results, and conclusion;
- the novelty and usefulness of the conceptual framing;
- engagement with the most relevant literature and competing interpretations;
- the logical flow within and across sections;
- whether each major claim is supported by evidence presented in the manuscript;
- whether Results and Discussion answer the research questions without repetition;
- whether limitations are proportionate and do not erase the contribution;
- the clarity, economy, and specificity of the writing;
- whether figures and tables communicate their intended message;
- venue fit, required format, length, anonymization, and visible submission quality when a venue is named.

For a venue-specific review, verify current requirements from the venue's official sources. Distinguish a rule violation from an editorial preference.

## Review stance

Judge the paper on the contribution it actually makes. Do not demand a different study merely because it would be stronger. Ask whether the current evidence and argument are sufficient for the paper's stated contribution and target venue.

Prioritize comments that would change a reviewer's understanding or decision. Avoid manufacturing minor issues. Do not repeat limitations the manuscript already handles unless the handling remains unclear or materially weakens the argument.

When a sentence can be fixed locally, quote or identify it and give a concrete replacement direction. When the problem is structural, explain which sections should change and what each should accomplish.

## Calibration from real decision letters

Zixin's own rejections (CHI 2027 Assisted Desk Rejection, Computers & Education reject after review, LAK27 reviews; stored in `manuscript-revision/comment-library/entries/`, local only) show which paper-facing problems decide outcomes. Check each one explicitly, in this order, before writing the verdict. All are judged from the manuscript text alone.

1. **Readability and positioning first.** Can a reader state the research gap in one sentence by the end of the introduction's second paragraph, or does it only appear in Related Work? Does the abstract use labels defined only later (condition names, ratio names, internal code names)? CHI desk-rejects on this before reading any statistics.
2. **Structure.** Flag one- or two-sentence subsections, results reported inside Methods, Methods not organized by research question, and an introduction that previews results at length.
3. **Rationale for every key choice.** The theoretical framework (why this model and not its alternatives), each coding definition (why a borderline category counts where it counts), sample size, and every system or design decision should carry a stated reason.
4. **Research-question alignment.** Flag a research question that bundles several questions, and any research question or claim that names something the study never tested (an "intervention window", "transfer failure").
5. **Claims within evidence.** Flag mechanism and causal vocabulary for behavioral or associational evidence ("trap", "self-reinforcing", "mechanistic core", "measures cognitive offloading" when the scheme classifies observable dialogue), generalization from a small or single-coder subsample, and practical recommendations for a system that was never deployed.
6. **Internal consistency.** Compare how the introduction, results, and discussion state the same finding; flag introduction claims about prior work that the paper's own reanalysis contradicts, and constructs defined one way and discussed another.
7. **Balanced headline numbers.** Flag a pooled or combined number emphasized while the strictest number (holdout, primary analysis) is weaker; reviewers notice.
8. **Reader-facing completeness.** Every supplement the text mentions is locatable by name; non-English figures carry translations; data language and any translation are described; the generative-AI declaration separates research-method use from manuscript-preparation use.
9. **Literature coverage.** Recent work in the target venue on the same topic is cited; published versions replace preprints.

### Clarity checks from the CHI 2027 desk rejection

The CHI Associate Chair and Subcommunity Chair rejected the paper mainly because it was "difficult to understand": the abstract and introduction were "very difficult to understand", the gap "remained unclear until the Related Work section", Section 4 needed reorganizing, design decisions lacked justification, the methodology lacked clarity, and the introduction was long. Their own summary of the paper misread the study design, which is the clearest sign that the writing failed. Run these tests on every manuscript, and report each failure as a major comment:

- **Outsider summary test.** Read only the title, abstract, and introduction, then write the one-sentence summary a reviewer would write (what was built or studied, with whom, how, what was found). If it misstates the design or the contribution, the framing has failed regardless of the results.
- **Abstract.** Every term is either common in the field or defined on the spot; condition names, ratio or index names, code labels, and phrases like "conventional proxies" are replaced by plain descriptions. The abstract states the problem, what was done, the setting and sample, the main results with their numbers, and one implication, in that order.
- **One gap, early.** The introduction states a single gap, in one sentence, by the end of its second paragraph. Several half-gaps spread over paragraphs three and four count as no gap. Related Work opens by naming the open problem and each subsection ends by saying what remains open for this paper.
- **Introduction length.** About 800-900 words for a journal or CHI paper; the results preview is at most one paragraph; contributions are stated compactly.
- **No empty sections.** A heading such as "Design goals" must contain the goals, each with its rationale. A subsection of one or two sentences is merged into its neighbor or filled with the missing content.
- **Methods a reader can follow.** Methods is ordered as context and participants, design and procedure, measures, then analysis subsections that follow the research questions. Measures describes procedures only; any result found there belongs in Results.
- **Why, not only what.** Each system or study component carries one sentence explaining why it was designed that way (for example, why two models, why a condensed prompt, why a particular trigger or fading rule).
- **Findable materials.** Every supplementary file the text mentions is named and cited at first use; non-English figure text is translated in the caption or an appendix.

Praise that recurs is also informative: transparent reporting, effect sizes with intervals, robustness checks, and an abstract that states purpose, methods, findings, and implications were credited by reviewers and need no change.

## Output

Lead with a concise verdict in the target venue's terms when known. Then provide:

1. a two- or three-sentence account of the contribution;
2. the strongest aspects of the paper;
3. major comments, ordered by likely effect on the review decision;
4. minor comments only when they are useful;
5. a short revision priority list.

Each major comment should state the paper-facing issue, why a reviewer would care, and a feasible revision. Refer to sections, pages, figures, tables, or manuscript lines when possible.

Do not edit the manuscript unless the user asks for revision. If a written review artifact is requested, save it beside the current manuscript with a dated, version-specific filename.
