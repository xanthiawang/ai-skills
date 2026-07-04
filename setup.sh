#!/usr/bin/env bash
# setup.sh — Deploy ai-skills to Claude Code, Codex, and Cursor.
#
# Skills with `alwaysApply: true` → always-loaded config files
# Skills without `alwaysApply`    → on-demand skill directories
#
# Always-on deployment:
#   Claude Code: @import in ~/.claude/CLAUDE.md (user-level, always loaded)
#   Codex:       Content in ~/.codex/AGENTS.md  (global, always loaded)
#   Cursor:      .mdc with alwaysApply: true
#
# On-demand deployment:
#   Claude Code: Symlink in ~/.claude/skills/
#   Codex:       Symlink in ~/.codex/skills/
#   Cursor:      .mdc with alwaysApply: false
#
# Usage:
#   ./setup.sh          # Deploy to all detected tools
#   ./setup.sh claude    # Claude Code only
#   ./setup.sh codex     # Codex only
#   ./setup.sh cursor    # Cursor only
#
# On a remote server: git clone <repo> ~/programs/ai-skills && cd ~/programs/ai-skills && ./setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGETS="${1:-all}"
ARCHIVE_STAMP="${AI_SKILLS_SYNC_STAMP:-$(date +%Y%m%d-%H%M%S)}"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()   { echo -e "${RED}[ERR]${NC} $1"; }

# ─── Discover and classify skills ────────────────────────────
SKILLS=()
ALWAYS_ON=()
ON_DEMAND=()

