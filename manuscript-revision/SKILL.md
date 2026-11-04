---
name: manuscript-revision
description: "Use when revising a scientific manuscript or its point-by-point (rebuttal) response for Zixin Wang — turning reviewer or coauthor comments into manuscript/response edits, marking changes (yellow [..]{.mark} highlight, gray custom-style reviewer text), updating citations, fixing figures, de-emphasizing method internals, reordering sections, or rebuilding the Quarto qmd-to-docx CLEAN/tracked-changes deliverables."
---

> **Zixin machine (2026-07-09, full Quarto adoption):** sources are `.qmd` — this skill's
> native format. Rebuild deliverables with `quarto render <draft>.qmd` (all formats, one
> command). The docx reference template is `~/programs/ai-skills/manuscript-revision/assets/template.docx`.

# Revising manuscripts + point-by-point responses

Reviewer/coauthor comments → edits to the manuscript and its point-by-point (P2P) rebuttal → rebuilt deliverables. This skill is the **judgment, house style, and the reusable build form (qmd markup + pipeline)** — but **not the project's paths** (concrete filenames/bib/build command live in the project CLAUDE.md and the YAML header).

> **Discover paper-specifics first.** The live bibliography, build command, figure locations, and file names live in the project's `CLAUDE.md`, its workspace memory (file-layout note), the manuscript's YAML header, and the build script. Read those before editing.

## Principles (non-negotiable)

1. **Data integrity.** Never fabricate data, numbers, citations, or results. Verify every claimed "inconsistency" against the actual file before changing it — automated findings are often wrong, and a verified-correct number stays.
2. **Don't expose weakness.** Confident, competitive framing. Reframe negatives as positives (3% error → 97% accuracy); describe the safeguard *mechanism*, not the past mistake. Keep every reviewer-demanded caveat.
3. **Reframe or demote, never delete or fabricate.** When a hit/row/claim becomes problematic, rename or down-rank it (preserving counts and structure); never invent a replacement.
4. **Plain published-journal prose** — no coined jargon, pitch-cadence, or AI tells.
5. **Sync across all copies; mark substantive changes; never touch a reviewer's question.**

## Comment library (anchors)

`comment-library/` is a local corpus of **real** editor/reviewer decision letters, parsed
into a consistent structure (see its `README.md` + `taxonomy.md`). Before writing a P2P,
check it for prior letters from the same journal — it pre-loads that journal's fixed
requirements (e.g. JMIR: prospective trial registration for RCTs or transfer to JMIR
Formative Research, funding statement distinct from Acknowledgements, mandatory
generative-AI disclosure, stand-alone captions, restricted figure types, clean+tracked
dual upload). Each stored comment is tagged with a **category** and a **fix-type**
(`reframe` / `add-statement` / `re-analyze` / `report-detail` / `revise-artifact` /
`register-or-justify` / `process`) so a recurring comment routes to a known response shape.
The library stores the *comment* and the *fix-type*, never an invented response — real
paper facts always come from the manuscript/authors. **Privacy:** `entries/` holds
third-party PII (author names, ms numbers, editor emails) and is gitignored — never commit
or transmit it.

## Template-conformance pass (final review ring, runs with the regression pass)

Before any conference/journal upload, fetch the venue's official template package (LaTeX
class + sample source, Word template if provided) and compare the rendered PDF **outline**
against the sample's section order and numbering: acknowledgments unnumbered (ACM `acks`,
hidden in anonymous mode), statements unnumbered, references before lettered appendices,
no one-sentence subsections. Verify with the PDF TOC (`fitz.get_toc()`) and `grep -c
'\\bibliography{' *.tex` = 1 — do not rely on the CfP page or comparable papers. Record the
template version and the checklist outcome in the submission manifest.

## Comment-library regression pass (final review ring)

Run the library the **other direction** as the last step before submission: instead of
answering a new letter, test the manuscript against **every stored comment** to catch a
recurring problem *before* a reviewer does (negative-preference regression). This is the
final ring of the review loop — run it after the manuscript is otherwise review-clean.

