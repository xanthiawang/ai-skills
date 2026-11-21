# Source

- Upstream: https://github.com/K-Dense-AI/claude-scientific-skills
- Commit: ec59a29a03d5c40f73ab40878df04860bc00e876
- Path: `skills/scientific-critical-thinking/` (SKILL.md and 8 references) plus root `LICENSE.md`, copied as `LICENSE`
- License: MIT (repo LICENSE.md and the skill's frontmatter)
- Imported: 2026-11-21
- Audit: SKILL.md read in full; the eight references were scanned with grep for commands, network calls, credentials and injected instructions, not read line by line. The only executable route was an optional OpenRouter figure command, which was removed (see below). Reference links point to methodology bodies such as Cochrane, GRADE, EQUATOR and FDA. PASS.

## Local changes

1. "Visual Aids": removed the command for the uninstalled scientific-schematics skill, which sends prompts to the third-party OpenRouter API. Figures now point to the nature-schematic skill, draw.io or matplotlib, matching Zixin's figure defaults. The frontmatter `compatibility` line was updated to match.
2. "Citing Scientific Agent Skills": same change as in experimental-design. Do not add K-Dense's paper to deliverables yourself; tell Zixin, and verify through CrossRef or OpenAlex before any citation.

An older copy, dated 2026-07-06, sits inside `~/programs/academic-forge/skills/claude-scientific-skills/`. This standalone copy is the current one.
