# Architecture v2: Skill as Data Provider

## Summary

I've redesigned the screenpipe-daily-journal skill based on your clarification:

**OLD**: Skill did both data extraction AND AI formatting (with Claude API)
**NEW**: Skill extracts raw data, Cursor Agent does the AI formatting

## Why This Design is Better

1. **Skill = Reusable Tool**: No API keys needed, purely data extraction
2. **Agent = Intelligent Formatter**: Has full context (can see example journals, your writing style, past conversations)
3. **Separation of Concerns**: Data extraction vs. content generation
4. **More Flexible**: Agent can adapt formatting based on the specific day and your preferences

## Two-Step Workflow

### Step 1: Skill Extracts Raw Data

```bash
bash /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/full_workflow_v2.sh 2026-01-31
```

**What it does**:
1. 👥 Detect people → Create `user.{name}.md` entries
2. 📸 Extract keyframes → PNG screenshots
3. 🎥 Create video symlinks
4. 📊 Extract raw data → JSON file

**Output**: `~/Documents/Manual Library/Dendron/notes/.cache/journal_raw_2026_01_31.json`

**JSON Structure**:
```json
{
  "date": "2026-01-31",
  "day_boundaries": {
    "start": "2026-01-31T01:00:00+00:00",
    "end": "2026-01-31T06:30:00+00:00",
    "duration_hours": 5.5
  },
  "sleep_periods": [...],
  "total_items": 1978,
  "hourly_data": {
    "1": {
      "ocr": [
        {
          "text": "Editing `.yabairc` configuration...",
          "timestamp": "2026-01-31T01:15:00+00:00",
          "activity": "Terminal work",
          "app_name": "Terminal",
          "window_name": "zsh"
        }
      ],
      "audio": [
        {
          "text": "KIO controller start and stop...",
          "timestamp": "2026-01-31T01:20:00+00:00"
        }
      ],
      "activities": {
        "Terminal work": 12,
        "Coding - Python": 8,
        "Meeting notes": 3
      }
    }
  },
  "keyframes": [...],
  "summary_stats": {...}
}
```

### Step 2: Cursor Agent Formats Journal

In Cursor, the agent (you):

1. **Reads raw JSON**
2. **References example**: `@daily.journal.2026.01.31.md`
3. **Analyzes with AI**: Understands what the user was actually working on
4. **Formats naturally**: Writes in the user's style
5. **Writes journal**: `daily.journal.2026.01.31.md`

**Example formatting task**:
```
"Format the raw journal data for 2026-01-31 into a journal matching 
 the style of @daily.journal.2026.01.31.md"
```

## Example: How You Should Format

### From Raw JSON (OCR text):
```json
{
  "hour": 1,
  "ocr": [
    {
      "text": "Editing `.yabairc` configuration file for window tiling...",
      "activity": "Terminal work"
    },
    {
      "text": "Working on `sketchybarrc` for status bar...",
      "activity": "Terminal work"
    }
  ],
  "audio": [
    {
      "text": "KIO controller start and stop just by command line for the recording..."
    }
  ]
}
```

### To Formatted Journal:
```markdown
### 1:00 AM - Late Night Coding Session

**macOS Window Management Development**
- Editing `.yabairc` configuration file for window tiling
- Working on `sketchybarrc` for status bar customization
- Testing window management rules and shortcuts

**Screenpipe Configuration**
- Reviewing screenpipe settings and shortcuts
- 🎤 _"KIO controller start and stop just by command line for the recording..."_
```

## Files Created

### New Files
- ✅ `scripts/extract_raw_data.py` - Raw data extractor
- ✅ `scripts/full_workflow_v2.sh` - New workflow script
- ✅ `ARCHITECTURE_V2.md` - This file
- ✅ `SKILL.md` - Completely rewritten with new architecture

### Modified Files
- ✅ `SKILL.md` - Documented two-step process with agent instructions

### Old Files (Keep for Reference)
- `scripts/generate_journal_v*.py` - Old AI generators (not used anymore)
- `scripts/full_workflow.sh` - Old workflow (deprecated)
- `SETUP.md`, `README_V5.md`, `IMPROVEMENTS.md` - Old docs (for v5 approach)

## Usage

### Quick: Use the Skill Directly

In Cursor:
```
@screenpipe-daily-journal 2026-01-31
```

