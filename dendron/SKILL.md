---
name: dendron
description: Collection of Dendron vault management skills for adding notes, querying the knowledge base, generating reports, syncing from website, detecting people, configuring vault settings, and the command center digital twin.
---

# Dendron Skills

Manage the Dendron knowledge vault at `~/Documents/Manual Library/Dendron/notes`. These skills handle the full lifecycle of note management: adding content, querying information, generating reports, syncing external sources, and detecting people from screenpipe data.

The vault uses Dendron's hierarchical note structure (`meet.*`, `user.*`, `proj.*`, `sci.*`, `daily.*`, etc.) with a SQLite database (`notes.db`) for fast queries and index files (`_index.by-person.md`, `_index.by-project.md`, `_index.by-topic.md`) for navigating relationships.

## Sub-Skills

| Skill | When to Use |
|-------|-------------|
| **dendron-add** | Adding any information to the vault (meetings, papers, projects, people, science notes, journal entries). Auto-classifies and routes to the correct hierarchy. |
| **dendron-config** | Setting up or switching Dendron vault paths. Auto-detects vault from CWD or reads saved config. |
| **dendron-generate** | Creating papers, reports, summaries, bibliographies, or literature reviews by synthesizing existing notes. |
| **dendron-query** | Finding information in the vault -- people, projects, topics, recent activity, or keyword search. |
| **dendron-sync-website** | Syncing bio, publications, grants, and project info from the Hugo website into Dendron. |
| **detect-people** | Creating user entries for people detected in screenpipe data, with AI-driven validation and web search enrichment. |
| **command-center** | Personal OS / Digital Twin — session briefings, interaction scoring (PRM-based), screenpipe intelligence pipeline, decision engine, meeting prep, task triage. Orchestrates all other dendron skills + external services (calendar, email, screenpipe). |
| **sync** | Vault sync pipeline — orchestrates Calendar, Email, Screenpipe, and WeChat adapters to continuously update all vault notes. Use `/sync` to run manually. |
| **session-sync** | Promotes important completed Claude Code/Codex transcript signals into sync manifests so decisions, corrections, and capture requests land in vault notes during `/sync`. |

---

## dendron-add

# Dendron Add (Smart Router)

**Universal entry point for adding ANY information to Dendron knowledge base with automatic routing**

### When to Use

Use this skill when the user wants to add information to their Dendron vault, including:
- Meeting notes or transcripts
- Paper references (PDF, DOI, arXiv)
- Project updates or status changes
- Person information or contact details
- Science concepts or research notes
- Daily journal entries
- Any unstructured content that needs categorization

### What It Does

1. **Analyzes** content to determine type (meeting, paper, project, person, science, daily)
2. **Extracts** entities (people, dates, topics, citations)
3. **Routes** to correct category automatically (meet.*, user.*, proj.*, sci.*, daily.*, scratch.*)
4. **Auto-categorizes** science notes by domain keywords
5. **Creates** note with rich frontmatter for structured queries
6. **Updates** all indexes (main + year + cross-reference)
7. **Commits** changes with clear message

### Usage

```
@dendron-add [content]
@dendron-add [file path]
@dendron-add [URL or DOI]
```

**Examples**:
- `@dendron-add "Met with Vadim today to discuss protein disaggregase project..."`
- `@dendron-add ~/Downloads/paper.pdf`
- `@dendron-add https://arxiv.org/abs/2021.12345`
- `@dendron-add "Project update: Disaggregase Phase 1 completed..."`

### Classification Logic

The skill uses indicators to automatically classify content type:

#### Meeting Indicators -> `meet.YYYY.MM.DD.md`
- Date patterns: "Jan 20", "2026-01-20", "meeting on..."
- People references: "with @name", "attendees:", names in title
- Meeting verbs: "discussed", "met with", "call with", "talked about"
- Action items: "TODO", "[ ]", "follow up", "action item"

