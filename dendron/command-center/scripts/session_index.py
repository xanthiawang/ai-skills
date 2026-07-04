#!/usr/bin/env python3
"""
FTS5 SQLite index over Claude Code and Codex session jsonl transcripts.

Borrowed from Hermes-Agent's SessionDB pattern. Replaces ad-hoc grep over
~/.claude/projects/.../*.jsonl with a fast full-text search that lets future
sessions recall decisions, drafts, and threads from prior conversations.

Usage:
    session_index.py build          # full reindex (drops existing table)
    session_index.py update         # incremental since last indexed mtime
    session_index.py search "query" # FTS5 match, returns session_id + snippet
    session_index.py session <id>   # dump indexed turns for one session
    session_index.py stats          # row counts, byte size, last update

Schema:
    sessions(session_id, file_path, first_ts, last_ts, n_turns, byte_size,
             indexed_at, source, cwd)
    turns(session_id, turn_idx, role, ts, content, is_user_typed)
    turns_fts(content) — FTS5 virtual table mirroring turns.content
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron-notes"
)
DB_PATH = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron/memory/session_index.db"
)
CODEX_SESSIONS_DIR = Path("/Users/A.Y/.codex/sessions")

# ---------------------------------------------------------------------------
# Noise filter — patterns anchored at start of (lstripped) content
# ---------------------------------------------------------------------------
_NOISE_PATTERNS = [
    r"^Base directory for this skill",
    r"^Based on these (recent user|Codex user)",
    r"^<command-name>",
    r"^<system-reminder>",
    r"^<local-command-stdout>",
    r"^<user-prompt-submit-hook>",
    r"^\[Request interrupted",
    r"^Caveat: The messages",
]
_NOISE_RE = re.compile("|".join(_NOISE_PATTERNS), re.IGNORECASE)


def is_user_typed(role: str, content: str) -> bool:
    """Return True iff content is a real human-typed user message."""
    if role != "user":
        return False
    if not content or not content.strip():
        return False
    s = content.lstrip()
    if _NOISE_RE.match(s):
        return False
    # Tool-result JSON payloads: list-of-dict with tool_use_id near start
    if s.startswith("[{") and "tool_use_id" in s[:120]:
        return False
    return True


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            file_path TEXT NOT NULL,
            first_ts TEXT,
            last_ts TEXT,
            n_turns INTEGER,
            byte_size INTEGER,
            indexed_at INTEGER,
            source TEXT NOT NULL DEFAULT 'claude',
            cwd TEXT
        );
        CREATE TABLE IF NOT EXISTS turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            turn_idx INTEGER,
            role TEXT,
            ts TEXT,
            content TEXT,
            is_user_typed INTEGER NOT NULL DEFAULT 0,
            UNIQUE(session_id, turn_idx)
        );
        CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id);
        CREATE INDEX IF NOT EXISTS idx_turns_user_typed ON turns(is_user_typed);
        CREATE INDEX IF NOT EXISTS idx_sessions_source ON sessions(source);
        CREATE VIRTUAL TABLE IF NOT EXISTS turns_fts USING fts5(
            content,
            content='turns',
            content_rowid='id',
            tokenize='porter unicode61'
        );
        CREATE TRIGGER IF NOT EXISTS turns_ai AFTER INSERT ON turns BEGIN
            INSERT INTO turns_fts(rowid, content) VALUES (new.id, new.content);
        END;
        CREATE TRIGGER IF NOT EXISTS turns_ad AFTER DELETE ON turns BEGIN
            INSERT INTO turns_fts(turns_fts, rowid, content) VALUES('delete', old.id, old.content);
        END;
    """)


# ---------------------------------------------------------------------------
# Claude jsonl parsing
# ---------------------------------------------------------------------------

def extract_text_claude(record: dict) -> tuple[str, str, str]:
    """(role, ts, text) — handle Claude Code jsonl record shapes."""
    role = record.get("type") or record.get("role") or ""
    ts = record.get("timestamp") or ""
    msg = record.get("message") or {}
    content = msg.get("content") if isinstance(msg, dict) else None

    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                tool = block.get("name", "")
                parts.append(f"[tool_use: {tool}]")
            elif block.get("type") == "tool_result":
                tr = block.get("content", "")
                if isinstance(tr, list):
                    tr = " ".join(
                        b.get("text", "") for b in tr if isinstance(b, dict)
                    )
                parts.append(f"[tool_result] {str(tr)[:500]}")
        text = "\n".join(p for p in parts if p)
    else:
        text = ""
    return role, ts, text