Procedure:
1. Build the anchor set = the structured comments across all `entries/*` (each already tagged
   category + fix-type) plus the per-letter "convergent themes". **Own-paper reject letters on
   the same topic are the highest-value anchors** — the reasons that killed the sibling paper
   are the ones most likely to recur; verify each is neutralized.
2. For each anchor, `grep` the manuscript for the vulnerable pattern (the term, the number, the
   missing statement) and classify: **HIT** (the problem is present) / **AT-RISK** (a defensible
   but probeable exposure) / **PASS** (grounded evidence it is defended). Evidence must be quoted
   from the manuscript, never assumed; declare `CANNOT VERIFY` where it needs human judgment.
3. Output a prioritized table (HIT → AT-RISK → PASS); route each HIT to its stored fix-type
   (`add-statement`, `reframe`, `re-analyze`, …) and apply via the normal Workflow.

Recurring required-statement anchors to always check: **GenAI-use disclosure** (research-method
use vs manuscript-prep, separately), funding statement distinct from Acknowledgements,
registration line, stand-alone captions. Recurring judgment anchors: mechanism/causal over-claim
from descriptive data, "non-significant ≠ no effect" (vote-counting), heterogeneous pooling
without invariance, internal number contradictions, RQ bundling.

**Writing anchors from Zixin's own rejections (2026-07 to 2026-11; entries for Computers & Education,
CHI 2027 ADR, LAK27).** Five patterns recurred across three venues and two manuscripts, so treat
them as habits to test for, not one-off fixes. Each maps to a taxonomy category:

| Pattern | Category | Grep / check in the manuscript |
|---|---|---|
| Behavioral evidence written as mechanism or causation | `CLAIMS-SCOPE` | `trap`, `self-reinforc`, `self-stabilis`, `mechanis`, `window`, `transfer fail`, `measures cognitive`; recommendations for an undeployed system |
| RQ bundles several questions, or names something untested | `RQ-ALIGNMENT` | count the questions inside each RQ; match each RQ phrase to a Results subsection that tests it; Methods ordered by RQ |
| Key choice with no stated reason | `RATIONALE` | theoretical framework vs alternatives, each borderline coding rule, sample size, every system-design decision |
| Introduction or definition contradicts own results | `INTERNAL-CONSISTENCY` | every prior-work number quoted in the introduction against the paper's own reanalysis; each construct's definition against its use in the Discussion |
| Reader cannot find what they need | `FRAMING-GAP`, `CLARITY-STRUCTURE`, `REPORTING-COMPLETENESS` | one-sentence gap by end of intro ¶2; no undefined labels in the abstract; no one- or two-sentence subsections; no results in Methods; supplements named and locatable; non-English figures translated |

**CHI clarity pass (required before any submission).** The CHI 2027 desk rejection was a
clarity rejection, not a statistics rejection: the abstract and introduction were "very difficult
to understand", the gap appeared only in Related Work, Section 3.1 "Design goals" was one sentence
with no goals, Section 4 mixed design, attrition and ethics and reported results under Measures,
and design decisions had no reasons. The reviewers' own summary misread the design. Before
submission, revise until each check passes, and keep the edits in `[..]{.mark}` like any other
substantive change:

| Check | Pass condition | What fixed it in StudyAI v51 |
|---|---|---|
| Outsider summary | A one-sentence summary written from title + abstract + intro alone states the design and contribution correctly | Rewritten abstract and introduction |
| Abstract labels | No term in the abstract is defined only later; condition, ratio and code names replaced by plain words | "session CO ratio", "Adaptive-first / Direct-first", "conventional proxies" removed |
| Single early gap | One gap sentence by the end of intro ¶2; Related Work opens with it and each subsection ends on it | Three scattered gaps replaced by one |
| Introduction length | About 800-900 words; results preview one paragraph | 1,392 to 839 words |
| No empty sections | Every heading delivers its content; no subsection under three sentences | Sec 3.1 rewritten as four goals with rationale; thin 3.4 and 3.6 merged |
| Methods order | Context and participants, design and procedure, measures, analysis by RQ; no results in Measures | Sec 4 reorganized; detector results moved to Results |
| Design rationale | One "why" sentence for every system or study component | Two-model split, concurrent calls, condensed prompt, trigger families, fading rule explained |
| Findable materials | Supplementary files named (S1, S2, ...) and cited at first use; non-English figures translated | S1-S5 labels; Fig 2 caption translation and appendix table |