#### Paper Indicators -> `user.authorYYYY.md`
- DOI: `10.xxxx/xxxxx`
- arXiv: `arXiv:YYYY.NNNNN`
- Author patterns: "et al.", "Author1, Author2, and Author3"
- Abstract markers: "Abstract:", "Summary:", "Introduction:"
- Journal names: "Nature", "Cell", "Science", "published in"

#### Project Indicators -> `proj.YYYY.project-name.md`
- Status keywords: "active", "paused", "completed", "progress", "milestone"
- Project names: Check existing `proj.*` files
- Update patterns: "Update:", "Status:", "Progress:"
- Timeline language: "Phase 1", "v1.0", "deadline"

#### Person Indicators -> `user.firstname-lastname.md`
- Contact info: email addresses, phone numbers
- Affiliations: university names, "Professor", "PhD student", "Dr."
- Roles: "PI", "collaborator", "colleague", "postdoc"
- Bio markers: "Research interests:", "Background:", "CV"

#### Science Indicators -> `sci.[domain].[topic].md`
- Domain keywords (see domain classification below)
- Technical terms: equations, algorithms, mechanisms, methods
- Protocol markers: "Methods:", "Protocol:", "Procedure:", "Steps:"
- Tool names: "AlphaFold", "RoseTTAfold", software names

#### Daily/Personal -> `daily.journal.YYYY.MM.DD.md`
- Diary-like language: "Today I...", "feeling", personal reflections
- Daily observations without clear structure
- Personal notes not fitting other categories

#### Ambiguous -> `scratch.YYYY.MM.DD.HHMMSS.md`
- If classification confidence <80%, route to scratch
- Flag for manual review
- User can later recategorize

### Domain Classification (for sci.* notes)

Auto-categorize science notes by keyword matching:

```yaml
biology: [protein, gene, cell, DNA, RNA, expression, genetic, biological, organism]
math: [equation, theorem, proof, statistics, probability, calculus, derivative, integral]
physics: [force, energy, quantum, thermodynamics, entropy, physical, particle]
ml: [neural, network, training, model, algorithm, deep learning, transformer, machine learning]
disease: [cancer, alzheimer, diabetes, pathology, symptoms, therapeutic, disease]
protein-design: [structure, folding, alphafold, rosetta, design, binder, computational]
tools: [software, pipeline, workflow, CLI, API, install, configuration, package]
protocol: [method, procedure, assay, protocol, steps, experimental, laboratory]
review: [review, summary, meta-analysis, literature, survey]
ideas: [hypothesis, idea, proposal, brainstorm, concept, theory]
```

**Multi-match resolution**:
- Use most specific domain (e.g., "protein-design" over "biology")
- If equal specificity, use primary keyword frequency
- Default to "ideas" if scientific but no clear domain

### Workflow

#### Step 1: Accept Input
- Read content from string, file path, or URL
- If file: read contents
- If URL: fetch and parse (handle DOI, arXiv, PDF)

#### Step 2: Analyze & Classify
```python
# Calculate confidence scores for each category
scores = {
    'meeting': count_meeting_indicators(content),
    'paper': count_paper_indicators(content),
    'project': count_project_indicators(content),
    'person': count_person_indicators(content),
    'science': count_science_indicators(content),
    'daily': count_daily_indicators(content)
}

# Get highest scoring category
category = max(scores, key=scores.get)
confidence = scores[category] / sum(scores.values())

# If confidence <80%, route to scratch
if confidence < 0.8:
    category = 'scratch'
```

#### Step 3: Extract Entities
- **People**: Use NER + regex for names, cross-check with existing `user.*` files via SQLite
- **Dates**: Parse various formats, convert to Dendron format `YYYY.MM.DD`
- **Projects**: Extract capitalized phrases, check against existing `proj.*` files
- **Topics**: Extract key concepts, map to sci.* domains
- **Citations**: Extract DOIs, arXiv IDs, author names

