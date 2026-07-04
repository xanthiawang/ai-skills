---
name: command-center
description: "Personal OS / Digital Twin — orchestrates screenpipe intelligence, vault knowledge, and external services into briefings, decisions, and autonomous actions."
---

# Command Center

**The Dendron Command Center turns Albert's vault into a digital twin — a system that knows what he knows, reasons with his priorities, and acts on his behalf.**

## When to Use

- **Session start**: Generate a morning/session briefing
- **"What should I focus on?"**: Priority analysis
- **"What was I doing N hours ago?"**: Screenpipe activity query
- **"Prepare for meeting with X"**: Meeting context prep
- **"Should I accept/do X?"**: Decision engine
- **"Triage stale items"**: Staleness sweep
- **"Draft a reply to X"**: High-risk draft (approval required)
- **Any dendron-add/query/generate pattern**: Pass through to existing skill

## Three-Tier Memory System

| Tier | File | Purpose | Refresh |
|------|------|---------|---------|
| **Working Memory** | `notes/_working-memory.md` | Hot index: today's focus, calendar, inbox, recent people, live tasks. | Every session |
| **Context Model** | `memory/command-center.md` | Medium-term: follow-ups, momentum, collaborator state, decision patterns. | End of each session |
| **Vault** | `notes/*.md` | Long-term: 419+ person profiles, projects, science notes, journals. | When data arrives |

**Always read in this order**: Working Memory → Context Model → Vault (as needed).

## Source Sync Matrix

Each data source has a defined cadence, output destinations, and cache key to avoid redundant fetches.

| Source | Cadence | Cache Key | Short-term Output | Long-term Output |
|--------|---------|-----------|-------------------|-----------------|
| **Calendar** | Every session | `_working-memory.md` header: `Calendar (synced HH:MM)` | Today's events + 7-day preview | Update `user.*.md` with last-meeting dates |
| **Email** | Every session | `_working-memory.md` header: `Email (synced YYYY-MM-DD)` | Inbox triage (Needs Action / Scheduled / Tracking) | Update `user.*.md` with new interaction context, new follow-ups → `command-center.md` |
| **Screenpipe** | Every session | `.cache/cc-screenpipe-YYYY-MM-DD-*.json` | Last 4-6 hours activity table | Daily journal entries, people interaction dates in `user.*.md` |
| **WeChat** | Every session (capped at 8 chats inline) + 6h pull cron + 5am notes cron | `_extracted/_weflow_state.json` (per-talker last_create_time), `_extracted/_weflow_note_state.json` (per-talker last_note_update_ts) | Inline note refresh of top-N most-active pending chats | Rewrite `## Recent (synced …)` in `user.*.md` for chats with new content |
| **Agent sessions** | Every session + twice-daily sync | `.cache/sync-state/session-sync-state.json` (processed transcript files) | `agent-session` sync manifest | Append important Codex/Claude decisions, corrections, capture requests, and managed file touches to `tool.agent-session-capture.md` or `_working-memory.md` |

### Sync Rules

