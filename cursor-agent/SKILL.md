---
name: cursor-agent
description: Spawn cursor-agent CLI instances from Claude Code to dispatch coding tasks, get second opinions, or run parallel work in headless mode. Use when you want to delegate a task to Cursor's AI agent.
---

# Cursor Agent — Cross-Tool Dispatch

Spawn `cursor-agent` CLI instances in headless mode from Claude Code. Dispatch coding tasks, get second opinions from different models, or run parallel work.

Default cost posture: use the best verified non-MAX model for long work. As of 2026-06-03, `cursor-agent models` and a smoke test confirmed `gpt-5.5-extra-high` is enabled locally. Do not use MAX variants for long tasks unless Albert explicitly approves token-billed MAX mode.

For long-running tasks that must not stop halfway, rely on the `raphel-loop` MCP exposed to Cursor Agent itself. Cursor Agent should be called once with `gpt-5.5-extra-high`; before it gives any final answer or stops, it must call `raphel_loop_checkpoint`. If the checkpoint returns `RAPHEL_DECISION: continue_work`, Cursor Agent must continue working inside the same interaction and call the checkpoint again before trying to stop.

## Quick Start

```bash
# Simple task - default long-task model (best verified non-MAX)
cursor-agent -p --output-format text --model gpt-5.5-extra-high --force --trust "Fix the type error in src/utils/parser.ts"

# Different model for a second opinion
cursor-agent -p --output-format text --model gemini-3.1-pro --force --trust "Review src/auth/middleware.ts for security issues"

# Read-only analysis
cursor-agent -p --output-format text --model gpt-5.5-extra-high --force --trust --mode plan "Analyze the test coverage gaps in this repo"

# Q&A mode
cursor-agent -p --output-format text --model gpt-5.5-extra-high --force --trust --mode ask "Explain the data flow from API request to database write"

# Isolated worktree
cursor-agent -p --output-format text --model gpt-5.5-extra-high --force --trust --worktree "Refactor the logging module to use structured logs"

# Different workspace
cursor-agent -p --output-format text --model gpt-5.5-extra-high --force --trust --workspace ~/Desktop/Projects/2026/Haven "Add input validation to the API endpoints"
```

## When to Use

```
Need to dispatch a task?
  ├── Want Claude models, stays in Claude Code context? → Use native Agent tool
  ├── Want GPT / Gemini / Grok models? → cursor-agent
  ├── Need Cursor-specific features (.cursorrules, Cursor MCP servers)? → cursor-agent
  ├── Want true process isolation (separate OS process)? → cursor-agent
  └── Running multiple independent tasks in parallel? → Multiple cursor-agent instances via parallel Bash calls
```

| Use cursor-agent when... | Use native Agent tool when... |
|--------------------------|-------------------------------|
| You want GPT-5, Gemini, Grok, or other non-Claude models | You want Claude models within Claude Code |
| You need Cursor-specific features (.cursorrules, Cursor rules) | Task is pure Claude Code work |
| You want true process isolation (separate process, no shared state) | Context isolation within Claude Code is enough |
| You need Cursor's MCP servers or extensions | Claude Code MCP servers suffice |
| You want to test the same task with a different AI stack | You're happy with Claude's response |

## Command Reference

### Core flags (always include)

| Flag | Value | Purpose |
|------|-------|---------|
| `-p` | (no value) | Headless/print mode — required for non-interactive use |
| `--output-format` | `text` | Plain text output to stdout |
| `--force` | (no value) | Auto-approve all tool calls |
| `--trust` | (no value) | Trust workspace without interactive prompt |
| `--approve-mcps` | (no value) | Approve configured MCP servers; include for long raphel-loop jobs |

### Defaults

| Flag | Default | Override |
|------|---------|---------|
| `--model` | `gpt-5.5-extra-high` | Any model from `cursor-agent models` |
| `--workspace` | Current working directory | Any absolute path |

### Optional flags

| Flag | Purpose |
|------|---------|
| `--worktree [name]` | Run in isolated git worktree (auto-named if no name given) |
| `--worktree-base <branch>` | Base branch for worktree (default: current HEAD) |
| `--mode plan` | Read-only planning/analysis mode — no file edits |
| `--mode ask` | Q&A mode — explanations and questions only, no edits |
| `--model <id>` | Override model (run `cursor-agent models` for full list) |

