---
name: dendron-query
description: Query Albert's Dendron knowledge vault for people, projects, meetings, scientific topics, recent activity, and prior decisions.
---

# Dendron Query

**Query the Dendron knowledge base using indexes and SQLite for efficient information retrieval**

## When to Use

Use this skill when the user wants to:
- Find everything about a person
- Get project status and context
- Research a scientific topic
- Find recent meetings or notes
- Search by keyword or concept
- Prepare for meetings
- Generate summaries or reports

## What It Does

1. **Parses** natural language query to determine intent
2. **Routes** to appropriate entry point (by-person, by-project, by-topic, by-date)
3. **Traverses** graph to collect related notes
4. **Reads** relevant notes in context
5. **Synthesizes** information with proper citations
6. **Returns** structured response with source links

## Usage

```
@dendron-query [natural language query]
```

**Examples**:
- `@dendron-query Find everything about Vadim Gladyshev`
- `@dendron-query What's the status of the disaggregase project?`
- `@dendron-query Show all papers on protein design`
- `@dendron-query What did I discuss in meetings last week?`
- `@dendron-query Find notes mentioning AlphaFold`

## Query Types & Routing

### Person Query → Use `_index.by-person.md`
**Indicators**: "about [Person]", "related to [Person]", "with [Person]"

**Workflow**:
1. Read `_index.by-person.md` → find person's section
2. Follow links to: projects, meetings, papers, contact info
3. Check recent daily mentions:
   ```sql
   SELECT fname, raw FROM Note n JOIN Vault v ON n.vaultId=v.id
   WHERE v.fsPath='.' AND fname LIKE 'daily.journal.%'
   AND date(n.updated/1000,'unixepoch')>=date('now','-30 day')
   AND raw LIKE '%person-name%';
   ```
4. Synthesize overview with links

### Project Query → Use `_index.by-project.md`
**Indicators**: "project status", "about [Project]", "[Project] progress"

**Workflow**:
1. Read `_index.by-project.md` → find project section
2. Read main project file: `proj.YYYY.project-name.md`
3. Extract people, science, meetings from frontmatter
4. Check recent mentions:
   ```sql
   SELECT fname, raw FROM Note n JOIN Vault v ON n.vaultId=v.id
   WHERE v.fsPath='.' AND raw LIKE '%project-name%'
   ORDER BY updated DESC LIMIT 10;
   ```
5. Return status + context + next steps

### Topic Query → Use `_index.by-topic.md`
**Indicators**: "papers on", "research about", "all notes on", "topic"

**Workflow**:
1. Read `_index.by-topic.md` → find topic section
2. Collect all linked notes (projects, science, papers)
3. Content search if needed:
   ```bash
   rg "topic-keyword" notes/ -g "sci.*.md" -g "proj.*.md"
   ```
4. Organize by type (background, projects, papers)
5. Return structured summary

### Date/Time Query → Use date-based SQLite
**Indicators**: "last week", "recent", "today", "meetings in January"

**Workflow**:
1. Parse date range
2. Query daily + meeting notes:
   ```sql
   SELECT fname, raw, title FROM Note n JOIN Vault v ON n.vaultId=v.id
   WHERE v.fsPath='.' 
   AND (fname LIKE 'daily.journal.%' OR fname LIKE 'meet.%')
   AND date(n.updated/1000,'unixepoch')>=date('now','-7 day')
   ORDER BY fname DESC;
   ```
3. Extract key points
4. Return chronological summary

### Keyword Search → Use ripgrep + SQLite
**Indicators**: "find notes with", "search for", "mentions of"

**Workflow**:
1. Use ripgrep for fast content search:
   ```bash
   rg "keyword" notes/ --json | head -50
   ```
2. Or SQLite:
   ```sql
   SELECT fname, title FROM Note n JOIN Vault v ON n.vaultId=v.id
   WHERE v.fsPath='.' AND raw LIKE '%keyword%'
   ORDER BY updated DESC LIMIT 20;
   ```
3. Group by category (sci, proj, meet, etc.)
4. Return with context snippets

## Common SQL Queries

