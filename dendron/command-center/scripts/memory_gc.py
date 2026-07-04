#!/usr/bin/env python3
"""
Memory garbage-collection / sanity report.

Scans the auto-memory directory for:
  • Stale files (mtime > N days, default 90)
  • Near-duplicate pairs (Jaccard similarity over content tokens > 0.55)
  • MEMORY.md links pointing to nonexistent files
  • Memory files not referenced from MEMORY.md (orphans)
  • Heuristic contradictions in feedback_*.md (always/never collision on shared key terms)

Reports to stdout. Never deletes — that's a human decision.

Usage:
    memory_gc.py
    memory_gc.py --stale-days 60
    memory_gc.py --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

MEMORY_DIR = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron/memory"
)
MEMORY_INDEX = MEMORY_DIR / "MEMORY.md"

DEFAULT_STALE_DAYS = 90
DUP_JACCARD_THRESHOLD = 0.55
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{2,}")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+\.md)\)")


def tokenize(text: str) -> set[str]:
    """Lowercase content tokens, no stopwords (Jaccard is robust to a few)."""
    return {t.lower() for t in TOKEN_RE.findall(text) if len(t) > 3}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def load_memory_index() -> tuple[set[str], list[str]]:
    """Returns (linked_filenames, broken_links)."""
    if not MEMORY_INDEX.exists():
        return set(), []
    text = MEMORY_INDEX.read_text()
    linked: set[str] = set()
    broken: list[str] = []
    for m in LINK_RE.finditer(text):
        target = m.group(1).strip()
        if target.startswith("http"):
            continue
        # Ignore MEMORY.md self-link and absolute paths to vault.
        if target.startswith("/"):
            continue
        linked.add(target)
        if not (MEMORY_DIR / target).exists():
            broken.append(target)
    return linked, broken


def find_stale(files: list[Path], stale_days: int) -> list[tuple[Path, int]]:
    cutoff = time.time() - stale_days * 86400
    out = []
    for fp in files:
        m = fp.stat().st_mtime
        if m < cutoff:
            age_days = int((time.time() - m) / 86400)
            out.append((fp, age_days))
    return sorted(out, key=lambda x: -x[1])


def find_duplicates(files: list[Path], threshold: float) -> list[tuple[Path, Path, float]]:
    tokens = {fp: tokenize(fp.read_text(errors="ignore")) for fp in files}
    pairs: list[tuple[Path, Path, float]] = []
    sorted_files = sorted(files, key=lambda p: p.name)
    for i, a in enumerate(sorted_files):
        for b in sorted_files[i + 1 :]:
            # Only compare same-prefix files (feedback vs feedback, project vs project).
            if a.name.split("_")[0] != b.name.split("_")[0]:
                continue
            sim = jaccard(tokens[a], tokens[b])
            if sim >= threshold:
                pairs.append((a, b, sim))
    return sorted(pairs, key=lambda x: -x[2])


# Contradiction detection: very simple. For each feedback file, extract
# imperatives ("always X", "never X", "don't X", "always do X"). Pair files
# that share a target noun but disagree on the modal.
RULE_RE = re.compile(
    r"\b(always|never|don'?t|do not|prefer|avoid|stop)\b\s+([a-z][a-z\- ]{3,40}?)(?=[\.\,\;\:\n])",
    re.IGNORECASE,
)
NEGATIVE_MODALS = {"never", "don't", "dont", "do not", "avoid", "stop"}


def find_contradictions(feedback_files: list[Path]) -> list[tuple[Path, Path, str, str, str]]:
    rules_by_file: dict[Path, list[tuple[str, str]]] = {}
    for fp in feedback_files:
        text = fp.read_text(errors="ignore")
        rules = []
        for m in RULE_RE.finditer(text):
            modal = m.group(1).lower().replace("’", "'")
            target = m.group(2).strip().lower()
            rules.append((modal, target))
        if rules:
            rules_by_file[fp] = rules

    out: list[tuple[Path, Path, str, str, str]] = []
    files = list(rules_by_file)
    for i, a in enumerate(files):
        for b in files[i + 1 :]:
            for ma, ta in rules_by_file[a]:
                for mb, tb in rules_by_file[b]:
                    if ta != tb:
                        continue
                    a_neg = ma in NEGATIVE_MODALS
                    b_neg = mb in NEGATIVE_MODALS
                    if a_neg != b_neg:
                        out.append((a, b, ta, ma, mb))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS)
    ap.add_argument("--dup-threshold", type=float, default=DUP_JACCARD_THRESHOLD)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    if not MEMORY_DIR.exists():
        print(f"Memory dir not found: {MEMORY_DIR}", file=sys.stderr)
        return 1

    files = sorted(p for p in MEMORY_DIR.glob("*.md") if p.name != "MEMORY.md")
    feedback = [p for p in files if p.name.startswith("feedback_")]

    linked, broken_links = load_memory_index()
    orphans = [
        p.name
        for p in files
        if p.name not in linked and not p.name.startswith("_")
    ]

    stale = find_stale(files, args.stale_days)
    duplicates = find_duplicates(files, args.dup_threshold)
    contradictions = find_contradictions(feedback)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "memory_dir": str(MEMORY_DIR),
        "n_files": len(files),
        "n_feedback": len(feedback),
        "stale_days_threshold": args.stale_days,
        "stale": [{"file": p.name, "age_days": d} for p, d in stale],
        "duplicate_pairs": [
            {"a": a.name, "b": b.name, "jaccard": round(s, 3)}
            for a, b, s in duplicates
        ],
        "broken_links_in_index": broken_links,
        "orphans_not_in_index": orphans,
        "contradictions": [
            {"a": a.name, "b": b.name, "target": t, "modal_a": ma, "modal_b": mb}
            for a, b, t, ma, mb in contradictions
        ],
    }

    if args.as_json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    # Markdown report.
    print(f"# Memory GC report — {report['generated_at']}")
    print(f"_{report['n_files']} files ({report['n_feedback']} feedback). Memory dir: `{MEMORY_DIR}`._\n")

    if stale:
        print(f"## Stale (>{args.stale_days} days unchanged) — {len(stale)} files")
        for fp, age in stale[:25]:
            print(f"- `{fp.name}` — {age} days")
        if len(stale) > 25:
            print(f"- _… {len(stale) - 25} more_")
        print()

    if duplicates:
        print(f"## Near-duplicate pairs (Jaccard ≥ {args.dup_threshold}) — {len(duplicates)}")
        for a, b, s in duplicates:
            print(f"- `{a.name}` ↔ `{b.name}` — {s:.2f}")
        print()

    if broken_links:
        print(f"## Broken MEMORY.md links — {len(broken_links)}")
        for t in broken_links:
            print(f"- `{t}`")
        print()

    if orphans:
        print(f"## Orphans (not linked from MEMORY.md) — {len(orphans)}")
        for n in orphans[:30]:
            print(f"- `{n}`")
        if len(orphans) > 30:
            print(f"- _… {len(orphans) - 30} more_")
        print()

    if contradictions:
        print(f"## Heuristic contradictions in feedback_*.md — {len(contradictions)}")
        print("_(modal-clash on shared target nouns. Manually verify — false positives are common.)_\n")
        for a, b, t, ma, mb in contradictions[:20]:
            print(f"- `{a.name}` says **{ma}** \"{t}\"; `{b.name}` says **{mb}** \"{t}\"")
        print()

    if not (stale or duplicates or broken_links or orphans or contradictions):
        print("Clean. No issues surfaced.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