The agent should automatically:
1. Run the workflow to extract raw data
2. Read the JSON
3. Reference the example journal style
4. Format and write the journal

### Manual: Two-Step Process

```bash
# Step 1: Extract raw data
bash /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/full_workflow_v2.sh 2026-01-31

# Step 2: Ask the agent to format
"Format the raw journal data for 2026-01-31 into a journal matching 
 the style of @daily.journal.2026.01.31.md"
```

## Agent Instructions (For You)

When the user invokes `@screenpipe-daily-journal [date]`:

1. **Run the workflow**:
   ```bash
   bash /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/full_workflow_v2.sh [date]
   ```

2. **Read the raw JSON**:
   ```
   ~/Documents/Manual Library/Dendron/notes/.cache/journal_raw_YYYY_MM_DD.json
   ```

3. **Reference example style**:
   ```
   @daily.journal.2026.01.31.md
   ```

4. **Format the journal** following these guidelines:

   **Frontmatter**:
   ```yaml
   ---
   id: daily.journal.YYYY.MM.DD
   title: 'YYYY.MM.DD'
   desc: 'Brief one-line summary'
   updated: [timestamp]
   created: [timestamp]
   traitIds:
     - journalNote
   ---
   ```

   **Day Summary**:
   - 2-3 sentences
   - Specific projects/activities, not generic categories
   - Example: "Journal automation development and testing. Worked on screenpipe daily journal skill - people detection, keyframe extraction. Late night coding session on macOS window management."

   **Timeline**:
   - Group by work sessions (not strict hourly)
   - Hour header: `### 1:00 AM - Session Name`
   - Activity headers: `**Activity Name**`
   - Specific details: What you did/decided, not just what app
   - Decisions: "Decision: ..."
   - Blockers: "Blocked: ..."
   - Important quotes: `- 🎤 _"quote text..."_`
   - Embed keyframes: `![Context](assets/journal_YYYY-MM-DD_moment_N.png)`

   **State & Open Questions**:
   - By project/area
   - Format:
     ```markdown
     **Project Name**
     - Status: [current state]
     - Blocker: [what's blocking, if any]
     - Next: [next concrete step]
     ```

   **Tasks**:
   - Only real, actionable tasks
   - Filter OCR garbage (e.g., "Will Take timed 95c" is garbage)
   - Group by category
   - Format: `- [ ] Task description`

   **Notes**:
   - Meta-observations
   - Patterns or insights
   - Anything that doesn't fit above

5. **Write the journal**:
   ```
   daily.journal.YYYY.MM.DD.md
   ```

6. **Update year index** (if needed):
   ```
   daily.journal.YYYY.md
   ```

## Key Points

1. **No API Keys Needed**: Skill doesn't need Anthropic API key
2. **Agent Does AI Work**: You have full context and can adapt
3. **Example-Driven**: Always reference `@daily.journal.2026.01.31.md` for style
4. **Filter Noise**: OCR can be garbled - extract meaningful content only
5. **Natural Language**: Write like a human, not a data dump

## Testing

To test the new workflow:

```bash
# Extract raw data for Jan 31
bash /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/full_workflow_v2.sh 2026-01-31

# Check the raw JSON
cat ~/Documents/Manual\ Library/Dendron/notes/.cache/journal_raw_2026_01_31.json | jq .

# Now format it (as agent):
# "Format the raw journal data for 2026-01-31 matching the style of @daily.journal.2026.01.31.md"
```

## Comparison with Old Approach

| Aspect | Old (v5) | New (v2) |
|--------|----------|----------|
| **Data Extraction** | In Python script | In Python script |
| **AI Analysis** | In Python (Claude API) | By Cursor Agent |
| **Formatting** | In Python script | By Cursor Agent |
| **API Keys** | Required (Anthropic) | Not needed |
| **Context Awareness** | Limited (prompt only) | Full (can see everything) |
| **Adaptability** | Fixed prompt | Dynamic, can adapt |
| **Cost** | ~$0.05/journal | Free (uses Cursor) |

## Next Steps

The new architecture is ready to use! Just invoke `@screenpipe-daily-journal [date]` and the agent will:
1. Extract raw data with the skill
2. Format it matching your style
3. Write the final journal

No API keys, no setup, just works.
