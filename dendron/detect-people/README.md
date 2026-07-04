# Detect People - Auto-Create User Entries

**Sub-skill of**: [screenpipe-daily-journal](../../screenpipe-daily-journal/SKILL.md)

Automatically detect people from screenpipe recordings and create `user.{name}.md` entries in Dendron.

## 🎯 Purpose

When you interact with people (meetings, emails, collaboration), this skill:
- Detects full names from OCR text and audio
- Creates Dendron user entries with bio information
- Links people throughout your journal
- Maintains contact database automatically

## 🚀 Quick Start

**As part of journal workflow** (automatic):
```bash
@screenpipe-daily-journal
```

**Standalone usage**:
```bash
@detect-people 2026-01-30
```

**Manual script**:
```bash
python3 ~/.cursor/skills/dendron/detect-people/scripts/detect_and_create_users.py 2026-01-30
```

## ✅ Detection Rules

**WILL create entry when**:
- ✅ Full name present (first + last): "Brian Athey"
- ✅ Professional context: meeting, email, interview, collaboration
- ✅ Entry doesn't already exist

**WILL NOT create entry when**:
- ❌ First name only: "Donghyun"
- ❌ Generic/common names without context
- ❌ Entry already exists: checks for `user.{slug}.md`
- ❌ No professional context keywords

## 📋 How It Works

### Step 1: Scan Screenpipe Data

Queries screenpipe for OCR and audio:
```python
# From all screens
text = "...meeting with Brian Athey about faculty position..."

# From audio transcriptions  
audio = "We can schedule with Ravi Allada next week..."
```

### Step 2: Extract Full Names

Pattern matching for capitalized names:
- Looks for `[Capital Word] [Capital Word]` patterns
- Near professional keywords: professor, dr, director, interview, email
- Validates both words are alphabetic and >2 characters

### Step 3: Check Existing Entries

```python
slug = "brian-athey"  # Normalized from "Brian Athey"
exists = Path("user.brian-athey.md").exists()
```

### Step 4: Create Entry (if new)

```markdown
---
id: user-brian-athey-001
title: Brian Athey
---

## Contact Info
_[Agent will web search to fill]_

## Role & Expertise
_[Agent will web search to fill]_

## Context
**How we connected**: Detected from journal
**Date**: 2026-01-30
**Context**: meeting with Brian Athey about faculty...
```

### Step 5: Web Research (by agent)

When agent runs the skill:
- Searches: "Brian Athey University of Michigan"
- Extracts: role, institution, email, research focus
- Updates entry with complete information

### Step 6: Link in Journal

Updates journal to link people:
```markdown
Before: "Email Brian Athey about visit dates"
After:  "Email [[Brian Athey|user.brian-athey]] about visit dates"
```

## 📸 Example Output

```
👥 Step 1/4: Detecting people and creating user entries...

Detected 3 potential people:
  ✓ Brian Athey - already exists (user.brian-athey.md)
  ➜ Ravi Allada - creating entry...
    💡 Tip: Search web for 'Ravi Allada' to complete bio information
  ✗ John - skipped (no last name)
  ✗ Smith - skipped (no first name)

Created 1 new user entry
```

## 🎨 User Entry Template

```markdown
---
id: user-{slug}-001
title: {Full Name}
desc: ''
updated: {timestamp}
created: {timestamp}
---

## Contact Info

- 🏢 Institution: {university/company}
- 📧 Email: {email}
- 🌐 Website: {url}
- 🌐 Lab/Profile: {lab_url}

## Role & Expertise

**{Title}**, {Department}

{Institution}

## Research/Work Focus

{Description of research interests, expertise, or work}

{Key contributions or notable achievements}

## Context

**How we connected**: {Meeting/Email/Collaboration/etc.}

**Date**: {YYYY-MM-DD}

**Topic**: {What was discussed or why they're relevant}

**Follow-up**: {Action items or next steps}

## Notes

{Additional context from interactions}
```

## 🔧 Customization

Edit script to change detection patterns:

```python
# ~/.cursor/skills/dendron/detect-people/scripts/detect_and_create_users.py

# Add more professional keywords
prof_keywords = [
    'professor', 'dr.', 'phd', 'director', 'chair',
    'scientist', 'researcher', 'postdoc', 'faculty',
    'ceo', 'founder', 'engineer', 'developer'  # Add more
]

# Change vault path
vault_path = Path.home() / "path/to/your/dendron/vault"
```

## 🔗 Integration with Other Skills

**Called by**:
- `screenpipe-daily-journal` (automatic)
- `full_workflow.sh` (step 1)

**Uses**:
- `dendron-config` (for vault path)
- Web search APIs (for bio information)

**Updates**:
- Daily journal files (adds links)
- Year index (preserves links)

## 🐛 Troubleshooting

**"No people detected"**
- Check if screenpipe has data: `curl http://localhost:3030/search?limit=10`
- Verify professional keywords in text
- Look for full names (first + last)

**"Entry not created"**
- Check if already exists: `ls ~/Documents/Manual\ Library/Dendron/notes/user.*.md`
- Verify full name format (not just first name)
- Check for professional context keywords

**"Web search not working"**
- Agent needs to manually search and update entries
- Run script, then fill in bio information manually
- Or use agent with web search capability

## 📚 Related Skills

- **screenpipe-daily-journal**: Parent skill, calls detect-people automatically
- **dendron-add**: Create other types of Dendron entries
- **dendron-config**: Manage vault paths

## 💡 Tips

1. **Let it run automatically**: Part of daily journal workflow
2. **Review entries**: Agent searches and fills bio, but review for accuracy
3. **Link everywhere**: Use `[[Name|user.slug]]` syntax in all notes
4. **Update context**: Add notes after each interaction
5. **Track relationships**: Note collaborations, projects, shared interests
