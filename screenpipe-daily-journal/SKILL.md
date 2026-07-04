---
name: screenpipe-daily-journal
description: Generate high signal-to-noise Dendron daily journal entries from screenpipe recordings.
---

# Screenpipe Daily Journal Generator

Generate high signal-to-noise daily journal entries from screenpipe recordings using a **two-step process**: the skill extracts raw data, and the Cursor Agent formats it into the final journal.

**Key Principles**:
- Optimize for future retrieval value, not completeness
- Compress continuous work sessions into single entries (no false precision)
- Only include audio quotes with actual content (skip testing/noise)
- Only embed screenshots that are irreconstructible (skip terminal/code)
- Put State & Open Questions first (what you'll actually need)
- Notes section contains valuable synthesis (make it prominent)

**NON-NEGOTIABLE Requirements** (every journal MUST have these):
1. **Screenshots**: At least 1-3 keyframes extracted and embedded. NO journal is complete without screenshots. If screenpipe has frame data, extract them. Zero-screenshot journals are REJECTED.
2. **People Detection**: Every person mentioned in audio/OCR must be linked. Create user entries for new people via detect-people skill.
3. **Synthesized Content**: Timeline entries must contain human-readable synthesis. Raw OCR text dumped into timeline is REJECTED. If OCR is garbled, describe what was happening based on context clues (app names, file names, timestamps).
4. **Meeting Detection**: Any Zoom/Teams/Meet participant list in OCR = a meeting happened. Identify it, extract participants, link people, and consider creating a separate meeting note.
5. **Correct Timeline Ordering**: Day runs 6 AM to 6 AM. Morning first, late night last. Verify ordering before finishing.

## Meeting Notes vs Daily Journal

**CRITICAL**: When audio indicates a substantial meeting or working session with rich content:

1. **Create a separate meeting note** (`meet.YYYY.MM.DD.md`) following the structured meeting format:
   - Use factual, topic-based organization (NOT journal narrative style)
   - Include: frontmatter, action items, topic sections with bullet points, direct quotes as blockquotes
   - Format like meeting minutes: structured, informational, organized by topic
   - Example: `meet.2026.01.29.md` (UMich interview)

2. **Reference it in the daily journal**:
   - Timeline entry should link to the meeting note
   - Keep timeline entry brief: meeting title, key topics list, link to full notes
   - Day summary should mention the meeting with a link

3. **When to create separate meeting notes**:
   - Formal meetings with other people (interviews, project discussions, collaborations)
   - Extended working sessions (>1 hour) with substantial content/decisions
   - Any session you'll want to reference later as a standalone document

4. **Timezone handling**:
   - Screenpipe outputs timestamps in UTC (with Z suffix)
   - Convert to local time (PST = UTC-8) for all human-readable times
   - Always specify timezone in meeting notes: `10:00am-3:39pm PST`
   - When in doubt about timing, note the UTC timestamps in a comment for verification

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Script (Data Extraction)                           │
│ - Extract screenpipe OCR/audio data                         │
│ - Output: Raw JSON with hourly data                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Cursor Agent (Analysis & Formatting)               │
│ - Read raw JSON data                                        │
│ - Detect people → Create user entries (dendron/detect)      │
│ - Analyze content & format journal                          │
│ - Identify key moments needing screenshots                  │
│ - Extract keyframes for those moments                       │
│ - Link videos to keyframes                                  │
│ - Embed screenshots/videos in timeline                      │
│ - Write final formatted journal                             │
└─────────────────────────────────────────────────────────────┘
```

**Why this design?**
- Script = lightweight, fast data extraction (no AI needed)
- Agent = intelligent analysis with full context
  - Creates people entries using detect-people skill
  - Understands which moments matter (meetings, decisions, blockers)
  - Selects keyframes based on content value, not heuristics
  - Only extracts screenshots that will actually be used
- Avoids wasting time extracting unnecessary keyframes

## Quick Start

### Option 1: Two-Step Manual Process

```bash
# Step 1: Extract raw OCR/audio data
bash /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/extract_raw_data.sh 2026-01-31

# Step 2: In Cursor, ask the agent:
# "Format the raw journal data for 2026-01-31 into a journal following
#  the template structure in @screenpipe-daily-journal skill"
```

### Option 2: Direct Skill Invocation

```bash
# In Cursor:
@screenpipe-daily-journal 2026-01-31

# The agent will automatically:
# 1. Run raw data extraction
# 2. Detect and create people entries
# 3. Analyze content and format journal
# 4. Extract keyframes for important moments
# 5. Link videos and embed in timeline
```

## What the Skill Provides (Raw Data)

The skill extracts and structures data into JSON:

```json
{
  "date": "2026-01-31",
  "day_boundaries": {
    "start": "2026-01-31T06:00:00-08:00",
    "end": "2026-02-01T06:00:00-08:00",
    "duration_hours": 24.0
  },
  "sleep_periods": [
    {
      "start": "2026-01-30T22:00:00+00:00",
      "end": "2026-01-31T01:00:00+00:00",
      "duration_hours": 3.0
    }
  ],
  "total_items": 1978,
  "hourly_data": {
    "1": {
      "ocr": [
        {
          "text": "Editing `.yabairc` configuration file...",
          "timestamp": "2026-01-31T01:15:00-08:00",
          "activity": "Terminal work"
        }
      ],
      "audio": [
        {
          "text": "KIO controller start and stop just by command line...",
          "timestamp": "2026-01-31T01:20:00-08:00"
        }
      ],
      "activities": {
        "Terminal work": 12,
        "Coding - Python": 8,
        "Meeting notes": 3
      }
    }
  },
  "keyframes": [
    {
      "number": "1",
      "image": "assets/journal_2026-01-31_moment_1.png",
      "video": "assets/journal_2026-01-31_moment_1.mp4"
    }
  ],
  "summary_stats": {
    "total_hours_active": 6,
    "total_ocr_items": 156,
    "total_audio_items": 42,
    "top_activities": {
      "Terminal work": 45,
      "Coding - Python": 38,
      "Email (Gmail)": 12
    }
  }
}
```

## What the Agent Does (Formatting)

The Cursor Agent takes the raw JSON and:

1. **Identifies People**: Searches audio transcripts and OCR for people mentions (meetings, emails, file references)
2. **Analyzes Content**: Understands what you were actually working on
3. **Groups Semantically**: Clusters activities by work session, not just time
4. **Extracts Context**: Finds decisions, blockers, next steps
5. **Links Collaborators**: Uses [[Name|user.slug]] format for all people mentioned
6. **Writes Naturally**: Formats in your writing style (see example below)
7. **Integrates Keyframes**: Embeds screenshots with meaningful context

### Example Output Format

The agent produces journals matching this structure (compressed, high signal-to-noise):

```markdown
---
id: a1b2c3d4e5f6g7h8i9j0k1l  # Generate 23-char lowercase alphanumeric ID
title: 'YYYY.MM.DD'
desc: 'Brief description of main activities'
updated: 1706457600000  # Unix timestamp in milliseconds
created: 1706457600000  # Unix timestamp in milliseconds
---

## Day Summary

2-3 sentences covering main activities and people involved. Specific projects, not generic categories.
Example: "Paper revision with [[Collaborator Name|user.collaborator-name]], late night integration work on X system. Meeting with [[Professor|user.professor]] about Y opportunity."

## State & Open Questions

**Project A (with Collaborator)**
- Status: Current state of the work
- Blocker: What's blocking progress (if anything)
- Next: What needs to happen next

**Project B**
- Status: Where things stand
- Next: Clear next action

**Project C**
- Status: Brief update
- Decision: Key decision made today
- Next: Follow-up action

## Tasks

### Inferred from Today

- [ ] Specific actionable task from project A
- [ ] Follow up with [[Person Name|user.person-name]] about X
- [ ] Technical task: specific implementation detail
- [ ] Research/read: specific paper or documentation

### Completed Today

- [x] Specific accomplishment (be concrete)
- [x] Meeting with [[Person|user.person]] about X
- [x] Implementation milestone: what exactly got done

## Timeline

<div class="timeline-container">
  <div class="timeline-line"></div>
  
  <div class="timeline-item">
    <div class="timeline-dot dot-meeting"></div>
    <div class="timeline-time">9:00 AM - 10:30 AM</div>
    <div class="timeline-card card-meeting">
      <div class="timeline-title">Meeting with Professor</div>
      <div class="timeline-content">
        <p>Discussed X project timeline with <a href="user.professor.md">Professor Name</a> and Y collaboration opportunity. <strong>Decision</strong>: Will pursue Z approach. 🎤 <em>"Key quote that captures important decision or insight"</em></p>
      </div>
    </div>
  </div>
  
  <div class="timeline-item">
    <div class="timeline-dot dot-email"></div>
    <div class="timeline-time">10:30 AM - 11:00 AM</div>
    <div class="timeline-card card-email">
      <div class="timeline-title">Email Correspondence</div>
      <div class="timeline-content">
        <p>Follow-ups on A, B, C projects.</p>
      </div>
    </div>
  </div>
  
  <div class="timeline-item">
    <div class="timeline-dot dot-dev"></div>
    <div class="timeline-time">2:00 PM - 6:00 PM</div>
    <div class="timeline-card card-dev">
      <div class="timeline-title">Project A Development</div>
      <div class="timeline-content">
        <p>Built X feature, integrated with Y system. Hit <strong>Blocker</strong>: Missing API documentation. Workaround: Used approach W instead.</p>
        
![Meeting whiteboard diagram](assets/journal_YYYY-MM-DD_moment_1.png)

        <p><a href="assets/journal_YYYY-MM-DD_moment_1.mp4">📹 Video recording</a></p>
        <p><em>Whiteboard diagram showing system architecture from meeting</em></p>
      </div>
    </div>
  </div>
  
  <div class="timeline-item">
    <div class="timeline-dot dot-research"></div>
    <div class="timeline-time">7:00 PM - 9:00 PM</div>
    <div class="timeline-card card-research">
      <div class="timeline-title">Project B Research</div>
      <div class="timeline-content">
        <p>Paper review and literature search for X topic related to <a href="proj.project-b.md">Project B</a>. Identified relevant approaches: method A from <a href="user.author.md">Author</a> paper shows promise for our use case.</p>
      </div>
    </div>
  </div>
  
</div>

## Notes

**Collaboration Dynamics**: Working with [[Collaborator|user.collaborator]] is moving faster than expected - their expertise in X domain is accelerating the Y component. Worth investing more time in this partnership.

**Technical Insight**: The Z approach we tried initially seemed promising but hit fundamental limitation W. The alternative approach using V is less elegant but actually more maintainable. Good learning for future projects.

**Work Pattern**: Morning meetings followed by uninterrupted afternoon development blocks is effective. Protecting the 2-6 PM window from meetings leads to better implementation progress.

**Strategic Context**: Multiple faculty position opportunities at different stages - UMich waiting on X, Stanford reviewing Y, collaborations with [[Person A|user.person-a]] and [[Person B|user.person-b]] strengthening application materials.
```

## Workflow Details

### Step 1: Extract Raw Data (Script)

```bash
bash /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/extract_raw_data.sh 2026-01-31
```

This extracts:
- OCR text from all screens (hourly grouping)
- Audio transcripts (hourly grouping)
- Summary statistics
- Outputs structured JSON to `.cache/journal_raw_2026_01_31.json`

**What it does NOT do**: No keyframe extraction, no video linking, no people detection. These happen after the agent analyzes content.

**Output Location**: `~/Documents/Manual Library/Dendron/notes/.cache/journal_raw_YYYY_MM_DD.json`

### Step 2: Format into Journal (Agent)

In Cursor, the agent performs intelligent analysis and formatting:

1. **Read raw JSON data** - Understand the full day's activities
2. **Detect and create people entries** - Use `dendron/detect-people` skill to scan audio/OCR and create user entries
3. **Analyze content semantically** - Understand what actually happened (not just regex patterns)
4. **Group activities by work session** - Identify context switches, meetings, development blocks
5. **Extract decisions, blockers, tasks** - Pull out actionable information
6. **Format journal structure** - Day summary, state, tasks, timeline, notes
7. **Identify key moments** - Which timeline entries need screenshots (meetings, debugging, important decisions)
8. **Extract keyframes for those moments** - Run extraction script for specific timestamps
9. **Link videos** - Create symlinks to screen recordings for those keyframes
10. **Embed in timeline** - Add images and video links to relevant timeline entries
11. **Write formatted journal** to `daily.journal.YYYY.MM.DD.md`

## Usage Examples

### Generate Today's Journal

```bash
# In Cursor:
@screenpipe-daily-journal

# Or two-step:
bash /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/extract_raw_data.sh today
# Then ask agent to format
```

### Generate for Specific Date

```bash
# In Cursor:
@screenpipe-daily-journal 2026-01-30

# Or two-step:
bash /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/extract_raw_data.sh 2026-01-30
# Then ask agent to format
```

### Regenerate Existing Journal

```bash
# Extract fresh raw data
bash /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/extract_raw_data.sh 2026-01-31

# In Cursor:
# "Regenerate journal for 2026-01-31 using the new raw data,
#  following the template in @screenpipe-daily-journal skill"
```

## Configuration

### Day Boundaries

**Important**: The pipeline uses **6 AM to 6 AM local time boundaries** to align with natural sleep/wake cycles. This captures a full work day from wake-up (6 AM) through late-night work sessions until the next morning (6 AM).

Sleep detection is still performed for context but does NOT exclude data from the output.

Edit `~/.screenpipe/journal_config.json`:

```json
{
  "screenpipe_port": 3030,
  "journal_path": "~/Documents/Manual Library/Dendron/notes",
  "focus_apps": ["Cursor", "Zotero", "Terminal"],
  "ignore_windows": ["screenpipe", "Settings", "Keepass"],
  "sleep_detection": {
    "min_gap_hours": 3.0,
    "default_wake_hour": 6,
    "late_night_cutoff_hour": 6
  }
}
```

**Day Boundary Details**:
- Journal day runs from 6:00 AM (local time) to 6:00 AM next day (local time)
- Late-night sessions (6 AM - 6 AM next day) are captured in a single journal entry
- Sleep detection provides context but doesn't filter data

**Sleep Detection Parameters** (for context only):
- `min_gap_hours`: Minimum inactivity gap to consider as sleep (default: 3.0)
- `default_wake_hour`: Reference wake time for analysis (default: 6 AM)

## Sub-Skills

### dendron/detect-people

**Invoked by agent during Step 2.** Detects people and creates user entries automatically.

**What it does**:
- Scans OCR text and audio for names
- **Phonetic matching**: Audio-detected names cross-checked with existing users
- **Web search validation**: All fields filled immediately or entry skipped
- **AI validation**: Uses judgment to filter UI elements, device names, OCR artifacts
- Creates complete `user.{name-slug}.md` entries with real information
- **Returns people list** for linking in journal timeline

**When it runs**: Agent calls this skill after reading raw JSON data, before formatting the journal. This ensures all people entries exist before the timeline is created.

**Key improvements (v2.0)**:
- AI validation instead of regex rules (0% false positives vs 90% before)
- No "[To be filled]" placeholders - all entries complete via web search
- Concise instructions (40 lines vs 300+ line protocol)

See: `~/.cursor/skills/dendron/detect-people/SKILL.md`

## Agent Instructions

When the user invokes `@screenpipe-daily-journal [date]`, you should:

1. **Run data extraction** to get raw OCR/audio:
   ```bash
   bash /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/extract_raw_data.sh [date]
   ```
   
   This extracts only the raw data (no keyframes yet).

2. **Detect and create people entries** - CRITICAL STEP:
   
   **You MUST be thorough - search multiple ways to find ALL people mentioned:**
   
   ```bash
   # Search 1: Audio for meeting/collaboration mentions
   cd "/Users/A.Y/Documents/Manual Library/Dendron/notes/.cache" && \
   jq -r '.hourly_data[].audio[]?.text // empty' journal_raw_YYYY_MM_DD.json | grep -iE "(met with|discussed with|talked to|email from|call with|working with)"
   
   # Search 2: OCR for user file references
   jq -r '.hourly_data[].ocr[]?.text // empty' journal_raw_YYYY_MM_DD.json | grep -iE "user\.[a-z-]+\.md"
   
   # Search 3: OCR for meeting file references  
   jq -r '.hourly_data[].ocr[]?.text // empty' journal_raw_YYYY_MM_DD.json | grep -iE "meet\.[0-9]+\.[0-9]+\.[0-9]+\.md"
   
   # Search 4: Check which existing user entries exist
   ls "/Users/A.Y/Documents/Manual Library/Dendron/notes/user."*.md
   ```
   
   **IMPORTANT**: If someone is mentioned in a meeting note (e.g., `meet.2026.01.29.md`), you should read that file to find attendees and link them too.
   
   **After finding people**: Invoke `dendron/detect-people` skill if any new people need entries created. Otherwise, just use the existing user entries for linking.
   
   **Link ALL people found**:
   - In timeline: `<a href="user.name.md">Name</a>`
   - In day summary: `[[Name|user.name]]` (wiki-link format works outside HTML blocks)
   - In state/tasks: `[[Name|user.name]]`

3. **Read the raw JSON** to understand the full day:
   ```
   ~/Documents/Manual Library/Dendron/notes/.cache/journal_raw_YYYY_MM_DD.json
   ```
   
   Sample key hours to understand activity patterns before writing.
   
   **Important**: The raw JSON includes an "activity" field (e.g., "Terminal - Python development") generated by regex pattern matching. DO NOT trust this blindly. Read the actual OCR text to understand what was happening. The script uses simple heuristics ("def " → Python, "$ " → Terminal) that miss context. You can understand semantic meaning by reading the actual text.

4. **Reference the journal template** - see "Example Output Format" section below for structure

5. **Generate proper frontmatter** - CRITICAL:

   **Node ID**: Generate 23-character lowercase alphanumeric ID:
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
   
   # Usage
   node_id = generate_dendron_id()  # e.g., "m8kj3n9p4q5r6s7t8u9v0w1"
   timestamp = get_timestamp_ms()   # e.g., 1706457600000
   ```
   
   **Frontmatter format**:
   ```yaml
   ---
   id: m8kj3n9p4q5r6s7t8u9v0w1  # 23-char lowercase alphanumeric
   title: 'YYYY.MM.DD'
   desc: 'Brief description of main activities'
   updated: 1706457600000  # Unix timestamp in milliseconds
   created: 1706457600000  # Unix timestamp in milliseconds
   ---
   ```

6. **Format the journal** with these guidelines:

   ## CRITICAL: Signal-to-Noise Ratio
   
   **The main goal is future retrieval value.** When you look back at this journal in 3 months, what will actually be useful? Optimize for that, not for completeness.
   
   ## Structure (in this order)
   
   ### 1. Day Summary (2-3 sentences)
   - Specific projects/activities, not generic categories
   - Include people's names if they were central to the day's work
   - Example: "Paper revision with [[Jin Yap|user.jin-yap]], late night macrowhisper integration work"
   
   ### 2. State & Open Questions (MOST IMPORTANT - put this FIRST after summary)
   - By project/area: status/blocker/next
   - Mention collaborators by name
   - This is what you'll actually need when resuming work
   - Example:
     ```
     **Paper Revision (with Jin Yap)**
     - Status: Making good progress on revisions
     - Next: Meet internal submission deadline
     
     **Macrowhisper Integration**
     - Status: Screen context script implemented
     - Blocker: Homebrew service file issues
     - Next: Resolve setup, test with Superwhisper
     ```
   
   ### 3. Tasks
   - **Inferred from Today**: Only real, actionable tasks (filter OCR garbage)
   - **Completed Today**: What actually got done
   - Include collaborator follow-ups with names
   
   ### 4. Timeline (Use Custom CSS Format)
   
   **CRITICAL ORDERING - Day runs 6 AM → 6 AM next day**: 
   
   The journal day starts at 6:00 AM and ends at 6:00 AM the following day. This means:
   - **Start timeline with**: Morning/afternoon activities (6 AM - noon, noon - 6 PM)
   - **Middle of timeline**: Evening activities (6 PM - midnight)
   - **END timeline with**: Late night/early morning (midnight - 6 AM) ← These go at the BOTTOM
   
   Example correct order:
   1. 11:00 AM - 12:00 PM (morning work)
   2. 2:00 PM - 4:00 PM (afternoon meeting)
   3. 7:00 PM - 9:00 PM (evening work)
   4. 10:00 PM - 11:00 PM (late evening)
   5. 12:00 AM - 1:00 AM (midnight) ← This is part of the same day
   6. 1:00 AM - 5:00 AM (late night coding) ← Last entry, at the BOTTOM
   
   **WHY**: Activities from midnight to 6 AM are the END of the work day that started at 6 AM the previous calendar day. They represent late-night work sessions that conclude the day.
   
   **CRITICAL FORMATTING**: Use the custom timeline HTML/CSS structure defined in `custom.css`. This creates a visual timeline with dots, cards, and proper styling.
   
   **Timeline HTML Structure**:
   
   ```html
   <div class="timeline-container">
     <div class="timeline-line"></div>
     
     <div class="timeline-item">
       <div class="timeline-dot dot-TYPE"></div>
       <div class="timeline-time">HH:MM AM/PM - HH:MM AM/PM</div>
       <div class="timeline-card card-TYPE">
         <div class="timeline-title">Activity Title</div>
         <div class="timeline-content">
           <p>Content here with HTML formatting. Use <strong>bold</strong>, <em>italic</em>, <code>code</code>, etc.</p>
           <p>Link to people: <a href="user.person-name.md">Person Name</a></p>
           <p>Link to notes: <a href="meet.2026.01.29.md">Meeting notes</a></p>
         </div>
       </div>
     </div>
     
     <!-- More timeline items... -->
     
   </div>
   ```
   
   **Note**: Images must be placed OUTSIDE the timeline container (see "Keyframes/Screenshots & Videos" section below for correct structure).
   
   **CRITICAL - Mixed HTML and Markdown**:
   
   Inside timeline HTML `<div>` tags, you must use HTML formatting. Markdown doesn't work inside HTML blocks:
   
   - **Bold**: Use `<strong>text</strong>` not `**text**`
   - **Italic**: Use `<em>text</em>` not `_text_` or `*text*`
   - **Code**: Use `<code>code</code>` not `` `code` ``
   - **Links**: Use `<a href="file.md">text</a>` not `[text](file.md)` or `[[wikilink]]`
   - **Paragraphs**: Wrap text blocks in `<p>text</p>` for proper spacing
   - **Images**: ❌ DON'T put images inside HTML divs - they won't render. Place them outside (see Keyframes section)
   
   Examples:
   - ❌ Wrong: `**Decision**: Met with [[Jin Yap|user.jin-yap]]`
   - ✅ Correct: `<p><strong>Decision</strong>: Met with <a href="user.jin-yap.md">Jin Yap</a></p>`
   - ❌ Wrong: `Built \`get_screen_context()\` function`
   - ✅ Correct: `<p>Built <code>get_screen_context()</code> function</p>`
   - ❌ Wrong: `<img src="assets/file.png">` or `![](assets/file.png)` inside timeline div
   - ✅ Correct: Close timeline div, add markdown image outside, reopen timeline div
   
   **Activity Types** (use for `dot-TYPE` and `card-TYPE`):
   - `dev` - Development/coding work
   - `research` - Research, paper reading, analysis
   - `meeting` - Meetings with people
   - `email` - Email correspondence
   - `general` - General work, documentation
   
   **Flexible Clustering - Don't Force Time Labels**:
   
   DO NOT artificially group into "Morning", "Afternoon", "Evening", "Late Night". Instead:
   
   - Group by ACTIVITY CLUSTERS and CONTEXT SWITCHES
   - If you have two distinct sessions within the same time period (e.g., two different projects in the evening), create separate entries
   - If the whole late night is one continuous coding session, keep it as ONE entry
   - Use actual timestamps as time ranges (e.g., "11:00 AM - 11:30 AM", not "Morning")
   
   Examples:
   - ❌ Bad: "Morning (9-11 AM)" with mixed activities
   - ✅ Good: "9:00 AM - 10:30 AM" with specific activity title
   - ❌ Bad: Three separate "Evening" entries for continuous work
   - ✅ Good: One "7:00 PM - 10:00 PM" entry for the continuous session
   
   **Only create separate timeline entries for**:
   - Meetings with people (include attendees, key decisions)
   - Context switches between different projects/activities
   - Distinct work sessions separated by breaks
   - Different types of work (meeting → development → email)
   
   **IMPORTANT - Substantial meetings get separate notes**:
   - If a meeting/working session is substantial (>1 hour, rich content, will be referenced later):
     - Create a separate `meet.YYYY.MM.DD.md` file (see "Meeting Notes vs Daily Journal" section)
     - Timeline entry should be BRIEF: title, bullet list of key topics, link to meeting note
     - Example: `<p>Extended working session. See detailed notes: <a href="meet.2026.02.02.md">meet.2026.02.02</a></p>`
     - Do NOT include full meeting content/quotes in the timeline
   
   **What to include in timeline content**:
   - Specific details (what you did/decided, not just "worked on X")
   - Decisions: prefix with `<strong>Decision</strong>:`
   - Blockers: prefix with `<strong>Blocker</strong>:`
   - **Link ALL people**: Use `<a href="user.slug.md">Name</a>` format
   - **Link relevant notes**: Use `<a href="note.id.md">Display Text</a>` format
   - Audio quotes: ONLY if they're actual content (decisions, ideas, blockers)
     - Format: `<em>"quote text"</em>`
     - ✅ Include: "you will be the first author", "we're making good progress on the revision"
     - ❌ Skip: "Hello, can you hear me?", "it's gonna be back", background media noise
   - **For meetings**: Brief summary + link to separate meeting note if substantial
   
   **Keyframes/Screenshots & Videos - CRITICAL STRUCTURE**:
   
   The script extracts 5 keyframes (PNG images) and creates video symlinks. Include them when they provide useful context.
   
   **IMPORTANT - Images MUST be placed OUTSIDE timeline HTML divs**:
   
   Markdown images don't render inside HTML `<div>` tags in Dendron. You must:
   1. Close the timeline container `</div>` before the image
   2. Add the image in markdown format (with blank lines before/after)
   3. Reopen a new timeline container `<div class="timeline-container">` after
   
   **Correct structure**:
   ```html
   <div class="timeline-container">
     <div class="timeline-line"></div>
     <div class="timeline-item">
       <div class="timeline-dot dot-dev"></div>
       <div class="timeline-time">11:00 AM - 12:00 PM</div>
       <div class="timeline-card card-dev">
         <div class="timeline-title">Activity Title</div>
         <div class="timeline-content">
           <p>Content describing the activity.</p>
         </div>
       </div>
     </div>
   </div>
   
   ![Screenshot description](assets/journal_YYYY-MM-DD_moment_N.png)
   
   *[📹 Video recording](assets/journal_YYYY-MM-DD_moment_N.mp4)*
   
   <div class="timeline-container">
     <div class="timeline-line"></div>
     <div class="timeline-item">
       <!-- Next activity... -->
     </div>
   </div>
   ```
   
   **What to include**:
   - Screenshots showing UI states, meeting content, debugging sessions, or important visual context
   - Skip purely terminal/code editor if content is reconstructible
   - Include if showing debugging progress, configuration work, or testing results
   
   ### 5. Notes (SYNTHESIS - This is gold)
   
   **This section contains the actually valuable insights.** Make this prominent.
   
   - Patterns you noticed (workflow efficiency, what worked/didn't work)
   - Meta-observations about your work style
   - Collaboration dynamics and context
   - Technical insights or lessons learned
   - Strategic positioning (e.g., "timing projects around faculty interviews")
   
   Example:
   ```
   Multiple research projects in active phase reveals strategic coordination around 
   faculty interview timeline. Late-night coding sessions (1-5 AM) productive for 
   infrastructure work when no interruptions. Homebrew service file issues are a 
   recurring pain point - consider documenting workaround.
   ```
   
   ### 6. Interaction Quality (conditional — only if score data exists)

   Check for `.cache/interaction_scores/YYYY-MM-DD.jsonl` (where YYYY-MM-DD matches the journal date).

   If the file exists, read it and generate:

   ```markdown
   ## Interaction Quality

   **Sessions scored**: N | **Interactions**: N | **Acceptance rate**: N%

   | Domain | +Score | -Score | Net | Notable |
   |--------|--------|--------|-----|---------|
   | [domain] | N | N | +/-N | [one-line note or —] |

   **Corrections log**:
   - [HH:MM] [domain]: [detail from score object]
   ```

   If no score file exists for this date, omit this section entirely (do not add an empty section).

   ## People Linking (always do this)
   
   - "Met with [[Jin Yap|user.jin-yap]] about revision" (from audio: "I just met with Jin Yap tonight...")
   - "Email from [[Brian Athey|user.brian-athey]] at UMich" (from OCR email client)
   - "Working on [[Tony Wyss-Coray|user.tony-wyss-coray]] user entry" (from OCR file name)
   
   ## Note Linking (intelligently link relevant notes)
   
   When you mention or work on other notes in the vault, link to them:
   
   - Meeting notes: "Finalized [[UMich faculty interview|meet.2026.01.29]] notes"
   - Project notes: "Continued work on [[ClockBase Agent|proj.2025.clockbase-agent]]"
   - Paper notes: "Read [[Riesselman 2018|sci.paper.riesselman2018]] about mutation effect prediction"
   - Other daily journals: "Follow-up from [[yesterday's discussion|daily.journal.2026.01.29]]"
   
   Look for OCR evidence of file names being edited (e.g., `meet.2026.01.29.md` in editor) and link to them.

6. **Identify key moments needing screenshots**:
   
   After formatting the timeline, review which entries would benefit from visual context:
   - Meetings (capture meeting content, whiteboards)
   - Debugging sessions (capture UI states, error messages)
   - Important decisions (capture context that led to decision)
   - Configuration work (if showing interesting state)
   
   Skip: Terminal windows showing code, text editors (reconstructible content)

7. **Extract keyframes for those specific moments**:
   
   **CRITICAL - Use timestamps from raw JSON with timezone AND verify they match the timeline**:
   
   When you identify a timeline entry that needs a screenshot, you MUST:
   
   a. **Verify timeline boundaries match data**: If your timeline says "5:00 PM - 7:00 PM" but the first data point is at 5:59 PM, either adjust the timeline to "~6:00 PM - 7:00 PM" OR use the 5:59 PM timestamp. The screenshot timestamp MUST fall within your stated timeline range.
   
   b. **Use exact timestamps from raw JSON**: The timestamps in the JSON include timezone information (e.g., `"2026-02-02T17:59:53-08:00"`). Use that EXACT timestamp when extracting keyframes.
   
   c. **DO NOT** create timestamps manually or round times without checking the data.
   
   d. **Verify the screenshot content matches the timeline description**: If your timeline entry is about "screen sharing presentation" but the timestamp you're using shows "PowerPoint editing", they don't match. Find the correct timestamp.
   
   **Example workflow**:
   ```bash
   # 1. You wrote timeline: "5:00 PM - 7:00 PM - Research Overview Presentation"
   
   # 2. Check what data exists in that time range:
   jq '.hourly_data["17"].ocr[0] | {timestamp, text: .text[0:100]}' journal_raw_2026_02_02.json
   # Output: "timestamp": "2026-02-02T17:59:53-08:00", "text": "Area 2 Intervention mining..."
   
   # 3. Extract keyframe using that EXACT timestamp:
   python /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/extract_keyframe_at_time.py \
     --date 2026-02-02 \
     --timestamp "2026-02-02T17:59:53-08:00" \
     --output "journal_2026-02-02_moment_1"
   
   # ✅ CORRECT - timestamp is within 5-7 PM range and shows "Area 2 Intervention"
   
   # ❌ WRONG - using 7:39 PM timestamp when timeline says 5-7 PM:
   python /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/extract_keyframe_at_time.py \
     --date 2026-02-02 \
     --timestamp "2026-02-02T19:39:42-08:00" \
     --output "journal_2026-02-02_moment_1"
   # This would show PowerPoint at 7:39 PM, which is AFTER the 5-7 PM period
   ```
   
   Then create video symlink:
   ```bash
   python /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/link_video_keyframes.py 2026-02-02
   ```
   
   This creates:
   - `assets/journal_2026-02-02_moment_1.png` (screenshot at 5:59 PM)
   - `assets/journal_2026-02-02_moment_1.mp4` (video symlink to recording around that time)
   
   **Understanding video filenames**:
   - Video files are named with 24-hour local time: `monitor_1_2026-02-02_18-47-13.mp4`
   - The timestamp `18-47-13` means 6:47:13 PM local time
   - This is correct if it falls within your timeline period
   - If your timeline is "5:00 PM - 7:00 PM" and the video is from 6:47 PM, that's correct ✅
   - If your timeline is "5:00 PM - 7:00 PM" but video is from 7:45 PM, that's wrong ❌
   
   **How to find the right timestamp**:
   1. Look at your timeline entry (e.g., "5:00 PM - 7:00 PM")
   2. Identify the LOCAL HOUR (17 = 5 PM, 18 = 6 PM, 19 = 7 PM)
   3. Read the raw JSON for those hours: `jq '.hourly_data["17"].ocr[0:2]' journal_raw_YYYY_MM_DD.json`
   4. Pick a timestamp that represents the activity you described
   5. Use that EXACT timestamp (with timezone) in the extraction command
   6. Verify: The screenshot should show what your timeline entry describes

8. **Embed screenshots/videos in timeline** - DO NOT SKIP THIS:
   
   **CRITICAL**: After extracting keyframes, you MUST embed them in the timeline. Add to the relevant `timeline-content` divs:
   
   ```html
        
![Description of what the screenshot shows](assets/journal_YYYY-MM-DD_moment_N.png)

        <p><a href="assets/journal_YYYY-MM-DD_moment_N.mp4">📹 Video recording</a></p>
   ```
   
   **Note**: Empty lines before/after image are required for proper markdown rendering inside HTML.

10. **Write the formatted journal** to:
    ```
    daily.journal.YYYY.MM.DD.md
    ```

11. **Update year index** if needed:
    ```
    daily.journal.YYYY.md
    ```

## Troubleshooting

**"No people linked in journal"**
- Automated detection may return 0 if audio is flagged as background content
- Agent MUST manually search audio transcripts: `jq -r '.hourly_data[].audio[].text' journal_raw_YYYY_MM_DD.json | grep -iE "(met with|email from|discussed)"`
- Check for meeting-related audio quotes - these almost always contain collaborator names
- Look for user file references in OCR: `user.{name}.md` being edited
- Cross-reference with existing user entries: `ls user.*.md`

**"No data found"**
- Check screenpipe is running: `ps aux | grep screenpipe`
- Verify port: `curl http://localhost:3030/search?limit=1`

**"Poor OCR quality"**
- Increase FPS: `--fps 1.0` or higher in screenpipe
- Check language settings: remove `--language chinese` if not needed

**"Missing keyframes"**
- Ensure `include_frames=true` in screenpipe query
- Check frame cache: `--enable-frame-cache`

**"Keyframe shows wrong time in screenshot"** or **"Screenshot doesn't match timeline entry"**
- **Root cause 1 - Timezone conversion error**: Using timestamps without timezone information
  - **Solution**: Always use timestamps from raw JSON that include timezone (e.g., `2026-01-31T19:30:00-08:00`)
  - **Never** create timestamps manually without timezone offset
  
- **Root cause 2 - Timeline/screenshot mismatch** (most common): Agent uses timestamp outside the timeline period
  - **Example**: Timeline says "5:00 PM - 7:00 PM" but screenshot extracted from 7:39 PM
  - **Solution**: 
    1. Check what hour the timestamp is from: `2026-02-02T19:39:42-08:00` = hour 19 = 7 PM
    2. If timeline says 5-7 PM, you need timestamps from hours 17 or 18, not hour 19
    3. Query the correct hour: `jq '.hourly_data["17"].ocr[0]' journal_raw_2026_02_02.json`
    4. Use that timestamp for keyframe extraction
  - **Verification**: The screenshot content should match the timeline entry description
  
- **Root cause 3 - Video link timing**: Video filename shows different time than timeline
  - **Example**: Timeline "5:00 PM - 7:00 PM" but video is `monitor_1_2026-02-02_19-30-15.mp4` (7:30 PM)
  - **Understanding**: Video filename uses 24-hour local time (`19-30-15` = 7:30:15 PM)
  - **Solution**: If video time is outside timeline range, the timeline boundaries are wrong
    - Either: Fix timeline to match actual data times
    - Or: Extract a different keyframe from within the correct time range

**"Journal quality poor"**
- Check the raw JSON - if OCR is garbled, no formatter can fix it
- Improve screenpipe settings first
- Review `ignore_windows` in config

## Design Philosophy

### Intelligence Where It Belongs

The workflow separates concerns clearly:

**Script (Dumb & Fast)**:
- Extract ALL raw data (OCR + audio)
- No decisions about what's important
- No heuristics about keyframes or activities
- Just structured data output

**Agent (Smart & Contextual)**:
- Understands semantic meaning of activities
- Identifies which moments need visual documentation
- Creates people entries with validation
- Selects keyframes based on content value
- Compresses timeline by work sessions
- Generates synthesis and insights

### Benefits of This Approach

1. **No wasted extraction**: Only extract keyframes that will be used
2. **Better keyframe selection**: Agent knows which moments matter (meetings, debugging, decisions) vs. which don't (terminal, code editor)
3. **Flexible**: Easy to adjust what gets included without changing scripts
4. **Fast**: Script runs quickly (no AI, no unnecessary image extraction)
5. **Smart**: Agent has full context when making decisions

### Evolution from Old Workflow

**Old approach (v1)**:
- Script extracted 5 keyframes using text length heuristic
- Often got useless screenshots (terminal windows, code editor)
- Agent had to work with whatever script provided

**Current approach (v2)**:
- Script extracts only raw data
- Agent analyzes content first
- Agent identifies 1-3 key moments needing screenshots
- Agent extracts only those specific keyframes
- Result: Better screenshots, less waste

## Files

### Current Scripts
- `extract_raw_data.sh` - Main data extraction script (OCR + audio → JSON)
- `extract_raw_data.py` - Python module for screenpipe querying
- `extract_keyframe_at_time.py` - Extract single keyframe at specific timestamp (called by agent)
- `link_video_keyframes.py` - Creates video symlinks for keyframes

### Sub-Skills
- `dendron/detect-people` - People detection and user entry creation (invoked by agent)

### Deprecated Scripts
- `full_workflow_v2.sh` - Old workflow that extracted all keyframes upfront (replaced by intelligent agent-driven extraction)
- `extract_keyframes.py` - Old bulk keyframe extraction (replaced by targeted extraction)
- `generate_journal_v*.py` - Old AI-powered generators (replaced by Cursor Agent)

## Related Skills

- **[[screenpipe-query]]** - Query screenpipe data
- **[[dendron/detect-people]]** - People detection and user entry creation
- **[[dendron-add]]** - Add journal insights to knowledge base

---

## FINAL VALIDATION CHECKLIST

Before marking a journal as complete, the agent MUST verify every item:

- [ ] **Screenshots embedded?** At least 1 keyframe extracted and embedded in the timeline. If zero screenshots, go back and extract them NOW.
- [ ] **People detected and linked?** All people from audio/OCR are linked with `[[Name|user.slug]]` or `<a href="user.slug.md">Name</a>`. New people have user entries created.
- [ ] **Meetings identified?** Any Zoom/Teams/Meet participant lists in OCR → meeting entry created. Substantial meetings (>1 hour) get separate `meet.YYYY.MM.DD.md` files.
- [ ] **Timeline ordering correct?** Morning (6 AM+) at top, late night (midnight-6 AM) at bottom.
- [ ] **Content synthesized?** No raw OCR dumps in timeline. Every timeline entry has human-readable description. Garbled OCR interpreted from context clues (app names, file paths, timestamps).
- [ ] **Audio quotes meaningful?** Only content-bearing quotes included (decisions, ideas, blockers). Background noise/media/game audio excluded.
- [ ] **Desc field specific?** Frontmatter `desc` names actual projects/activities, not generic categories like "General work, Web research."
- [ ] **Notes section has synthesis?** Patterns, insights, meta-observations present. Not just restating timeline.
- [ ] **Interaction Quality section present?** (Only if `.cache/interaction_scores/YYYY-MM-DD.jsonl` exists for this date. Omit if no score data.)

**If any item fails, fix it before writing the journal file.** A journal that fails these checks has negative retrieval value (worse than no journal at all because it creates false confidence that the day is documented).

---

**Key Point**: This skill is a **data provider**. The Cursor Agent does the AI analysis and formatting to match your journal style.