### Available models (notable)

| Model ID | Notes |
|----------|-------|
| `gpt-5.5-extra-high` | Default for long tasks. Best verified non-MAX model locally enabled on 2026-06-03. |
| `gpt-5.5-extra-high-fast` | Faster GPT-5.5 Extra High variant. Use when speed matters and it is still non-MAX. |
| `gpt-5.5-medium` | Lower-cost GPT-5.5 fallback when Extra High is unavailable or too expensive. |
| `claude-opus-4-8-high` | Claude non-MAX option. Avoid `max` variants unless explicitly approved. |
| `gemini-3.1-pro` | Google's top model |
| `grok-4.3` | xAI option shown by the local CLI |

Run `cursor-agent models` for the full current list. Before long jobs, prefer `gpt-5.5-extra-high`. If it disappears or errors, re-run a one-line smoke test in `--mode ask` and choose the strongest model that is not MAX.

## How to Dispatch

### Step 1: Construct the command

Always start with the core flags:

```bash
cursor-agent -p --output-format text --model gpt-5.5-extra-high --force --trust
```

Add optional flags as needed, then append the prompt as the final argument.

### Step 2: Write an effective prompt

Headless mode is **one-shot** — no back-and-forth. The prompt must be self-contained.

**Template:**
```
[TASK]: One-line description of what to do
[CONTEXT]: Relevant code, specs, error messages — paste inline
[WORKSPACE]: Which repo/directory (if not CWD)
[CONSTRAINTS]: What NOT to do (e.g., "don't modify tests", "don't add dependencies")
[OUTPUT]: What to return (summary of changes, code review, analysis)
```

**Rules:**
- **Self-contained** — include all context inline. The agent has no access to this conversation.
- **Specific output** — tell it exactly what to return.
- **Scoped** — one clear task. "Fix the auth bug" not "fix everything."
- **File-aware** — mention exact paths: `src/auth/middleware.ts:42`
- **Raphel checkpoint for long tasks** — tell Cursor Agent: "Before any final answer or stop, call the `raphel_loop_checkpoint` MCP tool. If it returns `continue_work`, continue implementation/verification in this same interaction."

### Step 3: Run via Bash

For durable long jobs, launch Cursor Agent once and make the checkpoint requirement explicit:

```bash
cursor-agent -p --output-format text --model gpt-5.5-extra-high --force --trust --approve-mcps \
  "TASK: Self-contained task prompt with success criteria.

RAPHEL LOOP REQUIREMENT:
Before any final answer or stop, call the raphel_loop_checkpoint MCP tool with status, summary, verification, remaining_work, and next_step. If it returns RAPHEL_DECISION: continue_work, continue implementation and verification inside this same Cursor Agent interaction. Only stop after raphel_loop_checkpoint returns finish_allowed."
```

If invoking from a client that exposes `raphel-loop` MCP directly, the wrapper tool remains available:

```text
Tool: start_cursor_loop
Arguments:
{
  "task": "Self-contained task prompt with success criteria",
  "workspace": "/absolute/path/to/repo",
  "model": "gpt-5.5-extra-high",
  "max_iterations": 12,
  "cursor_timeout_sec": 7200
}
```

Then poll:

```text
Tool: cursor_loop_status
Arguments: {"job_id": "<returned job_id>"}
```

If the MCP client does not expose `raphel-loop`, use the same loop directly:

```bash
~/programs/ai-skills/scripts/raphel_loop_mcp.py \
  --start "Self-contained task prompt with success criteria" \
  --workspace /absolute/path/to/repo \
  --model gpt-5.5-extra-high \
  --max-iterations 12 \
  --cursor-timeout-sec 7200

~/programs/ai-skills/scripts/raphel_loop_mcp.py --status <job_id>
```

Use the direct CLI path for shorter one-shot jobs:

```bash
# Run with timeout (300s = 5 min default)
timeout 300 cursor-agent -p --output-format text --model gpt-5.5-extra-high --force --trust "Your prompt here"
```

For long-running tasks where `raphel-loop` is unavailable, increase the timeout or omit it:

