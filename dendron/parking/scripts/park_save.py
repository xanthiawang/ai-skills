#!/usr/bin/env python3
"""park_save.py — write a row to tool.parked-convos.md.

Resolves the live session ID (Claude) or greps recent Codex sessions
by topic, verifies the jsonl, and appends a row.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

VAULT = Path("/Users/A.Y/Documents/Manual Library/Dendron/notes")
PARKED_TABLE = VAULT / "tool.parked-convos.md"
MEMORY_DIR = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron/memory"
)
CLAUDE_PROJECTS = Path("/Users/A.Y/.claude/projects")
CODEX_SESSIONS = Path("/Users/A.Y/.codex/sessions")
SESSION_INDEX = Path(
    "~/programs/ai-skills/dendron/command-center/scripts/session_index.py"
).expanduser()

EXPECTED_HEADER = (
    "| Date | Source | Topic | Session ID | Resume Command | Status | Notes |"
)


def assert_table_ready() -> None:
    """Fail fast if tool.parked-convos.md is missing or has the wrong schema.

    The Task 8 migration renames tool.claude-parked-convos.md and adds the
    Source + Session ID columns. Without that, park_save would either crash
    at append_row (file missing, FileNotFoundError with no hint) or silently
    corrupt a 5-column table by inserting a 7-column row.
    """
    if not PARKED_TABLE.exists():
        raise RuntimeError(
            f"Parked table not found at {PARKED_TABLE}. "
            "The Task 8 migration must run first "
            "(rename tool.claude-parked-convos.md -> tool.parked-convos.md "
            "+ add Source + Session ID columns)."
        )
    text = PARKED_TABLE.read_text()
    if EXPECTED_HEADER not in text:
        raise RuntimeError(
            f"{PARKED_TABLE} exists but does not have the expected 7-column header. "
            f"Expected: {EXPECTED_HEADER}"
        )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Append a parked-conversation row to tool.parked-convos.md."
    )
    ap.add_argument("--source", choices=["claude", "codex"], default="claude")
    ap.add_argument("--slug", required=True, help="Short topic slug (kebab-case)")
    ap.add_argument("--notes", default="", help="Free-text notes for the row")
    ap.add_argument(
        "--cwd-hint",
        default=None,
        help="For Codex: a path to bias session lookup; defaults to vault root",
    )
    args = ap.parse_args()
    if args.source == "claude":
        return park_claude(args)
    return park_codex(args)


# ---------------------------------------------------------------------------
# Claude flow
# ---------------------------------------------------------------------------

def park_claude(args) -> int:
    assert_table_ready()
    cwd = Path.cwd()
    enc = encode_cwd(cwd)
    project_dir = CLAUDE_PROJECTS / enc
    if not project_dir.exists():
        print(
            f"ERROR: no Claude project dir for cwd={cwd} (looked for {project_dir})",
            file=sys.stderr,
        )
        return 2
    jsonls = sorted(
        project_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not jsonls:
        print(f"ERROR: no jsonl files in {project_dir}", file=sys.stderr)
        return 2
    newest = jsonls[0]
    age = time.time() - newest.stat().st_mtime
    if age > 60:
        print(
            f"ERROR: newest jsonl {newest.name} is {age:.0f}s stale — likely not the live "
            "session. Refusing to park to avoid wrong session ID.",
            file=sys.stderr,
        )
        return 3
    session_id = newest.stem
    row = build_row("claude", args.slug, session_id, args.notes)
    append_row(row)
    write_project_memory(args.slug, args.notes, source="claude", session_id=session_id)
    incremental_index(newest)
    print(row)
    return 0


def encode_cwd(p: Path) -> str:
    """Mirror Claude's directory-name encoding.

    Claude turns each path component separator and special char into a hyphen.
    The resulting directory name starts with '-' because the path starts with '/'.
    Example: /Users/A.Y/Documents/Manual Library/Dendron/notes
             -> -Users-A-Y-Documents-Manual-Library-Dendron-notes
    """
    return str(p).replace("/", "-").replace(" ", "-").replace(".", "-")


# ---------------------------------------------------------------------------
# Codex flow
# ---------------------------------------------------------------------------

def park_codex(args) -> int:
    assert_table_ready()
    query = args.slug.replace("-", " ")
    candidates = grep_codex_sessions(query, limit=5)
    if not candidates:
        print(f"ERROR: no Codex session matching '{query}'", file=sys.stderr)
        return 2
    if len(candidates) == 1:
        chosen = candidates[0]
    else:
        # Emit JSON for the agent to disambiguate with Albert.
        print(json.dumps({"action": "disambiguate", "candidates": candidates}, indent=2))
        return 4
    session_id = chosen["session_id"]
    row = build_row("codex", args.slug, session_id, args.notes)
    append_row(row)
    write_project_memory(args.slug, args.notes, source="codex", session_id=session_id)
    incremental_index(Path(chosen["file_path"]))
    print(row)
    return 0


def grep_codex_sessions(query: str, *, limit: int = 5) -> list[dict]:
    """Find recent Codex rollouts that mention `query` in their first 200 turns.

    Returns a list of dicts:
      {session_id, file_path, mtime, excerpt}
    sorted by mtime descending. Up to `limit` entries.
    """
    pat = re.compile(re.escape(query), re.IGNORECASE)
    rollouts = sorted(
        CODEX_SESSIONS.rglob("rollout-*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    hits: list[dict] = []
    # Only scan the 200 most recent rollouts to keep parking fast.
    for jsonl in rollouts[:200]:
        first_match: str | None = None
        session_id_from_meta: str | None = None
        try:
            with jsonl.open() as fh:
                for i, line in enumerate(fh):
                    if i >= 200:
                        break
                    try:
                        d = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    # Capture session_id from session_meta if encountered.
                    if isinstance(d, dict):
                        if d.get("type") == "session_meta":
                            meta_payload = d.get("payload", {})
                            if isinstance(meta_payload, dict) and "id" in meta_payload:
                                session_id_from_meta = meta_payload["id"]
                    # Search the line text for the query.
                    payload = json.dumps(d) if isinstance(d, dict) else str(d)
                    if pat.search(payload):
                        first_match = payload[:160]
                        break
        except OSError:
            continue
        if first_match:
            # Prefer the session_id from session_meta if we found one;
            # otherwise fall back to filename UUID extraction.
            if session_id_from_meta:
                sid = session_id_from_meta
            else:
                stem = jsonl.stem
                parts = stem.split("-")
                # rollout-YYYY-MM-DDThh-mm-ss-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
                # Last 5 dash-separated tokens form the UUID.
                if len(parts) >= 5:
                    sid = "-".join(parts[-5:])
                else:
                    continue
            hits.append({
                "session_id": sid,
                "file_path": str(jsonl),
                "mtime": jsonl.stat().st_mtime,
                "excerpt": first_match,
            })
            if len(hits) >= limit:
                break
    return hits


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def build_row(source: str, slug: str, session_id: str, notes: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    if source == "claude":
        resume = f"claude -r {session_id} --dangerously-skip-permissions"
    else:
        resume = f"codex resume {session_id} --dangerously-bypass-approvals-and-sandbox"
    notes_clean = notes.replace("|", "\\|").replace("\n", " ").strip() or "—"
    return (
        f"| {today} | {source} | {slug} | `{session_id}` "
        f"| `{resume}` | parked | {notes_clean} |"
    )


def append_row(row: str) -> None:
    """Insert row right under the separator line after the `## Active` heading."""
    text = PARKED_TABLE.read_text()
    marker = "## Active"
    if marker not in text:
        raise RuntimeError(f"'{marker}' heading not found in {PARKED_TABLE}")
    lines = text.splitlines()
    active_idx = next(i for i, l in enumerate(lines) if l.strip() == marker)
    sep_idx = next(
        i
        for i in range(active_idx, len(lines))
        if re.match(r"\|\s*[-:|]+\s*\|", lines[i])
    )
    lines.insert(sep_idx + 1, row)
    PARKED_TABLE.write_text("\n".join(lines) + "\n")


def write_project_memory(
    slug: str, notes: str, *, source: str, session_id: str
) -> None:
    """Create or extend memory/project_<slug>.md atomically.

    Single write_text call: no torn-write data-loss window. Two branches:
      - new file: write header + body + park note in one shot
      - existing file: prepend header if missing, then append the park note,
        and write the assembled content once
    """
    path = MEMORY_DIR / f"project_{slug}.md"
    today = datetime.now().strftime("%Y-%m-%d")
    header = (
        f"---\nname: project_{slug}\n"
        f"description: Parked context for {slug} ({source} session {session_id})\n"
        f"type: project\n---\n\n"
    )
    park_note = f"\n## Park note {today}\n\n{notes.strip() or '_(no notes)_'}\n"
    if path.exists():
        existing = path.read_text()
        # Prepend header only if the name: line isn't already present
        if header.split("\n")[1] not in existing:
            content = header + existing
        else:
            content = existing
        content += park_note
        path.write_text(content)
    else:
        path.write_text(
            header
            + f"# project_{slug}\n\n"
            + f"**Parked:** {today} ({source} session `{session_id}`)\n\n"
            + f"## Notes\n\n{notes.strip() or '_(no notes)_'}\n"
        )


def incremental_index(jsonl: Path) -> None:
    """Best-effort: keep the FTS5 DB current for this newly parked session."""
    try:
        subprocess.run(
            ["python3", str(SESSION_INDEX), "--incremental", "--source", "both"],
            check=False,
            timeout=20,
            capture_output=True,
        )
    except Exception:
        pass  # never block park on index refresh


if __name__ == "__main__":
    sys.exit(main())