Two single-letter anchors to check as well: a pooled number emphasized over a weaker holdout
number (`SELECTIVE-REPORTING`), and missing same-venue recent work or preprints left in place of
published versions (`CITATION-COVERAGE`). For coding-scheme papers, also report human-human
agreement next to machine-human agreement, and re-measure human agreement after any codebook
revision that merges or renames codes.

## Workflow

`grep` the exact phrase → edit the manuscript and/or write the response (in **all** P2P copies) → mark substantive new text → rebuild → verify. In a P2P the unit is: reviewer text → author **response** → the **quoted, highlighted** manuscript change.

## Build form & markup (qmd → docx)

The manuscript and the P2P are **Quarto `.qmd`** files rendered to `.docx` (`quarto render x.qmd`; pandoc underneath). This *form* is reusable across papers; only the filenames are project-specific.

**YAML header — the four knobs.** When the output looks wrong, one of these is why:

```yaml
format:
  docx:
    reference-doc: manuscript_style.docx   # carries the NAMED docx styles (incl. ReviewerComment = gray)
bibliography: /path/My Library.bib          # native [@key] citations resolve against this...
csl: /path/nature.csl                       # ...formatted by this CSL (Nature here)
resource-path: [., figure_rev1, ...]        # EVERY figure directory must be listed or the image won't embed
```

- Raw `[@key]` survives into the output → wrong bibliography/csl path, or the key is missing from the **live** bib.
- A figure doesn't embed → its directory isn't in `resource-path`.
- Styling reverts to plain/black → `reference-doc` not applied.

**Yellow highlight = `[changed text]{.mark}`.** Wrap every substantive new/changed manuscript passage in a pandoc span with the `.mark` class; pandoc renders it as a yellow `w:highlight` run. Inline stats and whole inserted paragraphs both get wrapped:

```
... in the same window ([ANCOVA P = 1.1 × 10^-23^]{.mark}). [An entire newly
inserted sentence or paragraph is wrapped like this.]{.mark}
```

Mark **only substantive content** (never trivial grammar). Keep the `[` … `]{.mark}` brackets balanced — that is exactly what "revision-highlight markup balanced" in the verify step checks.

**Gray reviewer comments (P2P) — two stages.**

1. *Source:* wrap reviewer text in a pandoc custom-style div, which maps to the `ReviewerComment` paragraph style (color `747474`). A state machine decides what is gray: **enter** gray on a referee header / section heading (Summary, Strengths, Weaknesses, …) / numbered point / bullet; **exit** to black on `**Response**`, a `>` blockquote, a `#` heading, a figure `![`, or a `**Figure/Table …` legend — so author responses, edit-labels, and quoted changes stay black.
2. *Reinforce after render:* set the gray as a **direct run color** (`747474`) on every ReviewerComment run. Word / Pages / Google Docs honor a paragraph **style** color inconsistently and will otherwise show the comments black; only LibreOffice honors the style alone.

**P2P unit (literal markup):**

```
::: {custom-style="ReviewerComment"}
**Referee #N (Remarks to the Author):**

<reviewer point, verbatim — never edited>
:::

**Response**: <author reply, black text>

> [<quoted manuscript change, exactly as inserted into the manuscript>]{.mark}
```