### Recent Activity
```sql
-- Last 7 days
SELECT fname, title, date(updated/1000,'unixepoch') as modified
FROM Note n JOIN Vault v ON n.vaultId=v.id
WHERE v.fsPath='.' 
AND date(updated/1000,'unixepoch')>=date('now','-7 day')
ORDER BY updated DESC;
```

### All Meetings with Person
```sql
SELECT fname, raw FROM Note n JOIN Vault v ON n.vaultId=v.id
WHERE v.fsPath='.' AND fname LIKE 'meet.%'
AND raw LIKE '%person-name%'
ORDER BY fname DESC;
```

### Papers on Topic
```sql
SELECT fname, title, desc FROM Note n JOIN Vault v ON n.vaultId=v.id
WHERE v.fsPath='.' AND fname LIKE 'user.%'
AND (raw LIKE '%topic%' OR tags LIKE '%topic%');
```

### Project Status
```sql
SELECT fname, title, raw FROM Note n JOIN Vault v ON n.vaultId=v.id
WHERE v.fsPath='.' AND fname LIKE 'proj.%'
AND raw LIKE '%status%active%';
```

## Response Format

Structure responses with:
1. **Summary** - Key findings in 2-3 sentences
2. **Details** - Organized by category or chronology
3. **Sources** - Links to all referenced notes
4. **Next Steps** - Suggested follow-up queries or actions (if applicable)

**Example Response**:
```
## Summary
Vadim Gladyshev is the PI of the lab, collaborating on 3 active projects (ClockBase, ClockBase Agent, Disaggregase). Most recent meeting: 2023-12-28.

## Active Collaborations
- [[Disaggregase|proj.2025.disaggregase]] - De novo tau-specific disaggregase design
- [[ClockBase Agent|proj.2025.clockbase-agent]] - AI system for aging interventions
- [[ClockBase|proj.2022.clockbase]] - Biological age profiling platform (completed)

## Recent Context
- Last meeting: [[2023-12-28|meet.2023.12.28]] - Year-end review
- Lab page: [[Gladyshev Lab|sci.lab.gladyshev]]
- Contact: [[user.vadim-gladyshev]]

## Related Research
- Focus: Aging biology, longevity interventions
- Key papers: [List from user.* references]

## Next Steps
- Review recent project updates
- Check daily notes for mentions
- Prepare for next meeting
```

## Advanced Features

### Multi-Entity Queries
```
@dendron-query Find connections between AlphaFold and disaggregase project
```
- Query both entities
- Find intersection (shared notes, people, topics)
- Visualize relationships

### Temporal Queries
```
@dendron-query What changed in disaggregase project since last month?
```
- Query project at time T1 and T2
- Compare status, people, notes
- Show diff/changelog

### Aggregation Queries
```
@dendron-query List all active projects with their status
```
- Query all `proj.*` files
- Extract status from frontmatter
- Generate table/summary

## Vault Selection

**The skill works from any directory:**
- **Default**: Queries the vault of the current working directory
- **Cross-vault**: Can query across all workspace vaults if requested

**How it determines the vault**:
1. Check for `dendron.yml` in current directory or parent directories
2. Read `workspace.vaults` to find vault list
3. Use vault where CWD is located (match `fsPath`)
4. User can explicitly request cross-vault queries

**Example**:
```bash
# Query current vault
@dendron-query Find everything about Vadim Gladyshev

# Query all vaults (if user explicitly requests)
@dendron-query --all-vaults Find notes about protein design
```

## Configuration

Reads from `dendron.yml` for:
- Active vault path (`workspace.vaults[].fsPath`)
- Index file locations
- SQLite database path
- Workspace root location

## Dependencies

- Access to `notes.db` SQLite database
- Filesystem access to `notes/` directory
- `_index.by-person.md`, `_index.by-project.md`, `_index.by-topic.md`
- ripgrep (`rg`) for content search

## Related Skills

- [[dendron-add]] - Add new information (smart router)
- [[dendron-generate]] - Generate content from notes

## References

- Query patterns: `[[_index.agent-patterns]]`
- Index files: `[[_index.by-person]]`, `[[_index.by-project]]`, `[[_index.by-topic]]`
