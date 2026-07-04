---
name: dendron-add
description: Add information to Albert's Dendron vault with automatic routing for meetings, papers, projects, people, science notes, and journals.
---

# Dendron Add (Smart Router)

**Universal entry point for adding ANY information to Dendron knowledge base with automatic routing**

## When to Use

Use this skill when the user wants to add information to their Dendron vault, including:
- Meeting notes or transcripts
- Paper references (PDF, DOI, arXiv)
- Project updates or status changes
- Person information or contact details
- Science concepts or research notes
- Daily journal entries
- Any unstructured content that needs categorization

## What It Does

1. **Analyzes** content to determine type (meeting, paper, project, person, science, daily)
2. **Extracts** entities (people, dates, topics, citations)
3. **Routes** to correct category automatically (meet.*, user.*, proj.*, sci.*, daily.*, scratch.*)
4. **Auto-categorizes** science notes by domain keywords
5. **Creates** note with rich frontmatter for structured queries
6. **Updates** all indexes (main + year + cross-reference)  
7. **Commits** changes with clear message

## Usage

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

## Classification Logic

The skill uses indicators to automatically classify content type:

### Meeting Indicators → `meet.YYYY.MM.DD.md`
- Date patterns: "Jan 20", "2026-01-20", "meeting on..."
- People references: "with @name", "attendees:", names in title
- Meeting verbs: "discussed", "met with", "call with", "talked about"
- Action items: "TODO", "[ ]", "follow up", "action item"

### Paper Indicators → `user.authorYYYY.md`
- DOI: `10.xxxx/xxxxx`
- arXiv: `arXiv:YYYY.NNNNN`
- Author patterns: "et al.", "Author1, Author2, and Author3"
- Abstract markers: "Abstract:", "Summary:", "Introduction:"
- Journal names: "Nature", "Cell", "Science", "published in"

### Project Indicators → `proj.YYYY.project-name.md`
- Status keywords: "active", "paused", "completed", "progress", "milestone"
- Project names: Check existing `proj.*` files  
- Update patterns: "Update:", "Status:", "Progress:"
- Timeline language: "Phase 1", "v1.0", "deadline"

### Person Indicators → `user.firstname-lastname.md`
- Contact info: email addresses, phone numbers
- Affiliations: university names, "Professor", "PhD student", "Dr."
- Roles: "PI", "collaborator", "colleague", "postdoc"
- Bio markers: "Research interests:", "Background:", "CV"

### Science Indicators → `sci.[domain].[topic].md`
- Domain keywords (see domain classification below)
- Technical terms: equations, algorithms, mechanisms, methods
- Protocol markers: "Methods:", "Protocol:", "Procedure:", "Steps:"
- Tool names: "AlphaFold", "RoseTTAfold", software names

### Daily/Personal → `daily.journal.YYYY.MM.DD.md`
- Diary-like language: "Today I...", "feeling", personal reflections
- Daily observations without clear structure
- Personal notes not fitting other categories

### Ambiguous → `scratch.YYYY.MM.DD.HHMMSS.md`
- If classification confidence <80%, route to scratch
- Flag for manual review
- User can later recategorize

## Domain Classification (for sci.* notes)

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

## Workflow

### Step 1: Accept Input
- Read content from string, file path, or URL
- If file: read contents
- If URL: fetch and parse (handle DOI, arXiv, PDF)

### Step 2: Analyze & Classify
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

### Step 3: Extract Entities
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