**Fabrication hard-stop (the syntactic checks won't catch this).** The quoted change must be the **actual** text you inserted into the manuscript — copy it, don't compose a plausible one — and every number, clock name, *P*-value, and `Table/Fig` reference in the response must be real. If you don't have the manuscript or the value, **STOP and retrieve it** (grep the manuscript/analysis output, read the YAML/CLAUDE.md, ask the author); never fill the template with a confident-looking placeholder, and never ship one. A unit with balanced `[…]{.mark}` brackets, one clean gray div, and no em-dashes can still be entirely invented — passing the form checks is **not** sufficiency.

**Deliverables — a triad per document (6 files total).** For BOTH the manuscript and the P2P:

- **CLEAN / NATIVE** — rendered doc, citations resolved, no markup (what an editor reads).
- **TRACKED-ALL** — every revision shown as a tracked change.
- **TRACKED-SELECTED** — only the *substantive* tracked changes (trivia pre-accepted).

Tracked changes are **generated, not hand-authored**: a script diffs a flattened **baseline** docx against the CLEAN/NATIVE render and emits `w:ins`/`w:del` runs (author + date; full vs selected mode). The build runs on **copies** in a fixed order: render → format tables (native) → redline-inject (baseline vs native) → repack → inject coauthor margin comments → gray-reviewer-runs → re-apply table formatting (redline rebuilds `document.xml` and drops direct table XML) → flatten reference-list tracking.

**Post-render docx passes** (pandoc's reference-doc can't express these):

- **Tables:** the reference-doc Table style is borderless/narrow, so wide top-N tables wrap badly — apply a direct-XML pass (cell borders, column widths rebalanced to the page content width, shaded bold header). Re-apply *after* redline-inject.
- **Reference list:** it is machine-built from the `.bib`, so tracked-changes there are noise — flatten the ref-list runs to clean text in the tracked deliverables.

## House style (Zixin Wang)

- **No em-dashes** (`—`); use commas/periods. (en-dash `–` in ranges is fine; single hyphen for compound modifiers.)
- **American spelling**; British only inside a verbatim citation title.
- **No coined/marketing terms** ("headline", "precision longevity medicine", "productivity aid", invented `-tail`/`q0`-style labels) and **no pitch-cadence** ("paradigm-shifting", "provides a foundation for", gratuitous "rather than X" negation).
- **No AI tells**: "autonomously", "deploys specialized", over-used "robust", "supports that"→"indicates", "Together with…", "the figure supports the interpretation", vague "diverse".
- **Genes**: italicize a gene/allele/microRNA *symbol when the genetic element is perturbed* (mouse Title-case, human ALL-CAPS); do **NOT** italicize the same letters naming a **protein, secreted factor, enzyme, or drug target**; never inside data tables; never change casing. A **spelled-out gene name** ("Klotho") follows the same perturbed-vs-protein logic, but the manuscript's house style may want the official **symbol** (*Kl* / *KL*) instead — match the manuscript's existing usage; don't silently switch name↔symbol.
- **Consistency**: match the manuscript's dominant figure-callout style and P-value casing; "two-sided" on t-test/Mann-Whitney but not ANOVA omnibus or correlation; "Fisher's exact".

## Point-by-point tone

- **Keep the thanks, cut the flattery**: "We thank the reviewer for this suggestion/point" — drop "forward-looking / exceptionally thorough / grateful". Cut "important / useful" only when they **flatter the reviewer** ("this important reviewer", "very useful review"); **keep** them when they qualify a **scientific noun** ("this important framing", "this important point") — the shipped P2P does.
- **Don't apologize easily**: remove "we apologize", "we agree this was an error / needed to be more cautious"; reframe to confident-neutral.
- **Never edit the reviewer's question.**
- **Adequacy check**: does the response answer the point, and does the quoted change actually *deliver* what the response claims? Verify against the manuscript. Watch over-conceding, defensive openers, and the same limitation signalled three times.

## Coauthor margin comments

When an anchoring script injects comments into a tracked-changes doc, **drop an uncertain anchor rather than mis-place it** (require a long, unique-paragraph match; raise the fuzzy threshold) — a comment on the wrong paragraph is worse than a missing one.

## Citations

**Two forms — know which one the manuscript is in.**

- **Manual/numeric (authoring form):** superscript callouts `^1^`, `^1,4^`, `^10--12^` in the body and a hand-written `# References` numbered list at the end. No bib, no CSL. Easy to drift (a renumber breaks every callout).
- **Native Pandoc (ready-to-send form):** `[@key]` / `[@key1; @key2]` callouts resolved by the YAML `bibliography:` + `csl:` pair; the formatted reference list renders where you place the auto-bibliography anchor `::: {#refs} :::`; add `link-citations: true`. This is what ships.

**Numeric → native is a deliberate late conversion, not hand work.** A script (project-local) does it end-to-end: parse the manual `# References` list → for each entry **validate the DOI via Crossref content negotiation** (`Accept: application/x-bibtex` against `doi.org`) and write a project-local validated `.bib` plus a `number/key/doi/status` validation TSV (fallback `@misc` when no DOI) → mint stable author-year keys (`refNN_firstauthor_year`) → replace every numeric callout `^1--3^` with `[@k1; @k2; @k3]` → swap the manual list for `::: {#refs} :::` and point the YAML at the new bib + `nature.csl`. **Two traps the converter must respect.** (1) *Scientific-notation exponents.* A **negative** exponent is safe — the leading `-` is a non-digit, so `10^-4^` / `10^-23^` are skipped. But a **positive bare** exponent (`10^6^`, `10^23^`) is indistinguishable from a citation callout `^6^` and **will be mis-converted to `[@ref6]`**. Before converting, grep the body for `\^[0-9]` and confirm none are powers; write any positive power as `10^{6}` or `$10^{6}$` so it cannot collide. (2) *Author affiliation superscripts* — convert only the body **after `# Introduction`**, never the author/affiliation block.

- **Never fabricate**; the DOI/Crossref validation above is how metadata is verified (also PubMed/paperclip/the journal). Don't hand-author BibTeX you didn't validate.
- Cite generously, **including the PI's own relevant work**, but honor the PI's call on which self-citations to avoid.
- **Update preprints to their published version in place — keep the citation key** so existing `[@key]` uses don't break.
- **Edit the bibliography the manuscript YAML actually points to** (stale duplicate `.bib` copies are the classic trap; sync the copies, fix the live one).
- A Discussion/scientific claim not backed by our own data needs a citation, or reframe it as a methodological rationale rather than an asserted fact.
- **Verify:** no raw `[@key]` survives the render; the `::: {#refs}` list actually populated; no **leftover citation superscript** `^N^` (a missed callout — distinguish from exponents `10^-4^`); new keys present in the **live** bib.

## Method/scoring internals: de-emphasize

Keep tuning internals out of the Results narrative — odd in-house words (e.g. "floor" → "minimum score of N"), penalty/bonus point values, caps, per-stratum parameter lists. Present **one holistic description**. If a pipeline part is an awkward/weak point, de-emphasize it: don't highlight it, and drop "how many entries were affected" counts. Detailed mechanism lives in **Methods**, and only in the specific response where a reviewer demanded transparency.

## Figures

- **Assembled or data-driven figures go stale after any data/score re-export.** Compare the assembled-figure mtime to its source panels/data; if older, **re-assemble/regenerate** (run the script), then rebuild the figure deliverable **and any document that embeds the figure** — a manuscript may carry only callouts while the rebuttal embeds the image.
- **A re-export changes the NUMBERS, not just the picture.** The stale surface is every in-text value, table cell, *P*-value, and rank that derives from that data — not only the embedded image. After a re-export, re-grep the changed quantities across the manuscript **and** the P2P and reconcile them; a refreshed figure beside an old in-text number is the classic miss.
- **Map figures by caption/content, not by filename number** — figure numbering and panel filenames drift apart across rounds.

## Sync trap (files exist in copies)

The P2P often has several rendered variants (plain source + a styled/grey render) — **edit them all**; they diverge in openers, wording, and punctuation (watch a Unicode minus `−` vs ASCII `-`). Don't hand-edit **generated** files (e.g. a figures `.qmd` a script rebuilds) — change the source it reads. `diff` the copies afterward.

## Section order

Match the journal. Nature research articles run Intro → Results → Discussion → **Methods** → back matter → Tables → References. Reorder by swapping whole `#`-header blocks (content-based comment anchoring survives reordering).

## Rebuild + verify

- Build via the project's script; PDFs need headless `soffice`, figure scripts need `MPLBACKEND=Agg`; `cp` may be aliased (use `/bin/cp -f`).
- **Verify after every rebuild**: **`ACCEPT==NATIVE`** first — accepting every tracked change in a TRACKED deliverable must reproduce the CLEAN/NATIVE render character-for-character (after normalizing quotes/dashes and dropping `w:del`/superscript); this is the load-bearing invariant that the tracked doc and the clean doc are the same paper. **But it does not check the baseline:** ACCEPT==NATIVE passes even when the redline was diffed against the **wrong/stale baseline** (so the tracked changes themselves are wrong) — separately confirm the baseline is the correct pre-revision version. Then: 0 em-dashes; revision-highlight `[…]{.mark}` brackets balanced; citations resolve in the rendered doc (no raw `[@key]`, no unresolved-key superscripts; new keys present in the **live** bib); P2P copies' figure refs identical; deliverable mtimes all post-date your last data/figure change.
- **Semantic gate, not just syntax**: the checks above are all *syntactic* — a fully fabricated response/quote passes every one. Before shipping, confirm each quoted change traces to a real manuscript edit and each number to a real analysis output (see the fabrication hard-stop above).
- **High-stakes passes**: redundant verification — 3–5 read-only agents on the *same* check; a finding ≥2 surface independently is real, singletons are usually false alarms.
- **Run the verifier** — `revision_lint.py` ships with this skill (paper-agnostic; all paths are args, mirroring `nature_figure_utils.py`). It mechanizes the objective checks above so they are a non-zero exit, not a re-derived regex an agent gets subtly wrong:
  ```
  python revision_lint.py --qmd manuscript.qmd --qmd p2p.qmd                     # source gate
  python revision_lint.py --clean NATIVE.docx --tracked TRACKED.docx --baseline BASELINE.docx   # docx gate
  ```
  Checks: em-dash, `[…]{.mark}` balance, bare-positive-exponent vs citation-superscript collision, raw `[@key]` survival, `ACCEPT==NATIVE` (reuses the proven walker), baseline-non-triviality. It **verifies, never authors** — it cannot fabricate. **Green lint is necessary, not sufficient** (it is syntactic): the fabrication/semantic gate still applies by hand.

## Reusable tools vs paper-specific FORM

What **ships with this skill** (paper-agnostic, verify-only): `revision_lint.py`. What stays **project-local** (documented here as FORM, not shipped): the *authoring* generators — the redline-inject baseline diff, the coauthor comment re-anchoring (per-paper anchor JSON), the gray-reviewer wrapper, and the numeric→native citation converter. They are content-emitting and carry paper-specific assumptions (a flattened baseline docx, a `#refs` anchor, a comment-source map), so shipping them would create silent-drift and a fabrication surface; reproduce them from the FORM above and keep them in the project. Rule of thumb: **ship verifiers, document generators.**

## Common mistakes (real failure modes)

| Mistake | Fix |
|---|---|
| Edited a stale duplicate `.bib` → citations render raw | Edit the bib named in the manuscript YAML. |
| Didn't re-assemble a figure after its panels/data changed | Compare assembled vs source mtime; re-run the script. |
| P2P edit applied to one copy only | Edit every variant; reconcile divergent openers/minus signs. |
| Marked trivial grammar in yellow | Mark only substantive changes. |
| Acted on an unverified "numerical inconsistency" | Verify against the file first (reference counts ≠ the actual set). |
| Unified two numbers that measure different things | Check what each metric measures before reconciling. |
| Removed a reviewer-demanded caveat | Keep them even while de-emphasizing weaknesses. |

## Scaled review

Fan out read-only finder agents by dimension (awkward expression, overclaim, numerical inconsistency, broken cross-reference, unaddressed-reviewer, comment-mislocation); **adversarially verify** before applying; apply only high-confidence, house-style-consistent fixes; **flag judgment calls** (reviewer-demanded vs gratuitous) for the author rather than deciding unilaterally.
