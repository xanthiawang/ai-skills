#!/usr/bin/env python3
"""
Autonomous skill draft generator (Hermes-Agent style).

Walks a session's jsonl looking for repeated multi-step workflows. Clusters
tool-call sequences by canonical shape, filters out trivial single-tool
loops (e.g., Bash×N), proposes a SKILL.md draft for any cluster that fired
3+ times across the session.

Drafts land in `~/programs/ai-skills/_proposed/<auto-name>/SKILL.md` for
manual review. Does NOT auto-promote.

Usage:
    propose_skill.py <session_id>
    propose_skill.py --window 5         # sequence length to cluster (default 4)
    propose_skill.py --min-occurrences 3
    propose_skill.py --dry-run          # print drafts, don't write files
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
PROPOSED_DIR = Path("/Users/A.Y/programs/ai-skills/_proposed")

# Tool sequences shorter than this don't qualify — we want multi-step
# workflows, not monotonic Bash spam.
DEFAULT_WINDOW = 4
DEFAULT_MIN_OCCURRENCES = 3

# Filter trivial: a sequence of all-the-same tool is a loop, not a workflow.
def is_trivial(seq: tuple[str, ...]) -> bool:
    if len(set(seq)) == 1:
        return True
    # Mostly-same-tool (e.g., 3 of 4 are Bash) is also weak signal.
    most_common = Counter(seq).most_common(1)[0][1]
    return most_common >= len(seq) - 1


def collect_workflows(session_id: str, window: int) -> dict:
    fp = SESSION_DIR / f"{session_id}.jsonl"
    if not fp.exists():
        raise FileNotFoundError(fp)

    tool_calls: list[dict] = []  # [{tool, input, ts, idx}]
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
            msg = rec.get("message") or {}
            content = msg.get("content") if isinstance(msg, dict) else None
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") != "tool_use":
                    continue
                tool_calls.append(
                    {
                        "tool": block.get("name", "?"),
                        "input": block.get("input") or {},
                        "ts": ts,
                        "idx": idx,
                    }
                )

    # Slide a window of length `window` across tool_calls; canonical signature
    # is the tuple of tool names. Group call-tuples that share the signature.
    signatures: dict[tuple, list[list[dict]]] = defaultdict(list)
    for i in range(len(tool_calls) - window + 1):
        seq = tool_calls[i : i + window]
        sig = tuple(c["tool"] for c in seq)
        if is_trivial(sig):
            continue
        signatures[sig].append(seq)

    return {
        "session_id": session_id,
        "n_tool_calls": len(tool_calls),
        "signatures": signatures,
        "tool_calls": tool_calls,
    }


def slug_from_signature(sig: tuple[str, ...]) -> str:
    """A short hyphenated identifier derived from the tool sequence."""
    seen = []
    for t in sig:
        s = re.sub(r"[^a-z]", "", t.lower())[:6] or "x"
        if s not in seen:
            seen.append(s)
    return "-".join(seen)[:40]


def extract_user_intent(tool_calls: list[dict], session_id: str, window_idx: int) -> str:
    """Find the most recent user message before this window — proxy for trigger phrasing."""
    fp = SESSION_DIR / f"{session_id}.jsonl"
    target_line = tool_calls[window_idx]["idx"] if window_idx < len(tool_calls) else 0
    last_user = ""
    with fp.open() as f:
        for idx, line in enumerate(f):
            if idx >= target_line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (rec.get("type") == "user") or (rec.get("role") == "user"):
                msg = rec.get("message") or {}
                c = msg.get("content") if isinstance(msg, dict) else None
                if isinstance(c, str) and c.strip():
                    last_user = c.strip().splitlines()[0][:200]
    return last_user


def common_paths_in_inputs(occurrences: list[list[dict]]) -> list[str]:
    """Frequent file_path / command tokens across occurrences — for the skill's 'Files' section."""
    paths: Counter[str] = Counter()
    for occ in occurrences:
        for call in occ:
            inp = call.get("input") or {}
            for k in ("file_path", "path", "notebook_path"):
                v = inp.get(k)
                if v:
                    paths[str(v)] += 1
            cmd = inp.get("command")
            if cmd:
                # Extract the leading binary name.
                head = cmd.strip().split()[0] if cmd.strip() else ""
                if head:
                    paths[f"$ {head}"] += 1
    return [p for p, _ in paths.most_common(8)]


