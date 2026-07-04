#!/bin/bash
# Extract raw OCR/audio data from screenpipe - NO keyframes yet
# Keyframes will be extracted by agent after formatting
# Usage: ./extract_raw_data.sh [YYYY-MM-DD]

set -e

DATE=${1:-$(date +%Y-%m-%d)}
VAULT_PATH="$HOME/Documents/Manual Library/Dendron/notes"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_PATH="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "📅 Extracting raw data for: $DATE"
echo ""

# Extract raw data to JSON (OCR + audio only)
echo "📊 Extracting raw OCR and audio data..."
RAW_DATA_FILE="$VAULT_PATH/.cache/journal_raw_$(echo $DATE | tr '-' '_').json"
mkdir -p "$VAULT_PATH/.cache"
python3 "$SKILLS_PATH/screenpipe-daily-journal/scripts/extract_raw_data.py" "$DATE" -o "$RAW_DATA_FILE" --pretty

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Raw data extraction complete!"
    echo "📄 Raw data: $RAW_DATA_FILE"
    echo ""
    echo "🤖 Next: Use Cursor Agent to format into journal"
    echo ""
    echo "In Cursor, run:"
    echo "  @screenpipe-daily-journal $DATE"
    echo ""
    echo "The agent will:"
    echo "  1. Read this raw data"
    echo "  2. Detect and create people entries"
    echo "  3. Format the journal"
    echo "  4. Identify key moments"
    echo "  5. Extract keyframes for those moments"
    echo "  6. Link videos and embed in timeline"
else
    echo "❌ Error extracting raw data"
    exit 1
fi