def iter_claude_sessions():
    """Yield (session_id, jsonl_path, cwd) for each Claude Code session."""
    for jsonl in sorted(PROJECT_DIR.glob("*.jsonl")):
        session_id = jsonl.stem
        cwd = None
        try:
            with jsonl.open() as fh:
                for line in fh:
                    try:
                        d = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(d, dict) and d.get("cwd"):
                        cwd = d["cwd"]
                        break
        except OSError:
            continue
        yield session_id, jsonl, cwd


def _index_file(
    conn: sqlite3.Connection,
    jsonl_path: Path,
    session_id: str,
    cwd: str | None,
    source: str,
    extractor,
) -> int:
    """Generic per-file indexer. `extractor(record) -> (role, ts, text)`.

    Returns turn count indexed.
    """
    conn.execute("DELETE FROM turns WHERE session_id=?", (session_id,))
    n = 0
    first_ts = last_ts = None
    with jsonl_path.open() as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            role, ts, text = extractor(rec)
            if not text:
                continue
            if first_ts is None and ts:
                first_ts = ts
            if ts:
                last_ts = ts
            typed = 1 if is_user_typed(role, text) else 0
            conn.execute(
                "INSERT OR IGNORE INTO turns"
                "(session_id, turn_idx, role, ts, content, is_user_typed) "
                "VALUES (?,?,?,?,?,?)",
                (session_id, idx, role, ts, text, typed),
            )
            n += 1
    conn.execute(
        "INSERT OR REPLACE INTO sessions"
        "(session_id, file_path, first_ts, last_ts, n_turns, byte_size,"
        " indexed_at, source, cwd) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (
            session_id,
            str(jsonl_path),
            first_ts,
            last_ts,
            n,
            jsonl_path.stat().st_size,
            int(time.time()),
            source,
            cwd,
        ),
    )
    return n


# ---------------------------------------------------------------------------
# Codex jsonl parsing
# ---------------------------------------------------------------------------

def extract_text_codex(record: dict) -> tuple[str, str, str]:
    """(role, ts, text) — handle Codex rollout jsonl record shapes.

    Codex records use type='response_item' with payload.role and
    payload.content[].text (type='input_text' for user, 'output_text' for
    assistant).
    """
    if record.get("type") != "response_item":
        return "", "", ""
    ts = record.get("timestamp") or ""
    payload = record.get("payload") or {}
    if not isinstance(payload, dict):
        return "", "", ""
    role = payload.get("role") or ""
    # Normalise: Codex uses 'developer' for system-level injections
    if role == "developer":
        role = "system"
    content = payload.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            # input_text (user) or output_text (assistant)
            t = block.get("text") or ""
            if t:
                parts.append(t)
        text = "\n".join(p for p in parts if p)
    else:
        text = ""
    return role, ts, text


def iter_codex_sessions():
    """Yield (session_id, jsonl_path, cwd) for each Codex rollout."""
    if not CODEX_SESSIONS_DIR.exists():
        return
    for jsonl in sorted(CODEX_SESSIONS_DIR.rglob("rollout-*.jsonl")):
        # Extract session_id and cwd from session_meta (first record)
        session_id = None
        cwd = None
        try:
            with jsonl.open() as fh:
                for line in fh:
                    try:
                        d = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(d, dict):
                        continue
                    if d.get("type") == "session_meta":
                        p = d.get("payload") or {}
                        if isinstance(p, dict):
                            session_id = p.get("id")
                            cwd = p.get("cwd")
                        break
        except OSError:
            continue
        # Fallback: derive session_id from filename UUID portion
        if not session_id:
            stem = jsonl.stem  # rollout-<ISO>-<UUID>
            # UUID is everything after the last '-' group that looks like UUID
            # Strategy: split on '-', rejoin last 5 segments (standard UUID)
            parts = stem.split("-")
            if len(parts) >= 5:
                session_id = "-".join(parts[-5:])
            else:
                session_id = stem
        yield session_id, jsonl, cwd


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