def draft_skill_md(
    sig: tuple[str, ...],
    occurrences: list[list[dict]],
    user_intent: str,
    common: list[str],
) -> str:
    """Generate a SKILL.md draft for a candidate workflow."""
    name = slug_from_signature(sig)
    n = len(occurrences)
    sequence_str = " → ".join(sig)
    today = datetime.now().strftime("%Y-%m-%d")

    common_lines = "\n".join(f"- `{p}`" for p in common) or "- (none surfaced)"
    intent_line = f"> {user_intent!r}" if user_intent else "> _(no preceding user message)_"

    return f"""---
name: {name}
description: AUTO-DRAFTED — review before promotion. Workflow detected from session activity.
status: proposed
created: {today}
---

# {name}

> ⚠ AUTO-DRAFTED by `propose_skill.py` from a session pattern that fired {n}× — not yet validated. Edit, rename, or delete.

## When to use

Workflow that recurs in sessions matching this pattern. Most recent triggering user message:

{intent_line}

## Tool sequence (canonical)

```
{sequence_str}
```

Saw this exact sequence **{n} times** across the source session.

## Common inputs / paths surfaced

{common_lines}

## Suggested next steps for the human reviewer

1. **Decide if this is a real skill or a coincidence.** Some trigrams reflect a generic problem-solving rhythm (Read → Edit → Bash) that doesn't deserve a skill.
2. **Rename `{name}` to something descriptive** based on the actual goal (not the tool shape).
3. **Add a `When to Use` section** that triggers the skill from intent, not from tool sequence.
4. **Replace this draft body** with concrete instructions for the agent — what to read, what to write, what to verify.
5. Move from `_proposed/` to the appropriate `~/programs/ai-skills/<category>/` location, then commit.

## Provenance

- Source session: `{occurrences[0][0].get('idx', '?')}` … `{occurrences[-1][-1].get('idx', '?')}` (turn indices)
- Detected by: `command-center/scripts/propose_skill.py`
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("session_id")
    ap.add_argument("--window", type=int, default=DEFAULT_WINDOW)
    ap.add_argument("--min-occurrences", type=int, default=DEFAULT_MIN_OCCURRENCES)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = collect_workflows(args.session_id, args.window)
    candidates = sorted(
        (
            (sig, occs)
            for sig, occs in data["signatures"].items()
            if len(occs) >= args.min_occurrences
        ),
        key=lambda x: -len(x[1]),
    )

    if not candidates:
        print(
            f"No multi-step workflows fired ≥{args.min_occurrences}× "
            f"with window={args.window} in {args.session_id}",
            file=sys.stderr,
        )
        return 0

    print(f"Found {len(candidates)} candidate workflow(s):", file=sys.stderr)
    for sig, occs in candidates:
        print(f"  {len(occs):>3}× {' → '.join(sig)}", file=sys.stderr)

    if not args.dry_run:
        PROPOSED_DIR.mkdir(parents=True, exist_ok=True)

    written = []
    for sig, occs in candidates:
        slug = slug_from_signature(sig)
        # Find which window index in tool_calls these occurrences started at.
        first_call_idx = data["tool_calls"].index(occs[0][0]) if occs else 0
        intent = extract_user_intent(data["tool_calls"], args.session_id, first_call_idx)
        common = common_paths_in_inputs(occs)
        draft = draft_skill_md(sig, occs, intent, common)

        if args.dry_run:
            print(f"\n=== {slug} ===")
            print(draft)
            continue

        out_dir = PROPOSED_DIR / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "SKILL.md"
        # Don't clobber an already-promoted draft.
        if out_path.exists():
            stat = out_path.stat()
            backup = out_path.with_suffix(f".prev-{int(stat.st_mtime)}.md")
            out_path.rename(backup)
        out_path.write_text(draft)
        written.append(out_path)

    if written:
        print(f"\nWrote {len(written)} draft(s) to {PROPOSED_DIR}/", file=sys.stderr)
        for p in written:
            print(f"  {p}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
