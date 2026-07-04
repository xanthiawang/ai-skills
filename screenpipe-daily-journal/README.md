# Screenpipe Daily Journal - Complete Workflow

Automated daily journal generation from screenpipe recordings with AI insights, keyframes, and people detection.

**🌙 NEW: Sleep-Aware Day Boundaries** - The system now intelligently detects your sleep/wake cycle. Late-night work (e.g., 11 PM → 3 AM) is correctly part of the same day, not split at midnight. [See examples →](EXAMPLES.md)

## 🚀 Quick Start

**Generate journal for today**:
```bash
bash /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/full_workflow.sh
```

**Generate for specific date**:
```bash
bash /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/full_workflow.sh 2026-01-30
```

## 📋 Complete Workflow

The full workflow runs these steps automatically:

### 1. 👥 People Detection (3-5 seconds)
```bash
python3 ~/.cursor/skills/dendron/detect-people/scripts/detect_and_create_users.py 2026-01-30
```

**What it does**:
- Scans screenpipe OCR and audio for full names
- Only creates entries with first + last name
- Skips if user entry already exists
- Web searches for bio information (when run by agent)
- Creates `user.{name-slug}.md` entries
- Links people throughout journal

**Example output**:
```
✓ Brian Athey - creating entry...
  💡 Tip: Search web for 'Brian Athey' to complete bio
✓ Ravi Allada - already exists (user.ravi-allada.md)
```

### 2. 📸 Keyframe Extraction (10-15 seconds)
```bash
python3 /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/extract_keyframes.py 2026-01-30
```

**What it does**:
- Finds screens with substantial text (>150 chars)
- Filters out utility windows (screenpipe, Settings, etc.)
- Extracts frames from MP4 videos using ffmpeg
- Saves as PNG to `assets/journal_YYYY-MM-DD_moment_N.png`
- Top 5 keyframes selected

**Example output**:
```
✓ Extracted: journal_2026-01-30_moment_1.png
✓ Extracted: journal_2026-01-30_moment_2.png
...
```

### 3. 🎥 Video Symlink Creation (1-2 seconds)
```bash
python3 /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/link_video_keyframes.py 2026-01-30
```

**What it does**:
- Creates symlinks to original MP4 files
- Points to `~/.screenpipe/data/monitor_*.mp4`
- No storage duplication (symlink ~4KB)
- Enables viewing full video context

**Example output**:
```
✓ Linked: journal_2026-01-30_moment_1.mp4 -> monitor_4_2026-01-30_19-20-05.mp4
```

### 4. 📝 Journal Generation (5-10 seconds)
```bash
python3 /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/generate_journal_v2.py 2026-01-30
```

**What it does**:
- 🌙 **Detects sleep/wake cycle** - Finds intelligent day boundaries based on activity gaps
- Queries screenpipe for all day's data (using smart boundaries, not midnight)
- Extracts work context (not just apps)
- Generates timeline with specific details
- Identifies blockers and next steps
- Infers tasks from conversations
- Links to user entries for people

**Sleep-Aware Boundaries**:
The system analyzes a wider time window to detect sleep periods (gaps > 3 hours). If you work from 11 PM → 3 AM, that late-night session is correctly part of the same day:

```
Without smart boundaries:
- Jan 30: ...work... → midnight ❌ (splits session)
- Jan 31: 12 AM → 3 AM work... ❌ (messy)

With smart boundaries:
- Jan 30: 11 AM wake → 3 AM sleep ✅ (16 hours)
- Jan 31: 11 AM wake → next sleep ✅ (natural)
```

See [EXAMPLES.md](EXAMPLES.md) for detailed scenarios.

**Journal structure**:
```markdown
## Day Summary
Brief scannable overview

## Timeline
### 11:00 AM - Activity

![Screenshot](assets/journal_2026-01-30_moment_1.png)
_[View video context](assets/journal_2026-01-30_moment_1.mp4)_

- Specific detail about what you did
- Decision: What you decided
- Blocked: What's stuck
- 🎤 "Important quote from conversation"

## State & Open Questions
**Project Name**
- Status: Current state
- Blocker: What's stuck
- Next: What to do next

## Tasks
### Inferred from Today
- [ ] Action item with blocker noted

### Completed Today
- [x] What you finished
```

