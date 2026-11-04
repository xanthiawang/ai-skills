# Comment Taxonomy

Tag every stored comment with one **category** and one **fix-type**. This lets similar
future comments route to a known response shape.

## Categories

| Tag | Covers |
|---|---|
| `STUDY-DESIGN` | randomization, allocation, matching, blinding, trial registration, control-arm validity |
| `OUTCOME-VALIDITY` | confounds, measurement validity, what a score actually reflects, contamination between conditions |
| `STATISTICS` | choice of test, matched vs independent analysis, effect sizes, full-result reporting (not just "P<.001") |
| `CLAIMS-SCOPE` | over-claiming, generalization beyond sample, framing as preliminary/feasibility, clinical-benefit claims |
| `REPORTING-COMPLETENESS` | required statements — funding, AI-use disclosure, registration details, ethics, data/code availability |
| `FIGURES-TABLES` | non-permitted figure types, stand-alone captions (design/population/location/timeframe), table formatting |
| `FORMATTING-STYLE` | journal house style, word count, metadata, reference format |
| `PROCESS` | tracked-changes upload, response-letter formatting, file placement, transfer offers |
| `FRAMING-GAP` | research gap stated late or not at all, positioning against prior work unclear, conceptual leaps presented as established theory |
| `CLARITY-STRUCTURE` | hard-to-read abstract/introduction, undefined internal labels, thin or empty subsections, results placed in Methods, overlong introduction |
| `RQ-ALIGNMENT` | one RQ bundling several questions, an RQ naming something never tested, Methods/Results not organized by RQ |
| `RATIONALE` | theory, definition, coding rule, sample size, or system design choice stated without a reason |
| `INTERNAL-CONSISTENCY` | introduction claims contradicting own results, a construct defined one way and discussed another, numbers that disagree across sections |
| `SELECTIVE-REPORTING` | a favorable pooled/combined number emphasized while the strictest (holdout, primary) number is weaker |
| `CITATION-COVERAGE` | missing recent same-venue work, preprints cited instead of published versions |

## Fix-types

| Tag | Response shape |
|---|---|
| `reframe` | change wording/interpretation; no new data (e.g. "describe as nonrandomized", "frame as preliminary") |
| `add-statement` | insert a required block (funding, AI disclosure, registration line) |
| `re-analyze` | run a different/additional analysis (matched-pair primary, separate scoring) and report full results |
| `report-detail` | add a specific fact already known (registry number+date, number of sessions per participant) |
| `revise-artifact` | remake a figure/table/caption to comply |
| `register-or-justify` | provide trial registration, or justify its absence, or accept transfer |
| `process` | mechanical submission step (upload tracked copy, paste P2P) |

## House-style cross-reference

Anchors accumulate journal-specific patterns. When a journal recurs, note its fixed
requirements here so they are pre-loaded for the next paper:

- **JMIR family** — mandatory: funding statement (distinct from Acknowledgements; exact
  no-funding wording), generative-AI use disclosure, prospective trial registration for
  RCTs (else transfer to JMIR Formative Research), stand-alone table/figure captions,
  restricted figure types, clean + tracked-changes dual upload, P2P pasted (no formatting)
  into the editor notification.
- **ACM CHI (Papers)** — Assisted Desk Rejection is decided on readability and positioning
  before any statistics are read: a gap a reader can state by the end of the introduction's
  second paragraph, no undefined internal labels in the abstract, no one-sentence
  subsections, design decisions each with a rationale, Methods organized by RQ, every
  supplement the text mentions locatable, non-English figures translated, recent same-venue
  work cited, published versions over preprints.
- **Computers & Education** — keywords: at most 5, at least one from the journal list
  (technical check); construct operationalization and mechanism claims decide the outcome,
  so behavioral evidence must be worded as behavior; the editor may side with the more
  negative reviewer.
- **LAK / Journal of Learning Analytics** — rebuttal at most 500 words, flag-only (no new
  results); reviewers ask for the rationale of every coding definition, the effect of coding
  error on downstream analyses, sample-size justification, and release of coding prompts.
