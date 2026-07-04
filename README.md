# Albert agent skills

This repository is the source of truth for Albert's portable agent skills and
safe local agent setup. Installed skill folders in `~/.codex/skills/` and
`~/.claude/skills/` should be symlinks back into this checkout whenever
possible.

## Sync a machine

Clone or update the repository, then apply the managed setup:

```bash
git clone https://github.com/albert-ying/ai-skills.git ~/programs/ai-skills
cd ~/programs/ai-skills
./scripts/sync_agent_environment.sh apply
```

On a machine that already has the repository, use:

```bash
cd ~/programs/ai-skills
./scripts/sync_agent_environment.sh pull
```

The sync command deploys skills, applies safe Codex settings, and ensures local
MCP entries for Codex and Claude when the relevant CLIs are installed.

## What this repo syncs

- Personal skills under this repository.
- Symlinks into `~/.codex/skills/`, `~/.claude/skills/`, and Cursor rules.
- Safe Codex plugin preferences, including disabled Slack and Hugging Face
  plugin entries.
- Local MCP declarations for Codex, Claude, 1Password, Paperclip, Playwright,
  Screenpipe, and mobile MCP when available.

## What this repo must not sync

- OAuth tokens, API keys, `.env` files, and browser-extension tokens.
- `~/.codex/auth.json`, Codex or Claude logs, sqlite state, shell snapshots,
  session transcripts, and plugin caches.
- Personal data stores such as health databases, WeFlow tokens, Gmail
  credentials, and local Screenpipe databases.

Use 1Password or the local app login flow for secrets after the sync command
creates the non-secret MCP declarations.

## Maintenance rule

When an agent changes skills, MCP declarations, plugin choices, or agent
settings, it must update this repository, run
`./scripts/sync_agent_environment.sh apply`, verify with
`./scripts/sync_agent_environment.sh check`, and commit and push the result.
Do this as part of the work, not only when Albert asks for synchronization.
