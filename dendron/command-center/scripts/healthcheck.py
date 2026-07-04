#!/usr/bin/env python3
"""
Command-center operational healthcheck.

Checks freshness and hygiene for the Dendron command-center stack without
calling external APIs. It is designed to be safe at session start: read local
state, flag stale or missing pieces, and suggest the next local command.

Usage:
    healthcheck.py
    healthcheck.py --json
    healthcheck.py --quiet        # only show warnings/failures in markdown
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

VAULT_DIR = Path("/Users/A.Y/Documents/Manual Library/Dendron/notes")
MEMORY_DIR = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron/memory"
)
SESSION_DIR = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron-notes"
)
SESSION_DB = MEMORY_DIR / "session_index.db"
SKILL_SNAPSHOT = MEMORY_DIR / "skill-snapshot.json"

SYNC_THRESHOLDS_HOURS = {
    "calendar": 2,
    "email": 12,
    "screenpipe": 12,
    "wechat": 12,
    "superwhisper": 24,
}
SESSION_INDEX_WARN_HOURS = 6
SKILL_SNAPSHOT_WARN_HOURS = 48

SYNC_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|$")
SYNC_TIME_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})(?::\d{2})?\s*(?:UTC|Z)?"
)
JOURNAL_RE = re.compile(r"daily\.journal\.(\d{4})\.(\d{2})\.(\d{2})\.md$")
SCREENPIPE_RE = re.compile(r"cc-screenpipe-(\d{4})-(\d{2})-(\d{2})-\d+\.json$")


def check(name: str, severity: str, detail: str, next_action: str = "") -> dict:
    return {
        "name": name,
        "severity": severity,
        "detail": detail,
        "next_action": next_action,
    }


def parse_sync_datetime(value: str) -> datetime | None:
    match = SYNC_TIME_RE.search(value)
    if not match:
        return None
    dt = datetime.strptime(" ".join(match.groups()), "%Y-%m-%d %H:%M")
    return dt.replace(tzinfo=timezone.utc)


def parse_sync_status(text: str) -> list[dict]:
    rows: list[dict] = []
    in_sync = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## Sync Status"):
            in_sync = True
            continue
        if in_sync and line.startswith("## ") and not line.startswith("## Sync Status"):
            break
        if not in_sync or not line.startswith("|"):
            continue
        if "Source" in line and "Last sync" in line:
            continue
        if re.match(r"^\|\s*-+", line):
            continue
        match = SYNC_ROW_RE.match(line)
        if not match:
            continue
        source, last_sync, coverage = [part.strip() for part in match.groups()]
        rows.append(
            {
                "source": source,
                "last_sync": last_sync,
                "coverage": coverage,
                "last_sync_dt": parse_sync_datetime(last_sync),
            }
        )
    return rows


def check_sync_status(rows: list[dict], now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    checks: list[dict] = []
    if not rows:
        return [
            check(
                "sync.status",
                "fail",
                "No sync status table found in _working-memory.md.",
                "Run the sync pipeline, then refresh _working-memory.md.",
            )
        ]

    for row in rows:
        key = row["source"].strip().lower()
        name = f"sync.{key}"
        dt = row.get("last_sync_dt")
        if dt is None:
            checks.append(
                check(
                    name,
                    "warn",
                    f"Could not parse last sync time: {row['last_sync']}",
                    "Normalize the sync table timestamp to 'YYYY-MM-DD HH:MM UTC'.",
                )
            )
            continue
        age_h = (now - dt).total_seconds() / 3600
        threshold = SYNC_THRESHOLDS_HOURS.get(key, 24)
        severity = "ok" if age_h <= threshold else "warn"
        detail = f"{age_h:.1f}h old; coverage: {row['coverage']}"
        next_action = "" if severity == "ok" else f"Refresh {row['source']} sync."
        checks.append(check(name, severity, detail, next_action))
    return checks


def latest_file(paths: list[Path]) -> Path | None:
    existing = [p for p in paths if p.exists()]
    if not existing:
        return None
    return max(existing, key=lambda p: p.stat().st_mtime)


def check_working_memory(vault_dir: Path = VAULT_DIR, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    path = vault_dir / "_working-memory.md"
    if not path.exists():
        return [
            check(
                "working_memory.file",
                "fail",
                f"Missing {path}",
                "Rebuild _working-memory.md from the sync pipeline.",
            )
        ]
    text = path.read_text(errors="ignore")
    checks = [
        check(
            "working_memory.file",
            "ok",
            f"Found _working-memory.md ({path.stat().st_size} bytes).",
        )
    ]
    checks.extend(check_sync_status(parse_sync_status(text), now=now))
    return checks


def check_latest_daily_journal(vault_dir: Path = VAULT_DIR, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    journals = list(vault_dir.glob("daily.journal.*.md"))
    latest = latest_file(journals)
    if latest is None:
        return check(
            "daily_journal.latest",
            "warn",
            "No daily journal files found.",
            "Run daily journal generation after screenpipe sync.",
        )
    match = JOURNAL_RE.match(latest.name)
    if not match:
        return check("daily_journal.latest", "warn", f"Latest journal name is unusual: {latest.name}")
    journal_date = "-".join(match.groups())
    today = now.strftime("%Y-%m-%d")
    severity = "ok" if journal_date == today else "warn"
    next_action = "" if severity == "ok" else "Generate or refresh today's daily journal."
    return check(
        "daily_journal.latest",
        severity,
        f"Latest journal is {latest.name}.",
        next_action,
    )


def check_screenpipe_cache(vault_dir: Path = VAULT_DIR, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    caches = list((vault_dir / ".cache").glob("cc-screenpipe-*.json"))
    latest = latest_file(caches)
    if latest is None:
        return check(
            "screenpipe.cache",
            "warn",
            "No cc-screenpipe cache files found.",
            "Run screenpipe preprocessing.",
        )
    match = SCREENPIPE_RE.match(latest.name)
    if not match:
        return check("screenpipe.cache", "warn", f"Latest cache name is unusual: {latest.name}")
    cache_date = "-".join(match.groups())
    today = now.strftime("%Y-%m-%d")
    severity = "ok" if cache_date == today else "warn"
    next_action = "" if severity == "ok" else "Run screenpipe sync for today."
    return check("screenpipe.cache", severity, f"Latest cache is {latest.name}.", next_action)


def check_session_index(
    db_path: Path = SESSION_DB,
    session_dir: Path = SESSION_DIR,
    now: datetime | None = None,
) -> dict:
    _ = now or datetime.now(timezone.utc)
    if not db_path.exists():
        return check(
            "session_index.db",
            "fail",
            f"Missing session index DB at {db_path}.",
            "Run session_index.py build.",
        )
    if not session_dir.exists():
        return check(
            "session_index.db",
            "warn",
            f"Session transcript dir not found: {session_dir}",
        )
    latest_jsonl = latest_file(list(session_dir.glob("*.jsonl")))
    if latest_jsonl is None:
        return check("session_index.db", "warn", "No session transcripts found.")
    try:
        conn = sqlite3.connect(db_path)
        latest_indexed = conn.execute("SELECT MAX(indexed_at) FROM sessions").fetchone()[0]
        n_sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        conn.close()
    except Exception as exc:
        return check(
            "session_index.db",
            "fail",
            f"Could not read session index DB: {exc}",
            "Run session_index.py build.",
        )
    if not latest_indexed:
        return check(
            "session_index.db",
            "fail",
            "Session index has no indexed_at timestamp.",
            "Run session_index.py build.",
        )
    lag_h = (latest_jsonl.stat().st_mtime - latest_indexed) / 3600
    if lag_h <= SESSION_INDEX_WARN_HOURS:
        return check(
            "session_index.db",
            "ok",
            f"{n_sessions} sessions indexed; latest transcript lag {max(lag_h, 0):.1f}h.",
        )
    return check(
        "session_index.db",
        "warn",
        f"{n_sessions} sessions indexed; latest transcript is {lag_h:.1f}h newer than index.",
        "Run session_index.py update before continuity searches.",
    )


def check_skill_snapshot(path: Path = SKILL_SNAPSHOT, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    if not path.exists():
        return check(
            "skill_snapshot",
            "warn",
            f"Missing skill snapshot at {path}.",
            "Run skill_diff.py --snapshot.",
        )
    age_h = (now.timestamp() - path.stat().st_mtime) / 3600
    severity = "ok" if age_h <= SKILL_SNAPSHOT_WARN_HOURS else "warn"
    next_action = "" if severity == "ok" else "Run skill_diff.py --snapshot."
    return check("skill_snapshot", severity, f"Snapshot is {age_h:.1f}h old.", next_action)


def build_report(
    vault_dir: Path = VAULT_DIR,
    memory_dir: Path = MEMORY_DIR,
    session_dir: Path = SESSION_DIR,
    now: datetime | None = None,
) -> dict:
    now = now or datetime.now(timezone.utc)
    session_db = memory_dir / "session_index.db"
    skill_snapshot = memory_dir / "skill-snapshot.json"
    checks: list[dict] = []
    checks.extend(check_working_memory(vault_dir=vault_dir, now=now))
    checks.append(check_latest_daily_journal(vault_dir=vault_dir, now=now))
    checks.append(check_screenpipe_cache(vault_dir=vault_dir, now=now))
    checks.append(check_session_index(db_path=session_db, session_dir=session_dir, now=now))
    checks.append(check_skill_snapshot(path=skill_snapshot, now=now))
    if any(c["severity"] == "fail" for c in checks):
        status = "fail"
    elif any(c["severity"] == "warn" for c in checks):
        status = "warn"
    else:
        status = "ok"
    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "status": status,
        "checks": checks,
    }


def render_markdown(report: dict, quiet: bool = False) -> str:
    lines = [f"# Command Center Health ({report['status'].upper()})", ""]
    checks = report["checks"]
    if quiet:
        checks = [c for c in checks if c["severity"] != "ok"]
    if not checks:
        lines.append("All checks OK.")
        return "\n".join(lines) + "\n"
    markers = {"ok": "OK", "warn": "WARN", "fail": "FAIL"}
    for item in checks:
        line = f"- {markers.get(item['severity'], item['severity'].upper())} `{item['name']}`: {item['detail']}"
        if item.get("next_action"):
            line += f" Next: {item['next_action']}"
        lines.append(line)
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--vault", type=Path, default=VAULT_DIR)
    parser.add_argument("--memory-dir", type=Path, default=MEMORY_DIR)
    parser.add_argument("--session-dir", type=Path, default=SESSION_DIR)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    report = build_report(args.vault, args.memory_dir, args.session_dir)
    if args.as_json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(report, quiet=args.quiet))
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
