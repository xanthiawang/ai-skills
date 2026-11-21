#!/usr/bin/env bash
# Unpack a bundle made by export_secrets.sh on the new machine.
#
#   scripts/import_secrets.sh ai-secrets_YYYY-MM-DD.enc     asks for the passphrase
#
# Every key goes into the login keychain (service name = key name). Then, by the
# install_as column of config/secrets-manifest.tsv:
#   global   exported in every new shell through a managed block in ~/.zshrc
#   wrapper  only injected when a command runs through `ai-env <command>`, because a
#            global ANTHROPIC_API_KEY or OPENAI_API_KEY can switch Claude Code or Codex
#            from the signed-in account to pay-per-use API billing
#   claude   written into ~/.claude/settings.json "env" (a backup is kept)
#   keychain left in the keychain only (minimax MCP reads it there)
# Set AI_SECRETS_KEYCHAIN to a keychain file path to write somewhere other than the login keychain.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$REPO/config/secrets-manifest.tsv"
BUNDLE="${1:?usage: import_secrets.sh <bundle.enc>}"
KC="${AI_SECRETS_KEYCHAIN:-}"
ZSHRC="$HOME/.zshrc"
CLAUDE_SETTINGS="$HOME/.claude/settings.json"

install_as() { awk -F'\t' -v n="$1" '$1==n{print $4; exit}' "$MANIFEST"; }

decrypt() {
    if [ -n "${AI_SECRETS_PASS:-}" ]; then
        openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass env:AI_SECRETS_PASS -in "$BUNDLE"
    else
        openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -in "$BUNDLE"
    fi
}

LINES="$(decrypt)" || { echo "Decryption failed: wrong passphrase or damaged file." >&2; exit 1; }

global_names=()
claude_pairs=()
imported=()
while IFS=$'\t' read -r name b64; do
    [ -z "$name" ] && continue
    val="$(printf '%s' "$b64" | base64 --decode)"
    if [ -n "$KC" ]; then
        security add-generic-password -U -a "$USER" -s "$name" -w "$val" "$KC"
    else
        security add-generic-password -U -a "$USER" -s "$name" -w "$val"
    fi
    imported+=("$name")
    case "$(install_as "$name")" in
        global) global_names+=("$name") ;;
        claude) claude_pairs+=("$name") ;;
    esac
done <<< "$LINES"
unset LINES val

if [ ${#claude_pairs[@]} -gt 0 ]; then
    mkdir -p "$(dirname "$CLAUDE_SETTINGS")"
    [ -f "$CLAUDE_SETTINGS" ] || echo '{}' > "$CLAUDE_SETTINGS"
    cp "$CLAUDE_SETTINGS" "$CLAUDE_SETTINGS.bak-$(date +%Y%m%d-%H%M%S)"
    for name in "${claude_pairs[@]}"; do
        if [ -n "$KC" ]; then v="$(security find-generic-password -s "$name" -w "$KC")"; else v="$(security find-generic-password -s "$name" -w)"; fi
        tmp="$(mktemp)"
        jq --arg k "$name" --arg v "$v" '.env = ((.env // {}) + {($k): $v})' "$CLAUDE_SETTINGS" > "$tmp"
        mv "$tmp" "$CLAUDE_SETTINGS"
    done
    chmod 600 "$CLAUDE_SETTINGS"
    unset v
fi

START="# >>> ai-skills secrets (managed by import_secrets.sh) >>>"
END="# <<< ai-skills secrets <<<"
touch "$ZSHRC"
tmp="$(mktemp)"
awk -v s="$START" -v e="$END" '$0==s{skip=1} !skip{print} $0==e{skip=0}' "$ZSHRC" > "$tmp"
if [ ${#global_names[@]} -gt 0 ]; then
    {
        echo "$START"
        for name in "${global_names[@]}"; do
            echo "export $name=\"\$(security find-generic-password -s $name -w 2>/dev/null)\""
        done
        echo "$END"
    } >> "$tmp"
fi
mv "$tmp" "$ZSHRC"

mkdir -p "$HOME/.local/bin"
ln -sf "$REPO/scripts/ai-env" "$HOME/.local/bin/ai-env"

echo "Imported into keychain: ${imported[*]}"
[ ${#global_names[@]} -gt 0 ] && echo "Exported in new shells: ${global_names[*]}"
[ ${#claude_pairs[@]} -gt 0 ] && echo "Written to $CLAUDE_SETTINGS: ${claude_pairs[*]}"
echo "Run wrapper-only keys with: ai-env <command>"
for name in "${imported[@]}"; do
    if [ "$name" = "UIZZE_AUTHORIZATION" ]; then
        echo "Codex uizze MCP: put the keychain value of UIZZE_AUTHORIZATION into [mcp_servers.uizze.http_headers] Authorization in ~/.codex/config.toml"
    fi
done
