#!/usr/bin/env bash
# Sync Albert's agent skills, local MCP entries, and safe agent settings.
#
# Source of truth:
#   ~/programs/ai-skills
#
# This script intentionally does not sync secrets, OAuth tokens, sqlite state,
# logs, session transcripts, plugin caches, or browser-extension tokens.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MODE="${1:-apply}"
STAMP="${AI_SKILLS_SYNC_STAMP:-$(date +%Y%m%d-%H%M%S)}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

have_cmd() {
    command -v "$1" >/dev/null 2>&1
}

run_with_timeout() {
    local seconds="$1"
    shift

    if have_cmd timeout; then
        timeout "$seconds" "$@"
        return
    fi
    if have_cmd gtimeout; then
        gtimeout "$seconds" "$@"
        return
    fi

    # macOS does not ship GNU `timeout`. Use Python as a portable fallback and
    # terminate the whole child process group if the deadline is exceeded.
    python3 - "$seconds" "$@" <<'PY'
import os
import signal
import subprocess
import sys

seconds = float(sys.argv[1])
command = sys.argv[2:]
process = subprocess.Popen(command, start_new_session=True)
try:
    return_code = process.wait(timeout=seconds)
except subprocess.TimeoutExpired:
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
    return_code = 124
raise SystemExit(return_code)
PY
}

sync_skills() {
    "$REPO_ROOT/setup.sh" all
}

# External skills: third-party skill repos that cannot be vendored into this
# repo (no redistribution license) but are declared here so a new machine can
# reproduce the install. Cloned into ~/programs next to their companion tools
# and symlinked into ~/.claude/skills/.
sync_external_skills() {
    # Dreamina is distributed by its official installer, not vendored here.
    # Install CLI + Skill: curl -fsSL https://jimeng.jianying.com/canvas-cli/install.sh | bash
    # Keep OAuth credentials in the CLI's OS credential store.
    local dreamina_src="$HOME/.agents/skills/dreamina-canvas-cli"
    local dreamina_target
    if [ -f "$dreamina_src/SKILL.md" ]; then
        for dreamina_target in "$HOME/.codex/skills/dreamina-canvas-cli" "$HOME/.claude/skills/dreamina-canvas-cli"; do
            if [ -L "$dreamina_target" ] && [ "$(readlink "$dreamina_target")" = "$dreamina_src" ]; then
                info "external skill: Dreamina already linked"
            elif [ -e "$dreamina_target" ] || [ -L "$dreamina_target" ]; then
                warn "external skill: $dreamina_target exists; leaving as is"
            else
                mkdir -p "$(dirname "$dreamina_target")"
                ln -s "$dreamina_src" "$dreamina_target"
                info "external skill: Dreamina linked"
            fi
        done
    else
        warn "external skill: Dreamina not installed; use its official installer"
    fi

    # autocad-drafting (puran-water): companion skill for the autocad MCP
    # server declared in sync_claude_mcp. Upstream repo is archived (frozen
    # at aa80dbc, consolidated into PuranOS) and carries no license, so it
    # must stay out of this public repo.
    local src="$HOME/programs/autocad-drafting"
    local dst="$HOME/.claude/skills/autocad-drafting"
    if [ ! -d "$src" ]; then
        if git clone --depth 1 https://github.com/puran-water/autocad-drafting.git "$src"; then
            info "external skill: cloned autocad-drafting"
        else
            warn "external skill: failed to clone autocad-drafting; skipping"
            return
        fi
    fi
    if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
        info "external skill: autocad-drafting already linked"
    elif [ -e "$dst" ] || [ -L "$dst" ]; then
        warn "external skill: $dst exists and is not the expected symlink; leaving as is"
    else
        mkdir -p "$HOME/.claude/skills"
        ln -s "$src" "$dst"
        info "external skill: autocad-drafting → $dst"
    fi

    # unity-mcp-orchestrator (CoplayDev/unity-mcp, MIT): the official
    # companion skill lives inside the big server repo, so keep a sparse
    # checkout of just that directory and symlink it. `git pull` in
    # ~/programs/unity-mcp updates the skill.
    local u_repo="$HOME/programs/unity-mcp"
    local u_dst="$HOME/.claude/skills/unity-mcp-orchestrator"
    if [ ! -d "$u_repo" ]; then
        if git clone --depth 1 --filter=blob:none --sparse \
                https://github.com/CoplayDev/unity-mcp.git "$u_repo"; then
            git -C "$u_repo" sparse-checkout set unity-mcp-skill
            info "external skill: cloned unity-mcp-skill"
        else
            warn "external skill: failed to clone unity-mcp; skipping"
        fi
    fi
    if [ -d "$u_repo/unity-mcp-skill" ]; then
        if [ -L "$u_dst" ] && [ "$(readlink "$u_dst")" = "$u_repo/unity-mcp-skill" ]; then
            info "external skill: unity-mcp-orchestrator already linked"
        elif [ -e "$u_dst" ] || [ -L "$u_dst" ]; then
            warn "external skill: $u_dst exists and is not the expected symlink; leaving as is"
        else
            mkdir -p "$HOME/.claude/skills"
            ln -s "$u_repo/unity-mcp-skill" "$u_dst"
            info "external skill: unity-mcp-orchestrator → $u_dst"
        fi
    fi

}

