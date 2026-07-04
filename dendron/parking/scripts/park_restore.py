#!/usr/bin/env python3
"""park_restore.py — match a topic query against parked convos or the FTS5 index,
then spawn an iTerm tab running the resume command in YOLO mode."""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

from rapidfuzz import fuzz, process

VAULT = Path("/Users/A.Y/Documents/Manual Library/Dendron/notes")
PARKED_TABLE = VAULT / "tool.parked-convos.md"
DB_PATH = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron/memory/session_index.db"
)
SESSION_INDEX = Path(
    "~/programs/ai-skills/dendron/command-center/scripts/session_index.py"
).expanduser()
SPAWNER = Path(__file__).parent / "spawn_iterm.applescript"
STALE_SECS = 24 * 60 * 60  # 24h


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", help="Topic phrase to match (free text)")
    ap.add_argument("--safe", action="store_true",
                    help="Drop YOLO flag; resume with normal permission prompts")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print resolved candidate(s); don't spawn tab")
    args = ap.parse_args()
    hits = match_table(args.query)
    if not hits:
        ensure_fresh_index()
        hits = match_fts(args.query)
    if not hits:
        print(f"No parked or indexed session matches '{args.query}'", file=sys.stderr)
        return 2
    if len(hits) > 1:
        print(json.dumps({"action": "disambiguate", "candidates": hits[:5]}, indent=2))
        return 4
    chosen = hits[0]
    if args.dry_run:
        print(json.dumps(chosen, indent=2))
        return 0
    spawn(chosen, safe=args.safe)
    print(f"Spawned: {chosen['slug']} ({chosen['source']} {chosen['session_id']})")
    return 0


# ---------------------------------------------------------------------------
# Table matching (rapidfuzz against parked-convos)
# ---------------------------------------------------------------------------

ROW_RE = re.compile(
    r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(claude|codex)\s*\|\s*([^|]+?)\s*\|"
    r"\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$"
)


def parse_table() -> list[dict]:
    if not PARKED_TABLE.exists():
        return []
    rows: list[dict] = []
    for line in PARKED_TABLE.read_text().splitlines():
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        date, source, topic, sid, resume, status, notes = m.groups()
        rows.append({
            "date": date,
            "source": source,
            "slug": topic.strip(),
            "session_id": sid,
            "resume_cmd": resume,
            "status": status.strip(),
            "notes": notes.strip(),
            "cwd": None,
            "match_score": 0,
            "via": "table",
        })
    return rows


def match_table(query: str, *, threshold: int = 70) -> list[dict]:
    rows = parse_table()
    if not rows:
        return []
    topics = {i: r["slug"] for i, r in enumerate(rows)}
    # process.extract returns list of (match_string, score, key) tuples.
    # WRatio is used instead of token_set_ratio because it incorporates
    # partial_ratio, making "parking" correctly match "parking-system"
    # (token_set_ratio scores that pair at 66.7 due to length-ratio penalty;
    # WRatio uses the partial substring match and scores it at 90).
    matches = process.extract(query, topics, scorer=fuzz.WRatio, limit=5)
    out: list[dict] = []
    for _, score, idx in matches:
        if score < threshold:
            continue
        r = rows[idx].copy()
        r["match_score"] = score
        if r["cwd"] is None:
            r["cwd"] = lookup_cwd(r["session_id"])
        out.append(r)
    return out


def lookup_cwd(session_id: str) -> str:
    """Look up cwd from session_index.db; fallback to vault root."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT cwd FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        if row and row[0]:
            return row[0]
    except sqlite3.Error:
        pass
    return str(VAULT)


# ---------------------------------------------------------------------------
# FTS5 fallback
# ---------------------------------------------------------------------------

def ensure_fresh_index() -> None:
    """If DB is older than 24h (or missing), run an incremental update before FTS."""
    if not DB_PATH.exists():
        rebuild = True
    else:
        rebuild = (time.time() - DB_PATH.stat().st_mtime) > STALE_SECS
    if rebuild:
        subprocess.run(
            ["python3", str(SESSION_INDEX), "--incremental", "--source", "both"],
            check=False,
            timeout=120,
            capture_output=True,
        )


def match_fts(query: str, *, limit: int = 5) -> list[dict]:
    if not DB_PATH.exists():
        return []
    terms = " OR ".join(re.findall(r"\w+", query))
    if not terms:
        return []
    sql = """
        SELECT s.session_id, s.source, s.cwd, s.last_ts, t.content
        FROM turns t
        JOIN turns_fts f ON f.rowid = t.id
        JOIN sessions s ON s.session_id = t.session_id
        WHERE turns_fts MATCH ?
          AND t.is_user_typed = 1
        GROUP BY s.session_id
        ORDER BY s.last_ts DESC
        LIMIT ?
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            rows = conn.execute(sql, (terms, limit)).fetchall()
    except sqlite3.Error:
        return []
    out: list[dict] = []
    for session_id, source, cwd, last_ts, excerpt in rows:
        out.append({
            "date": last_ts[:10] if last_ts else "",
            "source": source,
            "slug": f"(unparked) {excerpt[:60]}",
            "session_id": session_id,
            "resume_cmd": build_resume(source, session_id),
            "status": "unparked",
            "notes": (excerpt or "")[:200],
            "cwd": cwd or str(VAULT),
            "match_score": 0,
            "via": "fts",
        })
    return out


def build_resume(source: str, session_id: str) -> str:
    if source == "claude":
        return f"claude -r {session_id} --dangerously-skip-permissions"
    return f"codex resume {session_id} --dangerously-bypass-approvals-and-sandbox"


# ---------------------------------------------------------------------------
# Spawn (Task 6 will implement)
# ---------------------------------------------------------------------------

def spawn(chosen: dict, *, safe: bool = False) -> None:
    """Spawn an iTerm tab running the resume command.

    If safe=True, strips the YOLO flags (--dangerously-skip-permissions,
    --dangerously-bypass-approvals-and-sandbox) so the resumed session
    will respect permission prompts.
    """
    cmd = chosen["resume_cmd"]
    if safe:
        cmd = cmd.replace(" --dangerously-skip-permissions", "")
        cmd = cmd.replace(" --dangerously-bypass-approvals-and-sandbox", "")
    cwd = chosen["cwd"] or str(VAULT)
    title = chosen["slug"][:30]
    subprocess.run(
        ["osascript", str(SPAWNER), cwd, title, cmd],
        check=True,
        timeout=10,
    )


if __name__ == "__main__":
    sys.exit(main())
