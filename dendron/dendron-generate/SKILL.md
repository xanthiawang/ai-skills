---
name: dendron-generate
description: Generate papers, reports, summaries, bibliographies, literature reviews, and talk outlines from Dendron vault notes.
---

# Dendron Generate

**Generate papers, reports, summaries, and bibliographies from Dendron knowledge base**

## When to Use

Use this skill when the user wants to:
- Write a paper or report from research notes
- Generate literature review from collected papers
- Create project summary or status report
- Compile bibliography from references
- Synthesize information across multiple notes
- Create presentation or talk outline

## What It Does

1. **Identifies** relevant notes using indexes (by-topic or by-project)
2. **Collects** all related notes (projects, science, papers, meetings)
3. **Reads** notes in logical order (background → methods → results)
4. **Synthesizes** information with proper structure
5. **Cites** sources using Dendron/Zotero format `[[@authorYYYY]]`
6. **Generates** formatted content in requested style
7. **Saves** as new note: `report.YYYY.MM-topic.md`

## Usage

```
@dendron-generate [topic/project] as [format]
```

**Formats**:
- `paper` - Academic paper with sections
- `report` - Project report or summary
- `summary` - Brief overview (1-2 pages)
- `bibliography` - Annotated bibliography
- `presentation` - Outline for talk/slides
- `review` - Literature review

**Examples**:
- `@dendron-generate disaggregase project as report`
- `@dendron-generate protein design as literature review`
- `@dendron-generate aging research as bibliography`
- `@dendron-generate ClockBase as project summary`

## Workflow

### Step 1: Identify Scope
Parse user request to determine:
- **Topic** or **Project** focus
- **Format** (paper, report, summary, etc.)
- **Optional**: Date range, specific sections

### Step 2: Collect Relevant Notes

**For Project-based Generation**:
1. Read `_index.by-project.md` → find project section
2. Get main project file: `proj.YYYY.project-name.md`
3. Follow links to collect:
   - Related science notes (from frontmatter `related_science`)
   - Related papers (from frontmatter or project content)
   - Meeting notes (from frontmatter `meetings`)
   - People involved (from frontmatter `people`)

**For Topic-based Generation**:
1. Read `_index.by-topic.md` → find topic section  
2. Collect all linked notes:
   - Science notes: `sci.domain.topic.*`
   - Papers: `user.authorYYYY.*`
   - Projects: `proj.*` related to topic
3. SQLite query for additional mentions:
   ```sql
   SELECT fname, raw, title FROM Note n JOIN Vault v ON n.vaultId=v.id
   WHERE v.fsPath='.' AND (
     fname LIKE '%topic%' 
     OR raw LIKE '%topic-keyword%'
   );
   ```

### Step 3: Organize Notes by Type

Group collected notes:
- **Background**: `sci.*` domain and concept notes
- **Methods**: `sci.protocol.*`, project methodology
- **Results**: Project files, meeting notes with findings
- **References**: `user.*` paper notes

### Step 4: Read Notes in Logical Order

**For Paper/Report**:
1. Read background notes (sci.*) first
2. Read methods/protocols
3. Read results from project files
4. Extract key findings from meetings
5. Collect citations from user.* references

**For Literature Review**:
1. Read all paper notes (user.*)
2. Sort chronologically or thematically
3. Extract abstracts, key findings, methods
4. Identify themes and gaps

**For Project Summary**:
1. Read main project file
2. Check status and milestones
3. Review recent meetings
4. Summarize progress and next steps

### Step 5: Generate Content

**Paper Structure**:
```markdown
# [Title]

## Abstract
[Synthesized overview]

## Introduction  
[Background from sci.* notes]

## Methods
[From sci.protocol.* and project notes]

## Results
[From project files and meetings]

## Discussion
[Synthesis and interpretation]

## References
[[@author2021]] - [Citation details]
[[@author2022]] - [Citation details]
```

