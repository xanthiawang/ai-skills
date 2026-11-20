# Source

- Upstream: https://github.com/ayghri/i-have-adhd
- Commit: 1ecea1993b7fce257ffbd686c070948b5e07eda6
- File: `skills/i-have-adhd/SKILL.md` (plus root `LICENSE`)
- License: MIT (see LICENSE)
- Imported: 2026-11-20
- Audit: SKILL.md read in full; pure Markdown, no scripts, no commands, no fetch or install instructions. PASS. The upstream repo's per-platform install scripts were not imported.

## Local changes

None. Frontmatter keeps `disable-model-invocation: true`, so Claude Code only runs it on `/i-have-adhd`; it stays on until "stop adhd mode" or "normal mode". Codex and Cursor do not read that field, so there it relies on the description saying to invoke it by command.
