#!/usr/bin/env python3
"""
Prepare command-center actions before Albert approves the final fire step.

This script consumes decision packets, applies a conservative classifier, writes
ready-to-review artifacts, and keeps an action ledger for duplicate suppression.
It never sends email, submits forms, edits calendars, or performs external side
effects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VAULT_DIR = Path("/Users/A.Y/Documents/Manual Library/Dendron/notes")
COMMAND_CENTER_DIR = VAULT_DIR / ".cache" / "command-center"
DEFAULT_DECISION_PACKET = COMMAND_CENTER_DIR / "decision-packets.json"
DEFAULT_OUTPUT_DIR = COMMAND_CENTER_DIR / "prepared-actions"
DEFAULT_LEDGER = COMMAND_CENTER_DIR / "action-ledger.json"
DEFAULT_SUMMARY = COMMAND_CENTER_DIR / "prepared-actions.json"
FINAL_ARTIFACT = "final.md"
BLOCKED_ARTIFACT = "blocked.md"

CONCRETE_TERMS = (
    "submit",
    "reply",
    "respond",
    "send",
    "verify submission",
    "formal reply",
    "sign",
    "file",
    "confirm",
    "accept",
    "decline",
    "negotiate",
)
VAGUE_TERMS = (
    "open the source thread",
    "resolve the next concrete step",
    "review",
)
SUPPRESSING_STATUSES = {"abandoned", "done", "fired", "fire_requested", "modified"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def item_fingerprint(item: dict[str, Any]) -> str:
    raw = "\n".join(
        str(item.get(key, "")) for key in ("title", "source", "reason", "next_action")
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug[:80] or "action"


def ledger_entry(ledger: dict[str, Any], action_id: str) -> dict[str, Any] | None:
    entry = (ledger.get("actions") or {}).get(action_id)
    return entry if isinstance(entry, dict) else None


def classify_item(item: dict[str, Any], ledger: dict[str, Any]) -> tuple[str, str]:
    action_id = str(item.get("id", ""))
    fingerprint = item_fingerprint(item)
    entry = ledger_entry(ledger, action_id)
    if entry and entry.get("status") in SUPPRESSING_STATUSES and entry.get("fingerprint") == fingerprint:
        return str(entry.get("status")), "suppressed by action ledger"

    if item.get("approval") != "required":
        return "skipped", "prepare_only item"

    text = " ".join(
        str(item.get(key, "")).lower() for key in ("title", "source", "reason", "next_action")
    )
    if any(term in text for term in VAGUE_TERMS) and "thread:" not in text:
        return "skipped", "vague next action without source evidence"
    if not any(term in text for term in CONCRETE_TERMS):
        return "skipped", "no concrete fireable action verb"
    if not (str(item.get("source", "")).startswith("email.") or "thread:" in text):
        return "skipped", "no email/source thread evidence"
    return "needs_draft", "requires Codex completion before Albert review"


def artifact_dir_for(output_dir: Path, item: dict[str, Any]) -> Path:
    action_id = str(item.get("id", "action"))
    title = safe_slug(str(item.get("title", "action")))
    return output_dir / f"{action_id}-{title}"


def render_brief(item: dict[str, Any], prepared_at: str) -> str:
    return "\n".join(
        [
            f"# Prepared Action: {item.get('title', 'Untitled')}",
            "",
            f"- Prepared at: {prepared_at}",
            f"- Source: {item.get('source', 'unknown')}",
            f"- Score: {item.get('score', 0)}",
            f"- Approval boundary: {item.get('approval', 'required')}",
            f"- Reason: {item.get('reason', 'queued')}",
            f"- Next action: {item.get('next_action', 'review')}",
            "",
            "## Status",
            "",
            "Prepared only. No external action has been taken.",
            "",
        ]
    )


def render_skip_brief(item: dict[str, Any], prepared_at: str, skip_reason: str) -> str:
    return "\n".join(
        [
            f"# Skipped Prepared Action: {item.get('title', 'Untitled')}",
            "",
            f"- Prepared at: {prepared_at}",
            f"- Source: {item.get('source', 'unknown')}",
            f"- Score: {item.get('score', 0)}",
            f"- Reason skipped: {skip_reason}",
            f"- Queue reason: {item.get('reason', 'queued')}",
            f"- Next action: {item.get('next_action', 'review')}",
            "",
            "## Status",
            "",
            "Skipped. The classifier did not find a concrete, fireable action with enough source evidence.",
            "",
        ]
    )


def render_draft(item: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# Draft Work Order: {item.get('title', 'Untitled')}",
            "",
            "This is not a finished draft. Do not present it to Albert as ready for review.",
            "",
            "## Proposed action",
            "",
            str(item.get("next_action", "review")),
            "",
            "## Completion bar",
            "",
            "- Open and read the source evidence/thread.",
            "- Produce a concrete, non-empty final artifact.",
            "- Verify the final artifact matches Albert's voice and the source evidence.",
            "- Keep external side effects blocked until Albert explicitly approves.",
            "",
        ]
    )


def completed_final_artifact(artifact_dir: Path) -> bool:
    final_path = artifact_dir / FINAL_ARTIFACT
    if not final_path.exists():
        return False
    text = final_path.read_text(errors="ignore").strip()
    if len(text) < 40:
        return False
    lowered = text.lower()
    blocked_terms = (
        "not a finished draft",
        "todo",
        "tbd",
        "placeholder",
        "needs source evidence",
    )
    return not any(term in lowered for term in blocked_terms)


def completed_blocked_artifact(artifact_dir: Path) -> bool:
    blocked_path = artifact_dir / BLOCKED_ARTIFACT
    if not blocked_path.exists():
        return False
    return len(blocked_path.read_text(errors="ignore").strip()) >= 20


def render_evidence(item: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Evidence",
            "",
            f"- Item id: {item.get('id', '')}",
            f"- Fingerprint: {item_fingerprint(item)}",
            f"- Source: {item.get('source', 'unknown')}",
            f"- Reason: {item.get('reason', 'queued')}",
            f"- Next action: {item.get('next_action', 'review')}",
            "",
        ]
    )


def render_risk(item: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Risk Review",
            "",
            "- External side effects are blocked in v1.",
            "- Albert must approve before any send, submit, sign, calendar edit, or form action.",
            f"- Source class: {item.get('source', 'unknown')}",
            f"- Approval class: {item.get('approval', 'required')}",
            "",
        ]
    )


def render_codex_prompt(item: dict[str, Any], artifact_dir: Path) -> str:
    return "\n".join(
        [
            "You are working from a prepared command-center action packet.",
            "",
            f"Artifact directory: {artifact_dir}",
            f"Title: {item.get('title', 'Untitled')}",
            f"Source: {item.get('source', 'unknown')}",
            f"Reason: {item.get('reason', 'queued')}",
            f"Next action: {item.get('next_action', 'review')}",
            "",
            "Read brief.md, evidence.md, risk.md, draft.md, and fire_plan.json.",
            "Prepare the final artifact for Albert. Do not send, submit, sign, or alter",
            "external systems unless Albert explicitly approves that final action in this session.",
            "",
        ]
    )


def write_text_if_missing(path: Path, text: str) -> None:
    if not path.exists():
        path.write_text(text)


def write_artifacts(
    item: dict[str, Any],
    artifact_dir: Path,
    prepared_at: str,
    status: str,
) -> dict[str, str]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "brief_path": artifact_dir / "brief.md",
        "draft_path": artifact_dir / "draft.md",
        "evidence_path": artifact_dir / "evidence.md",
        "risk_path": artifact_dir / "risk.md",
        "prompt_path": artifact_dir / "codex_prompt.md",
        "fire_plan_path": artifact_dir / "fire_plan.json",
        "final_path": artifact_dir / FINAL_ARTIFACT,
        "blocked_path": artifact_dir / BLOCKED_ARTIFACT,
    }
    paths["brief_path"].write_text(render_brief(item, prepared_at))
    write_text_if_missing(paths["draft_path"], render_draft(item))
    paths["evidence_path"].write_text(render_evidence(item))
    paths["risk_path"].write_text(render_risk(item))
    paths["prompt_path"].write_text(render_codex_prompt(item, artifact_dir))
    final_exists = paths["final_path"].exists()
    blocked_exists = paths["blocked_path"].exists()
    if status == "ready":
        draft_status = "complete"
    elif status == "blocked":
        draft_status = "blocked"
    else:
        draft_status = "needs_codex_completion"
    write_json(
        paths["fire_plan_path"],
        {
            "action_id": item.get("id", ""),
            "title": item.get("title", ""),
            "status": status,
            "operation": "finish_draft_then_manual_fire_after_review",
            "draft_status": draft_status,
            "external_side_effect": "blocked_until_explicit_approval",
            "artifact_dir": str(artifact_dir),
            "final_path": str(paths["final_path"]) if final_exists else "",
            "blocked_path": str(paths["blocked_path"]) if blocked_exists else "",
        },
    )
    result = {
        name: str(path)
        for name, path in paths.items()
        if name not in {"final_path", "blocked_path"}
        or (name == "final_path" and final_exists)
        or (name == "blocked_path" and blocked_exists)
    }
    return result


def write_skip_artifacts(
    item: dict[str, Any],
    artifact_dir: Path,
    prepared_at: str,
    skip_reason: str,
) -> dict[str, str]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    brief_path = artifact_dir / "brief.md"
    evidence_path = artifact_dir / "evidence.md"
    risk_path = artifact_dir / "risk.md"
    brief_path.write_text(render_skip_brief(item, prepared_at, skip_reason))
    evidence_path.write_text(render_evidence(item))
    risk_path.write_text(render_risk(item))
    return {
        "brief_path": str(brief_path),
        "evidence_path": str(evidence_path),
        "risk_path": str(risk_path),
    }


def action_from_item(
    item: dict[str, Any],
    output_dir: Path,
    ledger: dict[str, Any],
    prepared_at: str,
) -> dict[str, Any]:
    action_id = str(item.get("id", ""))
    fingerprint = item_fingerprint(item)
    status, skip_reason = classify_item(item, ledger)
    artifact_dir = artifact_dir_for(output_dir, item)
    if status == "needs_draft" and completed_final_artifact(artifact_dir):
        status = "ready"
        skip_reason = ""
    elif status == "needs_draft" and completed_blocked_artifact(artifact_dir):
        status = "blocked"
        skip_reason = "blocked by prep worker"
    action: dict[str, Any] = {
        "id": action_id,
        "decision_item_id": action_id,
        "fingerprint": fingerprint,
        "status": status,
        "title": item.get("title", "Untitled"),
        "source": item.get("source", "unknown"),
        "reason": item.get("reason", "queued"),
        "next_action": item.get("next_action", "review"),
        "artifact_dir": str(artifact_dir),
        "prepared_at": prepared_at,
        "risk": "approval_required",
        "confidence": "medium",
    }
    if status not in {"ready", "needs_draft", "blocked"}:
        action["skip_reason"] = skip_reason
        action.update(write_skip_artifacts(item, artifact_dir, prepared_at, skip_reason))
        return action
    if status in {"needs_draft", "blocked"}:
        action["skip_reason"] = skip_reason
    action.update(write_artifacts(item, artifact_dir, prepared_at, status))
    return action


def notification_events(
    actions: list[dict[str, Any]],
    previous_summary: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    previous_actions = {
        str(action.get("id", "")): action
        for action in (previous_summary or {}).get("actions", [])
        if action.get("id")
    }
    events = []
    for action in actions:
        previous = previous_actions.get(str(action.get("id", "")))
        previous_status = previous.get("status") if previous else None
        same_fingerprint = previous and previous.get("fingerprint") == action.get("fingerprint")
        if action.get("status") == "ready" and (
            previous_status != "ready" or not same_fingerprint
        ):
            events.append(
                {
                    "kind": "prepared_action_ready",
                    "action_id": action.get("id"),
                    "title": action.get("title"),
                    "status": action.get("status"),
                    "previous_status": previous_status,
                    "artifact_dir": action.get("artifact_dir"),
                    "message": "Prepared action is ready for Albert's final decision.",
                }
            )
        if action.get("status") == "blocked" and (
            previous_status != "blocked" or not same_fingerprint
        ):
            events.append(
                {
                    "kind": "prepared_action_blocked",
                    "action_id": action.get("id"),
                    "title": action.get("title"),
                    "status": action.get("status"),
                    "previous_status": previous_status,
                    "artifact_dir": action.get("artifact_dir"),
                    "message": "Prepared action needs missing human/source evidence.",
                }
            )
    return events


def build_prepared_actions(
    decision_packet: dict[str, Any],
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    ledger_path: Path = DEFAULT_LEDGER,
    summary_path: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or utc_now()
    prepared_at = now.isoformat(timespec="seconds")
    ledger = read_json(ledger_path, {"actions": {}})
    previous_summary = read_json(summary_path or DEFAULT_SUMMARY, {})
    actions = [
        action_from_item(item, output_dir=output_dir, ledger=ledger, prepared_at=prepared_at)
        for item in decision_packet.get("items", [])
    ]
    packet = {
        "generated_at": prepared_at,
        "decision_packet_generated_at": decision_packet.get("generated_at"),
        "ledger_path": str(ledger_path),
        "actions": actions,
        "ready_count": sum(1 for action in actions if action.get("status") == "ready"),
        "blocked_count": sum(1 for action in actions if action.get("status") == "blocked"),
        "needs_draft_count": sum(1 for action in actions if action.get("status") == "needs_draft"),
        "skipped_count": sum(1 for action in actions if action.get("status") == "skipped"),
        "notification_events": notification_events(actions, previous_summary),
    }
    write_json(summary_path or DEFAULT_SUMMARY, packet)
    return packet


def mark_action(
    action_id: str,
    status: str,
    ledger_path: Path = DEFAULT_LEDGER,
    fingerprint: str | None = None,
    reason: str = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or utc_now()
    ledger = read_json(ledger_path, {"actions": {}})
    actions = ledger.setdefault("actions", {})
    current = actions.get(action_id, {})
    if fingerprint is None:
        fingerprint = current.get("fingerprint", "")
    actions[action_id] = {
        **current,
        "status": status,
        "fingerprint": fingerprint,
        "reason": reason,
        "updated_at": now.isoformat(timespec="seconds"),
    }
    write_json(ledger_path, ledger)
    return ledger


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--decision-packet", type=Path, default=DEFAULT_DECISION_PACKET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--mark-id")
    parser.add_argument("--mark-status", choices=["abandoned", "done", "fired", "fire_requested", "modified"])
    parser.add_argument("--fingerprint")
    parser.add_argument("--reason", default="")
    args = parser.parse_args()

    if args.mark_id:
        if not args.mark_status:
            parser.error("--mark-status is required with --mark-id")
        ledger = mark_action(
            action_id=args.mark_id,
            status=args.mark_status,
            ledger_path=args.ledger,
            fingerprint=args.fingerprint,
            reason=args.reason,
        )
        if args.as_json:
            json.dump(ledger, sys.stdout, indent=2)
            sys.stdout.write("\n")
        return 0

    decision_packet = read_json(args.decision_packet, {"items": []})
    packet = build_prepared_actions(
        decision_packet=decision_packet,
        output_dir=args.output_dir,
        ledger_path=args.ledger,
        summary_path=args.summary,
    )
    if args.as_json:
        json.dump(packet, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(
            "prepared actions: "
            f"{packet['ready_count']} ready / "
            f"{packet['blocked_count']} blocked / "
            f"{packet['needs_draft_count']} needs_draft / "
            f"{packet['skipped_count']} skipped"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