### 5. 📚 Year Index Update (instant)

Appends to `daily.journal.YYYY.md`:
```markdown
**2026-01-30** - Brief summary from journal
  [[daily.journal.2026.01.30]]
```

## 🎯 Why This Workflow?

### PNG + Video = Best of Both Worlds
- **PNG**: Inline preview in Dendron/Obsidian/etc.
- **Video symlink**: Full context with scrubbing
- **Storage**: ~2MB PNG + ~4KB symlink (not duplicating 30MB video)

### Auto-Created User Entries
- **Before**: "Email Brian Athey" (who?)
- **After**: `[[Brian Athey|user.brian-athey]]` → Full bio, role, research
- Only creates with full names (skips "Donghyun" without last name)
- Web searches to complete information

### Content-Focused Timeline
- **Not**: "Cursor - Development work"
- **Is**: "Protein clock - Fixed overfitting bug, debugging NaN errors, next: add logging"
- Specific details you'll need in 6 months

### AI Handoff Ready
- **State & Open Questions** section shows:
  - What's in progress
  - What's blocking you
  - What's the next step
- Agent can pick up where you left off

## 🔧 Individual Components

Run parts of the workflow separately:

```bash
# Just detect people
python3 ~/.cursor/skills/dendron/detect-people/scripts/detect_and_create_users.py 2026-01-30

# Just extract keyframes (PNG)
python3 /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/extract_keyframes.py 2026-01-30

# Just create video symlinks
python3 /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/link_video_keyframes.py 2026-01-30

# Just generate journal
python3 /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/generate_journal_v2.py 2026-01-30 -o output.md
```

## 📦 Requirements

- **screenpipe**: Running and recording (`http://localhost:3030`)
- **ffmpeg**: For frame extraction (`brew install ffmpeg`)
- **Python 3**: With standard library
- **Dendron vault**: At `~/Documents/Manual Library/Dendron/notes`

## 🎨 Customization

Edit `~/.screenpipe/journal_config.json`:
```json
{
  "screenpipe_port": 3030,
  "journal_path": "/path/to/dendron/vault",
  "ignore_windows": ["screenpipe", "Settings", "1Password"],
  "max_keyframes": 5,
  "keyframe_threshold": 150,
  "sleep_detection": {
    "min_gap_hours": 3.0,
    "default_wake_hour": 6,
    "late_night_cutoff_hour": 6
  }
}
```

**Sleep Detection Settings**:
- `min_gap_hours`: Minimum inactivity to consider as sleep (default: 3.0)
  - Lower = detects shorter breaks as sleep
  - Higher = only long sleep periods counted
- `default_wake_hour`: Fallback if no sleep detected (default: 6 AM)
- `late_night_cutoff_hour`: Activities before this may belong to previous day (default: 6 AM)

**Example configurations**:
- **Night owl**: `{"default_wake_hour": 10, "late_night_cutoff_hour": 8}`
- **Light sleeper**: `{"min_gap_hours": 4.0}` (stricter sleep detection)
- **Frequent breaker**: `{"min_gap_hours": 2.5}` (more lenient)

## 🐛 Troubleshooting

**"Error querying screenpipe"**
- Check if screenpipe is running: `ps aux | grep screenpipe`
- Test API: `curl http://localhost:3030/health`

**"No data found"**
- Check date format: YYYY-MM-DD
- Verify screenpipe recorded that day
- Check screenpipe data directory: `ls ~/.screenpipe/data/`

**"FFmpeg not found"**
- Install: `brew install ffmpeg`

**User entries not creating**
- Check if full name is present (need first + last)
- Verify professional context keywords present
- Check if entry already exists: `ls ~/Documents/Manual\ Library/Dendron/notes/user.*.md`

## 📚 Related Skills

- **dendron/detect-people**: Auto-create user entries
- **screenpipe-query**: Query screenpipe data
- **dendron-add**: Add notes to Dendron

## 📝 Next Steps After Generation

1. **Review journal**: Add manual notes in "Notes" section
2. **Update tasks**: Fill in "Today" and "Completed" sections
3. **Complete user entries**: Add missing bio info
4. **Check State**: Update blockers and next steps
5. **Commit**: `git add . && git commit -m "Daily journal 2026-01-30"`
