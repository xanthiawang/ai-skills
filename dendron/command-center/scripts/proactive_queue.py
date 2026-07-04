#!/usr/bin/env python3
"""
Build a proactive command-center queue from local Dendron state.

The queue is intentionally conservative: it ranks already-surfaced obligations,
deadlines, blockers, and reply debt. It does not invent tasks or call external
services. Higher-risk actions still require Albert's approval.

Usage:
    proactive_queue.py
    proactive_queue.py --limit 8
    proactive_queue.py --json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

VAULT_DIR = Path("/Users/A.Y/Documents/Manual Library/Dendron/notes")
MEMORY_DIR = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron/memory"
)

ITEM_RE = re.compile(r"^\s*-\s+(?:\[(?P<box>[ xX])\]\s*)?(?P<body>.*)$")
HEADER_RE = re.compile(r"^(#{2,4})\s+(.+?)\s*$")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ACTION_RE = re.compile(r"\bAction:\s*([^.;\n]+)", re.IGNORECASE)


def ascii_clean(text: str) -> str:
    text = text.replace("—", " - ").replace("–", "-").replace("‑", "-")
    text = text.replace("★", "").replace("✅", "").replace("⚠️", "").replace("🔴", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -\t")


def strip_markup(text: str) -> str:
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = text.replace("**", "").replace("~~", "")
    return ascii_clean(text)


def first_active_email_block(working_memory: str) -> str:
    lines = working_memory.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.startswith("## Email Inbox") and "Active Items" in line:
            start = idx
            break
    if start is None:
        return ""
    end = len(lines)
    for idx in range(start + 1, len(lines)):
        if lines[idx].startswith("## Email Inbox"):
            end = idx
            break
        if lines[idx].startswith("## Sync Status"):
            end = idx
            break
    return "\n".join(lines[start:end])


def section_after_heading(text: str, heading_regex: str, stop_level: str = "###") -> str:
    pattern = re.compile(heading_regex, re.IGNORECASE)
    lines = text.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if pattern.search(line):
            start = idx + 1
            break
    if start is None:
        return ""
    stop_prefixes = (stop_level, "## ") if stop_level == "###" else (stop_level,)
    end = len(lines)
    for idx in range(start, len(lines)):
        line = lines[idx]
        if any(line.startswith(prefix) for prefix in stop_prefixes):
            end = idx
            break
    return "\n".join(lines[start:end])


def list_items(text: str) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        match = ITEM_RE.match(line)
        if match:
            if (match.group("box") or "").lower() == "x":
                continue
            item = match.group("body").strip()
            if item:
                items.append(item)
    return items


def title_from_item(raw: str) -> str:
    bold = BOLD_RE.search(raw)
    if bold:
        return strip_markup(bold.group(1))
    clean = strip_markup(raw)
    return re.split(r"\s+-\s+|\.\s+", clean, maxsplit=1)[0].strip()


def action_from_item(raw: str) -> str:
    action = ACTION_RE.search(raw)
    if action:
        return strip_markup(action.group(1)).rstrip(".")
    clean = strip_markup(raw)
    parts = re.split(r"\s+-\s+", clean, maxsplit=1)
    if len(parts) == 2:
        detail = parts[1].strip()
        if detail:
            return detail.rstrip(".")
    return "open the source thread and resolve the next concrete step"


def score_item(title: str, raw: str, base: int) -> tuple[int, str]:
    haystack = f"{title} {raw}".lower()
    score = base
    reasons: list[str] = []
    boosts = [
        ("overdue", 35, "overdue"),
        ("expires today", 35, "expires today"),
        ("expires", 20, "expires"),
        ("deadline", 18, "deadline"),
        ("due today", 18, "due today"),
        ("due", 10, "due"),
        ("stale", 12, "stale"),
        ("waiting on albert", 15, "waiting on Albert"),
        ("albert owes", 15, "waiting on Albert"),
        ("reply", 8, "reply"),
        ("respond", 8, "respond"),
        ("submit", 8, "submit"),
        ("verify", 6, "verify"),
    ]
    for term, points, reason in boosts:
        if term in haystack:
            score += points
            reasons.append(reason)
    penalties = [
        ("tracking", -60),
        ("fyi", -50),
        ("no immediate action", -60),
        ("awaiting student", -20),
        ("closed", -80),
        ("complete", -80),
    ]
    for term, points in penalties:
        if term in haystack:
            score += points
    return score, ", ".join(dict.fromkeys(reasons)) or "active obligation"


def make_item(raw: str, source: str, base: int) -> dict | None:
    title = title_from_item(raw)
    if not title:
        return None
    score, reason = score_item(title, raw, base)
    if score < 35:
        return None
    return {
        "score": score,
        "title": title,
        "source": source,
        "reason": reason,
        "next_action": action_from_item(raw),
    }


def collect_email_items(working_memory: str) -> list[dict]:
    block = first_active_email_block(working_memory)
    out: list[dict] = []
    for raw in list_items(section_after_heading(block, r"^### Needs Action \(HIGH\)")):
        item = make_item(raw, "email.high", 100)
        if item:
            out.append(item)
    for raw in list_items(section_after_heading(block, r"^### Needs Action \(MEDIUM\)")):
        item = make_item(raw, "email.medium", 70)
        if item:
            out.append(item)
    return out


def collect_live_tasks(working_memory: str) -> list[dict]:
    block = section_after_heading(working_memory, r"^## Live Tasks", stop_level="## ")
    out: list[dict] = []
    for raw in list_items(block):
        if raw.startswith("[x]") or raw.startswith("[X]"):
            continue
        item = make_item(raw, "working_memory.live_task", 52)
        if item:
            out.append(item)
    return out


def collect_command_center_items(command_center: str) -> list[dict]:
    high = section_after_heading(command_center, r"^### High Priority")
    out: list[dict] = []
    for raw in list_items(high):
        item = make_item(raw, "context.high_priority", 92)
        if item:
            out.append(item)
    return out


def collect_parked_items(parked_convos: str) -> list[dict]:
    out: list[dict] = []
    for line in parked_convos.splitlines():
        if not line.startswith("| 20"):
            continue
        cells = [strip_markup(cell) for cell in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        _, topic, _resume, status, notes = cells[:5]
        raw = f"{topic} - {status}. {notes}"
        item = make_item(raw, "parked_conversation", 58)
        if item:
            out.append(item)
    return out


def normalized_title_key(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def distinctive_ids(title: str) -> set[str]:
    return set(re.findall(r"\b[a-z]*-?\d{5,}[a-z0-9-]*\b|\b\d{5,}\b", title.lower()))


def dedupe_and_rank(items: list[dict], limit: int) -> list[dict]:
    ranked = sorted(items, key=lambda i: (-i["score"], i["title"]))
    selected: list[dict] = []
    seen_keys: set[str] = set()
    seen_ids: set[str] = set()
    for item in ranked:
        key = normalized_title_key(item["title"])
        ids = distinctive_ids(item["title"])
        if key in seen_keys:
            continue
        if ids and ids & seen_ids:
            continue
        selected.append(item)
        seen_keys.add(key)
        seen_ids.update(ids)
        if len(selected) >= limit:
            break
    return selected


def build_queue(
    working_memory: str,
    command_center: str,
    parked_convos: str,
    limit: int = 8,
) -> list[dict]:
    items: list[dict] = []
    items.extend(collect_email_items(working_memory))
    items.extend(collect_live_tasks(working_memory))
    items.extend(collect_command_center_items(command_center))
    items.extend(collect_parked_items(parked_convos))
    return dedupe_and_rank(items, limit=limit)


def render_json(items: list[dict]) -> str:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items": items,
    }
    return json.dumps(payload, indent=2) + "\n"


def render_markdown(items: list[dict]) -> str:
    lines = ["# Proactive Decision Queue", ""]
    if not items:
        lines.append("No actionable items surfaced from local command-center state.")
        return "\n".join(lines) + "\n"
    for idx, item in enumerate(items, 1):
        lines.append(
            f"{idx}. **{item['title']}** [{item['source']}, score {item['score']}]"
        )
        lines.append(f"   - Why: {item['reason']}")
        lines.append(f"   - Next: {item['next_action']}")
    return "\n".join(lines) + "\n"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--vault", type=Path, default=VAULT_DIR)
    parser.add_argument("--memory-dir", type=Path, default=MEMORY_DIR)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    working_memory = read_text(args.vault / "_working-memory.md")
    command_center = read_text(args.memory_dir / "command-center.md")
    parked_convos = read_text(args.vault / "tool.claude-parked-convos.md")
    items = build_queue(
        working_memory=working_memory,
        command_center=command_center,
        parked_convos=parked_convos,
        limit=args.limit,
    )
    sys.stdout.write(render_json(items) if args.as_json else render_markdown(items))
    return 0


if __name__ == "__main__":
    sys.exit(main())
