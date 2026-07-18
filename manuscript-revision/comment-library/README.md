# Revision Comment Library

A local corpus of **real** editor/reviewer decision letters **and coauthor pre-submission
feedback**, parsed into a consistent structure. It feeds the `manuscript-revision` skill in
two ways:

1. **Anchors** — real comments calibrate what reviewers actually demand (a journal's
   recurring asks: trial registration, matched-pair analysis, AI-use disclosure, funding
   statement, figure-type rules), so a P2P response is written to satisfy the *pattern*,
   not a guess.
2. **Response-strategy patterns** — each entry tags every comment with a category and the
   *type* of fix it needs (reframe / add-statement / re-analyze / re-score / register), so
   similar future comments route to a known-good response shape.

## Privacy (IMPORTANT)

Entries contain **third-party personal data** — real author names, manuscript numbers,
editor names and emails. Per Zixin's global rule ("never sync personal data stores"),
the `entries/` folder is **gitignored and never pushed**. Only this README, the schema,
and the category taxonomy are version-controlled. Do not commit or push `entries/*`.

## Layout

```
comment-library/
  README.md              # this file (committed)
  taxonomy.md            # comment categories + fix-types (committed)
  entries/               # real letters, one file per decision (LOCAL ONLY, gitignored)
    YYYY-MM_<journal>_<ms#>.md
  .gitignore             # ignores entries/
```

## Entry schema

Each file in `entries/` follows this front-matter + body:

```
---
journal: <name>            # e.g. JMIR Human Factors
ms_id: <manuscript #>
decision: <A accept | B minor | C revision&re-review | D major | reject>
due: <YYYY-MM-DD>
editor: <name>
received: <YYYY-MM-DD>     # date the letter arrived
status: <open | responded | resubmitted | accepted>
---

## Comments (structured)
For each comment: an ID, the verbatim text, a category tag, a severity, and the fix-type.

## Raw letter
The full pasted letter, verbatim, for reference.
```

## Adding a new entry

Paste the letter, then create `entries/YYYY-MM_<journal>_<ms#>.md` with the front matter,
split the editorial/reviewer comments into the structured list (tag each with a category
from `taxonomy.md` and a fix-type), and keep the raw letter at the bottom. Never fabricate
a response — the library stores the *comment* and the *fix-type*, not invented paper facts.
