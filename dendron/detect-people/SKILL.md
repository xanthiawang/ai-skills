---
name: detect-people
description: Create or update Dendron user entries for people detected in screenpipe data, using AI judgment to filter false positives.
---

# Detect People - AI-Driven Validation

Create user entries for people detected in screenpipe data. Uses AI judgment to filter false positives.

## Usage

```bash
# In Cursor:
@detect-people 2026-01-30
```

## Agent Instructions

### 1. Extract candidates
```bash
python3 ~/.cursor/skills/dendron/detect-people/scripts/extract_candidate_names.py [date]
```

Returns JSON with OCR/audio candidates and existing users.

### 2. Validate with AI judgment

For each candidate, determine if it's a real person:
- ✅ Real person with professional context → Create entry
- 🔗 Audio name matching existing user phonetically → Link to existing
- ❌ UI element, device name, OCR artifact → Skip

**Examples to skip**: "App Store", "HyperX SoloCast", "Enhanced Context", "Starting VideoCapture"

### 3. Create entries with ALL fields filled

**CRITICAL**: Never use placeholders like "[To be filled]". Every entry must be immediately populated.

For each validated person:
1. Web search for: name + "professor" OR name + "researcher" OR name + university
2. Extract: institution, role, email (if public), bio summary
3. Create entry with ALL information filled

**Example**: See `user.brian-athey.md` for proper format - all fields filled with real information from web search.

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

# Usage
node_id = generate_dendron_id()  # e.g., "m8kj3n9p4q5r6s7t8u9v0w1"
timestamp = get_timestamp_ms()   # e.g., 1706457600000
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

- 📧 Email: {actual email if found}
- 🏢 Institution: {actual institution}
- 🌐 {Website/profile URLs}

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

### 4. Return detected people for journal linking

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

**This list is used by journal generation to create [[Name|user.slug]] links in the journal text.**

Brief text summary:
- Created: X entries (list names)
- Linked: X audio names to existing users
- Skipped: X false positives (total only, don't list all)

---

**Key Principle**: When in doubt, skip. All created entries must be fully populated with real information.

**Auto-run**: This skill is automatically called during `@screenpipe-daily-journal` workflow.
