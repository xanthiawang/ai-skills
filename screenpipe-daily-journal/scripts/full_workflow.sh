#!/bin/bash
# Complete workflow for generating daily journal from screenpipe
# Usage: ./full_workflow.sh [YYYY-MM-DD]

set -e

DATE=${1:-$(date +%Y-%m-%d)}
VAULT_PATH="$HOME/Documents/Manual Library/Dendron/notes"
SKILLS_PATH="$HOME/.cursor/skills"

echo "📅 Generating journal for: $DATE"
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

# Step 4: Generate journal content with AI analysis
echo "📝 Step 4/4: Generating journal content with AI..."
JOURNAL_FILE="$VAULT_PATH/daily.journal.$(echo $DATE | tr '-' '.').md"
python3 "$SKILLS_PATH/screenpipe-daily-journal/scripts/generate_journal_v5.py" "$DATE" -o "$JOURNAL_FILE"
echo ""

# Step 5: Update year index
YEAR=$(echo $DATE | cut -d'-' -f1)
YEAR_FILE="$VAULT_PATH/daily.journal.$YEAR.md"

if [ -f "$YEAR_FILE" ]; then
    # Check if entry already exists
    if ! grep -q "daily.journal.$(echo $DATE | tr '-' '.')" "$YEAR_FILE"; then
        echo "📚 Step 5/5: Updating year index..."
        # Extract brief summary from journal
        SUMMARY=$(grep "^desc:" "$JOURNAL_FILE" | sed "s/desc: '//" | sed "s/'//")
        
        # Append to year file
        echo "" >> "$YEAR_FILE"
        echo "**$DATE** - $SUMMARY" >> "$YEAR_FILE"
        echo "  [[daily.journal.$(echo $DATE | tr '-' '.')]]" >> "$YEAR_FILE"
        echo ""
    fi
fi

echo "✅ Journal generation complete!"
echo "📄 File: $JOURNAL_FILE"
echo ""
echo "💡 Next steps:"
echo "   - Review journal and add manual notes"
echo "   - Update task sections (Today, Completed)"
echo "   - Fill in any missing context in user entries"
