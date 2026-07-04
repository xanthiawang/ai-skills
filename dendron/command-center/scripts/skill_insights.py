#!/usr/bin/env python3
"""
Skill usage telemetry, ported from Hermes-Agent's insights._compute_skill_breakdown.

Walks Claude Code session jsonl files looking for Skill tool invocations,
counts per-skill loads + last-used timestamps, writes a JSON summary that
the command-center skill can read at session start to surface stale or
heavily-used skills.

Usage:
    skill_insights.py             # write memory/skill-insights.json
    skill_insights.py --print     # also dump report to stdout
    skill_insights.py --since DAYS  # only count sessions touched in last N days
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_DIR = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron-notes"
)
OUT_PATH = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron/memory/skill-insights.json"
)


def parse_ts(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def walk_sessions(since_days: int | None) -> dict:
    cutoff = (
        datetime.now(timezone.utc) - timedelta(days=since_days)
        if since_days
        else None
    )
    counts_total: Counter[str] = Counter()
    counts_recent: Counter[str] = Counter()
    last_used: dict[str, str] = {}
    sessions_touched: dict[str, set] = defaultdict(set)

    for fp in sorted(PROJECT_DIR.glob("*.jsonl")):
        sid = fp.stem
        with fp.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = rec.get("message") or {}
                content = msg.get("content") if isinstance(msg, dict) else None
                if not isinstance(content, list):
                    continue
                ts_str = rec.get("timestamp") or ""
                ts_dt = parse_ts(ts_str)
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_use":
                        continue
                    if block.get("name") != "Skill":
                        continue
                    skill = (block.get("input") or {}).get("skill") or "?"
                    counts_total[skill] += 1
                    sessions_touched[skill].add(sid)
                    if ts_str and (skill not in last_used or ts_str > last_used[skill]):
                        last_used[skill] = ts_str
                    if cutoff and ts_dt and ts_dt >= cutoff:
                        counts_recent[skill] += 1

    # Cold bucket: skills not invoked in >30 days.
    now = datetime.now(timezone.utc)
    cold: dict[str, int] = {}
    for skill, ts in last_used.items():
        dt = parse_ts(ts)
        if dt:
            age_days = (now - dt).days
            if age_days > 30:
                cold[skill] = age_days

    return {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lookback_days": since_days,
        "total": dict(counts_total.most_common()),
        "last_7d": dict(counts_recent.most_common()) if since_days else {},
        "last_used": last_used,
        "sessions_touched": {k: len(v) for k, v in sessions_touched.items()},
        "cold_30d": dict(sorted(cold.items(), key=lambda x: -x[1])),
    }


def format_report(data: dict) -> str:
    lines = [
        f"# Skill Insights ({data['generated_at']})",
        "",
        f"_Lookback: {data['lookback_days']} days_" if data["lookback_days"] else "",
        "",
        "## Top skills (all-time invocations)",
    ]
    for skill, n in list(data["total"].items())[:15]:
        last = data["last_used"].get(skill, "?")[:10]
        ns = data["sessions_touched"].get(skill, 0)
        lines.append(f"- **{skill}** — {n} calls / {ns} sessions / last {last}")
    if data.get("last_7d"):
        lines += ["", "## Recent (last 7 days)"]
        for skill, n in list(data["last_7d"].items())[:10]:
            lines.append(f"- {skill} — {n}")

    cold = [
        s
        for s, last in data["last_used"].items()
        if last
        and (datetime.now(timezone.utc) - parse_ts(last)).days > 30
    ]
    if cold:
        lines += ["", "## Cold (>30 days unused)"]
        for s in sorted(cold):
            lines.append(f"- {s} — last {data['last_used'][s][:10]}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--since", type=int, default=7, help="Days lookback for 'recent' bucket")
    ap.add_argument("--print", action="store_true", dest="do_print")
    args = ap.parse_args()

    data = walk_sessions(args.since)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(data, indent=2))
    print(f"Wrote {OUT_PATH}", file=sys.stderr)
    if args.do_print:
        print(format_report(data))
    return 0


if __name__ == "__main__":
    sys.exit(main())
