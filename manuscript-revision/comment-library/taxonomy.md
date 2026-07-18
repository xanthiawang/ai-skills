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