def _build_or_update(args, incremental: bool) -> int:
    conn = connect()
    init_schema(conn)

    if not incremental:
        conn.execute("DELETE FROM turns")
        conn.execute("DELETE FROM sessions")
        conn.execute("INSERT INTO turns_fts(turns_fts) VALUES('rebuild')")

    sources_to_walk: list[tuple[str, object, object]] = []
    source_arg = getattr(args, "source", "both")
    if source_arg in ("claude", "both"):
        sources_to_walk.append(("claude", iter_claude_sessions, extract_text_claude))
    if source_arg in ("codex", "both"):
        sources_to_walk.append(("codex", iter_codex_sessions, extract_text_codex))

    total = 0
    total_files = 0
    for source, walker, extractor in sources_to_walk:
        # Compute the per-source mtime cutoff ONCE before iteration; doing it
        # inside the inner loop would let each freshly-indexed file's
        # wall-clock indexed_at become the new MAX, causing every subsequent
        # existing file (mtime <= now) to be skipped.
        if incremental:
            latest = conn.execute(
                "SELECT MAX(indexed_at) FROM sessions WHERE source = ?",
                (source,),
            ).fetchone()[0] or 0
        else:
            latest = 0
        for session_id, jsonl_path, cwd in walker():
            if incremental and jsonl_path.stat().st_mtime <= latest:
                continue
            n = _index_file(conn, jsonl_path, session_id, cwd, source, extractor)
            total += n
            total_files += 1
            if n > 0:
                print(f"  [{source}] {jsonl_path.name}: {n} turns")
    conn.commit()
    conn.close()
    action = "Updated" if incremental else "Indexed"
    print(f"{action} {total} turns from {total_files} sessions → {DB_PATH}")
    return 0


def cmd_build(args) -> int:
    return _build_or_update(args, incremental=False)


def cmd_update(args) -> int:
    return _build_or_update(args, incremental=True)


def cmd_search(args) -> int:
    conn = connect()
    cur = conn.execute(
        """
        SELECT s.session_id, s.last_ts, s.source, t.turn_idx, t.role,
               snippet(turns_fts, 0, '«', '»', '…', 16) AS snip
        FROM turns_fts
        JOIN turns t ON turns_fts.rowid=t.id
        JOIN sessions s ON t.session_id=s.session_id
        WHERE turns_fts MATCH ?
        ORDER BY s.last_ts DESC
        LIMIT ?
        """,
        (args.query, args.limit),
    )
    for sid, last_ts, source, idx, role, snip in cur:
        print(f"\n[{last_ts or '?'}] {sid} ({source}) #{idx} ({role})")
        print(f"  {snip}")
    conn.close()
    return 0


def cmd_session(args) -> int:
    conn = connect()
    cur = conn.execute(
        "SELECT turn_idx, role, ts, content FROM turns WHERE session_id=? ORDER BY turn_idx",
        (args.session_id,),
    )
    for idx, role, ts, content in cur:
        print(f"--- #{idx} [{role}] {ts}")
        print(content[:1000])
    conn.close()
    return 0


def cmd_stats(_args) -> int:
    conn = connect()
    init_schema(conn)
    n_sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    n_turns = conn.execute("SELECT COUNT(*) FROM turns").fetchone()[0]
    last = conn.execute("SELECT MAX(indexed_at) FROM sessions").fetchone()[0]
    db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
    print(f"Sessions: {n_sessions}")
    print(f"Turns:    {n_turns}")
    print(f"Last idx: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last)) if last else 'never'}")
    print(f"DB size:  {db_size/1024:.1f} KB")
    print()
    # Per-source breakdown
    for src, cnt in conn.execute(
        "SELECT source, COUNT(*) FROM sessions GROUP BY source ORDER BY source"
    ):
        print(f"  Sessions [{src}]: {cnt}")
    print()
    # is_user_typed breakdown
    for typed, cnt in conn.execute(
        "SELECT is_user_typed, COUNT(*) FROM turns WHERE role='user' GROUP BY is_user_typed ORDER BY is_user_typed"
    ):
        label = "typed" if typed else "auto"
        print(f"  User turns [{label}]: {cnt}")
    conn.close()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument(
        "--source",
        choices=["claude", "codex", "both"],
        default="both",
        help="Which session source to walk (default: both)",
    )
    ap.add_argument(
        "--incremental",
        action="store_true",
        help="Only index sessions newer than the latest indexed_at (same as 'update' subcommand)",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    sub.add_parser("update")
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=20)
    s = sub.add_parser("session")
    s.add_argument("session_id")
    sub.add_parser("stats")
    args = ap.parse_args()

    # --incremental flag applies to build/update commands
    if args.incremental and args.cmd == "build":
        # override: build with incremental = update
        return cmd_update(args)

    return {
        "build": cmd_build,
        "update": cmd_update,
        "search": cmd_search,
        "session": cmd_session,
        "stats": cmd_stats,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
