#!/usr/bin/env python3
"""park_audit.py — health check for tool.parked-convos.md.

Emits a markdown report of:
  1. Session IDs appearing on multiple distinct rows (data drift).
  2. Rows whose session jsonl no longer exists on disk.
  3. Rows older than 60 days still flagged active/parked.
  4. Rows whose declared source doesn't match the session ID format.
"""
from __future__ import annotations

import re
import sys
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

VAULT = Path("/Users/A.Y/Documents/Manual Library/Dendron/notes")
PARKED_TABLE = VAULT / "tool.parked-convos.md"
CLAUDE_PROJECTS = Path("/Users/A.Y/.claude/projects")
CODEX_SESSIONS = Path("/Users/A.Y/.codex/sessions")

ROW_RE = re.compile(
    r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(claude|codex)\s*\|\s*([^|]+?)\s*\|"
    r"\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$"
)


def parse_rows() -> list[dict]:
    if not PARKED_TABLE.exists():
        return []
    rows: list[dict] = []
    for line in PARKED_TABLE.read_text().splitlines():
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        d, source, slug, sid, _, status, notes = m.groups()
        rows.append({
            "date": d,
            "source": source,
            "slug": slug.strip(),
            "session_id": sid,
            "status": status.strip(),
            "notes": notes.strip(),
        })
    return rows


def find_jsonl(source: str, session_id: str) -> Path | None:
    if source == "claude":
        for jsonl in CLAUDE_PROJECTS.rglob(f"{session_id}.jsonl"):
            return jsonl
        return None
    # Codex: filename ends with -<UUID>.jsonl
    for jsonl in CODEX_SESSIONS.rglob(f"*-{session_id}.jsonl"):
        return jsonl
    return None


def uuid_version(s: str) -> int | None:
    try:
        return uuid.UUID(s).version
    except (ValueError, TypeError):
        return None


def main() -> int:
    rows = parse_rows()
    if not rows:
        print("No parked rows found.")
        return 0
    by_sid: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        # Archived rows are exempt from the duplicate-session-ID check — they
        # deliberately preserve history including the original shared session.
        if r["status"].lower() == "archived":
            continue
        by_sid[r["session_id"]].append(r)
    dupes = {sid: rs for sid, rs in by_sid.items() if len(rs) > 1}
    missing = [(r, find_jsonl(r["source"], r["session_id"])) for r in rows]
    missing = [r for r, p in missing if p is None]
    cutoff = date.today() - timedelta(days=60)
    stale = [
        r for r in rows
        if r["status"].lower() in {"active", "parked"}
        and datetime.strptime(r["date"], "%Y-%m-%d").date() < cutoff
    ]
    source_mismatch = []
    for r in rows:
        v = uuid_version(r["session_id"])
        if v is None:
            continue
        if r["source"] == "codex" and v not in {7, 4}:
            # Codex uses UUIDv7; tolerate v4 in older entries
            source_mismatch.append(r)
    # Emit markdown report
    out: list[str] = ["# Park audit report", ""]
    out.append(f"_Generated {datetime.now():%Y-%m-%d %H:%M}_")
    out.append("")
    out.append(f"- Rows scanned: {len(rows)}")
    out.append(f"- Duplicate session IDs: {len(dupes)}")
    out.append(f"- Missing jsonls: {len(missing)}")
    out.append(f"- Stale active rows (>60d): {len(stale)}")
    out.append(f"- Source-format mismatches: {len(source_mismatch)}")
    out.append("")
    if dupes:
        out.append("## Duplicate session IDs")
        for sid, rs in dupes.items():
            out.append(f"\n### `{sid}` — {len(rs)} rows")
            for r in rs:
                out.append(f"- {r['date']} | {r['slug']} | {r['notes'][:80]}")
    if missing:
        out.append("\n## Missing jsonls")
        for r in missing:
            out.append(f"- {r['date']} | {r['source']} | {r['slug']} | `{r['session_id']}`")
    if stale:
        out.append("\n## Stale active rows (>60d)")
        for r in stale:
            out.append(f"- {r['date']} | {r['slug']} | status: {r['status']}")
    if source_mismatch:
        out.append("\n## Source-format mismatches")
        for r in source_mismatch:
            out.append(
                f"- {r['date']} | declared `{r['source']}` | UUID v{uuid_version(r['session_id'])} "
                f"| {r['slug']}"
            )
    print("\n".join(out))
    return 0 if not (dupes or missing or stale or source_mismatch) else 1


if __name__ == "__main__":
    sys.exit(main())
