# Source

- Upstream: https://github.com/affaan-m/everything-claude-code
- Commit: 4adeee6732a12d1540f49a4d50a38ce8c97f9a53
- Files: `.agents/skills/change-impact/SKILL.md`, `.agents/skills/change-impact/agents/openai.yaml`, root `LICENSE`
- License: MIT (see LICENSE)
- Imported: 2026-11-21
- Audit: SKILL.md and openai.yaml read in full; pure Markdown and YAML, no scripts, no commands to run, no fetch or install instructions. The skill is read-only by default and treats repository content as evidence, not instructions. PASS.

## Local changes

1. 2026-11-21: added one paragraph under "Related Skills". The four skills it routes to (architecture-decision-records, contract-first, test-collaboration, module-regression) are not installed here, so their checks are done inline.

Role in this setup: the code-specific form of step 6 ("after-action reconciliation") of the full-chain rule in `global-preferences`.
