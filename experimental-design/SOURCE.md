# Source

- Upstream: https://github.com/K-Dense-AI/claude-scientific-skills
- Commit: ec59a29a03d5c40f73ab40878df04860bc00e876
- Path: `skills/experimental-design/` (SKILL.md, 4 references, 2 scripts) plus root `LICENSE.md`, copied as `LICENSE`
- License: MIT (repo LICENSE.md and the skill's frontmatter)
- Imported: 2026-11-21
- Audit: SKILL.md and both scripts read in full; the four references were scanned with grep for commands, network calls, credentials and injected instructions, not read line by line. The scripts use only numpy, pandas and pydoe; they make no network calls, write no files and start no processes. The references hold no commands, and their links point to methodology bodies such as NIST and CONSORT. PASS. The scripts were reviewed but not executed here, because running downloaded code was blocked by the permission check.

## Dependencies

- `scripts/randomization.py` needs numpy and pandas, which the conda `viz` environment already has (numpy 2.5.1, pandas 3.0.5).
- `scripts/doe_designs.py` also needs `pydoe==1.5.0`, which is not installed yet. Install it into `viz` when a factorial or response-surface design is first needed.

## Local changes

1. "Related skills": added a paragraph saying statistical-power, statistical-analysis, statsmodels and pymc are not installed standalone here, so that work is done inline.
2. "Citing Scientific Agent Skills": replaced the instruction to add K-Dense's paper to the user's references, and to fetch arXiv, with: tell Zixin in chat, and verify through CrossRef or OpenAlex before any citation. Reason: Zixin's authoring pipeline requires every citation to be verified and to carry an argument.

An older copy, dated 2026-07-06, sits inside `~/programs/academic-forge/skills/claude-scientific-skills/`. This standalone copy is the current one.
