#!/usr/bin/env bash
# Pack the API keys listed in config/secrets-manifest.tsv into one encrypted file.
# Values never touch disk in plain text and are never printed.
#
#   scripts/export_secrets.sh --list            show which keys were found (names only)
#   scripts/export_secrets.sh [output.enc]      encrypt; asks for a passphrase twice
#
# Move the .enc file to the new machine by AirDrop or USB, never through this repo,
# and send the passphrase by a different channel.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$REPO/config/secrets-manifest.tsv"
ENV_FILE="${IDEA_FORGE_ENV:-$HOME/Desktop/StudyChat_Project/scripts/system/.env}"
CLAUDE_SETTINGS="$HOME/.claude/settings.json"
CODEX_CONFIG="$HOME/.codex/config.toml"

from_keychain() { security find-generic-password -s "$1" -w 2>/dev/null || true; }
from_envfile() {
    [ -f "$ENV_FILE" ] || return 0
    grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2- | sed -e 's/^["'\'']//' -e 's/["'\'']$//'
}
from_claude_settings() {
    [ -f "$CLAUDE_SETTINGS" ] || return 0
    jq -r --arg k "$1" '.env[$k] // empty' "$CLAUDE_SETTINGS"
}
from_codex_uizze_header() {
    [ -f "$CODEX_CONFIG" ] || return 0
    awk '/^\[/{inblk=($0=="[mcp_servers.uizze.http_headers]")} inblk && /^Authorization *=/{sub(/^Authorization *= *"/,""); sub(/"[ \t]*$/,""); print; exit}' "$CODEX_CONFIG"
}

lookup() {
    local name="$1" sources="$2" src val=""
    IFS=',' read -r -a list <<< "$sources"
    for src in "${list[@]}"; do
        case "$src" in
            keychain)           val="$(from_keychain "$name")" ;;
            envfile)            val="$(from_envfile "$name")" ;;
            claude-settings)    val="$(from_claude_settings "$name")" ;;
            codex-uizze-header) val="$(from_codex_uizze_header)" ;;
        esac
        [ -n "$val" ] && { printf '%s' "$val"; return 0; }
    done
    # Keys added to the keychain later are picked up too.
    from_keychain "$name"
}

payload() {
    local found=0
    while IFS=$'\t' read -r name _used sources _install _where; do
        [ "$name" = "name" ] && continue
        val="$(lookup "$name" "$sources")"
        [ -z "$val" ] && continue
        printf '%s\t%s\n' "$name" "$(printf '%s' "$val" | base64 | tr -d '\n')"
        found=$((found + 1))
    done < "$MANIFEST"
    [ "$found" -gt 0 ] || { echo "No keys found; nothing to export." >&2; return 1; }
}

if [ "${1:-}" = "--list" ]; then
    while IFS=$'\t' read -r name used sources _install _where; do
        [ "$name" = "name" ] && continue
        if [ -n "$(lookup "$name" "$sources")" ]; then s="FOUND"; else s="missing"; fi
        printf '%-22s %-8s %s\n' "$name" "$s" "$used"
    done < "$MANIFEST"
    exit 0
fi

OUT="${1:-$HOME/Desktop/ai-secrets_$(date +%Y-%m-%d).enc}"
case "$(cd "$(dirname "$OUT")" && pwd)/" in
    "$REPO"/*) echo "Refusing to write the bundle inside the repo: $OUT" >&2; exit 1 ;;
esac

umask 077
if [ -n "${AI_SECRETS_PASS:-}" ]; then
    payload | openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt -pass env:AI_SECRETS_PASS -out "$OUT"
else
    payload | openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt -out "$OUT"
fi
chmod 600 "$OUT"
echo "Wrote $OUT"
echo "Keys inside: $("$0" --list | awk '$2=="FOUND"{print $1}' | tr '\n' ' ')"
