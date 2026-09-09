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

## Output

Lead with a concise verdict in the target venue's terms when known. Then provide:

1. a two- or three-sentence account of the contribution;
2. the strongest aspects of the paper;
3. major comments, ordered by likely effect on the review decision;
4. minor comments only when they are useful;
5. a short revision priority list.

Each major comment should state the paper-facing issue, why a reviewer would care, and a feasible revision. Refer to sections, pages, figures, tables, or manuscript lines when possible.

Do not edit the manuscript unless the user asks for revision. If a written review artifact is requested, save it beside the current manuscript with a dated, version-specific filename.
