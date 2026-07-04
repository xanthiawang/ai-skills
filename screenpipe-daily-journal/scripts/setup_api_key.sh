#!/bin/bash
# Setup helper for Anthropic API key

set -e

echo "🔧 Screenpipe Journal - API Key Setup"
echo ""

# Check if key already set
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "✅ ANTHROPIC_API_KEY is already set (length: ${#ANTHROPIC_API_KEY})"
    echo ""
    echo "Test the API connection:"
    echo "  curl -s https://api.anthropic.com/v1/messages \\"
    echo "    -H 'x-api-key: \$ANTHROPIC_API_KEY' \\"
    echo "    -H 'anthropic-version: 2023-06-01' \\"
    echo "    -H 'content-type: application/json' \\"
    echo "    -d '{\"model\":\"claude-sonnet-4-20250514\",\"max_tokens\":10,\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}'"
    exit 0
fi

echo "API key not found in environment."
echo ""

# Check shell config files
SHELL_CONFIG=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
else
    echo "⚠️  No .zshrc or .bashrc found."
    echo "   Create one manually or export in current session."
    exit 1
fi

echo "Found shell config: $SHELL_CONFIG"
echo ""

# Check if already in config (but not exported in current shell)
if grep -q "ANTHROPIC_API_KEY" "$SHELL_CONFIG" 2>/dev/null; then
    echo "✅ API key found in $SHELL_CONFIG"
    echo ""
    echo "Reload your shell to activate:"
    echo "  source $SHELL_CONFIG"
    echo ""
    echo "Or run in current session:"
    echo "  export ANTHROPIC_API_KEY=\"your-key-here\""
    exit 0
fi

# Guide user to add it
echo "📝 To add your API key:"
echo ""
echo "1. Get your key from: https://console.anthropic.com/"
echo ""
echo "2. Add to $SHELL_CONFIG:"
echo "   echo 'export ANTHROPIC_API_KEY=\"sk-ant-your-key-here\"' >> $SHELL_CONFIG"
echo ""
echo "3. Reload shell:"
echo "   source $SHELL_CONFIG"
echo ""
echo "4. Test this script again:"
echo "   bash /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-daily-journal/scripts/setup_api_key.sh"
echo ""
