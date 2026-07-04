#!/usr/bin/env python3
"""
Phase C reflection — per-session digest of what happened.

Walks one session's jsonl transcript and surfaces: which skills fired, which
tools errored, what user corrections appeared, what files/memory/drafts were
produced, what notable patterns repeated. The agent reads this digest before
parking to decide what to persist into vault, memory, or skill updates.

Usage:
    reflect.py                       # latest completed session
    reflect.py <session_id>
    reflect.py --output <path>       # write to file (default: stdout)
    reflect.py --json                # machine-readable JSON output

Designed to plug into the parked-convos protocol: when the user says "park",
the agent calls this script, reviews suggestions, then writes the project
memo + parked-convos row.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SESSION_DIR = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron-notes"
)
VAULT_PREFIX = "/Users/A.Y/Documents/Manual Library/Dendron/notes"
MEMORY_PREFIX = "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron/memory"

# User-correction heuristic: opening tokens that strongly suggest a course
# correction or rejection of the prior assistant turn.
CORRECTION_RE = re.compile(
    r"^\s*("
    r"no[,\.\s]|"
    r"nope|"
    r"don'?t\b|"
    r"stop\b|"
    r"actually\b|"
    r"instead\b|"
    r"wrong\b|"
    r"that'?s not|"
    r"not (what|that|right)|"
    r"undo\b|"
    r"revert\b|"
    r"why did you"
    r")",
    re.IGNORECASE,
)


def latest_session_id() -> str | None:
    files = sorted(
        SESSION_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not files:
        return None
    # Skip in-progress (the most recent could be the live one).
    for fp in files:
        # If file mtime is older than 5 minutes, treat as completed.
        age = (datetime.now().timestamp() - fp.stat().st_mtime)
        if age > 300:
            return fp.stem
    return files[0].stem if files else None


def parse_ts(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def walk_session(session_id: str) -> dict:
    fp = SESSION_DIR / f"{session_id}.jsonl"
    if not fp.exists():
        raise FileNotFoundError(fp)

    skills_fired: Counter[str] = Counter()
    skills_last_ts: dict[str, str] = {}
    tools_used: Counter[str] = Counter()
    tool_errors: Counter[str] = Counter()
    user_corrections: list[tuple[int, str]] = []
    files_written: list[tuple[str, str]] = []  # (tool, path)
    bash_commands: list[str] = []
    drafts_created: list[dict] = []
    skill_calls_in_order: list[str] = []
    tool_sequence: list[str] = []  # canonical name list, used for pattern detection

    first_ts = last_ts = None
    n_user = n_assistant = 0

    with fp.open() as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = rec.get("timestamp") or ""
            if ts:
                if first_ts is None:
                    first_ts = ts
                last_ts = ts

            role = rec.get("type") or rec.get("role") or ""
            msg = rec.get("message") or {}
            content = msg.get("content") if isinstance(msg, dict) else None

            if role == "user":
                n_user += 1
                # Plain string user content → check for correction tokens.
                if isinstance(content, str) and content.strip():
                    if CORRECTION_RE.search(content):
                        snippet = content.strip().splitlines()[0][:160]
                        user_corrections.append((idx, snippet))
                continue

            if role == "assistant":
                n_assistant += 1

            if not isinstance(content, list):
                continue

            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")

                if btype == "tool_use":
                    tname = block.get("name", "?")
                    tools_used[tname] += 1
                    tool_sequence.append(tname)
                    binp = block.get("input") or {}
                    if tname == "Skill":
                        sk = binp.get("skill", "?")
                        skills_fired[sk] += 1
                        skills_last_ts[sk] = ts
                        skill_calls_in_order.append(sk)
                    elif tname in ("Write", "Edit", "NotebookEdit"):
                        path = binp.get("file_path") or binp.get("notebook_path", "")
                        if path:
                            files_written.append((tname, path))
                    elif tname == "Bash":
                        cmd = binp.get("command", "")
                        if cmd:
                            bash_commands.append(cmd[:200])
                    elif "gmail_create_draft" in tname.lower():
                        drafts_created.append(
                            {
                                "to": binp.get("to") or binp.get("recipient", ""),
                                "subject": binp.get("subject", ""),
                            }
                        )
                elif btype == "tool_result":
                    if block.get("is_error"):
                        # Find the matching tool_use to credit the error.
                        # (Simple: assume the most recent tool_use is the cause.)
                        if tool_sequence:
                            tool_errors[tool_sequence[-1]] += 1

    duration_min = None
    if first_ts and last_ts:
        a, b = parse_ts(first_ts), parse_ts(last_ts)
        if a and b:
            duration_min = round((b - a).total_seconds() / 60, 1)

    # Pattern detection: trigrams of tool calls that repeat 3+ times.
    trigram_counts: Counter[tuple] = Counter()
    for i in range(len(tool_sequence) - 2):
        trigram_counts[tuple(tool_sequence[i : i + 3])] += 1
    repeated_trigrams = [(g, n) for g, n in trigram_counts.most_common(8) if n >= 3]

    # Files modified, by category.
    vault_notes = sorted({p for _, p in files_written if p.startswith(VAULT_PREFIX)})
    memory_files = sorted({p for _, p in files_written if p.startswith(MEMORY_PREFIX)})
    other_files = sorted(
        {p for _, p in files_written if not (p.startswith(VAULT_PREFIX) or p.startswith(MEMORY_PREFIX))}
    )

    return {
        "session_id": session_id,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "duration_min": duration_min,
        "n_user_turns": n_user,
        "n_assistant_turns": n_assistant,
        "skills_fired": dict(skills_fired.most_common()),
        "skills_last_ts": skills_last_ts,
        "tools_used": dict(tools_used.most_common()),
        "tool_errors": dict(tool_errors.most_common()),
        "user_corrections": user_corrections,
        "vault_notes_touched": vault_notes,
        "memory_files_touched": memory_files,
        "other_files_touched": other_files,
        "bash_commands_count": len(bash_commands),
        "drafts_created": drafts_created,
        "repeated_trigrams": repeated_trigrams,
    }


def format_markdown(data: dict) -> str:
    lines = [
        f"# Phase C Reflection — session `{data['session_id']}`",
        "",
        f"_{data['n_user_turns']} user turns · {data['n_assistant_turns']} assistant turns · "
        f"duration {data['duration_min'] or '?'} min · "
        f"{data['first_ts'] or '?'} → {data['last_ts'] or '?'}_",
        "",
    ]

    # Skills.
    if data["skills_fired"]:
        lines += ["## Skills fired"]
        for sk, n in data["skills_fired"].items():
            last = data["skills_last_ts"].get(sk, "")[:19]
            lines.append(f"- `{sk}` — {n}× (last: {last})")
        lines.append("")

    # Tools.
    if data["tools_used"]:
        lines += ["## Tools used"]
        for tool, n in list(data["tools_used"].items())[:15]:
            err = data["tool_errors"].get(tool, 0)
            err_str = f" — **{err} errors**" if err else ""
            lines.append(f"- {tool}: {n}{err_str}")
        lines.append("")

    # User corrections.
    if data["user_corrections"]:
        lines += [
            "## User corrections detected",
            "_Heuristic: user messages opening with no/don't/stop/actually/wrong/etc. Review for feedback memos to write._",
            "",
        ]
        for idx, snippet in data["user_corrections"][:8]:
            lines.append(f"- (turn {idx}) {snippet!r}")
        lines.append("")

    # Files.
    if data["vault_notes_touched"]:
        lines += [f"## Vault notes touched ({len(data['vault_notes_touched'])})"]
        for p in data["vault_notes_touched"][:20]:
            lines.append(f"- `{Path(p).name}`")
        lines.append("")

    if data["memory_files_touched"]:
        lines += [f"## Auto-memory files touched ({len(data['memory_files_touched'])})"]
        for p in data["memory_files_touched"][:20]:
            lines.append(f"- `{Path(p).name}`")
        lines.append("")

    if data["other_files_touched"]:
        lines += [f"## Other files touched ({len(data['other_files_touched'])})"]
        for p in data["other_files_touched"][:15]:
            lines.append(f"- `{p}`")
        lines.append("")

    # Drafts.
    if data["drafts_created"]:
        lines += [f"## Gmail drafts created ({len(data['drafts_created'])})"]
        for d in data["drafts_created"]:
            lines.append(f"- to {d.get('to', '?')} — {d.get('subject', '?')!r}")
        lines.append("")

    # Repeated patterns.
    if data["repeated_trigrams"]:
        lines += [
            "## Repeated tool patterns",
            "_Trigrams that fired 3+ times — candidates for skill promotion._",
            "",
        ]
        for trigram, n in data["repeated_trigrams"]:
            lines.append(f"- {' → '.join(trigram)} ({n}×)")
        lines.append("")

    # Suggested actions (heuristic).
    suggestions = []
    if data["user_corrections"]:
        suggestions.append(
            f"Review {len(data['user_corrections'])} user-correction message(s) — "
            f"consider writing `feedback_*.md` for any preferences/rules surfaced."
        )
    if data["repeated_trigrams"]:
        suggestions.append(
            f"Run `propose_skill.py {data['session_id']}` to draft a skill from the "
            f"{len(data['repeated_trigrams'])} repeated tool pattern(s)."
        )
    if data["tool_errors"]:
        err_tools = list(data["tool_errors"].keys())[:3]
        suggestions.append(
            f"Tools that errored ({', '.join(err_tools)}) — check whether SKILL.md "
            f"or `tool.*.md` notes need updating with the failure modes encountered."
        )
    if not data["vault_notes_touched"] and (data["n_assistant_turns"] or 0) > 20:
        suggestions.append(
            "No vault notes were written this session despite 20+ assistant turns — "
            "review whether work should have been captured per the Vault Capture Rule."
        )
    if data["drafts_created"]:
        suggestions.append(
            f"{len(data['drafts_created'])} Gmail draft(s) created — confirm whether sent, "
            f"and update relevant `user.*.md` interaction logs."
        )

    if suggestions:
        lines += ["## Suggested actions"]
        for s in suggestions:
            lines.append(f"- {s}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("session_id", nargs="?", help="Session id (default: latest completed)")
    ap.add_argument("--output", help="Write markdown to file instead of stdout")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    sid = args.session_id or latest_session_id()
    if not sid:
        print("No session found", file=sys.stderr)
        return 1

    data = walk_session(sid)
    out = json.dumps(data, indent=2, default=str) if args.as_json else format_markdown(data)

    if args.output:
        Path(args.output).write_text(out)
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(out)
        if not out.endswith("\n"):
            sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
