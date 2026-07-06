#!/usr/bin/env python3
"""Read-only file intake scanner for Albert's Downloads/Desktop workbench."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

HOME = Path.home()
DEFAULT_ROOTS = [HOME / "Downloads", HOME / "Desktop"]
DAY = 86400

SKIP_NAMES = {
    ".DS_Store",
    "_quarantine",
    "Recents",
}

EXT_KINDS = {
    ".pdf": "pdf",
    ".doc": "document",
    ".docx": "document",
    ".rtf": "document",
    ".txt": "text",
    ".md": "text",
    ".ppt": "slide-deck",
    ".pptx": "slide-deck",
    ".key": "slide-deck",
    ".xls": "spreadsheet",
    ".xlsx": "spreadsheet",
    ".csv": "spreadsheet",
    ".tsv": "spreadsheet",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".tif": "image",
    ".tiff": "image",
    ".svg": "image",
    ".zip": "archive",
    ".tar": "archive",
    ".gz": "archive",
    ".dmg": "installer",
    ".pkg": "installer",
    ".app": "installer",
    ".pdb": "structure",
    ".cif": "structure",
    ".pse": "structure",
    ".rds": "data",
    ".rdata": "data",
    ".parquet": "data",
    ".h5ad": "data",
}

PROJECT_HINTS = (
    ("clockbase", "Manuscripts/2022_clock_base"),
    ("clock_base", "Manuscripts/2022_clock_base"),
    ("timepie", "Manuscripts/2026_timepie"),
    ("methylgpt", "Manuscripts/2024_methylGPT"),
    ("organelle", "Manuscripts/2026_organelle_clock or Projects/2025/organelle_clock"),
    ("pathage", "Manuscripts/2023_pathage"),
    ("thrive", "Projects/2026/thrive"),
    ("novokine", "Projects/2026/novokine-prioritization"),
    ("biogami", "Grant/2026_ARPA-H_BIOGAMI"),
    ("arpa", "Grant/2026_ARPA-H_BIOGAMI or matching Grant folder"),
    ("japan_visa", "Projects/2026/japan_visa"),
    ("hk_visa", "Projects/2026/hk_visa_ttps"),
    ("ttps", "Projects/2026/hk_visa_ttps"),
    ("dab-kin", "Projects/2026/dab-kin-2026"),
    ("dab_kin", "Projects/2026/dab-kin-2026"),
)

PERSONAL_HINTS = (
    "passport",
    "visa",
    "uscis",
    "i-765",
    "i-983",
    "i20",
    "i-20",
    "stem opt",
    "employment verification",
    "tax",
    "w-2",
    "1099",
    "bank",
    "medical",
    "health",
)

TRAVEL_HINTS = (
    "receipt",
    "invoice",
    "itinerary",
    "hotel",
    "flight",
    "delta",
    "jetblue",
    "united",
    "uber",
    "lyft",
    "amtrak",
)


@dataclass
class Candidate:
    path: str
    candidate_id: str
    name: str
    kind: str
    size_bytes: int
    modified_at: str
    age_days: int
    intent: str
    confidence: str
    route_hint: str
    safe_action: str
    rationale: str


def local_time(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def classify_kind(path: Path) -> str:
    if path.is_dir():
        if path.suffix.lower() == ".app":
            return "installer"
        return "folder"
    return EXT_KINDS.get(path.suffix.lower(), "unknown")


def classify(path: Path, kind: str, age_days: int) -> tuple[str, str, str, str, str]:
    name = path.name
    lowered = name.lower()

    if name.startswith("~$") or lowered.endswith((".crdownload", ".download", ".part")):
        return ("review", "low", "", "record-only", "temporary or lock/download-in-progress file")

    for token, route in PROJECT_HINTS:
        if token in lowered:
            return (
                "route",
                "high",
                route,
                "current-task-only",
                f"filename matches project token '{token}'",
            )

    if any(token in lowered for token in PERSONAL_HINTS):
        return (
            "record",
            "medium",
            "~/Documents/Manual Library/Personal Info/",
            "ask-before-move",
            "personal/admin document; approval required before moving",
        )

    if any(token in lowered for token in TRAVEL_HINTS):
        return (
            "record",
            "medium",
            "~/Documents/Manual Library/Personal Info/Financial or project travel folder",
            "ask-before-move",
            "receipt/travel/admin document; approval required before moving",
        )

    if kind == "installer":
        return (
            "installer-cleanup",
            "medium",
            "remove/archive after install confirmation",
            "ask-before-move",
            "installer or app bundle in intake zone",
        )

    if kind == "archive":
        return (
            "review",
            "medium",
            "matching project _inbox/ or archive folder",
            "ask-before-move",
            "archive needs project context before routing",
        )

    if kind == "image" and lowered.startswith(("cleanshot", "screenshot", "screen shot", "screen recording")):
        return (
            "quarantine-candidate",
            "medium",
            "~/Pictures/screenshots/YYYY-MM/",
            "checklist-only",
            "screenshot cleanup belongs to drift checklist",
        )

    if age_days >= 60 and kind in {"pdf", "document", "slide-deck", "spreadsheet", "archive"}:
        return (
            "quarantine-candidate",
            "medium",
            "~/Downloads/_quarantine/YYYY-MM/",
            "checklist-only",
            "stale intake file belongs to drift checklist",
        )

    if kind in {"pdf", "document", "slide-deck", "spreadsheet", "image", "data", "structure"}:
        return (
            "review",
            "low",
            "",
            "ask-before-move",
            "needs task or project context",
        )

    return ("review", "low", "", "record-only", "no routing rule matched")


def candidate_id(path: Path, size: int, mtime: float) -> str:
    raw = f"{path}|{size}|{int(mtime)}".encode("utf-8", errors="replace")
    return hashlib.sha1(raw).hexdigest()[:12]


def iter_entries(roots: list[Path], days: int) -> list[Candidate]:
    now = time.time()
    cutoff = now - days * DAY
    candidates: list[Candidate] = []

    for root in roots:
        try:
            entries = sorted(root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        except (FileNotFoundError, NotADirectoryError, PermissionError, OSError) as exc:
            print(f"warning: cannot scan {root}: {exc}", file=sys.stderr)
            continue

        for path in entries:
            if path.name in SKIP_NAMES or path.name.startswith("."):
                continue
            try:
                stat = path.stat()
            except (FileNotFoundError, PermissionError, OSError) as exc:
                print(f"warning: cannot stat {path}: {exc}", file=sys.stderr)
                continue
            if stat.st_mtime < cutoff:
                continue

            kind = classify_kind(path)
            age = int((now - stat.st_mtime) // DAY)
            intent, confidence, route_hint, safe_action, rationale = classify(path, kind, age)
            candidates.append(
                Candidate(
                    path=str(path),
                    candidate_id=candidate_id(path, stat.st_size, stat.st_mtime),
                    name=path.name,
                    kind=kind,
                    size_bytes=stat.st_size,
                    modified_at=local_time(stat.st_mtime),
                    age_days=age,
                    intent=intent,
                    confidence=confidence,
                    route_hint=route_hint,
                    safe_action=safe_action,
                    rationale=rationale,
                )
            )

    return candidates


def fmt_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "K", "M", "G", "T"):
        if value < 1024 or unit == "T":
            return f"{value:.1f}{unit}" if unit != "B" else f"{int(value)}B"
        value /= 1024
    return f"{size}B"


def render_markdown(candidates: list[Candidate], roots: list[Path], days: int, limit: int) -> str:
    shown = candidates[:limit]
    counts: dict[str, int] = {}
    for candidate in candidates:
        counts[candidate.safe_action] = counts.get(candidate.safe_action, 0) + 1

    lines = [
        "# File Intake Scan",
        "",
        f"- Generated: {local_time(time.time())}",
        f"- Mode: read-only",
        f"- Roots: {', '.join(str(root) for root in roots)}",
        f"- Window: last {days} days",
        f"- Candidates: {len(candidates)}",
    ]
    if counts:
        lines.append(f"- Safe-action counts: {', '.join(f'{key}={value}' for key, value in sorted(counts.items()))}")
    lines.extend(["", "| ID | File | Kind | Age | Size | Confidence | Safe action | Hint | Rationale |", "|---|---|---:|---:|---:|---|---|---|---|"])

    for candidate in shown:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{candidate.candidate_id}`",
                    f"`{candidate.path}`",
                    candidate.kind,
                    f"{candidate.age_days}d",
                    fmt_size(candidate.size_bytes),
                    candidate.confidence,
                    candidate.safe_action,
                    candidate.route_hint or "",
                    candidate.rationale,
                ]
            )
            + " |"
        )

    if len(candidates) > limit:
        lines.append("")
        lines.append(f"Showing {limit} of {len(candidates)} candidates. Increase `--max` to show more.")
    return "\n".join(lines) + "\n"


def render_json(candidates: list[Candidate], roots: list[Path], days: int) -> str:
    payload = {
        "generated_at": local_time(time.time()),
        "mode": "read-only",
        "roots": [str(root) for root in roots],
        "window_days": days,
        "candidate_count": len(candidates),
        "candidates": [asdict(candidate) for candidate in candidates],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", action="append", type=Path, help="Root to scan; repeatable. Defaults to Downloads and Desktop.")
    parser.add_argument("--days", type=int, default=30, help="Only include entries modified in the last N days.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--max", type=int, default=80, help="Maximum markdown rows to print.")
    parser.add_argument("--out", type=Path, help="Optional output file.")
    args = parser.parse_args()

    roots = args.path if args.path else DEFAULT_ROOTS
    candidates = iter_entries(roots, args.days)
    candidates.sort(key=lambda c: (c.safe_action != "current-task-only", c.confidence != "high", c.age_days, c.path))

    if args.format == "json":
        output = render_json(candidates, roots, args.days)
    else:
        output = render_markdown(candidates, roots, args.days, args.max)

    if args.out:
        try:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(output, encoding="utf-8")
        except OSError as exc:
            print(f"error: cannot write {args.out}: {exc}", file=sys.stderr)
            return 2
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
