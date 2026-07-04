#!/bin/bash
# Complete workflow for generating daily journal from screenpipe
# This script extracts RAW DATA only - formatting is done by Cursor Agent
# Usage: ./full_workflow_v2.sh [YYYY-MM-DD]

set -e

DATE=${1:-$(date +%Y-%m-%d)}
VAULT_PATH="$HOME/Documents/Manual Library/Dendron/notes"
SKILLS_PATH="$HOME/.cursor/skills"

echo "📅 Extracting raw data for: $DATE"
echo ""

# Step 1: Detect people and create user entries
echo "👥 Step 1/4: Detecting people and creating user entries..."
python3 "$SKILLS_PATH/dendron/detect-people/scripts/detect_and_create_users.py" "$DATE"
echo ""

# Step 2: Extract keyframe screenshots (PNG)
echo "📸 Step 2/4: Extracting keyframe screenshots..."
python3 "$SKILLS_PATH/screenpipe-daily-journal/scripts/extract_keyframes.py" "$DATE"
echo ""

# Step 3: Create video symlinks
echo "🎥 Step 3/4: Creating video symlinks..."
python3 "$SKILLS_PATH/screenpipe-daily-journal/scripts/link_video_keyframes.py" "$DATE"
echo ""

# Step 4: Extract raw data to JSON
echo "📊 Step 4/4: Extracting raw data..."
RAW_DATA_FILE="$VAULT_PATH/.cache/journal_raw_$(echo $DATE | tr '-' '_').json"
mkdir -p "$VAULT_PATH/.cache"
python3 "$SKILLS_PATH/screenpipe-daily-journal/scripts/extract_raw_data.py" "$DATE" -o "$RAW_DATA_FILE" --pretty
echo ""

echo "✅ Raw data extraction complete!"
echo "📄 Raw data: $RAW_DATA_FILE"
echo ""
echo "🤖 Next: Use Cursor Agent to format into journal"
echo ""
echo "In Cursor, run:"
echo "  @screenpipe-daily-journal format $DATE"
echo ""
echo "Or manually:"
echo "  1. Read raw data: $RAW_DATA_FILE"
echo "  2. Reference example: daily.journal.2026.01.31.md"
echo "  3. Format into: daily.journal.$(echo $DATE | tr '-' '.').md"
