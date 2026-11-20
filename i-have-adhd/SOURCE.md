# Source

- Upstream: https://github.com/ayghri/i-have-adhd
- Commit: 1ecea1993b7fce257ffbd686c070948b5e07eda6
- File: `skills/i-have-adhd/SKILL.md` (plus root `LICENSE`)
- License: MIT (see LICENSE)
- Imported: 2026-11-20
- Audit: SKILL.md read in full; pure Markdown, no scripts, no commands, no fetch or install instructions. PASS. The upstream repo's per-platform install scripts were not imported.

## Local changes

1. 2026-11-20: added `alwaysApply: true`, so `setup.sh` loads it every session (Claude @import, Codex AGENTS.md, Cursor alwaysApply). "stop adhd mode" still turns it off for one session.
2. 2026-11-20: added break-rule 7 so `writing-voice` governs deliverable text (papers, emails, reports) while these rules shape the chat reply.