**SQLite query to check existing notes**:
```sql
SELECT fname FROM Note n JOIN Vault v ON n.vaultId=v.id
WHERE v.fsPath='.' AND fname='target.note.id';
```

#### Step 4: Generate Filename
Follow Dendron conventions:
- **Meeting**: `meet.YYYY.MM.DD.md` (from extracted date)
- **Paper**: `user.firstauthorYYYY.md` (from author + year)
- **Project**: `proj.YYYY.project-name.md` (check existing or create)
- **Person**: `user.firstname-lastname.md` (lowercase, hyphenated)
- **Science**: `sci.[domain].[topic].md` (auto-categorized domain)
- **Daily**: `daily.journal.YYYY.MM.DD.md` (today's date)
- **Scratch**: `scratch.YYYY.MM.DD.HHMMSS.md` (timestamp)

#### Step 5: Create Note with Rich Frontmatter

**CRITICAL**: All notes MUST include these required Dendron fields:
- `id`: Unique alphanumeric string (generate using random lowercase alphanumeric, 23 chars)
- `title`: Note title
- `desc`: Brief description (can be empty string)
- `updated`: Unix timestamp in milliseconds (current time)
- `created`: Unix timestamp in milliseconds (current time)

**Meeting**:
```yaml
---
id: AbC123xYz456789012345  # Generate unique 23-char alphanumeric ID
title: [Extracted or ask user]
desc: '[Brief description]'
updated: 1706457600000  # Unix timestamp
created: 1706457600000  # Unix timestamp
date: 2026.01.28  # Custom field
attendees:
  - user.person1
  - user.person2
projects:
  - proj.YYYY.project-name
topics:
  - extracted-topics
---
```

**Paper**:
```yaml
---
id: xYz789AbC012345678901  # Generate unique 23-char alphanumeric ID
title: "[Paper title]"
desc: '[Brief description]'
updated: 1706457600000  # Unix timestamp
created: 1706457600000  # Unix timestamp
authors:
  - Author1
  - Author2
year: YYYY
journal: [Journal name]
doi: [if available]
domains:
  - auto-categorized-domain
topics:
  - extracted-topics
related_projects:
  - proj.YYYY.project-name
---
```

**Project**:
```yaml
---
id: pQr456xYz890123456789  # Generate unique 23-char alphanumeric ID
title: [Project name]
desc: '[Brief description]'
updated: 1706457600000  # Unix timestamp
created: 1706457600000  # Unix timestamp
status: active
start_date: YYYY.MM.DD
people:
  - user.person1
topics:
  - extracted-topics
related_science:
  - sci.domain.topic
---
```

**Science**:
```yaml
---
id: stu123def456789012345  # Generate unique 23-char alphanumeric ID
title: [Topic name]
desc: '[Brief description]'
updated: 1706457600000  # Unix timestamp
created: 1706457600000  # Unix timestamp
domain: [auto-categorized]
subdomain: [if applicable]
related_papers:
  - user.authorYYYY
related_projects:
  - proj.YYYY.project-name
---
```

**How to generate the ID**:
```python
import random
import string
import time

def generate_dendron_id():
    """Generate a 23-character lowercase alphanumeric ID for Dendron"""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(23))

def get_timestamp_ms():
    """Get current Unix timestamp in milliseconds"""
    return int(time.time() * 1000)

# Usage
note_id = generate_dendron_id()  # e.g., "a1b2c3d4e5f6g7h8i9j0k1l"
timestamp = get_timestamp_ms()   # e.g., 1706457600000
```

#### Step 6: Cascading Index Updates

Update all relevant indexes (use diff-based updates, not full rewrites):

1. **Main category index**: `meet.md`, `user.md`, `proj.md`, etc.
   - Add entry with one-line summary
   - Keep chronological or alphabetical order

2. **Year/month indexes**: If applicable
   - `meet.YYYY.md`, `meet.YYYY.MM.md`
   - `proj.YYYY.md`

3. **Cross-reference indexes**:
   - `_index.by-person.md` (if people involved)
   - `_index.by-project.md` (if project mentioned)
   - `_index.by-topic.md` (if topics identified)

#### Step 7: Show Preview & Confirm
```
Classification: Meeting Note
Confidence: 92%
Route: meet.2026.01.28.md
Attendees: Vadim Gladyshev, Alex Tyshkovskiy
Projects: proj.2025.disaggregase
Topics: protein design, tau aggregation

Creating note with rich metadata...
Updating indexes:
  - meet.md
  - meet.2026.md
  - _index.by-person.md (Vadim Gladyshev, Alex Tyshkovskiy)
  - _index.by-project.md (Disaggregase)

Proceed? (Y/n)
```

#### Step 8: Commit
```bash
git add notes/meet.2026.01.28.md notes/meet.md notes/meet.2026.md notes/_index.*
git commit -m "Add: meeting - Discussion with Gladyshev lab on disaggregase design"
```

### Entity Extraction Details

#### People Names
- Regex: `\b[A-Z][a-z]+ [A-Z][a-z]+\b` (Title Case)
- Cross-check with existing `user.*` files:
  ```sql
  SELECT fname FROM Note WHERE fname LIKE 'user.%';
  ```
- Convert to Dendron format: `firstname-lastname` (lowercase, hyphenated)
- If not found, ask user: "Create new person entry for [Name]?"

#### Dates
- Parse various formats:
  - "Jan 20, 2026", "January 20 2026"
  - "2026-01-20", "20-Jan-2026", "1/20/2026"
  - "today", "yesterday"
- Convert to Dendron format: `YYYY.MM.DD` (dots, not hyphens)

#### Citations
- **DOI**: `10\.\d{4,}/[\S]+`
- **arXiv**: `arXiv:\d{4}\.\d{4,}`
- **Author extraction**:
  - From "Author et al. (YYYY)" pattern
  - From bibtex/citation strings
  - From PDF metadata

#### Projects
- Look for capitalized multi-word phrases
- Cross-reference with existing projects:
  ```sql
  SELECT fname, title FROM Note WHERE fname LIKE 'proj.%';
  ```
- If ambiguous, ask user: "Add to existing project [Project A] or create new?"

#### Topics
- Extract noun phrases
- Map to existing tags:
  ```sql
  SELECT fname FROM Note WHERE fname LIKE 'tags.%';
  ```
- Cross-reference with `_index.by-topic.md` categories

### Safety & Validation

#### Before Creating
1. **Check for duplicates**:
   ```sql
   SELECT fname FROM Note WHERE fname='proposed.note.id';
   ```
2. **Validate date format**: Must be `YYYY.MM.DD`
3. **Confirm ambiguous classifications**: If confidence <80%

#### Never Do
- Overwrite existing notes without confirmation
- Create notes with spaces or special characters in filename
- Skip frontmatter metadata
- Forget to update indexes

### Advanced Features

- **Batch Adding**: `@dendron-add --batch [folder path]` -- process all files in a folder
- **Force Category**: `@dendron-add --force-category=meeting [content]` -- skip classification
- **Dry Run**: `@dendron-add --dry-run [content]` -- preview without creating files

---

## dendron-config

# Dendron Configuration

Universal configuration system for Dendron skills. Auto-detects vault location or allows manual configuration.

### Auto-Detection

Dendron skills automatically detect your vault by:

1. **Current directory**: Check if you're inside a Dendron vault
2. **dendron.yml**: Look for `dendron.yml` in parent directories
3. **Workspace config**: Read from VSCode/Cursor workspace settings
4. **Saved config**: Use `~/.cursor/dendron-config.json`

### Manual Configuration

Set vault explicitly:

```bash
@dendron-config set /Users/A.Y/Documents/Manual Library/Dendron/notes
```

Or configure multiple vaults:

```bash
@dendron-config add-vault personal ~/Dendron/personal
@dendron-config add-vault work ~/work/dendron-vault
@dendron-config set-default personal
```

### Configuration File

Location: `~/.cursor/dendron-config.json`

```json
{
  "default_vault": "personal",
  "vaults": {
    "personal": {
      "path": "/Users/A.Y/Documents/Manual Library/Dendron/notes",
      "db_path": "/Users/A.Y/Documents/Manual Library/Dendron/notes.db"
    },
    "work": {
      "path": "/Users/A.Y/work/dendron-vault",
      "db_path": "/Users/A.Y/work/dendron.db"
    }
  },
  "screenpipe": {
    "enabled": true,
    "auto_journal": true
  }
}
```

### Vault Detection Logic

```python
def find_vault() -> str:
    # 1. Check saved config
    if config_exists():
        return load_config()['default_vault']

    # 2. Check current directory
    cwd = os.getcwd()
    if is_dendron_vault(cwd):
        return cwd

    # 3. Search parent directories for dendron.yml
    for parent in get_parents(cwd):
        if (parent / 'dendron.yml').exists():
            return str(parent / 'notes')

    # 4. Ask user
    return prompt_for_vault()
```

### Commands

| Command | Description |
|---------|-------------|
| `@dendron-config set /path/to/vault` | Set default vault |
| `@dendron-config list` | List configured vaults |
| `@dendron-config add-vault <name> <path>` | Add a vault |
| `@dendron-config use <name>` | Switch active vault |
| `@dendron-config current` | Show current vault |

All Dendron skills (dendron-add, dendron-query, dendron-generate) use this configuration automatically.

---

## dendron-generate

# Dendron Generate

**Generate papers, reports, summaries, and bibliographies from Dendron knowledge base**

### When to Use

Use this skill when the user wants to:
- Write a paper or report from research notes
- Generate literature review from collected papers
- Create project summary or status report
- Compile bibliography from references
- Synthesize information across multiple notes
- Create presentation or talk outline

### What It Does

1. **Identifies** relevant notes using indexes (by-topic or by-project)
2. **Collects** all related notes (projects, science, papers, meetings)
3. **Reads** notes in logical order (background -> methods -> results)
4. **Synthesizes** information with proper structure
5. **Cites** sources using Dendron/Zotero format `[[@authorYYYY]]`
6. **Generates** formatted content in requested style
7. **Saves** as new note: `report.YYYY.MM-topic.md`

### Usage

```
@dendron-generate [topic/project] as [format]
```

**Formats**: `paper`, `report`, `summary`, `bibliography`, `presentation`, `review`

**Examples**:
- `@dendron-generate disaggregase project as report`
- `@dendron-generate protein design as literature review`
- `@dendron-generate aging research as bibliography`
- `@dendron-generate ClockBase as project summary`

### Workflow

#### Step 1: Identify Scope
Parse user request to determine:
- **Topic** or **Project** focus
- **Format** (paper, report, summary, etc.)
- **Optional**: Date range, specific sections

#### Step 2: Collect Relevant Notes

**For Project-based Generation**:
1. Read `_index.by-project.md` -> find project section
2. Get main project file: `proj.YYYY.project-name.md`
3. Follow links to collect: related science notes, papers, meeting notes, people

**For Topic-based Generation**:
1. Read `_index.by-topic.md` -> find topic section
2. Collect all linked notes: science, papers, projects
3. SQLite query for additional mentions:
   ```sql
   SELECT fname, raw, title FROM Note n JOIN Vault v ON n.vaultId=v.id
   WHERE v.fsPath='.' AND (
     fname LIKE '%topic%'
     OR raw LIKE '%topic-keyword%'
   );
   ```

#### Step 3: Organize Notes by Type

Group collected notes:
- **Background**: `sci.*` domain and concept notes
- **Methods**: `sci.protocol.*`, project methodology
- **Results**: Project files, meeting notes with findings
- **References**: `user.*` paper notes

#### Step 4: Generate Content

**Paper Structure**: Abstract, Introduction, Methods, Results, Discussion, References

**Report Structure**: Executive Summary, Background, Progress, Current Status, Next Steps, References

**Bibliography Structure**: Annotated entries grouped by year with citation, summary, key findings, relevance

**Literature Review**: Introduction, thematic/chronological organization, synthesis, conclusion, bibliography

#### Step 5: Add Proper Citations

Use Dendron/Zotero format:
- **Inline**: `[[@authorYYYY]]` or `[@authorYYYY; @authorYYYY]`
- **Full citation**: Extract from `user.authorYYYY.md` frontmatter

#### Step 6: Save Generated Content

Create new note as `report.YYYY.MM-[topic-name].md` with full Dendron frontmatter (id, title, desc, updated, created) plus custom fields (date_generated, format, topic, sources).

#### Step 7: Commit
```bash
git add notes/report.YYYY.MM-topic.md
git commit -m "Generate: report - [Topic] [Format]"
```

---

## dendron-query

# Dendron Query

**Query the Dendron knowledge base using indexes and SQLite for efficient information retrieval**

### When to Use

Use this skill when the user wants to:
- Find everything about a person
- Get project status and context
- Research a scientific topic
- Find recent meetings or notes
- Search by keyword or concept
- Prepare for meetings
- Generate summaries or reports

### What It Does

1. **Parses** natural language query to determine intent
2. **Routes** to appropriate entry point (by-person, by-project, by-topic, by-date)
3. **Traverses** graph to collect related notes
4. **Reads** relevant notes in context
5. **Synthesizes** information with proper citations
6. **Returns** structured response with source links

### Usage

```
@dendron-query [natural language query]
```

**Examples**:
- `@dendron-query Find everything about Vadim Gladyshev`
- `@dendron-query What's the status of the disaggregase project?`
- `@dendron-query Show all papers on protein design`
- `@dendron-query What did I discuss in meetings last week?`

### Query Types & Routing

#### Person Query -> Use `_index.by-person.md`
**Indicators**: "about [Person]", "related to [Person]", "with [Person]"

1. Read `_index.by-person.md` -> find person's section
2. Follow links to: projects, meetings, papers, contact info
3. Check recent daily mentions via SQLite
4. Synthesize overview with links

#### Project Query -> Use `_index.by-project.md`
**Indicators**: "project status", "about [Project]", "[Project] progress"

1. Read `_index.by-project.md` -> find project section
2. Read main project file: `proj.YYYY.project-name.md`
3. Extract people, science, meetings from frontmatter
4. Check recent mentions via SQLite
5. Return status + context + next steps

#### Topic Query -> Use `_index.by-topic.md`
**Indicators**: "papers on", "research about", "all notes on", "topic"

1. Read `_index.by-topic.md` -> find topic section
2. Collect all linked notes (projects, science, papers)
3. Content search with ripgrep if needed
4. Organize by type and return structured summary

#### Date/Time Query -> Use date-based SQLite
**Indicators**: "last week", "recent", "today", "meetings in January"

```sql
SELECT fname, raw, title FROM Note n JOIN Vault v ON n.vaultId=v.id
WHERE v.fsPath='.'
AND (fname LIKE 'daily.journal.%' OR fname LIKE 'meet.%')
AND date(n.updated/1000,'unixepoch')>=date('now','-7 day')
ORDER BY fname DESC;
```

#### Keyword Search -> Use ripgrep + SQLite
**Indicators**: "find notes with", "search for", "mentions of"

```sql
SELECT fname, title FROM Note n JOIN Vault v ON n.vaultId=v.id
WHERE v.fsPath='.' AND raw LIKE '%keyword%'
ORDER BY updated DESC LIMIT 20;
```

### Common SQL Queries

```sql
-- Recent activity (last 7 days)
SELECT fname, title, date(updated/1000,'unixepoch') as modified
FROM Note n JOIN Vault v ON n.vaultId=v.id
WHERE v.fsPath='.' AND date(updated/1000,'unixepoch')>=date('now','-7 day')
ORDER BY updated DESC;

-- All meetings with a person
SELECT fname, raw FROM Note n JOIN Vault v ON n.vaultId=v.id
WHERE v.fsPath='.' AND fname LIKE 'meet.%' AND raw LIKE '%person-name%'
ORDER BY fname DESC;

-- Papers on a topic
SELECT fname, title, desc FROM Note n JOIN Vault v ON n.vaultId=v.id
WHERE v.fsPath='.' AND fname LIKE 'user.%'
AND (raw LIKE '%topic%' OR tags LIKE '%topic%');

-- Active projects
SELECT fname, title, raw FROM Note n JOIN Vault v ON n.vaultId=v.id
WHERE v.fsPath='.' AND fname LIKE 'proj.%' AND raw LIKE '%status%active%';
```

### Response Format

Structure responses with:
1. **Summary** -- Key findings in 2-3 sentences
2. **Details** -- Organized by category or chronology
3. **Sources** -- Links to all referenced notes
4. **Next Steps** -- Suggested follow-up queries or actions (if applicable)

### Advanced Features

- **Multi-Entity Queries**: Find connections between two entities (shared notes, people, topics)
- **Temporal Queries**: Compare project state at different time points
- **Aggregation Queries**: List all active projects with status summaries

---

## dendron-sync-website

# Dendron Sync Website

**Sync information from personal Hugo website to Dendron knowledge base**

### When to Use

Use this skill when the user wants to:
- Update Dendron notes from their website content
- Sync bio, CV, publications, research, grants from website
- Keep personal information current across platforms
- Extract publications from website to create user.* references
- Update project descriptions from website research page

### What It Does

1. **Reads** Hugo website content from `/Users/A.Y/Desktop/Projects/website/kejunying.com/content/`
2. **Extracts** structured information: bio, CV, publications, research projects, grants, talks
3. **Updates** corresponding Dendron notes (`personal.*`, `personal.grant.*`, `proj.*`, `user.*`)
4. **Preserves** existing Dendron content (merge, don't overwrite)
5. **Commits** changes with clear message

### Usage

```
@dendron-sync-website
@dendron-sync-website --section=bio
@dendron-sync-website --section=publications
@dendron-sync-website --section=grants
@dendron-sync-website --dry-run
```

### Website Structure

**Hugo content location**: `/Users/A.Y/Desktop/Projects/website/kejunying.com/content/`

**Key files**:
- `about/index.md` -- Bio, contact information, current position
- `cv/Ying_cv.qmd` -- Full CV with education, research experience, grants, publications
- `research/index.md` -- Research highlights and publication list
- `talks/index.md` -- Presentations and talks

### Sync Workflows

#### Sync Bio & Contact Info
**Source**: `content/about/index.md`
**Extract**: Current position, affiliations, contact info, bio paragraph
**Update**: `personal.md` or `personal.history.md`

#### Sync Grants & Fellowships
**Source**: `content/cv/Ying_cv.qmd` (Grants section)
**Extract**: Grant name, agency, title, period
**Update**: `personal.grant.*` files

#### Sync Publications
**Source**: `content/research/index.md` or `cv/Ying_cv.qmd`
**Extract**: Author list, title, journal, year, DOI
**Update**: Create/update `user.firstauthorYYYY.md`, update `user.md` index

#### Sync Research Projects
**Source**: `content/research/index.md` or `content/cv/Ying_cv.qmd`
**Extract**: Project names, descriptions, status, collaborators
**Update**: Existing `proj.*` files

### Safety & Validation

- **Backup**: Ensure git is clean before syncing
- **Dry-run**: Show what would change without making edits
- **Merge strategy**: Preserve existing Dendron content, don't overwrite
- **Conflict resolution**: Flag mismatches for user review

### Configuration File

Create `.dendron-sync.json` in vault root:
```json
{
  "website_path": "/Users/A.Y/Desktop/Projects/website/kejunying.com",
  "last_sync": "2026-01-28T12:00:00Z",
  "sync_sections": ["bio", "grants", "publications", "projects"],
  "auto_commit": true,
  "dry_run": false,
  "merge_strategy": "preserve_dendron"
}
```

### Extraction Patterns

**DOI**: `https?://doi\.org/(10\.\d{4,}/[\S]+)` or `10\.\d{4,}/[\S]+`

**Author Parsing**: `K Ying, S Paulson, A Eames, ..., VN Gladyshev` -> First author: Ying -> `user.ying2025`

**Grant Period**: `\hfill 2025 -- 2028` -> start_date: 2025, end_date: 2028

---

## detect-people

# Detect People - AI-Driven Validation

Create user entries for people detected in screenpipe data. Uses AI judgment to filter false positives.

### Usage

```bash
@detect-people 2026-01-30
```

### Agent Instructions

#### 1. Extract candidates
```bash
python3 ~/.cursor/skills/dendron/detect-people/scripts/extract_candidate_names.py [date]
```

Returns JSON with OCR/audio candidates and existing users.

#### 2. Validate with AI judgment

For each candidate, determine if it's a real person:
- Real person with professional context -> Create entry
- Audio name matching existing user phonetically -> Link to existing
- UI element, device name, OCR artifact -> Skip

**Examples to skip**: "App Store", "HyperX SoloCast", "Enhanced Context", "Starting VideoCapture"

#### 3. Create entries with ALL fields filled

**CRITICAL**: Never use placeholders like "[To be filled]". Every entry must be immediately populated.

For each validated person:
1. Web search for: name + "professor" OR name + "researcher" OR name + university
2. Extract: institution, role, email (if public), bio summary
3. Create entry with ALL information filled

**Generate proper node ID**:
```python
import random
import string
import time

def generate_dendron_id():
    """Generate 23-char lowercase alphanumeric ID"""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(23))

def get_timestamp_ms():
    """Get current Unix timestamp in milliseconds"""
    return int(time.time() * 1000)
```

Template:
```markdown
---
id: m8kj3n9p4q5r6s7t8u9v0w1  # Generate 23-char lowercase alphanumeric ID
title: {Full Name}
desc: '{one-line role/institution}'
updated: 1706457600000  # Unix timestamp in milliseconds
created: 1706457600000  # Unix timestamp in milliseconds
---

## Contact Info

- Email: {actual email if found}
- Institution: {actual institution}
- {Website/profile URLs}

## Role & Expertise

{Title/role}

{Brief research/expertise summary}

## Context

**How we connected**: Detected from journal/screenpipe

**Date**: {date}

**Context**: {screenpipe interaction context}

## Notes

{Any relevant observations from context}
```

**If web search finds nothing**: Skip creating the entry (likely false positive).

#### 4. Return detected people for journal linking

Return JSON with all people mentioned (new + existing):
```json
{
  "people": [
    {"name": "Jin Yap", "slug": "jin-yap", "status": "existing"},
    {"name": "Brian Athey", "slug": "brian-athey", "status": "created"}
  ],
  "summary": {
    "created": 1,
    "linked": 0,
    "skipped": 42
  }
}
```

This list is used by journal generation to create `[[Name|user.slug]]` links in the journal text.

**Key Principle**: When in doubt, skip. All created entries must be fully populated with real information.

**Auto-run**: This skill is automatically called during `@screenpipe-daily-journal` workflow.