archive_path() {
    local path="$1" archive_root="$2" label="$3"
    if [ ! -e "$path" ] && [ ! -L "$path" ]; then
        return
    fi
    mkdir -p "$archive_root/$STAMP"
    local dest="$archive_root/$STAMP/$(basename "$path")"
    if [ -e "$dest" ] || [ -L "$dest" ]; then
        dest="$archive_root/$STAMP/$(basename "$path").$RANDOM"
    fi
    mv "$path" "$dest"
    warn "$label: archived $(basename "$path") at $dest"
}

cleanup_legacy_skill_aliases() {
    archive_path "$HOME/.codex/skills/taiyiyuan" "$HOME/.codex/skills.disabled" "codex skill"
    archive_path "$HOME/.codex/skills/dendron-command-center" "$HOME/.codex/skills.disabled" "codex skill"
    archive_path "$HOME/.codex/skills/dendron-sync" "$HOME/.codex/skills.disabled" "codex skill"
    archive_path "$HOME/.claude/skills/taiyiyuan" "$HOME/.claude/skills.disabled" "claude skill"
    rm -f "$HOME/.cursor/rules/taiyiyuan.mdc"
}

install_codex_pywal_theme() {
    local template_src="$REPO_ROOT/config/wal/templates/codex-pywal.tmTheme"
    local template_dest="$HOME/.config/wal/templates/codex-pywal.tmTheme"
    local rendered_theme="$HOME/.cache/wal/codex-pywal.tmTheme"
    local codex_theme_dir="$HOME/.codex/themes"
    local codex_theme="$codex_theme_dir/pywal.tmTheme"

    if [ ! -f "$template_src" ]; then
        warn "codex theme: missing managed pywal template at $template_src"
        return
    fi

    mkdir -p "$(dirname "$template_dest")" "$codex_theme_dir"
    cp "$template_src" "$template_dest"

    local wal_bin=""
    if [ -x "$HOME/.local/bin/wal" ]; then
        wal_bin="$HOME/.local/bin/wal"
    elif have_cmd wal; then
        wal_bin="$(command -v wal)"
    fi

    if [ -n "$wal_bin" ]; then
        if "$wal_bin" -R -n -e -s -t -q; then
            info "codex theme: rendered pywal template"
        else
            warn "codex theme: pywal restore failed; keeping existing rendered theme if present"
        fi
    else
        warn "codex theme: wal not found; keeping existing rendered theme if present"
    fi

    if [ -f "$rendered_theme" ]; then
        ln -sfn "$rendered_theme" "$codex_theme"
        info "codex theme: linked pywal theme into $codex_theme"
    else
        warn "codex theme: rendered theme not found at $rendered_theme"
    fi

    if have_cmd plutil; then
        plutil -lint "$template_dest" >/dev/null || warn "codex theme: template plist validation failed"
        if [ -f "$rendered_theme" ]; then
            plutil -lint "$rendered_theme" >/dev/null || warn "codex theme: rendered plist validation failed"
        fi
    fi
}

