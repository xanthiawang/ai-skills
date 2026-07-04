---
name: dendron-sync-website
description: Sync Albert's personal Hugo website content into Dendron notes, including bio, CV, publications, projects, grants, and talks.
---

# Dendron Sync Website

**Sync information from personal Hugo website to Dendron knowledge base**

## When to Use

Use this skill when the user wants to:
- Update Dendron notes from their website content
- Sync bio, CV, publications, research, grants from website
- Keep personal information current across platforms
- Extract publications from website to create user.* references
- Update project descriptions from website research page

## What It Does

1. **Reads** Hugo website content from `/Users/A.Y/Desktop/Projects/website/kejunying.com/content/`
2. **Extracts** structured information:
   - Bio & contact info (from `about/index.md`)
   - CV details (from `cv/Ying_cv.qmd`)
   - Publications (from `research/index.md` or CV)
   - Research projects (from `research/index.md`)
   - Grants and fellowships (from CV)
   - Presentations/talks (from `talks/index.md`)
3. **Updates** corresponding Dendron notes:
   - `personal.history.md` or `personal.md` (bio, contact)
   - `personal.grant.*` (grants and fellowships)
   - `proj.*` (research projects)
   - `user.authorYYYY.md` (publications)
4. **Preserves** existing Dendron content (merge, don't overwrite)
5. **Commits** changes with clear message

## Usage

```
@dendron-sync-website
@dendron-sync-website --section=bio
@dendron-sync-website --section=publications
@dendron-sync-website --section=grants
@dendron-sync-website --dry-run
```

**Options**:
- `--section` - Sync only specific section (bio, publications, grants, projects)
- `--dry-run` - Show what would be updated without making changes
- `--vault` - Specify Dendron vault path (default: auto-detect)

## Website Structure

**Hugo content location**: `/Users/A.Y/Desktop/Projects/website/kejunying.com/content/`

**Key files**:
- `about/index.md` - Bio, contact information, current position
- `cv/Ying_cv.qmd` - Full CV with education, research experience, grants, publications
- `research/index.md` - Research highlights and publication list
- `talks/index.md` - Presentations and talks
- `blog/` - Blog posts (optional sync)

## Sync Workflows

### Sync Bio & Contact Info

**Source**: `content/about/index.md`

**Extract**:
- Current position (Postdoctoral Researcher at Stanford/UW)
- Affiliations (Wyss-Coray lab, Baker lab)
- Contact info (emails, office, social links)
- Bio paragraph (research focus, achievements)

**Update Dendron**:
- `personal.md` or `personal.history.md`
- Add/update contact section
- Update current position
- Sync bio (preserve existing detailed content)

**Example**:
```markdown
# Kejun "Albert" Ying

## Current Position

**Postdoctoral Researcher**
- Stanford University (Wyss-Coray lab) & University of Washington (Baker lab)
- NIH/NIA K00 Fellow (2025-2028)
- Focus: Aging systems biology and protein design for neurodegeneration

## Contact

- Email: keying@stanford.edu, kying0@uw.edu
- Office: 290 Jane Stanford Way, Stanford, CA 94305
- Twitter: @kejunying
- LinkedIn: [kejun-albert-ying](https://www.linkedin.com/in/kejun-albert-ying/)
- Scholar: [JS7AdkcAAAAJ](https://scholar.google.com/citations?user=JS7AdkcAAAAJ)
- GitHub: [albert-ying](https://github.com/albert-ying)

## Bio

[Extracted from website about section]
```

### Sync Grants & Fellowships

**Source**: `content/cv/Ying_cv.qmd` (Grants section)

**Extract**:
- K00 Post-doctoral Transition Award (NIH/NIA, 2025-2028)
- F99 Transition to Aging Research (NIH/NIA)
- Other grants and fellowships

**Update Dendron**:
- Create/update files in `personal.grant.*`
- Example: `personal.grant.nih-nia-k00.md`

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

**Example**:
```markdown
---
id: m8kj3n9p4q5r6s7t8u9v0w1  # Generate 23-char lowercase alphanumeric ID
title: NIH/NIA K00 Post-doctoral Transition Award
desc: 'Using causal aging biomarkers and protein design for anti-aging interventions'
updated: 1706457600000  # Unix timestamp in milliseconds
created: 1706457600000  # Unix timestamp in milliseconds
status: active
agency: NIH/NIA
amount: [if specified]
period: 2025-2028
---

# K00 Post-doctoral Transition Award

**Agency**: NIH/NIA  
**Title**: Using causal aging biomarkers and protein design to develop novel anti-aging interventions  
**Period**: 2025-2028  
**Status**: Active

## Project Summary

[Extract from website or CV]

## Related

- [[Projects|proj]] - Research projects funded
- [[Personal|personal]] - Career information
```

### Sync Publications

**Source**: `content/research/index.md` or `cv/Ying_cv.qmd`

**Extract**:
- Author list (identify first author)
- Title
- Journal
- Year
- DOI
- Brief description/TLDR

**Update Dendron**:
- Create `user.firstauthorYYYY.md` for each paper
- Update `user.md` index
- Cross-reference with related projects if mentioned

**Example**:
From website:
```markdown
#### A Unified Framework for Systematic Curation and Evaluation of Aging Biomarkers
K Ying, S Paulson, A Eames, A Tyshkovskiy, ..., VN Gladyshev
Nature Aging
DOI: 10.1038/s43587-025-00987-y
```

Create Dendron note:
```markdown
---
id: a1b2c3d4e5f6g7h8i9j0k1l  # Generate 23-char lowercase alphanumeric ID
title: "A Unified Framework for Systematic Curation and Evaluation of Aging Biomarkers"
desc: 'Framework for curating and evaluating aging biomarkers'
updated: 1706457600000  # Unix timestamp in milliseconds
created: 1706457600000  # Unix timestamp in milliseconds
authors:
  - Ying, K.
  - Paulson, S.
  - Eames, A.
  - Tyshkovskiy, A.
  - Gladyshev, VN.
year: 2025
journal: Nature Aging
doi: 10.1038/s43587-025-00987-y
first_author: true
domains:
  - biology
  - aging
topics:
  - biomarkers
  - aging-clocks
  - evaluation-framework
related_projects:
  - proj.2022.clockbase
  - proj.2025.clockbase-agent
---

# A Unified Framework for Systematic Curation and Evaluation of Aging Biomarkers

**Authors**: K Ying, S Paulson, A Eames, A Tyshkovskiy, ..., VN Gladyshev  
**Journal**: Nature Aging (2025)  
**DOI**: 10.1038/s43587-025-00987-y  
**Role**: First author

## Summary

This work presents a comprehensive framework for systematically curating and evaluating aging biomarkers, addressing the challenge of standardizing the assessment of biological age measurements.

## Related

- [[ClockBase|proj.2022.clockbase]]
- [[ClockBase Agent|proj.2025.clockbase-agent]]
- [[Science|sci]]
```

### Sync Research Projects

**Source**: `content/research/index.md` or `content/cv/Ying_cv.qmd` (Research Experience section)

**Extract**:
- Project names (ClockBase, MethylGPT, Disaggregase, etc.)
- Descriptions
- Status (from website context or CV dates)
- Collaborators
- Timeframes

**Update Dendron**:
- Update existing `proj.*` files with descriptions
- Add collaborators to frontmatter
- Update project status if changed

**Match Logic**:
```python
# Match website projects to Dendron projects
website_projects = extract_projects_from_website()
dendron_projects = list_dendron_projects()  # from proj.* files

for wp in website_projects:
    # Try to match by name (fuzzy matching)
    matched = find_closest_match(wp.name, dendron_projects)
    if matched:
        update_project(matched, wp)
    else:
        # Ask user: "Found new project on website: [name]. Create in Dendron?"
        create_new_project(wp)
```

## Implementation Details

### Step 1: Detect Dendron Vault
```bash
# Find dendron.yml
find_dendron_yml() {
    current_dir = os.getcwd()
    while current_dir != '/':
        if os.path.exists(f"{current_dir}/dendron.yml"):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    return None
}

# Or use manual specification
vault_path = args.vault or find_dendron_yml()
notes_dir = f"{vault_path}/notes"
```

### Step 2: Parse Hugo Content

**Parse frontmatter + content**:
```python
import frontmatter

# Read Hugo markdown file
with open('content/about/index.md') as f:
    post = frontmatter.load(f)
    title = post['title']
    content = post.content
```

**Extract structured data**:
- Use regex for contact info (emails, phone, links)
- Parse markdown sections (## headers)
- Extract DOIs, author lists, years from publications
- Identify project names and descriptions

### Step 3: Match & Update

**For publications**:
1. Extract author + year → generate `user.authorYYYY` ID
2. Check if exists in Dendron:
   ```sql
   SELECT fname FROM Note WHERE fname='user.authorYYYY';
   ```
3. If exists: merge new info (don't overwrite existing content)
4. If not: create new note with rich frontmatter

**For grants**:
1. Parse grant name → generate `personal.grant.[slug]` ID
2. Check if exists
3. Update or create with dates, agency, amount, description

**For bio**:
1. Read existing `personal.md` or `personal.history.md`
2. Update specific sections (Contact, Current Position)
3. Preserve other existing content (notes, private info, etc.)

### Step 4: Commit Changes

```bash
git add notes/personal.* notes/user.ying*.md notes/proj.*.md
git commit -m "Sync from website: Update [sections]

- Updated bio and contact info from about page
- Added [N] publications from research page
- Updated [N] grant entries from CV
- Synced project descriptions"
```

## Safety & Validation

### Before Updating
1. **Backup**: Ensure git is clean or commit pending changes
2. **Dry-run**: Show what would change without making edits
3. **Confirm**: Ask user to confirm if significant changes detected

### Merge Strategy
- **Don't overwrite**: Preserve existing Dendron content
- **Append or update**: Add new info, update changed info
- **User review**: Flag conflicts for manual resolution

### Conflict Resolution
If website has different info than Dendron:
```
Conflict detected in personal.grant.nih-nia-k00.md:
  Website: Period 2025-2028
  Dendron: Period 2025-2027

Options:
1. Use website version (update Dendron)
2. Keep Dendron version (skip)
3. Manual merge

Choose: 
```

## Advanced Features

### Incremental Sync
- Track last sync date
- Only process changes since last sync
- Store sync metadata in `.dendron-sync.json`

### Two-Way Sync (Future)
- Sync Dendron → Website (for private notes going public)
- Detect which source is newer
- Handle bidirectional updates

### Scheduled Sync
- Run automatically (e.g., weekly)
- Cron job or GitHub Action
- Email summary of changes

## Configuration File

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

## Example Usage

### Full Sync
```
@dendron-sync-website

Output:
✓ Read website content
✓ Extracted:
  - Bio & contact info
  - 15 publications (3 new)
  - 4 grants (1 updated)
  - 6 research projects (2 new)
  
Updates to make:
  - personal.md: Update current position
  - personal.grant.nih-nia-k00.md: Update (NEW)
  - user.ying2025.md: Create (NEW) - Nature Aging paper
  - user.ying2025b.md: Create (NEW) - Nature Medicine paper
  - proj.2025.disaggregase.md: Update description
  
Proceed? (Y/n)
```

### Section-Specific Sync
```
@dendron-sync-website --section=publications

Output:
✓ Scanning website publications...
✓ Found 15 publications
✓ Checking Dendron...
  - 12 already exist
  - 3 new publications to add
  
Creating:
  - user.ying2025.md - Nature Aging biomarkers paper
  - user.ying2025b.md - Nature Medicine paper
  - user.paulson2025.md - Collaborative paper
  
Proceed? (Y/n)
```

### Dry Run
```
@dendron-sync-website --dry-run

Output:
[DRY RUN - No changes will be made]

Would update 7 files:
  1. personal.md - Update current position from "Visiting Scholar" to "Postdoctoral Researcher"
  2. personal.grant.nih-nia-k00.md - Create new grant entry
  3. user.ying2025.md - Create new publication
  4. user.ying2025b.md - Create new publication
  5. proj.2025.disaggregase.md - Update description
  6. _index.by-person.md - Add new publications
  7. _index.by-topic.md - Add new topics from papers
```

## Parsing Rules

### Bio & Contact (from `content/about/index.md`)

**Extract patterns**:
- Current position: Regex for "postdoctoral researcher", "at Stanford", etc.
- Emails: `[\w\.-]+@[\w\.-]+`
- Social links: Twitter, LinkedIn, GitHub URLs
- Affiliations: Lab names, institutions

**Update `personal.md`**:
```markdown
## Current Position

**Postdoctoral Researcher** (2025 - Present)
- Stanford University (Wyss-Coray lab)  
- University of Washington (Baker lab)
- NIH/NIA K00 Fellow

## Contact

[Extracted from website]

## Bio

[Extracted paragraph from website]
```

### Publications (from `content/research/index.md`)

**Parse format**:
```markdown
#### [Title](DOI link)
##### Authors
***Journal***
`tldr`: Description
```

**Extract**:
- First author last name + year → `user.authorYYYY`
- Title, authors, journal, DOI
- TLDR as description

**Create/update** `user.authorYYYY.md`

### Grants (from `content/cv/Ying_cv.qmd`)

**Parse format**:
```
**Grant Name** \hfill Agency
*Title*, \hfill Years
```

**Extract**:
- Grant name
- Agency (NIH/NIA, NSF, etc.)
- Title/description
- Period (start-end years)

**Create** `personal.grant.[slug].md`

### Projects (from `content/research/index.md` or CV)

**Match to existing projects**:
- ClockBase → `proj.2022.clockbase`
- MethylGPT → (create if doesn't exist)
- Disaggregase → `proj.2025.disaggregase`

**Update descriptions** from website

## Implementation Steps

### 1. Read Website Content
```python
website_path = "/Users/A.Y/Desktop/Projects/website/kejunying.com/content/"
about = read_file(f"{website_path}/about/index.md")
cv = read_file(f"{website_path}/cv/Ying_cv.qmd")
research = read_file(f"{website_path}/research/index.md")
```

### 2. Parse Structured Data
```python
data = {
    'bio': extract_bio(about),
    'contact': extract_contact(about),
    'position': extract_current_position(about, cv),
    'grants': extract_grants(cv),
    'publications': extract_publications(research, cv),
    'projects': extract_projects(research, cv)
}
```

### 3. Match to Dendron Notes
```python
# For each publication
for pub in data['publications']:
    author_year = f"user.{pub['first_author'].lower()}{pub['year']}"
    if note_exists(author_year):
        updates[author_year] = merge_publication_data(existing, pub)
    else:
        creates[author_year] = create_publication_note(pub)
```

### 4. Preview Changes
```
Show user:
- Files to create (N)
- Files to update (M)
- Conflicts detected (K)

Wait for confirmation
```

### 5. Apply Updates
```python
for note_id, content in creates.items():
    write_file(f"notes/{note_id}.md", content)
    
for note_id, updates in updates.items():
    apply_updates(f"notes/{note_id}.md", updates)
```

### 6. Update Indexes
- Add new publications to `user.md`
- Update `_index.by-person.md` if own publications
- Update `_index.by-topic.md` with new topics
- Update project indexes if project info changed

### 7. Commit
```bash
git add notes/personal.* notes/user.ying*.md notes/_index.*
git commit -m "Sync from website: [summary of changes]"
```

## Extraction Patterns

### DOI Extraction
```regex
https?://doi\.org/(10\.\d{4,}/[\S]+)
doi\.org/(10\.\d{4,}/[\S]+)
10\.\d{4,}/[\S]+
```

### Author Parsing
```markdown
K Ying, S Paulson, A Eames, ..., VN Gladyshev

Parsed:
- First author: Ying, K. (2025) → user.ying2025
- Authors list: [Ying, K., Paulson, S., Eames, A., ..., Gladyshev, VN.]
```

### Grant Period Parsing
```
\hfill 2025 -- 2028
→ start_date: 2025, end_date: 2028

\hfill 2024 -- Present
→ start_date: 2024, end_date: null, status: active
```

## Conflict Scenarios

### Scenario 1: Publication exists with different info
```
Website: Nature Aging (2025)
Dendron: Nature Aging (2024)

→ Ask user: Year mismatch. Use website (2025)?
```

### Scenario 2: Grant amount differs
```
Website: No amount specified
Dendron: $100,000

→ Preserve Dendron amount (more detailed info)
```

### Scenario 3: Bio significantly different
```
Website: 2 paragraphs
Dendron: 5 paragraphs with private notes

→ Merge: Update public bio section, preserve private notes
```

## Testing

Before deploying:
1. ✓ Test with dry-run mode
2. ✓ Verify parsing of all sections
3. ✓ Check DOI extraction accuracy
4. ✓ Validate author name parsing
5. ✓ Test merge logic (don't lose data)
6. ✓ Verify git commits are clean

## Future Enhancements

- Parse BibTeX from `cv/peer-reviewed.bib` for complete citation data
- Sync blog posts to `personal.blog.*` or `sci.blog.*`
- Sync talks to `meet.*` or new `talks.*` category
- Image sync (profile photo, figures)
- Bidirectional sync (Dendron → Website)
- Auto-sync on website git push (GitHub Action)

## Dependencies

- Hugo website at known path
- Python `frontmatter` library for parsing
- Regex for extraction patterns
- Access to Dendron vault
- Git for commits

## Related Skills

- [[dendron-add]] - Add new information (can be used for manual additions)
- [[dendron-query]] - Query existing information
- [[dendron-generate]] - Generate content from notes

## References

- Website path: `/Users/A.Y/Desktop/Projects/website/kejunying.com`
- Dendron vault: Detected from CWD or specified with `--vault`
- Index patterns: `[[_index.agent-patterns]]`
