#!/usr/bin/env python3
"""
Track SKILL.md changes across the ai-skills tree.

Walks `~/programs/ai-skills/` for SKILL.md files. For each one in a git repo,
shows commits in the last N days with diff stats. Surfaces in the briefing
so agent-introduced regressions get caught one session later, not three.

Usage:
    skill_diff.py                    # last 7 days, all skill repos
    skill_diff.py --since-days 1
    skill_diff.py --since-session    # diff against snapshot at last session
    skill_diff.py --snapshot         # write current SKILL.md hashes to memory/skill-snapshot.json
    skill_diff.py --json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILLS_ROOT = Path("/Users/A.Y/programs/ai-skills")
SNAPSHOT = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron/memory/skill-snapshot.json"
)


def find_skill_files() -> list[Path]:
    if not SKILLS_ROOT.exists():
        return []
    return sorted(p for p in SKILLS_ROOT.rglob("SKILL.md") if "_proposed" not in p.parts)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def repo_root_for(path: Path) -> Path | None:
    p = path.parent
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    return None


def git_log_since(path: Path, since: str) -> list[dict]:
    repo = repo_root_for(path)
    if not repo:
        return []
    try:
        rel = path.relative_to(repo)
        out = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "log",
                f"--since={since}",
                "--pretty=format:%H%x09%ad%x09%s",
                "--date=short",
                "--",
                str(rel),
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except Exception:
        return []

    commits = []
    for line in (out.stdout or "").splitlines():
        parts = line.split("\t", 2)
        if len(parts) < 3:
            continue
        sha, date, subject = parts
        try:
            stat = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "show",
                    "--stat",
                    "--format=",
                    f"{sha}",
                    "--",
                    str(rel),
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            stat_line = next(
                (
                    l.strip()
                    for l in (stat.stdout or "").splitlines()
                    if "insertion" in l or "deletion" in l or "changed" in l
                ),
                "",
            )
        except Exception:
            stat_line = ""
        commits.append(
            {"sha": sha[:12], "date": date, "subject": subject, "stat": stat_line}
        )
    return commits


def write_snapshot() -> None:
    files = find_skill_files()
    data = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hashes": {str(p.relative_to(SKILLS_ROOT)): file_hash(p) for p in files},
    }
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(data, indent=2))
    print(f"Wrote {SNAPSHOT} ({len(data['hashes'])} skills)", file=sys.stderr)


def diff_against_snapshot() -> dict:
    if not SNAPSHOT.exists():
        return {
            "error": f"No snapshot at {SNAPSHOT}. Run with --snapshot first.",
            "diffs": [],
        }
    prev = json.loads(SNAPSHOT.read_text())
    prev_hashes: dict[str, str] = prev.get("hashes", {})
    files = find_skill_files()
    diffs = []
    for fp in files:
        rel = str(fp.relative_to(SKILLS_ROOT))
        cur = file_hash(fp)
        old = prev_hashes.get(rel)
        if old is None:
            diffs.append({"rel": rel, "status": "new", "old": None, "new": cur})
        elif old != cur:
            diffs.append(
                {"rel": rel, "status": "changed", "old": old, "new": cur}
            )
    # Detect deletions.
    cur_keys = {str(p.relative_to(SKILLS_ROOT)) for p in files}
    for rel, old in prev_hashes.items():
        if rel not in cur_keys:
            diffs.append({"rel": rel, "status": "deleted", "old": old, "new": None})
    return {"snapshot_at": prev.get("generated_at"), "diffs": diffs}


def report_since_days(days: int, as_json: bool) -> int:
    since = f"{days} days ago"
    files = find_skill_files()
    blocks = []
    for fp in files:
        commits = git_log_since(fp, since)
        if commits:
            blocks.append({"rel": str(fp.relative_to(SKILLS_ROOT)), "commits": commits})

    if as_json:
        json.dump({"since": since, "skills": blocks}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if not blocks:
        print(f"No SKILL.md changes in the last {days} days.")
        return 0

    print(f"# SKILL.md changes since {days} days ago\n")
    for b in blocks:
        print(f"## `{b['rel']}`")
        for c in b["commits"]:
            print(f"- `{c['sha']}` {c['date']} — {c['subject']}")
            if c["stat"]:
                print(f"  _{c['stat']}_")
        print()
    return 0


def report_since_session(as_json: bool) -> int:
    result = diff_against_snapshot()
    if as_json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if "error" in result:
        print(result["error"], file=sys.stderr)
        return 1
    print(f"# SKILL.md diffs since snapshot at {result['snapshot_at']}\n")
    if not result["diffs"]:
        print("No changes since snapshot.")
        return 0
    for d in result["diffs"]:
        marker = {"new": "[+]", "changed": "[~]", "deleted": "[-]"}.get(d["status"], "[?]")
        old = d["old"] or "(none)"
        new = d["new"] or "(none)"
        print(f"- {marker} `{d['rel']}` — {old} → {new}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--since-days", type=int, default=7)
    ap.add_argument("--since-session", action="store_true")
    ap.add_argument("--snapshot", action="store_true")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    if args.snapshot:
        write_snapshot()
        return 0
    if args.since_session:
        return report_since_session(args.as_json)
    return report_since_days(args.since_days, args.as_json)


if __name__ == "__main__":
    sys.exit(main())