for d in "$SCRIPT_DIR"/*/; do
    [ -f "$d/SKILL.md" ] || continue
    name="$(basename "$d")"
    if git -C "$SCRIPT_DIR" check-ignore -q "$name" 2>/dev/null; then
        warn "Skipping local-only ignored skill alias: $name"
        continue
    fi
    SKILLS+=("$name")
    if awk '/^---$/{n++; next} n==1 && /^alwaysApply: *true/{found=1; exit} n>=2{exit} END{exit !found}' "$d/SKILL.md" 2>/dev/null; then
        ALWAYS_ON+=("$name")
    else
        ON_DEMAND+=("$name")
    fi
done

if [ ${#SKILLS[@]} -eq 0 ]; then
    err "No skills found in $SCRIPT_DIR"; exit 1
fi

echo "Found ${#SKILLS[@]} skills:"
[ ${#ALWAYS_ON[@]} -gt 0 ] && echo "  Always-on: ${ALWAYS_ON[*]}"
[ ${#ON_DEMAND[@]} -gt 0 ] && echo "  On-demand: ${ON_DEMAND[*]}"
echo ""

# ─── Helpers ─────────────────────────────────────────────────

MARKER_START="<!-- ai-skills-start -->"
MARKER_END="<!-- ai-skills-end -->"

# Strip YAML frontmatter, output body only.
strip_frontmatter() {
    awk 'BEGIN{n=0} /^---$/{n++; next} n>=2{print}' "$1"
}

# Write a managed block into a file, preserving user content outside markers.
write_managed_block() {
    local file="$1" content="$2"
    local block
    block="$(printf '%s\n%s%s' "$MARKER_START" "$content" "$MARKER_END")"

    if [ -f "$file" ]; then
        if grep -qF "$MARKER_START" "$file"; then
            # Remove old managed block
            awk -v s="$MARKER_START" -v e="$MARKER_END" '
                index($0,s)==1{skip=1;next} index($0,e)==1{skip=0;next} !skip
            ' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
        fi
        # Append new block
        printf '\n%s\n' "$block" >> "$file"
    else
        printf '%s\n' "$block" > "$file"
    fi
}

symlink_skill() {
    local src="$1" dst="$2" label="$3" name="$4"
    if [ -L "$dst" ]; then
        if [ "$(readlink "$dst")" = "$src" ]; then
            info "$label: $name (already linked)"; return
        fi
        archive_existing "$dst" "$label" "$name"
    elif [ -d "$dst" ]; then
        archive_existing "$dst" "$label" "$name"
    fi
    ln -s "$src" "$dst"
    info "$label: $name → $dst"
}

archive_existing() {
    local dst="$1" label="$2" name="$3"
    local archive_root archived
    archive_root="$(dirname "$dst").disabled/$ARCHIVE_STAMP"
    archived="$archive_root/$name"
    mkdir -p "$archive_root"
    if [ -e "$archived" ] || [ -L "$archived" ]; then
        archived="$archive_root/${name}.$RANDOM"
    fi
    mv "$dst" "$archived"
    warn "$label: $name — archived existing install at $archived"
}

remove_stale_symlink() {
    local dst="$1" label="$2" name="$3"
    if [ -L "$dst" ]; then
        rm "$dst"
        info "$label: removed $name from skills/ (now always-on)"
    elif [ -e "$dst" ]; then
        archive_existing "$dst" "$label" "$name"
        rm -rf "$dst"
        info "$label: removed $name from skills/ (now always-on)"
    fi
}

# ─── Claude Code ──────────────────────────────────────────────
# On-demand skills:  symlinked to ~/.claude/skills/
# Always-on skills:  @import in ~/.claude/CLAUDE.md (loaded every session)
link_claude() {
    local skills_dir="$HOME/.claude/skills"
    mkdir -p "$skills_dir"

    # Symlink on-demand skills
    for skill in "${ON_DEMAND[@]}"; do
        symlink_skill "$SCRIPT_DIR/$skill" "$skills_dir/$skill" "claude" "$skill"
    done

    # Remove always-on skills from skills/ (they go to CLAUDE.md instead)
    for skill in "${ALWAYS_ON[@]}"; do
        remove_stale_symlink "$skills_dir/$skill" "claude" "$skill"
    done

    # Write @imports for always-on skills into ~/.claude/CLAUDE.md
    if [ ${#ALWAYS_ON[@]} -gt 0 ]; then
        local imports=""
        for skill in "${ALWAYS_ON[@]}"; do
            imports+="@$SCRIPT_DIR/$skill/SKILL.md"$'\n'
        done
        write_managed_block "$HOME/.claude/CLAUDE.md" "$imports"
        info "claude: ~/.claude/CLAUDE.md updated (always-on @imports)"
    fi
}

# ─── Codex ────────────────────────────────────────────────────
# On-demand skills:  symlinked to ~/.codex/skills/
# Always-on skills:  inlined into ~/.codex/AGENTS.md (loaded every session)
link_codex() {
    local skills_dir="$HOME/.codex/skills"
    mkdir -p "$skills_dir"

    # Symlink on-demand skills
    for skill in "${ON_DEMAND[@]}"; do
        symlink_skill "$SCRIPT_DIR/$skill" "$skills_dir/$skill" "codex " "$skill"
    done

    # Remove always-on skills from skills/
    for skill in "${ALWAYS_ON[@]}"; do
        remove_stale_symlink "$skills_dir/$skill" "codex " "$skill"
    done

    # Generate ~/.codex/AGENTS.md with always-on content (frontmatter stripped)
    if [ ${#ALWAYS_ON[@]} -gt 0 ]; then
        local content=""
        for skill in "${ALWAYS_ON[@]}"; do
            content+="$(strip_frontmatter "$SCRIPT_DIR/$skill/SKILL.md")"$'\n'
        done
        write_managed_block "$HOME/.codex/AGENTS.md" "$content"
        info "codex:  ~/.codex/AGENTS.md updated (always-on content)"
    fi
}

# ─── Cursor ───────────────────────────────────────────────────
# All skills become .mdc files. alwaysApply read from frontmatter.
link_cursor() {
    local cursor_rules="$HOME/.cursor/rules"
    mkdir -p "$cursor_rules"

    for skill in "${SKILLS[@]}"; do
        local src="$SCRIPT_DIR/$skill/SKILL.md"
        local dst="$cursor_rules/${skill}.mdc"
        [ -f "$src" ] || { warn "cursor: $skill — SKILL.md not found, skipping"; continue; }

        local desc always_apply
        desc=$(awk '/^---$/{n++; next} n==1 && /^description:/{gsub(/^description: *"?|"$/,""); print; exit}' "$src")
        always_apply=$(awk '/^---$/{n++; next} n==1 && /^alwaysApply:/{gsub(/^alwaysApply: */,""); print; exit}' "$src")
        [ -z "$always_apply" ] && always_apply="false"

        {
            echo "---"
            echo "description: $desc"
            echo "globs:"
            echo "alwaysApply: $always_apply"
            echo "---"
            echo ""
            strip_frontmatter "$src"
        } > "$dst"

        info "cursor: $skill → $dst (alwaysApply: $always_apply)"
    done
}

# ─── Run ──────────────────────────────────────────────────────
case "$TARGETS" in
    all)
        echo "=== Claude Code ===" ; link_claude ; echo ""
        echo "=== Codex ===" ; link_codex ; echo ""
        echo "=== Cursor ===" ; link_cursor
        ;;
    claude) link_claude ;;
    codex)  link_codex ;;
    cursor) link_cursor ;;
    *) err "Unknown target: $TARGETS (use: all, claude, codex, cursor)"; exit 1 ;;
esac

echo ""
echo "Done."
echo ""
echo "Always-on:  ~/.claude/CLAUDE.md (@imports), ~/.codex/AGENTS.md, ~/.cursor/rules/ (alwaysApply: true)"
echo "On-demand:  ~/.claude/skills/, ~/.codex/skills/, ~/.cursor/rules/ (alwaysApply: false)"
echo ""
echo "Codex AGENTS.md and Cursor .mdc are generated copies — re-run after editing skills."
echo "Claude @imports resolve through the filesystem — edits propagate instantly."
