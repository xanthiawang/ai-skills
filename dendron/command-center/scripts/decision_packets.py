#!/usr/bin/env python3
"""
Build command-center decision packets for cron and TUI consumers.

This is the backend bridge between the proactive queue and any review surface.
It reads local command-center state only, writes a cache JSON file, and can emit
`[SILENT]` when nothing material changed. External actions remain approval
gated; packets describe what to review, not what to execute.

Usage:
    decision_packets.py
    decision_packets.py --json
    decision_packets.py --silent-if-unchanged
    decision_packets.py --output notes/.cache/command-center/decision-packets.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import healthcheck  # type: ignore  # local script module
import proactive_queue  # type: ignore  # local script module

VAULT_DIR = Path("/Users/A.Y/Documents/Manual Library/Dendron/notes")
MEMORY_DIR = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron/memory"
)
SESSION_DIR = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron-notes"
)
DEFAULT_OUTPUT = VAULT_DIR / ".cache" / "command-center" / "decision-packets.json"
DEFAULT_LEDGER = VAULT_DIR / ".cache" / "command-center" / "action-ledger.json"

APPROVAL_TERMS = (
    "send",
    "submit",
    "reply",
    "respond",
    "confirm",
    "accept",
    "decline",
    "file ",
    "sign",
    "before midnight",
)

ACTIVE_THREAD_TERMS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "command-center": (
        "Command Center",
        "command-center",
        (
            "command-center",
            "agentic cortex",
            "agent-dynamic-canvas",
            "decision-desk",
            "dendron/notes",
            "proactive board",
        ),
    ),
    "thrive-ppformer": (
        "THRIVE / PPformer",
        "thrive",
        ("thrive", "ppformer", "plasma protein transformer", "arpa-h"),
    ),
    "faculty-search": (
        "Faculty search",
        "faculty-search",
        (
            "faculty search",
            "michigan mni",
            "mni/dcmb",
            "umich",
            "dcmb",
            "offer call",
            "offer received",
            "ravi",
        ),
    ),
    "nature-revision": (
        "Nature revision",
        "nature-revision",
        ("nature ms", "30825a-z", "revision", "aging-ai-agent", "vadim"),
    ),
    "binder-pipeline": (
        "Binder pipeline",
        "binder-pipeline",
        ("binder", "small_molecule_binder", "baker", "ipd"),
    ),
}


def stable_item_id(item: dict[str, Any]) -> str:
    raw = "\n".join(
        str(item.get(key, "")) for key in ("title", "source", "next_action")
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def item_fingerprint(item: dict[str, Any]) -> str:
    raw = "\n".join(
        str(item.get(key, "")) for key in ("title", "source", "reason", "next_action")
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def approval_for_item(item: dict[str, Any]) -> str:
    text = " ".join(
        str(item.get(key, "")).lower()
        for key in ("title", "source", "reason", "next_action")
    )
    if any(term in text for term in APPROVAL_TERMS):
        return "required"
    return "prepare_only"


def normalize_item(item: dict[str, Any], previous_ids: set[str]) -> dict[str, Any]:
    item_id = stable_item_id(item)
    normalized = dict(item)
    normalized["id"] = item_id
    normalized["approval"] = approval_for_item(item)
    normalized["state"] = "carried" if item_id in previous_ids else "new"
    return normalized


def run_text_command(args: list[str], timeout: float = 1.0) -> str:
    try:
        return subprocess.check_output(
            args,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
    except Exception:
        return ""


def frontmost_app_name() -> str:
    script = (
        'tell application "System Events" to get name of first application '
        "process whose frontmost is true"
    )
    return run_text_command(["osascript", "-e", script]).strip()


def process_snapshot() -> list[str]:
    output = run_text_command(["ps", "-axo", "pid=,comm=,args="], timeout=1.5)
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    useful_terms = (
        "codex",
        "cursor",
        "agent-dynamic-canvas",
        "dendron",
        "screenpipe",
        "bun run",
        "python3",
        "iTerm",
    )
    return [line for line in lines if any(term.lower() in line.lower() for term in useful_terms)][:80]


def infer_active_context(
    vault_dir: Path = VAULT_DIR,
    now: datetime | None = None,
    frontmost_app: str | None = None,
    process_lines: list[str] | None = None,
    working_memory: str | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    if frontmost_app is None:
        frontmost_app = frontmost_app_name()
    if process_lines is None:
        process_lines = process_snapshot()
    if working_memory is None:
        working_memory = proactive_queue.read_text(vault_dir / "_working-memory.md")[:8000]

    haystack_lines = [frontmost_app, *process_lines, working_memory]
    threads: list[dict[str, Any]] = []
    for thread_id, (label, _, terms) in ACTIVE_THREAD_TERMS.items():
        evidence = []
        for line in haystack_lines:
            lowered = line.lower()
            if any(term in lowered for term in terms):
                evidence.append(line[:180])
            if len(evidence) >= 3:
                break
        if evidence:
            threads.append(
                {
                    "id": thread_id,
                    "label": label,
                    "score": min(100, 55 + 15 * len(evidence)),
                    "evidence": evidence,
                }
            )
    threads.sort(key=lambda thread: int(thread.get("score", 0)), reverse=True)
    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "frontmost_app": frontmost_app,
        "threads": threads[:5],
        "process_sample_count": len(process_lines),
    }


def active_thread_for_item(
    item: dict[str, Any],
    active_context: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not active_context:
        return None
    item_text = " ".join(
        str(item.get(key, "")).lower() for key in ("title", "source", "reason", "next_action")
    )
    for thread in active_context.get("threads", []):
        thread_id = str(thread.get("id", ""))
        terms = ACTIVE_THREAD_TERMS.get(thread_id, ("", "", ()))[2]
        if any(term in item_text for term in terms):
            return thread
    return None


def apply_active_context(
    items: list[dict[str, Any]],
    active_context: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    annotated = []
    for item in items:
        normalized = dict(item)
        thread = active_thread_for_item(normalized, active_context)
        if thread:
            normalized["active_thread"] = thread.get("id")
            normalized["active_thread_label"] = thread.get("label")
            normalized["active_context_score"] = min(60, int(thread.get("score", 0)))
            evidence = (thread.get("evidence") or ["active process"])[0]
            normalized["why_shown_now"] = (
                f"Related to active work: {thread.get('label')} ({str(evidence)[:100]})"
            )
        else:
            normalized["active_context_score"] = 0
            normalized["why_shown_now"] = "Queued by priority and deadline state."
        annotated.append(normalized)
    return sorted(
        annotated,
        key=lambda item: (
            int(item.get("score", 0)) + int(item.get("active_context_score", 0)),
            int(item.get("score", 0)),
        ),
        reverse=True,
    )


def previous_item_ids(previous: dict[str, Any] | None) -> set[str]:
    if not previous:
        return set()
    return {
        str(item.get("id"))
        for item in previous.get("items", [])
        if item.get("id")
    }


def suppressed_by_ledger(item: dict[str, Any], ledger: dict[str, Any] | None) -> bool:
    if not ledger:
        return False
    action = (ledger.get("actions") or {}).get(str(item.get("id", "")))
    if not action:
        return False
    if action.get("status") not in {"abandoned", "done", "fired", "fire_requested", "modified"}:
        return False
    return action.get("fingerprint") == item_fingerprint(item)


def build_packet(
    health: dict[str, Any],
    items: list[dict[str, Any]],
    previous: dict[str, Any] | None,
    now: datetime | None = None,
    ledger: dict[str, Any] | None = None,
    active_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    prev_ids = previous_item_ids(previous)
    candidates = [normalize_item(item, prev_ids) for item in items]
    normalized_items = [item for item in candidates if not suppressed_by_ledger(item, ledger)]
    normalized_items = apply_active_context(normalized_items, active_context)
    suppressed_count = len(candidates) - len(normalized_items)
    current_ids = {item["id"] for item in normalized_items}
    removed = prev_ids - current_ids
    new = current_ids - prev_ids
    unchanged = current_ids & prev_ids
    approval_required = [
        item for item in normalized_items if item.get("approval") == "required"
    ]
    previous_health = (previous or {}).get("health", {}).get("status")
    health_status = health.get("status", "unknown")
    health_changed = previous_health is not None and previous_health != health_status

    if health_status == "fail":
        status = "health_failed"
    elif new or health_changed:
        status = "needs_decision"
    else:
        status = "silent"

    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "status": status,
        "health": health,
        "changes": {
            "new": len(new),
            "removed": len(removed),
            "unchanged": len(unchanged),
        },
        "approval_required_count": len(approval_required),
        "suppressed_count": suppressed_count,
        "active_context": active_context or {"threads": []},
        "items": normalized_items,
    }


def should_emit_silent(packet: dict[str, Any]) -> bool:
    return packet.get("status") == "silent"


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def read_ledger(path: Path = DEFAULT_LEDGER) -> dict[str, Any] | None:
    return read_json(path)


def write_packet(packet: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(packet, indent=2) + "\n")


def build_live_packet(
    vault_dir: Path = VAULT_DIR,
    memory_dir: Path = MEMORY_DIR,
    session_dir: Path = SESSION_DIR,
    output: Path = DEFAULT_OUTPUT,
    ledger_path: Path = DEFAULT_LEDGER,
    limit: int = 8,
) -> dict[str, Any]:
    previous = read_json(output)
    ledger = read_ledger(ledger_path)
    health = healthcheck.build_report(vault_dir, memory_dir, session_dir)
    working_memory = proactive_queue.read_text(vault_dir / "_working-memory.md")
    command_center = proactive_queue.read_text(memory_dir / "command-center.md")
    parked_convos = proactive_queue.read_text(vault_dir / "tool.claude-parked-convos.md")
    items = proactive_queue.build_queue(
        working_memory=working_memory,
        command_center=command_center,
        parked_convos=parked_convos,
        limit=limit,
    )
    active_context = infer_active_context(vault_dir=vault_dir)
    return build_packet(
        health=health,
        items=items,
        previous=previous,
        ledger=ledger,
        active_context=active_context,
    )


def render_markdown(packet: dict[str, Any]) -> str:
    lines = [
        f"# Decision Packet ({packet['status']})",
        "",
        f"- Generated: {packet['generated_at']}",
        f"- Health: {packet['health'].get('status', 'unknown')}",
        (
            f"- Changes: {packet['changes']['new']} new, "
            f"{packet['changes']['unchanged']} carried, "
            f"{packet['changes']['removed']} removed"
        ),
        f"- Approval required: {packet['approval_required_count']}",
        "",
    ]
    if not packet.get("items"):
        lines.append("No decision items.")
        return "\n".join(lines) + "\n"
    for idx, item in enumerate(packet["items"], 1):
        lines.append(
            f"{idx}. {item['title']} [{item['source']}, score {item['score']}, {item['state']}]"
        )
        lines.append(f"   - Why: {item['reason']}")
        lines.append(f"   - Next: {item['next_action']}")
        lines.append(f"   - Approval: {item['approval']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--vault", type=Path, default=VAULT_DIR)
    parser.add_argument("--memory-dir", type=Path, default=MEMORY_DIR)
    parser.add_argument("--session-dir", type=Path, default=SESSION_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--silent-if-unchanged", action="store_true")
    args = parser.parse_args()

    packet = build_live_packet(
        vault_dir=args.vault,
        memory_dir=args.memory_dir,
        session_dir=args.session_dir,
        output=args.output,
        ledger_path=args.ledger,
        limit=args.limit,
    )
    write_packet(packet, args.output)

    if args.silent_if_unchanged and should_emit_silent(packet):
        print("[SILENT]")
        return 0
    if args.as_json:
        json.dump(packet, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(packet))
    return 0


if __name__ == "__main__":
    sys.exit(main())