1. **Check cache before fetching.** If a source's cache key shows it was synced today (or within 1 hour for calendar), skip re-fetch. User can say "refresh" to force.
2. **Short-term writes go to `_working-memory.md`.** This file is the single pane of glass for "what's active right now."
3. **Long-term writes go to vault notes.** When a source reveals a new person interaction, update the relevant `user.*.md` with the date and context. When a source reveals a follow-up, add it to `command-center.md`.
4. **People are the connective tissue.** Every source can surface people interactions. ALL of them should flow into the person's `user.*.md` note — not just the source that created the note originally.
5. **Incremental by default.** Never reprocess unchanged data. WeChat uses msg-count diff. Email uses date cache. Screenpipe uses preprocessor cache. Calendar is always live (it's cheap).

---

## Session-Start Briefing

### Step 0: Inject Live State

Run once at session start before any other agent dispatch. **Pick the template by day-of-week**:

```bash
SCRIPTS=/Users/A.Y/programs/ai-skills/dendron/command-center/scripts
TEMPLATES=/Users/A.Y/programs/ai-skills/dendron/command-center/templates
# Sunday → weekly-planning bundle; otherwise the default inline template.
if [ "$(date +%u)" = "7" ]; then
    python3 "$SCRIPTS/inject_live_state.py" --template "$TEMPLATES/sunday.md"
else
    python3 "$SCRIPTS/inject_live_state.py"
fi
```

The default template expands `${VAULT_DIR}`, `${SESSION_ID}`, `${TODAY}`, etc. and runs inline `` !`shell` `` snippets to surface: command-center health, proactive decision queue, sync-cache freshness, latest screenpipe cache filename, most recent daily journal, top 5 jsonl session ids, pending feedback memos, working-memory sync header, parked-conversations top, recent skill-insights, cold skills, and SKILL.md diffs since last session. One read replaces 5+ procedural Bash calls and keeps prompt cache hits high.

Other templates available for explicit use: `prep-meeting.md`, `park.md`, `review.md`. Pass any of them via `--template <path>`.

### Step 0.5: Health Gate + Proactive Queue

Run local health and queue checks before trusting cached context:

```bash
python3 "$SCRIPTS/healthcheck.py" --quiet
python3 "$SCRIPTS/proactive_queue.py" --limit 5
```

**Health gate rules:**
- If health returns `FAIL`, say what is broken and fix local state if possible before presenting a briefing.
- If health returns `WARN`, include the warning in the briefing and prefer live refresh for the stale source.
- If `session_index.db` is stale, run `python3 "$SCRIPTS/session_index.py" update` before using cross-session continuity.

**Proactive queue rules:**
- Treat the queue as the default candidate set for "what matters now."
- Show at most 5 items in briefings unless Albert asks for a full sweep.
- Each proactive suggestion must include source, reason, and one concrete next action.
- Do not send email, send drafts, delete events, or respond to invitations without explicit approval.

### Step 1: Check Cache

Read `.cache/cc-briefing-YYYY-MM-DD.json` in the vault directory. If it exists and is <1 hour old, present the cached briefing with: "Cached from {time}. Say 'refresh' for live data." Then skip to Step 4.

### Step 1.5: Launch Sync Pipeline (background)

Invoke the `/sync` skill in background mode. This dispatches calendar, email, screenpipe,
and wechat adapters in parallel. Manifests are applied by the vault-updater as they arrive.
The briefing agents (Step 2) run concurrently using cached state — they don't wait for sync.

The sync pipeline replaces the former inline email sync. See `ai-skills/dendron/sync/SKILL.md`.
It now includes `agent-session` capture so completed Claude Code and Codex transcripts
are audited during sync rather than only at voluntary session-end reflection.

### Step 1.6: Score Previous Session (background)

Launch the Session Scorer Agent as a background subagent. It scores the previous session while the briefing agents run in parallel — it does NOT block the briefing.

**Dispatch prompt** (use Agent tool with `run_in_background: true`):

```
You are the Session Scorer Agent. Read and follow the full instructions at:
/Users/A.Y/programs/ai-skills/dendron/command-center/scorer-agent-prompt.md

**Session to score**: Find the most recent COMPLETED session JSONL at:
~/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron-notes/
List ONLY top-level *.jsonl files (NOT inside subagents/ subdirectories).
Sort by modification time. Pick the SECOND-most-recent file (the most
recent is the CURRENT session). Read its UUID from the filename.

**Skip check**: Read .cache/interaction_scores/_last_scored.txt (if it exists).
If the session ID matches, skip scoring — already done.

**Feedback files**: Read all files matching feedback_*.md in:
/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron/memory/

**Gmail drafts**: Search the transcript for any tool_use blocks with
name "mcp__claude_ai_Gmail__gmail_create_draft". For each, extract the
draft ID from the subsequent tool_result block. Call gmail_read_message
with that ID to check status. If draft ID is not extractable, fall back
to gmail_search_messages with the subject and recipient.

**Output**: Write scored JSONL to:
notes/.cache/interaction_scores/YYYY-MM-DD.jsonl (append mode)

**Marker**: After scoring, write to:
notes/.cache/interaction_scores/_last_scored.txt
Format: SESSION_ID\nYYYY-MM-DDTHH:MM:SSZ

**Token budget**: If the session transcript exceeds 80K tokens (estimate
by file size: ~4 bytes per token, so >320KB), first summarize to just
user/assistant text content before scoring.

**Working memory**: After scoring, append one line to _working-memory.md
under ## Insights:
"Interaction scoring: [date] [N] interactions, [N]% accepted, [N] corrections ([top domain])"
```

**When it completes**: The background agent writes its output files silently. The briefing does not depend on scoring results — scoring is informational for the daily journal and weekly synthesis.

### Step 2: Dispatch 5 Parallel Agents (with sync pipeline running in background)

Send a **single message with 5 Agent tool calls** for maximum parallelism. Use the prompt templates below.

#### Agent 1: Calendar Agent (foreground)

```
You are the Calendar Agent for Albert's command center briefing.

**Task**: Get today's and next 7 days' events from Google Calendar.

**Optimization**: If the sync pipeline has already run this session (check for a fresh
`.cache/sync-state/calendar-manifest-*.json` file from today), read the manifest's working
memory changes instead of calling gcal_list_events again. Only call the API if no fresh
manifest exists.

**Steps**:
1. Call gcal_list_events for today and next 7 days
2. For each meeting, check if there's a matching vault note:
   - Look for meet.YYYY.MM.DD.md files
   - Look for user.*.md files matching attendee names
3. Flag meetings that have NO vault prep (new contacts, no past meetings)

**Output format** (markdown):
## Today's Events
- [time] [event name] — [attendees if any] — [vault links if found]

## Next 7 Days
- [date] [time] [event] — [notes]

## Needs Prep
- [events with unknown attendees or no past meeting notes]

**Constraints**:
- If calendar MCP is unavailable, output: "Calendar: unavailable (MCP not connected)"
- Never fabricate events
- Keep output concise
```

#### Agent 2: Continuity Agent (foreground)

```
You are the Continuity Agent for Albert's command center briefing.

**Task**: Determine what Albert was working on and what's unfinished — across the latest session AND the cross-session FTS5 index, not just yesterday's journal.

**Steps**:
1. Read `notes/_working-memory.md` (if it exists)
2. Read `memory/command-center.md` (context model)
3. Find the most recent `daily.journal.*.md` file and read its "State & Open Questions" and "Tasks" sections
4. **Cross-session threads (NEW 2026-04-27)**: query the FTS5 session index for unresolved markers across the last ~30 sessions:
   ```bash
   python3 ${SKILL_DIR}/scripts/session_index.py search "park OR parked OR carry-forward OR blocked OR awaiting" --limit 30
   ```
   Then for each parked thread in `tool.claude-parked-convos.md`, check whether the blocker mentioned in its "Status" column may have resolved since the row was logged (e.g., "waiting Harvard W-2 reprint" — has the W-2 actually arrived per recent inbox?).
5. Extract:
   - Current focus areas
   - Uncompleted tasks (- [ ] items)
   - Open questions from last session
   - Carry-forward items
   - **Parked threads with potentially resolved blockers** (NEW)

**Output format** (markdown):
## Last Session
- Date: [date]
- Focus: [what was being worked on]

## Carry-Forward
- [unfinished tasks with source links]
- [open questions]

## Cross-Session Threads
- [parked or blocked items from prior sessions whose blockers may have moved]

## Current Focus
- Primary: [main thing]
- Secondary: [other active items]

**Constraints**:
- Read REAL files, don't guess content
- If `_working-memory.md` doesn't exist, rely on daily journal + FTS5 query
- Quote specific tasks verbatim from source files
- For parked-thread freshness check: only flag if recent activity suggests the blocker resolved — never speculate
```

#### Agent 3: Staleness Agent (foreground)

```
You are the Staleness Agent for Albert's command center briefing.

**Task**: Find overdue tasks, stale projects, and forgotten follow-ups.

**Steps**:
1. Grep for "- [ ]" across recent daily.journal.2026.*.md and meet.2026.*.md files
2. For each unchecked task, calculate age (days since the file date)
3. Check proj.*.md files — flag any not updated in >30 days
4. Check meeting action items (meet.*.md) — flag follow-ups >7 days old

**Thresholds**:
- Tasks >14 days: "Needs Triage"
- Meeting follow-ups >7 days: "Overdue Follow-Up"
- Projects >30 days no update: "Stale Project"

**Output format** (markdown):
## Overdue Follow-Ups (>7 days)
- [task] — from [source file] — [age] days old

## Tasks Needing Triage (>14 days)
- [task] — from [source file]

## Stale Projects
- [project] — last updated [date]

**Constraints**:
- Only report items with REAL dates from filenames/timestamps
- Max 10 items per category
- Sort by age (oldest first)
```

#### Agent 4: Screenpipe Agent (foreground)

```
You are the Screenpipe Agent for Albert's command center briefing.

**Task**: Summarize recent activity from screenpipe data.

**Steps**:
1. Check for preprocessed cache files at notes/.cache/cc-screenpipe-YYYY-MM-DD-*.json
2. If cache exists, read and summarize sessions
3. If no cache, try running: python3 /Users/A.Y/programs/ai-skills/dendron/command-center/scripts/preprocess_screenpipe.py --date [today] --stats-only
4. If preprocessor fails, try the screenpipe MCP search-content tool for the last 2 hours
5. Summarize: what apps were used, what was being worked on, any notable interactions

**Output format** (markdown):
## Recent Activity
| Time Range | Activity | App | Duration |
|------------|----------|-----|----------|
| [times] | [what] | [app] | [min] |

## Key Observations
- [what's being actively worked on]
- [notable people interactions]

**Constraints**:
- If screenpipe is unavailable, output: "Screenpipe: unavailable"
- Summarize, don't dump raw data
- Focus on the last 4-6 hours
```

#### Agent 5: Insight Agent (background)

```
You are the Insight Agent for Albert's command center briefing.

**Task**: Find 0-2 non-obvious connections across the vault that are relevant NOW.

**Steps**:
1. Read notes/_index.by-person.md, notes/_index.by-project.md, notes/_index.by-topic.md
2. Cross-reference: are there people connected to multiple active projects?
3. Check: are there science notes relevant to current work that haven't been referenced recently?
4. Look for: deadline convergences, people who should be connected, papers relevant to active projects

**Rules**:
- MAX 2 insights. Zero is fine if nothing is genuinely interesting.
- Each insight must connect at least 2 vault entities
- Never force connections

**Output format** (markdown):
## Connections
- [Insight with specific vault links and reasoning]

OR

## Connections
(No non-obvious connections found today.)
```

### Step 3: Compose Briefing

After all foreground agents return, compose the briefing:

```markdown
# {Greeting}, Albert. {DayOfWeek}, {Month} {Day}

## Right Now
- [Calendar: today's events, linked to vault notes]
- [Screenpipe: what you were just doing, if data exists]
- [Continuity: carry-forward from last session]
- [Blockers: anything explicitly flagged]

## This Week
- [Upcoming meetings/deadlines, next 7 days]
- [Overdue follow-ups with age and source links]
- [Open meeting action items >7 days]

## Strategic View
- [Project momentum table from context model]
- [Grant/paper deadlines approaching]
- [Stale items needing triage (max 3)]

## Suggested Actions (max 5, ordered by urgency)
- [Use `proactive_queue.py --limit 5` as the first pass, then merge agent-specific findings]
- [Each with reasoning: "Because X deadline is in 3 days..."]

## Connections (only if Insight Agent returned something)
- [Cross-entity insights, 0-2 max]
```

**Deduplication**: If multiple agents surface the same item, show it once in the most relevant section.

### Step 3.5: Display via Claude Canvas

Render the composed briefing in a Claude Canvas tmux split (`spawn document --scenario display`) with `title: "Briefing — {DayOfWeek} {Month} {Day}"`. See the global preferences SKILL for the spawn command, scenario reference, and gotchas. This applies to briefings, TODOs, meeting prep, and any other multi-section command-center output.

### Step 4: Cache & Update

1. Write briefing JSON to `.cache/cc-briefing-YYYY-MM-DD.json`
2. Update `memory/command-center.md` with session date and any new follow-ups discovered
3. Update `_working-memory.md` with standardized sync headers and new data:

```markdown
## Source Sync Status
| Source | Last Synced | Status |
|--------|------------|--------|
| Calendar | YYYY-MM-DD HH:MM | ✓ |
| Email | YYYY-MM-DD | ✓ |
| Screenpipe | YYYY-MM-DD HH:MM | ✓ / unavailable |
| WeChat | YYYY-MM-DD HH:MM | ✓ N processed, M deferred / unavailable |
```

4. **Long-term writeback**: Handled by vault-updater via sync manifests. No manual writeback needed here.

---

## Screenpipe Intelligence Pipeline (Phase 2)

**Replaced by `screenpipe-sync` adapter.** See `ai-skills/dendron/sync/screenpipe-sync/SKILL.md`.

The screenpipe-sync adapter runs as part of the `/sync` pipeline at session start.
It consumes preprocessed screenpipe data and produces a manifest that the vault-updater
applies. The old Phase 2 JSON format (`file`/`action`/`risk`) is deprecated.

---

## Reactive Command Routing

When the user asks something, match to the appropriate handler:

**Presentation default**: Any multi-section markdown output (briefings, TODO lists, meeting prep, status summaries, decision analyses) should be rendered via Claude Canvas (`spawn document --scenario display`) when `$TMUX` is set. See Step 3.5 above. Single-sentence answers and tool-call confirmations stay inline.

| Pattern | Route | Risk |
|---------|-------|------|
| "What should I focus on?" | `proactive_queue.py` + context model + calendar + deadlines → canvas | Read-only |
| "What are my TODOs?" | Compile from working memory + context model → canvas display | Read-only |
| "What was I doing N hours ago?" | Query preprocessed screenpipe cache for that time window | Read-only |
| "What did I discuss with X?" | → invoke `dendron-query` with person intent | Read-only |
| "Draft a reply to X's email" | Read Gmail via MCP → draft in Albert's voice → **present for approval** | High-risk |
| "Update [project] status" | Edit proj.*.md frontmatter/content | Low-risk (auto) |
| "Mark X as done" | Find `- [ ]` in source note → change to `- [x]` | Low-risk (auto) |
| "Schedule follow-up with X" | `gcal_create_event` + meeting stub → **ask first** | High-risk |
| "Prepare for meeting with X" | Person profile + past meetings + recent screenpipe + calendar → canvas | Read-only |
| "Summarize my week/month" | → invoke `dendron-generate` with date range → canvas | Read-only |
| "Triage stale items" | Show staleness results, accept batch decisions | Mixed |
| "Should I accept [invitation/talk]?" | Decision engine (below) | Read-only |
| dendron-add/query/generate patterns | Pass through to existing skill | Varies |
| "/dendron improve" or "interaction quality report" | Weekly Synthesizer: read score files, generate report | Read-only |

---

## Proactivity Model

The command center should behave like a chief-of-staff layer, not a passive search tool. It should surface likely next actions before Albert asks, while keeping high-risk actions behind approval.

### Proactivity ladder

| Level | Agent may do | Approval required? |
|---|---|---|
| L0 Observe | Read local vault, caches, transcripts, sync manifests, Gmail/calendar metadata when relevant | No |
| L1 Surface | Rank tasks, flag stale state, identify conflicts, produce briefings and queues | No |
| L2 Prepare | Draft emails, calendar blocks, meeting agendas, project checklists, file bundles | Show before use |
| L3 Execute low-risk local edits | Mark local TODOs done when explicitly requested, update vault notes from confirmed facts, run local sync/index/health scripts | Usually no |
| L4 External action | Send email, send drafts, delete or move calendar events, reply to invitations, submit forms | Yes, explicit |

### Proactive triggers

Run `proactive_queue.py` when:
- session starts,
- Albert asks what to focus on,
- sync finishes and new HIGH inbox or deadline items appear,
- a meeting is within 24 hours and has no prep note,
- a parked blocker changes status,
- healthcheck reports stale context that could make advice unreliable.

### Ranking principles

Prefer items with hard deadlines, external waiting parties, expiring IDs or forms, overdue reviewer/editorial work, and tasks Albert explicitly owes. Suppress pure FYI, tracking-only, transparent calendar events, and recurring general lab events unless evidence says Albert must act.

---

## Decision Engine

When asked "Should I...?", "What should I prioritize?", or similar:

1. **Gather context**: Read relevant vault notes, calendar, screenpipe activity, context model
2. **Apply Albert's priorities**: From plan.md, stated goals, decision patterns in context model
3. **Reason transparently**: Show the factors considered, not just the conclusion
4. **Present as recommendation**: "I'd recommend X because [reasons]. But consider Y if [condition]."
5. **Never fabricate**: If data is missing, say so explicitly

### Decision factors to weigh:
- Calendar load (next 7 days)
- Active deadlines (grants, papers, applications)
- Project momentum (from context model)
- Energy patterns (how many consecutive days on same task?)
- Stated priorities (from plan.md and recent decisions)

---

## Self-Improvement Loop

The command center maintains itself across three nested cadences. Each phase has explicit triggers and writes to specific destinations — no implicit improvement, no surprise rewrites.

### Phase A — Per-turn memory nudge

After every substantive turn, before moving to the next user message, ask:

> *"Did this turn surface anything novel and load-bearing — a preference, a constraint, a relationship fact, a recurring obstacle, a validated approach? If yes, has it already been captured in `MEMORY.md` or a topic file?"*

If novel and missing:
- **User preference / correction / validated approach** → new `feedback_*.md` (lead with the rule, then **Why:** and **How to apply:** lines)
- **People / relationship fact** → update `user.<name>.md` directly in the vault
- **Project state change** → update the matching `project_*.md` in auto-memory or `proj.YYYY.<name>.md` in the vault
- **External resource pointer** → `reference_*.md`

Skip when: the fact lives in code/git already, was already saved, or is purely conversational. Default bias is **save when in doubt** — duplicate saves are cheap, missed rules cost rework.

### Phase B — Per-task skill review

When a non-trivial workflow completes (multi-step, took meaningful effort, or hit a sharp edge worth remembering), run a quick three-question check:

1. **Did any existing SKILL.md instruction prove wrong, stale, or missing a critical step?** → edit that SKILL.md inline. Commit alongside the work.
2. **Did the workflow follow a pattern likely to repeat?** → if yes, propose either a SKILL.md update OR a new skill (criteria below).
3. **Did a tool/script behave unexpectedly?** → log in the relevant `tool.*.md` vault note, with the failure mode and the fix.

Skill *promotion* criteria (when to write a new skill instead of just updating):
- The workflow was 5+ steps and not specific to a single project
- It required orchestrating 3+ tools or sources
- The user is likely to ask for it again by name in another session
- It has clear inputs, outputs, and a stable shape

Promotion target: `~/programs/ai-skills/<category>/<skill-name>/SKILL.md`. New skills must include a `description` frontmatter line and a "When to Use" section so future sessions can discover them.

### Phase C — Per-session reflection

Before parking or session end, the agent reflects:

1. **Run skill insights**: `python3 ${SKILL_DIR}/scripts/skill_insights.py --since 7 --print` — see which skills fired this week and which went cold (>30 days unused).
2. **Update session index**: `python3 ${SKILL_DIR}/scripts/session_index.py update` — keeps cross-session FTS5 search current.
3. **Snapshot SKILL.md state**: `python3 ${SKILL_DIR}/scripts/skill_diff.py --snapshot` — required for the next session's "Skill Changes Since Last Session" diff to be meaningful. Without this, the snapshot ages out and the diff degrades to noise.
4. **Audit MEMORY.md**: any entries that turned out to be wrong this session? Outdated project status? Update or remove now, not later.
5. **Carry forward to working memory**: surface any unresolved threads with explicit next-step text so the next session's continuity agent can pick them up cleanly.

The interaction scorer (Step 1.6) and weekly synthesizer (`/dendron improve`) are the higher-frequency expressions of this same loop — Phase C feeds them, they feed back into `feedback_*.md` files which Phase A respects.

### Cron jobs and the `[SILENT]` pattern

Long-running cron jobs (daily journal generation, screenpipe rollups, learning-queue digests) should emit nothing on uneventful days. Wrap with `silent_wrap.sh`:

```bash
${SKILL_DIR}/scripts/silent_wrap.sh -- claude "/dendron-screenpipe-journal" \
    "If nothing notable happened in the last 24h, reply with [SILENT]."
```

If the model returns `[SILENT]` as the last non-blank line, the wrapper drops the entire output — no log entry, no commit. Combine with `tick_lock.sh` for at-most-one execution:

```bash
${SKILL_DIR}/scripts/tick_lock.sh /tmp/cc-journal.lock 30 -- silent_wrap.sh -- <cmd>
```

This pattern fixes the sketchybar restart loop on `degraded` audio: gate the restart with a 30s tick lock so a flapping health probe can't fire 5 restarts in 90 seconds.

### Self-improvement helper scripts

| Script | Purpose | When to run |
|---|---|---|
| `inject_live_state.py` | Token + inline-shell expansion for live-state injection. Default template surfaces health, proactive queue, sync-cache, screenpipe, journal, parked-convos, skill insights, cold skills, skill-diff. Custom templates via `--template <path>` | Session start (Step 0) |
| `healthcheck.py` | Local operational healthcheck for stale syncs, missing working memory, missing/current daily journal, screenpipe cache, stale session index, and stale skill snapshot | Session start before trusting cached context; weekly review |
| `proactive_queue.py` | Conservative ranked queue from active inbox sections, live tasks, high-priority context items, and parked blockers. Produces source, reason, score, and next action | Session start, "what should I focus on?", post-sync triage |
| `decision_packets.py` | Backend bridge for cron/TUI. Combines health + proactive queue + active-process context, writes `.cache/command-center/decision-packets.json`, marks new/carried/removed items, adds `why_shown_now`, and can emit `[SILENT]` when unchanged | Cron/launchd report layer; consumed by `agent-dynamic-canvas decision-desk` |
| `prepared_actions.py` | Speculative preparation layer. Reads decision packets, applies a strict classifier, writes artifacts under `.cache/command-center/prepared-actions/`, marks concrete jobs `needs_draft` until `final.md` or `blocked.md` exists, promotes completed packets to `ready` or `blocked`, emits one-shot transition events, and maintains `.cache/command-center/action-ledger.json` for duplicate suppression | LaunchAgent after every decision packet refresh; TUI fire/modify/abandon/done layer |
| `prep_worker.py` | Headless background prep launcher for `needs_draft` actions. Starts bounded bypass-enabled `codex exec` jobs, records them in `.cache/command-center/prep-worker-jobs.json`, and tells workers to write `final.md` only when evidence is sufficient or `blocked.md` when source evidence/human input is missing. If Codex exits or times out without an artifact, the supervisor writes `blocked.md` so the desk does not stay at `draft` forever | LaunchAgent after prepared-action refresh; manual dry runs with `--dry-run --json` |
| `decision_daemon.sh` | LaunchAgent runner around `decision_packets.py --silent-if-unchanged`, `prepared_actions.py`, and `prep_worker.py`. On non-silent packets or one-shot prepared-action `ready`/`blocked` transitions, sends a local macOS banner by default; modal popup alerts are opt-in only | Installed at `~/.local/bin/command-center-decisions.sh`; run every 15 min by `com.dendron.command-center-decisions` |
| `session_index.py` | FTS5 over `*.jsonl` transcripts (build / update / search / stats) | Update at Phase C; query when resolving "we discussed earlier" references |
| `skill_insights.py` | Per-skill invocation counts + last-used timestamps + `cold_30d` bucket | Weekly via cron, or before Phase C |
| `reflect.py [<session_id>]` | Per-session digest: skills fired, tools errored, files/memory/drafts touched, repeated patterns, suggested actions | Phase C — before parking |
| `propose_skill.py <session_id>` | Detect repeated multi-step workflows (window=4, ≥3 occurrences), draft `_proposed/<slug>/SKILL.md`. Filters trivial single-tool loops | When `reflect.py` flags repeated patterns worth promoting |
| `memory_gc.py` | Auto-memory hygiene: stale (>90d), near-duplicates (Jaccard ≥0.55), broken MEMORY.md links, orphans, contradiction heuristic on feedback memos | Periodic — weekly or monthly |
| `skill_diff.py` | Track SKILL.md changes across `~/programs/ai-skills/`. Modes: `--since-days N` (git log), `--snapshot` (write hashes), `--since-session` (diff against snapshot). Catches agent-introduced regressions | Session start (default template) and after Phase B skill edits |
| `honcho_adapter.py` | Thin Honcho SDK client (write/query/mirror-session). Auto-no-ops when `HONCHO_BASE_URL` is unset. See `tool.honcho-ab.md` for the A/B protocol | Only when honcho services are running |
| `honcho_install.sh` | One-shot Honcho install: clones repo, configures `.env` with Anthropic key, brings up 4-service docker compose, installs SDK | Once, when starting the A/B |
| `enrich_user_profile.py` | Synthesize *operational* facts (optimizes for / avoids / what works / open threads) from existing `user.*.md` profiles via Claude API. Appends a clearly-marked, idempotent, reversible section. Dry-run by default; cost estimate via `--estimate-cost` (full sweep ≈ $7-8) | One-shot per user, or batch-with-confirm |
| `silent_wrap.sh` | Drop output if last line is `[SILENT]` | Wrap any noisy cron job |
| `tick_lock.sh` | flock-based at-most-one execution | Wrap any cron / restart loop that could flap |
| `preprocess_screenpipe.py` | Existing screenpipe rollup → cache | Background at session start |

### Live-state templates (`templates/`)

| Template | Use case |
|---|---|
| `prep-meeting.md` | Before a meeting — today's calendar, recent meet notes, pending action items, stale-interaction people, suggested attendee deep-dives |
| `park.md` | When parking a conversation — runs `reflect.py` inline, lists currently parked threads, runs `memory_gc.py`, includes the park-protocol checklist |
| `review.md` | Weekly review — skill insights, vault commits this week, memory diffs, stale tasks, project momentum, cold skills |
| `sunday.md` | Sunday planning — week ahead, active projects, HIGH inbox, parked threads, memory hygiene + cold skills, recurring Sunday events |

Invoke with: `python3 ${SKILL_DIR}/scripts/inject_live_state.py --template ${SKILL_DIR}/templates/<name>.md`

### Decision desk TUI

The vim-keybinding TUI lives in `/Users/A.Y/Desktop/Projects/agent-dynamic-canvas`
and consumes decision packets from this command-center backend.

Generate or refresh the packet:

```bash
python3 ${SKILL_DIR}/scripts/decision_packets.py --json
```

Open the TUI:

```bash
decision-desk
```

This opens the desk in a new tab of the current iTerm window. Use
`decision-desk --inline` to render in the current terminal. While open, the TUI
watches the cached packet and refreshes every 15 seconds. Use `--no-watch` for
a static snapshot.

Open with live regeneration:

```bash
cd /Users/A.Y/Desktop/Projects/agent-dynamic-canvas
bun run src/cli.tsx decision-desk --live --limit 8
```

Background dynamic refresh is installed as:

```bash
~/.local/bin/command-center-decisions.sh
~/Library/LaunchAgents/com.dendron.command-center-decisions.plist
```

The LaunchAgent runs every 15 minutes. It writes
`.cache/command-center/decision-packets.json`, appends logs to
`.cache/command-center-decisions-cron.log`, and notifies only when either
`decision_packets.py --silent-if-unchanged` emits a non-silent packet or a
prepared action transitions into `ready` or `blocked`. Repeated ticks stay
silent unless the packet changes, a prepared action changes state, or another material state
transition occurs. The default notification mode is
`COMMAND_CENTER_NOTIFY_MODE=notification`: a Notification Center banner with
sound, with no modal popup alert. Use `COMMAND_CENTER_NOTIFY_MODE=popup` or
`both` only when an interrupting modal alert is explicitly desired, and use
`none` to disable notifications.

After every packet refresh, the daemon also runs `prepared_actions.py`. That
script prepares artifacts before Albert is asked to fire anything, then
`prep_worker.py` launches at most one headless Codex worker for a `needs_draft`
action that has not recently been worked. The daemon waits up to
`COMMAND_CENTER_PREP_WORKER_WAIT_SECONDS` (default 300 seconds), then reruns
`prepared_actions.py` so the same tick can surface `ready` or `blocked`:

```bash
.cache/command-center/prepared-actions.json
.cache/command-center/prepared-actions/<action-id>-<slug>/
.cache/command-center/action-ledger.json
.cache/command-center/prep-worker-jobs.json
```

The classifier intentionally skips vague items such as "open the source thread
and resolve the next concrete step." It prepares only concrete,
approval-required actions with email/thread evidence. Concrete jobs start as
`needs_draft`; they are not presented as fire-ready until a real `final.md`
exists in the action artifact directory. If the worker cannot safely finish
from real evidence, it writes `blocked.md`; that becomes a `blocked` state and
prevents duplicate relaunches until the source changes. Worker timeouts or
missing-artifact exits are converted into supervisor-authored `blocked.md`
files, not left as invisible failures. `needs_draft -> ready`
and `needs_draft -> blocked` transitions create one notification event, then
stay quiet on later ticks. The ledger suppresses abandoned, done, fired,
fire-requested, or modified actions until the source fingerprint changes. In
the TUI, `d` marks a selected action as already done; use this when Albert
handled the item outside the board and it should not come back unless the
source changes.

The decision desk is an approval surface only. It may mark local review state in
the TUI session, but it must not send mail, reply to invitations, move calendar
events, or submit forms without an explicit separate approval command.

### Wired into cron (2026-04-27)

- `~/.local/bin/daily-journal.sh` — wrapped with `silent_wrap.sh`; prompt instructs the model to emit `[SILENT]` on uneventful days (machine off, no calendar, <5 screenpipe sessions, no audio).
- `~/.local/bin/daily-learning.sh` — wrapped; emits `[SILENT]` when the queue has no entries with status `queued`.
- `~/.config/sketchybar/plugins/screenpipe_status.sh` — restart now fires only on missing `/health`, not `degraded` audio. Restart wrapped with `tick_lock.sh /tmp/cc-sketchybar-restart.lock 0 --` (nonblocking) so concurrent ticks can't queue overlapping restarts. Backup at `screenpipe_status.sh.bak-20260427`.

---

## Weekly Interaction Scoring (`/dendron improve`)

When triggered (Sunday auto-prompt or explicit `/dendron improve`):

1. **Read score files**: Glob `.cache/interaction_scores/*.jsonl` for the past 7 days
2. **Read previous report**: Check for the most recent `report.interaction-quality.*.md`
3. **Read feedback files**: All `feedback_*.md` in auto-memory
4. **Read working memory**: Current `_working-memory.md` for priority analysis
5. **Dispatch Weekly Synthesizer**: Use the prompt at `command-center/weekly-synthesizer-prompt.md`
6. **Present report**: Show the report to Albert with proposals highlighted
7. **Wait for approval**: For each proposal, Albert can approve, reject, or modify
8. **Actuate approved changes**: Create/update `feedback_*.md` files or adjust working memory priorities as proposed
9. **Log rejections**: For rejected proposals, note in the report file: `**Status: REJECTED** — [Albert's reason if given]`

### Sunday Auto-Prompt

During Step 3 (Compose Briefing), if today is Sunday and `.cache/interaction_scores/` has score files from the past 7 days, append to the briefing:

> **Weekly interaction report ready.** Say `/dendron improve` to review patterns and proposed changes from this week's sessions.

---

## Meeting Context Prep

When a meeting is detected or "prepare for meeting with X" is requested:

1. **Identify attendees** → look up `user.*.md` profiles
2. **Find past meetings** → `meet.*.md` with same attendees
3. **Extract open threads** → unresolved `- [ ]` items from past meetings
4. **Check recent activity** → screenpipe data for work related to meeting topics
5. **Compose prep brief**: who they are, last interaction, open items, relevant recent work

Dispatch 3 parallel agents: (Person lookup, Past meetings, Recent activity).

---

## Autonomy Tiers

| Tier | Actions | Behavior |
|------|---------|----------|
| **Auto** | Update timestamps, mark tasks done, update context model, cache management, add progress notes | Execute silently, log in context model |
| **Draft & Present** | Draft emails, create calendar events, archive projects, send messages, create new notes | Show draft, wait for approval |
| **Read-only** | Queries, summaries, briefings, decision analysis, meeting prep | Always safe, no confirmation needed |

---

## Auto-Decay Thresholds

| Item Type | Threshold | Action |
|-----------|-----------|--------|
| Unchecked tasks (`- [ ]`) | >14 days | Surface in briefing "Needs Triage" |
| Meeting follow-ups | >7 days no completion evidence | Surface as "Overdue Follow-Up" |
| Project notes | No update >30 days | Flag for status review |
| Dismissed items | After user-set delay (default 14 days) | Re-surface once, then archive |

---

## Working Memory Management

### Update Triggers
- After Phase 2 screenpipe analysis completes
- After briefing composition
- When user explicitly changes focus
- At session end (auto-update)

### Vault Capture Rule (MANDATORY)
Every non-trivial task Albert asks me to do MUST produce a **Dendron vault note** (or update an existing one) BEFORE I report completion. The vault is his long-term memory; if work isn't captured there, it's lost the moment the session ends.

Route by task type:

| Task type | Hierarchy |
|-----------|-----------|
| System config / dotfile / script / MCP / hook | `tool.<name>.md` |
| Meeting or person interaction | `meet.YYYY.MM.DD.md` + update `user.<name>.md` |
| Project work, decisions, status | `proj.YYYY.<name>.md` |
| Research / scientific synthesis | `sci.<domain>.<topic>.md` |
| Reports, briefings, deep analyses | `report.<topic>.<date>.md` |
| Drafts (substantial) | Link from related proj/user/meet note |
| Decisions / reasoning | Embed in relevant proj/user/journal note |

Skip only for: pure lookups, typo fixes, acknowledgments, ephemeral diagnostics. Default bias is capture-over-skip.

Auto-memory carries one-line pointers only — never detail. See `feedback_capture_work_in_vault.md` for the full routing table, frontmatter template, and criteria. Non-negotiable.

### Daily Rollover
At end of day (or next morning's first session):
1. Read current `_working-memory.md`
2. Summarize key items into daily journal if not already captured
3. Reset working memory for new day, carrying over unresolved items

### Working Memory Template

```markdown
---
id: [existing-id]
title: Working Memory
desc: 'Hot index of current state - auto-updated by command center'
updated: [timestamp]
created: [existing-created]
---

## Current Focus
- **Primary**: [main task/project]
- **Secondary**: [other active items]
- **Context**: [brief description of where things stand]

## Today's Activity (from screenpipe)
| Time | Activity | Duration | Key Detail |
|------|----------|----------|------------|

## Live Tasks
- [ ] [task with source link]

## People Interacted With Today
- **[Name]**: [context] ([vault link])

## Recent Decisions
- [decision with date]

## Insights
- [observation or realization]
```

---

## Context Model Management

The context model (`memory/command-center.md`) persists across sessions.

### Auto-update (low-risk):
- Session date and focus
- Momentum scores (from vault timestamps + screenpipe)
- Collaborator last-contact dates
- Completed follow-ups

### Ask first:
- Priority changes
- Decision pattern updates
- Permanent suppressions
- Archiving projects

### Pattern Learning
After each decision recommendation:
- If Albert accepts → reinforce the pattern
- If Albert overrides → note the exception
- Patterns are descriptive ("tends to"), not prescriptive ("always")

---

## Integration with Existing Skills

| Skill | How Command Center Uses It |
|-------|---------------------------|
| `dendron-add` | Route content additions |
| `dendron-query` | Delegate person/project/topic queries |
| `dendron-generate` | Delegate report/summary generation |
| `dendron-sync-website` | Trigger when website data is stale |
| `detect-people` | Call when screenpipe surfaces unknown people |
| `screenpipe-query` | Ad-hoc screenpipe queries beyond preprocessed cache |
| `screenpipe-daily-journal` | Daily journal generation (complementary) |
| `interaction-scoring` | Score previous session, accumulate daily, synthesize weekly |

## External Services (via MCP)

| Service | Tools | Used For |
|---------|-------|----------|
| Google Calendar | `gcal_list_events`, `gcal_create_event`, etc. | Events, scheduling, meeting prep |
| Gmail | `gmail_search_messages`, `gmail_read_message`, `gmail_create_draft` | Email context, follow-ups, drafts |
| Screenpipe | `search-content`, `export-video` + `screenpipe://context` | Real-time activity, transcripts |
| PubMed | `search_articles`, `get_full_text_article` | Research context |
| bioRxiv | `search_preprints`, `get_preprint` | Latest preprints |

## Vault Data Sources

| Source | Query Method | Used For |
|--------|-------------|---------|
| `daily.journal.*.md` | Read latest, grep tasks | Continuity, task tracking |
| `meet.*.md` | Grep action items | Follow-up tracking, meeting prep |
| `proj.*.md` | Read frontmatter timestamps | Momentum scoring |
| `user.*.md` | Read profiles | People context |
| `_index.by-*.md` | Read directly | Cross-entity insights |
| `plan.md` | Read | Strategic priorities |
| `personal.grant.*.md` | Read, extract deadlines | Deadline tracking |
| SQLite `notes.db` | SQL queries | Fast metadata queries |