**Report Structure**:
```markdown
# [Project Name] Report

**Date**: YYYY-MM-DD
**Status**: [From project frontmatter]
**Lead**: [From project people]

## Executive Summary
[2-3 paragraph overview]

## Background
[From related science notes]

## Progress
[From project file and meetings]

## Current Status
[From frontmatter and recent updates]

## Next Steps
[Action items and milestones]

## References
[Related papers and notes]
```

**Bibliography Structure**:
```markdown
# Annotated Bibliography: [Topic]

## [Year]

### [Author YYYY] - [Title]
**Citation**: [Full citation]
**Summary**: [From paper abstract/desc]
**Key Findings**: [Extracted points]
**Relevance**: [To current work]
**Related**: [[Projects|proj.*]], [[Notes|sci.*]]

---
[Repeat for each paper]
```

### Step 6: Add Proper Citations

Use Dendron/Zotero format:
- **Inline**: `[[@authorYYYY]]` or `[@authorYYYY; @authorYYYY]`
- **Full citation**: Extract from `user.authorYYYY.md` frontmatter:
  ```
  Author, A., Author, B., & Author, C. (YYYY). Title. Journal, volume(issue), pages. DOI
  ```

**Extract from frontmatter**:
```yaml
---
id: user.baek2021
title: "Accurate prediction of protein structures..."
authors:
  - Baek, M.
  - DiMaio, F.
year: 2021
journal: Science
doi: 10.1126/science.abj8754
---
```

### Step 7: Save Generated Content

Create new note:
- **Filename**: `report.YYYY.MM-[topic-name].md`
- **Location**: `/notes/report.YYYY.MM-[topic-name].md`
- **Frontmatter**:
  ```yaml
  ---
  id: abc123xyz456789012345  # Generate unique 23-char alphanumeric ID
  title: "Disaggregase Project Report"
  desc: 'Project summary and status'
  updated: 1706457600000  # Unix timestamp in milliseconds
  created: 1706457600000  # Unix timestamp in milliseconds
  date_generated: 2026.01.28  # Custom field
  format: report
  topic: disaggregase
  sources:
    - proj.2025.disaggregase
    - sci.protein-design.alphafold
    - meet.2026.01.20
  ---
  ```

**CRITICAL**: All generated notes MUST include these required Dendron fields:
- `id`: Unique alphanumeric string (generate using random lowercase alphanumeric, 23 chars)
- `title`: Note title
- `desc`: Brief description (can be empty string)
- `updated`: Unix timestamp in milliseconds (current time)
- `created`: Unix timestamp in milliseconds (current time)

**Python helper to generate correct frontmatter**:
```python
import random
import string
import time

def generate_dendron_id():
    """Generate a 23-character lowercase alphanumeric ID"""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(23))

def get_timestamp_ms():
    """Get current Unix timestamp in milliseconds"""
    return int(time.time() * 1000)
```

### Step 8: Commit
```bash
git add notes/report.YYYY.MM-topic.md
git commit -m "Generate: report - [Topic] [Format]"
```

## Format Templates

### Academic Paper
- Abstract (150-250 words)
- Introduction (background, motivation, contributions)
- Related Work (literature review with citations)
- Methods (detailed methodology)
- Results (findings with figures/tables)
- Discussion (interpretation, limitations)
- Conclusion (summary and future work)
- References (full bibliography)

### Project Report
- Executive Summary
- Background & Motivation
- Objectives & Goals
- Progress to Date
- Current Status & Metrics
- Challenges & Solutions
- Next Steps & Timeline
- Resources & Team
- References & Appendices

### Literature Review
- Introduction (scope and purpose)
- Organization (by theme or chronology)
- For each paper:
  - Citation
  - Summary
  - Key contributions
  - Methodology
  - Limitations
- Synthesis (themes, gaps, trends)
- Conclusion (state of field, future directions)
- Full Bibliography

### Brief Summary
- Title & Date
- Purpose (1-2 sentences)
- Key Points (3-5 bullets)
- Context (1 paragraph)
- Implications (1 paragraph)
- Sources (links to notes)