apply_codex_settings() {
    local config="$HOME/.codex/config.toml"
    mkdir -p "$(dirname "$config")"

    python3 - "$config" <<'PY'
from __future__ import annotations

import re
import sys
import json
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8") if path.exists() else ""
if text.strip():
    tomllib.loads(text)

lines = text.splitlines()


def set_root_key(key: str, value: str) -> None:
    section_start = len(lines)
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section_start = index
            break

    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for index in range(section_start):
        if pattern.match(lines[index]):
            lines[index] = f"{key} = {value}"
            return

    insert_at = section_start
    while insert_at > 0 and not lines[insert_at - 1].strip():
        insert_at -= 1
    lines.insert(insert_at, f"{key} = {value}")


def remove_root_key(key: str) -> None:
    section_start = len(lines)
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section_start = index
            break

    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for index in range(section_start - 1, -1, -1):
        if pattern.match(lines[index]):
            del lines[index]


def section_bounds(section: str):
    header = f"[{section}]"
    start = None
    for index, line in enumerate(lines):
        if line.strip() == header:
            start = index
            break
    if start is None:
        return None, None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            end = index
            break
    return start, end


def has_key(section: str, key: str) -> bool:
    start, end = section_bounds(section)
    if start is None:
        return False
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    return any(pattern.match(lines[i]) for i in range(start + 1, end))


def set_key(section: str, key: str, value: str) -> None:
    start, end = section_bounds(section)
    header = f"[{section}]"

    if start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend([header, f"{key} = {value}"])
        return

    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for index in range(start + 1, end):
        if pattern.match(lines[index]):
            lines[index] = f"{key} = {value}"
            return

    lines.insert(end, f"{key} = {value}")


def quote(value: str) -> str:
    return json.dumps(value)


def load_wal_theme() -> dict[str, str] | None:
    colors_path = Path.home() / ".cache/wal/colors.json"
    try:
        data = json.loads(colors_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[skip] codex desktop theme: {colors_path} not found", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"[skip] codex desktop theme: failed to read {colors_path}: {exc}", file=sys.stderr)
        return None

    special = data.get("special", {})
    colors = data.get("colors", {})

    def color(name: str, fallback: str) -> str:
        value = special.get(name) if name in special else colors.get(name)
        if isinstance(value, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            return value
        return fallback

    return {
        "surface": color("background", "#181214"),
        "ink": color("foreground", "#c5c3c4"),
        "accent": color("color4", color("cursor", "#c5c3c4")),
        "diff_added": color("color2", "#A5A29A"),
        "diff_removed": color("color1", "#928F8A"),
        "skill": color("color5", "#CDC8BC"),
    }


def apply_desktop_pywal_theme() -> None:
    theme = load_wal_theme()
    if theme is None:
        return

    # Codex.app reads these desktop settings from ~/.codex/config.toml.
    for section, contrast in (
        ("desktop.appearanceLightChromeTheme", "45"),
        ("desktop.appearanceDarkChromeTheme", "60"),
    ):
        set_key(section, "accent", quote(theme["accent"]))
        set_key(section, "contrast", contrast)
        set_key(section, "ink", quote(theme["ink"]))
        set_key(section, "opaqueWindows", "false")
        set_key(section, "surface", quote(theme["surface"]))
        set_key(f"{section}.fonts", "code", quote('"Jetbrains Mono"'))
        set_key(f"{section}.fonts", "ui", quote("Inter"))
        set_key(f"{section}.semanticColors", "diffAdded", quote(theme["diff_added"]))
        set_key(f"{section}.semanticColors", "diffRemoved", quote(theme["diff_removed"]))
        set_key(f"{section}.semanticColors", "skill", quote(theme["skill"]))


def remove_section(section: str) -> None:
    start, end = section_bounds(section)
    if start is None:
        return

    while start > 0 and not lines[start - 1].strip():
        start -= 1
    del lines[start:end]


# Model availability is account- and rollout-dependent. Preserve the user's
# selected model and reasoning effort instead of pinning a temporary fallback.
# Do not force an API service tier for ChatGPT-authenticated Codex models. The
# client will warn and omit unsupported tiers such as the legacy `priority`.
remove_root_key("service_tier")
set_root_key("sandbox_mode", '"workspace-write"')
set_root_key("suppress_unstable_features_warning", "true")
set_key("sandbox_workspace_write", "network_access", "true")
set_key("tui", "theme", '"pywal"')
apply_desktop_pywal_theme()
set_key('plugins."slack@claude-plugins-official"', "enabled", "false")
set_key('plugins."slack@openai-curated"', "enabled", "false")
set_key('plugins."hugging-face@openai-curated"', "enabled", "false")
# The Superwhisper Codex hook opens an interactive dictation/edit window at
# turn boundaries. Keep the standalone Superwhisper app available, but leave
# this intrusive Codex integration disabled by default.
set_key('plugins."superwhisper@superwhisper"', "enabled", "false")
remove_section("mcp_servers.scg")

# Only layer enabled_tools on top of an existing 1password MCP entry. Writing
# this key into a section that lacks a transport (command/args/url) would
# produce an "invalid transport" config that breaks the codex CLI.
if has_key("mcp_servers.1password", "command") or has_key(
    "mcp_servers.1password", "url"
):
    set_key(
        "mcp_servers.1password",
        "enabled_tools",
        '["vault_list", "item_lookup", "password_read"]',
    )
else:
    print(
        "[skip] mcp_servers.1password has no transport yet — "
        "skipping enabled_tools (sync_mcp will add the transport first)",
        file=sys.stderr,
    )

# Keep situational MCP servers installed without launching them in every Codex
# session. They can still be enabled per run with
# `-c mcp_servers.<name>.enabled=true`.
for section in (
    "mcp_servers.codex-cli",
    "mcp_servers.1password",
    "mcp_servers.mobile-mcp",
):
    if section_bounds(section)[0] is not None:
        set_key(section, "enabled", "false")

for section in (
    "mcp_servers.paperclip",
    "mcp_servers.screenpipe",
):
    if section_bounds(section)[0] is not None:
        set_key(section, "enabled", "true")

# Screenpipe normally starts quickly from the local npm cache. Paperclip is a
# remote OAuth server and needs more headroom on intermittent networks.
if section_bounds("mcp_servers.screenpipe")[0] is not None:
    set_key("mcp_servers.screenpipe", "startup_timeout_sec", "60.0")
if section_bounds("mcp_servers.paperclip")[0] is not None:
    set_key("mcp_servers.paperclip", "startup_timeout_sec", "120.0")

updated = "\n".join(lines).rstrip() + "\n"
tomllib.loads(updated)
path.write_text(updated, encoding="utf-8")
PY
    info "codex: safe settings applied to $config"
}

codex_has_mcp() {
    run_with_timeout 10 codex mcp get "$1" >/dev/null 2>&1
}

ensure_codex_stdio_mcp() {
    local name="$1"
    shift
    if codex_has_mcp "$name"; then
        info "codex mcp: $name already configured"
    else
        codex mcp add "$name" -- "$@"
        info "codex mcp: added $name"
    fi
}

ensure_codex_http_mcp() {
    local name="$1" url="$2"
    if codex_has_mcp "$name"; then
        info "codex mcp: $name already configured"
        return
    fi
    # `codex mcp add --url` writes the entry to config and then attempts an
    # interactive OAuth flow; if the user cannot complete it (no browser, or
    # the deadline elapses) the command exits nonzero. The config entry is
    # still persisted, so treat OAuth failure as a soft warning instead of
    # letting `set -e` abort the rest of the sync.
    local oauth_timeout="${AI_SKILLS_MCP_OAUTH_TIMEOUT_SEC:-30}"
    if run_with_timeout "$oauth_timeout" codex mcp add "$name" --url "$url"; then
        info "codex mcp: added $name"
    elif codex_has_mcp "$name"; then
        warn "codex mcp: $name added but auth incomplete — finish login later"
    else
        warn "codex mcp: failed to add $name"
    fi
}

ensure_codex_paperclip_mcp() {
    local expected_url="https://paperclip.gxl.ai/mcp"
    local details

    if codex_has_mcp paperclip; then
        details="$(codex mcp get paperclip 2>/dev/null || true)"
        if grep -Fq "transport: streamable_http" <<<"$details" &&
            grep -Fq "url: $expected_url" <<<"$details"; then
            info "codex mcp: paperclip already configured"
            return
        fi
        codex mcp remove paperclip
        info "codex mcp: removed outdated paperclip entry"
    fi

    ensure_codex_http_mcp paperclip "$expected_url"
}

ensure_codex_screenpipe_mcp() {
    local expected_args="args: --offline -y screenpipe-mcp"
    local details

    if codex_has_mcp screenpipe; then
        details="$(codex mcp get screenpipe 2>/dev/null || true)"
        if grep -Fq "transport: stdio" <<<"$details" &&
            grep -Fq "command: npx" <<<"$details" &&
            grep -Fq -- "$expected_args" <<<"$details"; then
            info "codex mcp: screenpipe already configured for offline startup"
            return
        fi
        codex mcp remove screenpipe
        info "codex mcp: removed outdated screenpipe entry"
    fi

    codex mcp add screenpipe -- npx --offline -y screenpipe-mcp
    info "codex mcp: added screenpipe with offline npm startup"
}

find_local_touchdesigner_mcp_cli() {
    local stable_cli="$HOME/programs/touchdesigner-mcp-server-runtime/node_modules/touchdesigner-mcp-server/dist/cli.js"
    if [ -f "$stable_cli" ]; then
        printf '%s\n' "$stable_cli"
        return
    fi
    find "$HOME/.npm/_npx" \
        -path '*/node_modules/touchdesigner-mcp-server/dist/cli.js' \
        -type f -print -quit 2>/dev/null || true
}

ensure_codex_touchdesigner_mcp() {
    local cached_cli details
    cached_cli="$(find_local_touchdesigner_mcp_cli)"

    # Prefer the stable local 2.0.0 runtime (falling back to npm's cache).
    # `npx ...@latest` consults the registry on every startup and can block an
    # otherwise local MCP session.
    if [ -n "$cached_cli" ] && have_cmd node; then
        if codex_has_mcp touchdesigner; then
            details="$(codex mcp get touchdesigner 2>/dev/null || true)"
            if grep -Fq "command: node" <<<"$details" &&
                grep -Fq "args: $cached_cli --stdio" <<<"$details"; then
                info "codex mcp: touchdesigner already configured for local startup"
                return
            fi
            codex mcp remove touchdesigner
            info "codex mcp: removed network-dependent touchdesigner entry"
        fi
        codex mcp add touchdesigner -- node "$cached_cli" --stdio
        info "codex mcp: added touchdesigner from local npm cache"
        return
    fi

    ensure_codex_stdio_mcp touchdesigner npx -y touchdesigner-mcp-server@2.0.0 --stdio
}

ensure_codex_design_suite_mcp() {
    local blender_server="$HOME/programs/blender-mcp-official/.venv/bin/blender-mcp"
    local autocad_python="$HOME/programs/autocad-mcp/.venv/bin/python"

    # Blender Foundation Lab MCP. The official Blender extension is configured
    # on 9877 so it can coexist with the older community addon on 9876 during
    # migration. The server reads these connection details from its env.
    if [ -x "$blender_server" ]; then
        if codex_has_mcp blender; then
            info "codex mcp: blender already configured"
        else
            codex mcp add blender \
                --env BLENDER_MCP_HOST=127.0.0.1 \
                --env BLENDER_MCP_PORT=9877 \
                -- "$blender_server"
            info "codex mcp: added blender (official Blender Lab MCP)"
        fi
    else
        warn "codex mcp: official Blender Lab server not installed; skipping blender"
    fi

    # TouchDesigner bridge (8beeeaaat/touchdesigner-mcp). The stdio server
    # connects lazily to mcp_webserver_base.tox on http://127.0.0.1:9981.
    ensure_codex_touchdesigner_mcp

    # AutoCAD live automation backends are Windows-only. On macOS, pin the
    # puran-water server to ezdxf for real DXF file creation/editing.
    if [ -x "$autocad_python" ]; then
        if codex_has_mcp autocad; then
            info "codex mcp: autocad already configured"
        else
            codex mcp add autocad \
                --env AUTOCAD_MCP_BACKEND=ezdxf \
                -- "$autocad_python" -m autocad_mcp
            info "codex mcp: added autocad (ezdxf backend)"
        fi
    else
        warn "codex mcp: autocad-mcp environment not installed; skipping autocad"
    fi

    # dcc-mcp-maya embeds a Streamable HTTP MCP server in Maya. The endpoint
    # is reachable only while Maya is running with its managed plugin loaded.
    ensure_codex_http_mcp maya http://127.0.0.1:9765/mcp

    # CoplayDev MCP for Unity. Start the local HTTP server from
    # Window > MCP for Unity after installing the editor package.
    ensure_codex_http_mcp unityMCP http://127.0.0.1:8080/mcp
}

remove_codex_mcp_if_present() {
    local name="$1"
    if codex_has_mcp "$name"; then
        codex mcp remove "$name"
        info "codex mcp: removed $name"
    fi
}

apply_codex_mcp_defaults() {
	local config="$HOME/.codex/config.toml"
	[ -f "$config" ] || return

	python3 - "$config" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
if text.strip():
    tomllib.loads(text)

lines = text.splitlines()


def section_bounds(section: str):
    header = f"[{section}]"
    start = None
    for index, line in enumerate(lines):
        if line.strip() == header:
            start = index
            break
    if start is None:
        return None, None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            end = index
            break
    return start, end


def set_key(section: str, key: str, value: str) -> None:
    start, end = section_bounds(section)
    if start is None:
        return

    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for index in range(start + 1, end):
        if pattern.match(lines[index]):
            lines[index] = f"{key} = {value}"
            return

    lines.insert(end, f"{key} = {value}")


for section in (
    "mcp_servers.codex-cli",
    "mcp_servers.1password",
    "mcp_servers.mobile-mcp",
):
    set_key(section, "enabled", "false")

for section in (
    "mcp_servers.paperclip",
    "mcp_servers.screenpipe",
    "mcp_servers.blender",
    "mcp_servers.touchdesigner",
    "mcp_servers.autocad",
    "mcp_servers.maya",
    "mcp_servers.unityMCP",
):
    set_key(section, "enabled", "true")

set_key("mcp_servers.screenpipe", "startup_timeout_sec", "60.0")
set_key("mcp_servers.paperclip", "startup_timeout_sec", "120.0")

# DCC/CAD tools can execute code or mutate open scenes. Keep them available,
# but require an explicit approval before each tool call.
for section in (
    "mcp_servers.blender",
    "mcp_servers.touchdesigner",
    "mcp_servers.autocad",
    "mcp_servers.maya",
    "mcp_servers.unityMCP",
):
    set_key(section, "default_tools_approval_mode", '"prompt"')
    set_key(section, "startup_timeout_sec", "60.0")
    set_key(section, "tool_timeout_sec", "180.0")

updated = "\n".join(lines).rstrip() + "\n"
tomllib.loads(updated)
path.write_text(updated, encoding="utf-8")
PY
	info "codex mcp: applied default enabled/disabled policy"
}

# Uizze credentials stay in the local Codex config and are never synchronized.
ensure_codex_uizze_mcp() {
    python3 - <<'UIZZE_PY'
from pathlib import Path
import re
p = Path.home() / ".codex/config.toml"
s = p.read_text() if p.exists() else ""
if not re.search(r"(?m)^\[mcp_servers\.uizze\]$", s):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s + '\n[mcp_servers.uizze]\nurl = "https://uizze.com/mcp"\n')
print("Uizze endpoint configured; local credentials preserved")
UIZZE_PY
}

sync_codex_mcp() {
    if ! have_cmd codex; then
        warn "codex CLI not found; skipping Codex MCP sync"
        return
    fi

    local codex_bin
    codex_bin="$(command -v codex)"
    ensure_codex_stdio_mcp codex "$codex_bin" mcp-server
    ensure_codex_stdio_mcp codex-cli npx -y codex-mcp-server
    ensure_codex_stdio_mcp mobile-mcp npx -y @mobilenext/mobile-mcp@latest
    ensure_codex_screenpipe_mcp
    ensure_codex_stdio_mcp 1password npx -y @jrejaud/op-mcp@1.0.0
    ensure_codex_paperclip_mcp
    # Match the protected-resource metadata's canonical US URL for OAuth.
    # Credentials stay in the client's local credential store, never this repo.
    ensure_codex_http_mcp elevenlabs https://api.us.elevenlabs.io/v1/mcp
    ensure_codex_design_suite_mcp
    ensure_codex_uizze_mcp
    remove_codex_mcp_if_present scg

    # raphel-loop is Cursor Agent-only. Remove older Codex registrations that
    # were created before the scope was narrowed.
    remove_codex_mcp_if_present raphel-loop

    # Playwright removed 2026-05-30: Albert no longer uses chrome-beta, and
    # codex's bundled chrome plugin + claude-in-chrome cover browser automation.
    remove_codex_mcp_if_present playwright

    remove_codex_mcp_if_present slack
    apply_codex_mcp_defaults
}

claude_has_mcp() {
    run_with_timeout 10 claude mcp get "$1" >/dev/null 2>&1
}

ensure_claude_stdio_mcp() {
    local name="$1"
    shift
    if claude_has_mcp "$name"; then
        info "claude mcp: $name already configured"
    else
        claude mcp add -s user "$name" -- "$@"
        info "claude mcp: added $name"
    fi
}

ensure_claude_http_mcp() {
    local name="$1" url="$2"
    if claude_has_mcp "$name"; then
        info "claude mcp: $name already configured"
    else
        claude mcp add -s user --transport http "$name" "$url"
        info "claude mcp: added $name"
    fi
}

ensure_claude_touchdesigner_mcp() {
    local cached_cli details
    cached_cli="$(find_local_touchdesigner_mcp_cli)"

    if [ -n "$cached_cli" ] && have_cmd node; then
        if claude_has_mcp touchdesigner; then
            details="$(claude mcp get touchdesigner 2>/dev/null || true)"
            if grep -Fq "Command: node" <<<"$details" &&
                grep -Fq "Args: $cached_cli --stdio" <<<"$details"; then
                info "claude mcp: touchdesigner already configured for local startup"
                return
            fi
            claude mcp remove touchdesigner
            info "claude mcp: removed network-dependent touchdesigner entry"
        fi
        claude mcp add -s user touchdesigner -- node "$cached_cli" --stdio
        info "claude mcp: added touchdesigner from local npm cache"
        return
    fi

    ensure_claude_stdio_mcp touchdesigner npx -y touchdesigner-mcp-server@2.0.0 --stdio
}

ensure_claude_paperclip_mcp() {
    local expected_args="Args: -y mcp-remote https://paperclip.gxl.ai/mcp"
    local details

    if claude_has_mcp paperclip; then
        details="$(claude mcp get paperclip 2>/dev/null || true)"
        if grep -Fq "Type: stdio" <<<"$details" &&
            grep -Fq "Command: npx" <<<"$details" &&
            grep -Fq -- "$expected_args" <<<"$details"; then
            info "claude mcp: paperclip already configured"
            return
        fi
        claude mcp remove paperclip
        info "claude mcp: removed outdated paperclip entry"
    fi

    if claude mcp add -s user paperclip -- npx -y mcp-remote https://paperclip.gxl.ai/mcp; then
        info "claude mcp: added paperclip via mcp-remote"
    elif run_with_timeout 10 claude mcp list 2>/dev/null | grep -Fq "paperclip"; then
        info "claude mcp: paperclip already configured"
    else
        warn "claude mcp: failed to add paperclip"
    fi
}

sync_claude_mcp() {
    if ! have_cmd claude; then
        warn "claude CLI not found; skipping Claude MCP sync"
        return
    fi

    local codex_bin
    codex_bin="$(command -v codex || true)"
    if [ -n "$codex_bin" ]; then
        ensure_claude_stdio_mcp codex "$codex_bin" mcp-server
    fi
    ensure_claude_stdio_mcp mobile-mcp npx -y @mobilenext/mobile-mcp@latest
    # Playwright removed 2026-05-30: redundant with claude-in-chrome (which
    # drives the real Chrome); it was spawning temp-profile automation windows.
    if claude_has_mcp playwright; then
        claude mcp remove playwright
        info "claude mcp: removed playwright"
    fi
    ensure_claude_stdio_mcp 1password npx -y @jrejaud/op-mcp@1.0.0
    # Blender MCP (ahujasid/blender-mcp): pairs with the BlenderMCP addon
    # installed inside Blender; tools only work while Blender's addon server
    # is running, but the stdio entry is safe to declare unconditionally.
    if have_cmd uvx; then
        ensure_claude_stdio_mcp blender uvx blender-mcp
    fi
    # Hyper3D Rodin official remote MCP (2026-09-17; endpoint from
    # DeemosTech/hyper3d-cli). OAuth per machine: run
    # `claude mcp login hyper3d` once. Generation spends Hyper3D credits.
    ensure_claude_http_mcp hyper3d https://api.hyper3d.com/api/mcp
    # Design-suite MCP bridges (2026-08-29): each server runs standalone and
    # connects lazily to its host app (TouchDesigner / Rhino / FreeCAD), so
    # declaring them is safe even before the host software is installed.
    ensure_claude_touchdesigner_mcp
    if have_cmd uvx; then
        # rhinomcp targets the mcp 1.x SDK and breaks on py3.13+/mcp 2.x —
        # pin both until upstream migrates.
        ensure_claude_stdio_mcp rhino uvx --python 3.12 --with "mcp<2" rhinomcp
        ensure_claude_stdio_mcp freecad uvx freecad-mcp
    fi
    # AutoCAD MCP (puran-water/autocad-mcp) with the cross-platform ezdxf
    # headless backend: generates/edits DXF files that open in AutoCAD.
    # Live-AutoCAD control backends are Windows-only, so macOS pins
    # AUTOCAD_MCP_BACKEND=ezdxf. Needs a local clone at
    # ~/programs/autocad-mcp with `uv sync` already run; skipped otherwise.
    if [ -x "$HOME/programs/autocad-mcp/.venv/bin/python" ]; then
        if claude_has_mcp autocad; then
            info "claude mcp: autocad already configured"
        else
            claude mcp add -s user autocad \
                --env AUTOCAD_MCP_BACKEND=ezdxf \
                -- "$HOME/programs/autocad-mcp/.venv/bin/python" -m autocad_mcp
            info "claude mcp: added autocad (ezdxf backend)"
        fi
    fi
    # Maya embeds a Streamable HTTP server at this loopback endpoint. It is
    # expected to be offline whenever Maya is not running.
    ensure_claude_http_mcp maya http://127.0.0.1:9765/mcp
    # Stata MCP (sepinetam/stata-mcp): drives licensed Stata via its console
    # CLI (tools: stata_do, get_data_info, help, read_log). StataNow/MP
    # install on this machine; symlink the CLI into ~/.local/bin (on PATH)
    # and point STATA_CLI at it. Skipped when Stata is not installed.
    local stata_cli="/Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp"
    if [ -x "$stata_cli" ] && have_cmd uvx; then
        mkdir -p "$HOME/.local/bin"
        ln -sf "$stata_cli" "$HOME/.local/bin/stata-mp"
        if claude_has_mcp stata; then
            info "claude mcp: stata already configured"
        else
            claude mcp add -s user stata \
                --env STATA_CLI="$HOME/.local/bin/stata-mp" \
                -- uvx stata-mcp
            info "claude mcp: added stata"
        fi
    fi
    # Zotero MCP (zotero-mcp on PyPI): reads the local Zotero 7 API at
    # http://localhost:23119 — tools work while Zotero is open. Pairs with
    # the citation workflow's connector-import convention.
    if have_cmd uvx; then
        if claude_has_mcp zotero; then
            info "claude mcp: zotero already configured"
        else
            claude mcp add -s user zotero --env ZOTERO_LOCAL=true -- uvx zotero-mcp
            info "claude mcp: added zotero"
        fi
    fi
    # Apple MCP (dhravya/apple-mcp): Notes/Reminders/Calendar/Contacts/
    # Messages/Mail/Maps via AppleScript; each app is gated by a macOS TCC
    # permission prompt on first use.
    if have_cmd bunx; then
        ensure_claude_stdio_mcp apple bunx apple-mcp
    fi
    # MCP for Unity (CoplayDev, official PyPI dist `mcpforunityserver`).
    # NOTE: the PyPI package `unity-mcp-server` is an unaffiliated fork
    # (points at github.com/mzbswh) — do not use it. Claude uses the stdio
    # transport here; Codex uses the in-Editor HTTP endpoint (see
    # sync_codex_mcp). Both need the com.coplaydev.unity-mcp UPM package in
    # the open Unity project and a running Editor bridge.
    # Claude connects over the SAME in-Editor HTTP endpoint as Codex. The
    # Unity side is pinned to HTTP transport (EditorConfigurationCache
    # SetUseHttpTransport(true) in UnityMcpConnectOnce.cs), so a stdio server
    # would find no Editor: stdio discovery needs Unity's TCP bridge, which
    # HTTP mode does not open. Verified 2026-09-07 via read_console.
    ensure_claude_http_mcp unity http://127.0.0.1:8080/mcp
    # raphel-loop is Cursor Agent-only. Remove older Claude registrations that
    # were created before the scope was narrowed. Use unconditional remove
    # because broken entries can appear in `claude mcp list` even when
    # `claude mcp get` cannot load them.
    run_with_timeout 10 claude mcp remove raphel-loop >/dev/null 2>&1 || true
    info "claude mcp: ensured raphel-loop absent"
    ensure_claude_paperclip_mcp
}

sync_cursor_mcp() {
    local cursor_mcp="$HOME/.cursor/mcp.json"
    local raphel_loop_mcp="$REPO_ROOT/scripts/raphel_loop_mcp.py"
    local python_bin
    python_bin="$(command -v python3)"

    mkdir -p "$(dirname "$cursor_mcp")"
    PYTHON_BIN="$python_bin" RAPHEL_LOOP_MCP="$raphel_loop_mcp" CURSOR_MCP="$cursor_mcp" python3 - <<'PY'
import json
import os
from pathlib import Path

path = Path(os.environ["CURSOR_MCP"])
if path.exists():
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
else:
    data = {}

servers = data.setdefault("mcpServers", {})
servers["raphel-loop"] = {
    "command": os.environ["PYTHON_BIN"],
    "args": [os.environ["RAPHEL_LOOP_MCP"]],
    "timeout": 60,
    "autoApprove": ["raphel_loop_checkpoint"],
}

tmp = path.with_suffix(path.suffix + ".tmp")
with tmp.open("w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2, sort_keys=False)
    handle.write("\n")
tmp.replace(path)
PY
    info "cursor mcp: refreshed raphel-loop in $cursor_mcp"
}

sync_mcp() {
    sync_codex_mcp
    sync_claude_mcp
    sync_cursor_mcp
}

install_managed_launchers() {
    local source="$REPO_ROOT/scripts/dendron-daily-sync.sh"
    local target="$HOME/.local/bin/dendron-daily-sync.sh"

    if [ -f "$source" ]; then
        mkdir -p "$(dirname "$target")"
        cp "$source" "$target"
        chmod +x "$target"
        info "launchers: installed $(basename "$target")"
    else
        warn "launchers: missing $source"
    fi
}

check_sync() {
    git -C "$REPO_ROOT" status --short --branch
    if have_cmd codex; then
        echo ""
        codex mcp list || true
    fi
    if have_cmd claude; then
        echo ""
        claude mcp list || true
    fi
    if [ -f "$HOME/.cursor/mcp.json" ]; then
        echo ""
        python3 - <<'PY'
import json
from pathlib import Path

path = Path.home() / ".cursor" / "mcp.json"
data = json.loads(path.read_text(encoding="utf-8"))
server = data.get("mcpServers", {}).get("raphel-loop")
if server:
    print(f"cursor raphel-loop: {server.get('command')} {' '.join(server.get('args', []))}")
else:
    print("cursor raphel-loop: not configured")
PY
    fi
}

case "$MODE" in
    apply)
        sync_skills
        cleanup_legacy_skill_aliases
        sync_external_skills
        # sync_mcp must run before apply_codex_settings: the latter layers
        # enabled_tools onto MCP sections that the former creates with the
        # required transport. Reversed order can leave a half-formed
        # [mcp_servers.1password] section with no transport, which makes the
        # codex CLI refuse to load any config.
        sync_mcp
        install_managed_launchers
        install_codex_pywal_theme
        apply_codex_settings
        ;;
    pull)
        git -C "$REPO_ROOT" pull --ff-only
        "$0" apply
        ;;
    skills)
        sync_skills
        cleanup_legacy_skill_aliases
        sync_external_skills
        ;;
    settings)
        install_managed_launchers
        install_codex_pywal_theme
        apply_codex_settings
        ;;
    mcp)
        sync_mcp
        ;;
    check)
        check_sync
        ;;
    *)
        cat <<USAGE
Usage: $0 [apply|pull|skills|settings|mcp|check]

  apply     Sync skills, safe settings, and local MCP entries.
  pull      Fast-forward this repo, then run apply.
  skills    Deploy skills only.
  settings  Apply safe local settings only.
  mcp       Ensure local MCP entries only.
  check     Show repo and MCP status.
USAGE
        exit 2
        ;;
esac