### Step 4: Generate Filename
Follow Dendron conventions:
- **Meeting**: `meet.YYYY.MM.DD.md` (from extracted date)
- **Paper**: `user.firstauthorYYYY.md` (from author + year)
- **Project**: `proj.YYYY.project-name.md` (check existing or create)
- **Person**: `user.firstname-lastname.md` (lowercase, hyphenated)
- **Science**: `sci.[domain].[topic].md` (auto-categorized domain)
- **Daily**: `daily.journal.YYYY.MM.DD.md` (today's date)
- **Scratch**: `scratch.YYYY.MM.DD.HHMMSS.md` (timestamp)

### Step 5: Create Note with Rich Frontmatter

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

### Step 6: Cascading Index Updates

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

**Example update pattern**:
```python
# Read index file
index_content = read_file('notes/meet.md')

# Find insertion point (e.g., ## 2026 section)
insertion_point = find_section_for_year(index_content, 2026)

# Add new entry
new_entry = '- [[2026-01-28 - Meeting with Person|meet.2026.01.28]] - Brief summary'
insert_at(index_content, insertion_point, new_entry)

# Write back
write_file('notes/meet.md', index_content)
```

### Step 7: Show Preview & Confirm
```
Classification: Meeting Note
Confidence: 92%
Route: meet.2026.01.28.md
Attendees: Vadim Gladyshev, Alex Tyshkovskiy
Projects: proj.2025.disaggregase
Topics: protein design, tau aggregation

Creating note with rich metadata...
Updating indexes:
  ✓ meet.md
  ✓ meet.2026.md  
  ✓ _index.by-person.md (Vadim Gladyshev, Alex Tyshkovskiy)
  ✓ _index.by-project.md (Disaggregase)

Proceed? (Y/n)
```

### Step 8: Commit
```bash
git add notes/meet.2026.01.28.md notes/meet.md notes/meet.2026.md notes/_index.*
git commit -m "Add: meeting - Discussion with Gladyshev lab on disaggregase design"
```

## Entity Extraction Details

### People Names
- Regex: `\b[A-Z][a-z]+ [A-Z][a-z]+\b` (Title Case)
- Cross-check with existing `user.*` files:
  ```sql
  SELECT fname FROM Note WHERE fname LIKE 'user.%';
  ```
- Convert to Dendron format: `firstname-lastname` (lowercase, hyphenated)
- If not found, ask user: "Create new person entry for [Name]?"

### Dates
- Parse various formats:
  - "Jan 20, 2026", "January 20 2026"
  - "2026-01-20", "20-Jan-2026", "1/20/2026"
  - "today", "yesterday"
- Convert to Dendron format: `YYYY.MM.DD` (dots, not hyphens)

### Citations
- **DOI**: `10\.\d{4,}/[\S]+`
- **arXiv**: `arXiv:\d{4}\.\d{4,}`
- **Author extraction**: 
  - From "Author et al. (YYYY)" pattern
  - From bibtex/citation strings
  - From PDF metadata

### Projects
- Look for capitalized multi-word phrases
- Cross-reference with existing projects:
  ```sql
  SELECT fname, title FROM Note WHERE fname LIKE 'proj.%';
  ```
- If ambiguous, ask user: "Add to existing project [Project A] or create new?"

### Topics
- Extract noun phrases
- Map to existing tags:
  ```sql
  SELECT fname FROM Note WHERE fname LIKE 'tags.%';
  ```
- Cross-reference with `_index.by-topic.md` categories

## Safety & Validation

### Before Creating
1. **Check for duplicates**:
   ```sql
   SELECT fname FROM Note WHERE fname='proposed.note.id';
   ```
2. **Validate date format**: Must be `YYYY.MM.DD`
3. **Confirm ambiguous classifications**: If confidence <80%

### Never Do
- Overwrite existing notes without confirmation
- Create notes with spaces or special characters in filename
- Skip frontmatter metadata
- Forget to update indexes

### Error Handling
- If file exists: Ask "Note exists. Update (merge) or create variant?"
- If classification uncertain: Route to scratch with note
- If entity extraction fails: Create note anyway, flag for manual linking
- If index update fails: Log error but don't block note creation

## Advanced Features

### Batch Adding
```
@dendron-add --batch [folder path]
```
- Process all files in folder
- Auto-classify each
- Generate summary report

### Force Category
```
@dendron-add --force-category=meeting [content]
```
- Skip classification
- Use specified category

### Dry Run
```
@dendron-add --dry-run [content]
```
- Show classification and routing
- Don't create files
- Useful for testing

## Vault Selection

**The skill works from any directory:**
- **Default**: Uses the vault of the current working directory (the active vault)
- **Manual**: User can specify vault with `--vault` flag

**How it determines the vault**:
1. Check for `dendron.yml` in current directory or parent directories
2. Read `workspace.vaults` to find vault list
3. Default to vault where CWD is located (match `fsPath`)
4. If outside any vault, ask user to specify or use first vault

**Example**:
```bash
# From within Dendron vault directory
@dendron-add "Meeting notes..."

# From outside, specify vault
@dendron-add --vault="/Users/me/Documents/Dendron/notes" "Meeting notes..."
```

## Configuration

The skill reads from `dendron.yml` for:
- Active vault path (`workspace.vaults[0].fsPath`)
- Date format preference
- Template hierarchy
- Workspace root location

## Dependencies

- Access to Dendron `notes.db` SQLite database
- Filesystem access to `notes/` directory
- Git for commits
- Natural language processing for entity extraction

## Examples

### Example 1: Meeting Note
**Input**:
```
Met with Vadim Gladyshev today to discuss the disaggregase project. We reviewed the AlphaFold predictions for the tau-binding domains. Action items: 1) Run SOD1 assays by Friday, 2) Prepare Springboard Fellowship application.
```

**Classification**: Meeting (95% confidence)
**Route**: `meet.2026.01.28.md`
**Extracted**:
- Date: 2026.01.28 (today)
- Attendees: Vadim Gladyshev
- Project: Disaggregase
- Topics: Protein design, tau, AlphaFold
- Action items: 2 tasks

**Updates**:
- `meet.md`, `meet.2026.md`
- `_index.by-person.md` (Vadim section)
- `_index.by-project.md` (Disaggregase section)

### Example 2: Paper PDF
**Input**: `/Users/me/Downloads/alphafold-paper.pdf`

**Classification**: Paper (98% confidence)
**Route**: `user.baek2021.md`
**Extracted** (from PDF metadata + content):
- Authors: Baek, M., DiMaio, F., et al.
- Year: 2021
- Title: "Accurate prediction of protein structures..."
- DOI: 10.1126/science.abj8754
- Domain: protein-design, ml
- Topics: structure-prediction, deep-learning

**Updates**:
- `user.md` (2021 section)
- `_index.by-topic.md` (Protein Design section)

### Example 3: Project Update
**Input**:
```
Progress update on ClockBase Agent: Completed data pipeline integration. Now processing 2M+ molecular profiles. Next milestone: ML model training by end of month. Status: active, on track.
```

**Classification**: Project update (89% confidence)
**Route**: Update existing `proj.2025.clockbase-agent.md`
**Action**: Append to file, update status field
**Updates**:
- `proj.2025.clockbase-agent.md` (content + frontmatter)
- `proj.md` (update status if changed)
- `_index.by-project.md` (update progress)
- `daily.journal.2026.01.28.md` (add project update entry)

## Related Skills

- [[dendron-query]] - Query the knowledge base
- [[dendron-generate]] - Generate content from notes

## References

- Classification logic: `[[_index.agent-patterns]]`
- File conventions: `[[README.structure]]`
- Frontmatter schemas: `[[_index.agent-patterns]]`