```bash
cursor-agent -p --output-format text --model gpt-5.5-extra-high --force --trust "Your prompt here"
```

### Step 4: Read the output

The full text output is returned to stdout. Read it, integrate the results, and decide next steps.

## Dispatch Patterns

### Pattern 1: Simple task

```bash
timeout 300 cursor-agent -p --output-format text --model gpt-5.5-extra-high --force --trust \
  "Fix the TypeError in src/utils/parser.ts:42. The error is 'Cannot read property map of undefined'. The input array can be null when the API returns no results. Add a null check. Return a summary of what you changed."
```

### Pattern 2: Parallel dispatch

Run multiple independent tasks simultaneously by making parallel Bash calls:

```bash
# Task 1 - in one Bash call
timeout 300 cursor-agent -p --output-format text --model gpt-5.5-extra-high --force --trust \
  "Fix failing tests in tests/auth.test.ts. Error: expected 401, got 200. Return summary."

# Task 2 - in a parallel Bash call
timeout 300 cursor-agent -p --output-format text --model gemini-3.1-pro --force --trust \
  "Fix failing tests in tests/api.test.ts. Error: timeout after 5000ms. Return summary."
```

**Important:** Parallel tasks must be independent — different files, different subsystems. If they touch the same files, run sequentially.

### Pattern 3: Worktree isolation

When the task might conflict with your current work:

```bash
timeout 600 cursor-agent -p --output-format text --model gpt-5.5-extra-high --force --trust \
  --worktree refactor-logging \
  "Refactor all logging in src/ to use structured JSON logs. Currently using console.log. Return summary of all files changed."
```

The worktree creates an isolated git branch. Review and merge results afterward.

### Pattern 4: Analysis / planning (read-only)

```bash
timeout 300 cursor-agent -p --output-format text --model gpt-5.5-extra-high --force --trust \
  --mode plan \
  "Analyze this codebase and identify: 1) Dead code that can be removed, 2) Functions with no test coverage, 3) Potential security issues. Return a structured report."
```

### Pattern 5: Second opinion with different model

```bash
# Get the default non-MAX GPT take
timeout 300 cursor-agent -p --output-format text --model gpt-5.5-extra-high --force --trust \
  --mode ask \
  "Review the architecture in src/core/. Is the event-driven approach appropriate? What would you change?"

# Get a Claude non-MAX take
timeout 300 cursor-agent -p --output-format text --model claude-opus-4-8-high --force --trust \
  --mode ask \
  "Review the architecture in src/core/. Is the event-driven approach appropriate? What would you change?"
```

### Pattern 6: Different workspace

```bash
timeout 300 cursor-agent -p --output-format text --model gpt-5.5-extra-high --force --trust \
  --workspace <your-project-workspace> \
  "Add input validation to all POST endpoints in src/api/routes/. Use zod schemas. Return summary."
```

## Error Handling

| Scenario | What happens | What to do |
|----------|-------------|------------|
| `command not found` | cursor-agent not installed | Install: `npm install -g @anthropic-ai/cursor-agent` or check `~/.local/bin/` is in PATH |
| Auth error | API key missing or expired | Tell user to run `! cursor-agent login` |
| Non-zero exit | Command failed | Read stderr output for diagnostics |
| Timeout | Task took too long | Break task into smaller pieces, or increase timeout |
| Empty output | Agent produced nothing | Re-run with `--output-format json` for diagnostics, or simplify the prompt |
| Worktree conflict | Branch already exists | Use a different worktree name or clean up old worktrees |

### Checking auth status

```bash
cursor-agent status
```

## Integration with Claude Code

This skill complements Claude Code's native Agent tool:

- **Native Agent tool** — spawns Claude sub-agents within Claude Code's process. Fast, shared MCP servers, Claude models only.
- **cursor-agent skill** — spawns a separate Cursor process. True isolation, access to all Cursor models (GPT, Gemini, Grok, Claude), Cursor-specific features.

Use both together for maximum coverage:
1. Use native Agent for tasks that benefit from Claude Code's context and MCP servers
2. Use cursor-agent for tasks that need different models, true isolation, or Cursor features
3. Dispatch both in parallel for independent tasks across different domains
