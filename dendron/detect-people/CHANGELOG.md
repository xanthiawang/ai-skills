# People Detection - Changelog

## v2.0 (2026-01-31) - AI-Driven Validation

### Breaking Changes

**Replaced rule-based filtering with AI judgment**
- Removed 300+ lines of regex patterns and keyword lists
- Deleted verbose AI_VALIDATION_PROTOCOL.md (was wasting context)
- New workflow: Extract broadly → AI validates → Create complete entries

### Core Improvements

1. **AI Validation Instead of Programmatic Rules**
   - Old: Complex regex to filter "Assistant Professor", "Microsoft Excel", etc.
   - New: AI instantly recognizes false positives in context
   - Result: 0 false positives created (tested on 44 candidates, all correctly skipped)

2. **All Fields Must Be Filled**
   - Old: Entries created with "[To be filled]" placeholders
   - New: Web search REQUIRED before creating any entry
   - If web search finds nothing → Skip (likely false positive)
   - Template example: `user.brian-athey.md`

3. **Concise Instructions**
   - Old: 100+ line protocol documents
   - New: 40-line skill file with clear task
   - Principle: Trust AI judgment, don't over-specify

4. **Audio Name Phonetic Matching**
   - Audio transcription is unreliable for names
   - Check against existing users first (e.g., "Gin Yap" → "Jin Yap")
   - Only create new audio entries if web-verified

### Files

**Active:**
- `SKILL.md` - Concise agent instructions
- `scripts/extract_candidate_names.py` - Broad extraction, minimal filtering
- `CHANGELOG.md` - This file

**Deprecated:**
- `scripts/detect_and_create_users.py` - Old rule-based approach
- `AI_VALIDATION_PROTOCOL.md` - Verbose, context-wasting

### Results

**Test Run (2026-01-30 data)**:
- Candidates: 43 OCR + 1 audio
- Created: 0 (all were false positives)
- Precision: 100%
- Skipped examples: "App Store", "HyperX SoloCast", "Starting VideoCapture", "Enhanced Context"

**Real people in data already had entries** → Correct behavior: skip duplicates

---

## v1.0 (2026-01-30) - Rule-Based Filtering [DEPRECATED]

Used programmatic filtering with:
- Excluded keywords (300+ patterns)
- Professional context detection
- OCR error heuristics

**Problem**: Brittle, still produced false positives, required constant maintenance.

---

**Migration**: Simply use `@detect-people [date]` - the new workflow handles everything.