## Citation Management

### Extracting Citations
From `user.authorYYYY.md` files:
1. Read frontmatter for structured data
2. Generate citation string in requested format (APA, MLA, Chicago, etc.)
3. Cross-reference DOI if available

### Building Bibliography
1. Collect all `user.*` references from sources
2. Sort alphabetically by first author
3. Generate formatted citations
4. Add links back to note files

**Example**:
```markdown
## References

Baek, M., DiMaio, F., Anishchenko, I., et al. (2021). Accurate prediction of protein structures and interactions using a three-track neural network. *Science*, 373(6557), 871-876. DOI: 10.1126/science.abj8754 [[Note|user.baek2021]]
```

## Advanced Features

### Include Figures/Tables
- Detect image references in source notes
- Copy to report assets folder
- Generate figure/table captions
- Number sequentially

### Cross-Referencing
- Link between sections
- Reference figures/tables
- Cross-link to source notes

### Version Control
- Save drafts with version numbers
- Track changes from source notes
- Regenerate when sources updated

### Custom Templates
- User can define custom formats
- Store in `template.*` hierarchy
- Apply during generation

## Quality Control

Before finalizing:
1. ✓ All citations have sources
2. ✓ No broken links to notes
3. ✓ Proper frontmatter
4. ✓ Logical flow and structure
5. ✓ Spell/grammar check
6. ✓ Consistent formatting

## Vault Selection

**The skill works from any directory:**
- **Default**: Generates content from the vault of the current working directory
- **Multi-vault**: Can aggregate from multiple vaults if requested

**How it determines the vault**:
1. Check for `dendron.yml` in current directory or parent directories
2. Read `workspace.vaults` to find vault list
3. Use vault where CWD is located (match `fsPath`)
4. For multi-vault generation, collect from all vaults

**Example**:
```bash
# Generate from current vault
@dendron-generate disaggregase as report

# Generate from specific vault
@dendron-generate --vault="/path/to/vault" protein-design as review
```

## Configuration

Reads from `dendron.yml` for:
- Active vault path (`workspace.vaults[].fsPath`)
- Citation style preference
- Output format defaults
- Workspace root location

## Dependencies

- Access to `notes.db` SQLite database
- Filesystem access to `notes/` directory
- Index files for navigation
- Citation formatting library (optional)

## Examples

### Example 1: Project Report
**Input**: `@dendron-generate disaggregase as report`

**Process**:
1. Read `_index.by-project.md` → Disaggregase section
2. Collect:
   - `proj.2025.disaggregase.md`
   - `sci.protein-design.alphafold.md`
   - `sci.protocol.sod1-assays.md`
   - `meet.2026.01.20.md`
   - `user.baek2021.md` (AlphaFold paper)
3. Generate report with sections
4. Save as `report.2026.01-disaggregase.md`

**Output**: 5-page project report with status, progress, methods, next steps

### Example 2: Literature Review
**Input**: `@dendron-generate protein design as literature review`

**Process**:
1. Read `_index.by-topic.md` → Protein Design section
2. Collect all papers:
   - `user.baek2021.md` (AlphaFold)
   - [other protein design papers]
3. Sort chronologically
4. Generate annotated review
5. Save as `report.2026.01-protein-design-review.md`

**Output**: Literature review with 10-15 papers, organized by approach (physics-based, ML-based, hybrid)

### Example 3: Quick Summary
**Input**: `@dendron-generate ClockBase as summary`

**Process**:
1. Read `proj.2022.clockbase.md`
2. Extract key points
3. Generate 1-page summary
4. Save as `report.2026.01-clockbase-summary.md`

**Output**: Brief overview with purpose, methods, results, links

## Related Skills

- [[dendron-add]] - Add new information (smart router)
- [[dendron-query]] - Query the knowledge base

## References

- Content synthesis patterns: `[[_index.agent-patterns]]`
- Citation formats: Zotero compatibility
- Index navigation: `[[_index.by-project]]`, `[[_index.by-topic]]`
