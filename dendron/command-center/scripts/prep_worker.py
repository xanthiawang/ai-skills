#!/usr/bin/env python3
"""
Launch headless Codex workers for command-center actions that still need drafts.

The worker is intentionally conservative: it starts local Codex exec jobs for
`needs_draft` actions, tells them to write `final.md` only when the evidence is
enough, and records launches in a job ledger to avoid repeated background work.
It never sends, submits, signs, or mutates external systems.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

VAULT_DIR = Path("/Users/A.Y/Documents/Manual Library/Dendron/notes")
COMMAND_CENTER_DIR = VAULT_DIR / ".cache" / "command-center"
DEFAULT_PREPARED_ACTIONS = COMMAND_CENTER_DIR / "prepared-actions.json"
DEFAULT_JOB_LEDGER = COMMAND_CENTER_DIR / "prep-worker-jobs.json"
STALE_AFTER = timedelta(hours=6)


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


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def process_is_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def job_key(action: dict[str, Any]) -> str:
    return f"{action.get('id', '')}:{action.get('fingerprint', '')}"


def action_is_recently_launched(
    action: dict[str, Any],
    ledger: dict[str, Any],
    now: datetime | None = None,
) -> bool:
    now = now or utc_now()
    job = (ledger.get("jobs") or {}).get(job_key(action))
    if not isinstance(job, dict):
        return False
    if job.get("status") == "ready":
        return True
    launched_at = parse_time(job.get("launched_at"))
    if process_is_alive(job.get("pid")):
        return True
    return launched_at is not None and now - launched_at < STALE_AFTER


def text_artifact_exists(path: Path) -> bool:
    return path.exists() and bool(path.read_text(errors="ignore").strip())


def action_has_final(action: dict[str, Any]) -> bool:
    artifact_dir = Path(str(action.get("artifact_dir", "")))
    final_path = artifact_dir / "final.md"
    return text_artifact_exists(final_path)


def action_has_blocked(action: dict[str, Any]) -> bool:
    artifact_dir = Path(str(action.get("artifact_dir", "")))
    blocked_path = artifact_dir / "blocked.md"
    return text_artifact_exists(blocked_path)


def artifact_outcome(artifact_dir: Path) -> str:
    final_path = artifact_dir / "final.md"
    blocked_path = artifact_dir / "blocked.md"
    if text_artifact_exists(final_path):
        return "final"
    if text_artifact_exists(blocked_path):
        return "blocked"
    return "missing"


def codex_command_args(artifact_dir: Path, last_message_path: Path) -> list[str]:
    return [
        "codex",
        "exec",
        "--ignore-user-config",
        "--cd",
        str(artifact_dir),
        "--skip-git-repo-check",
        "--dangerously-bypass-approvals-and-sandbox",
        "--output-last-message",
        str(last_message_path),
        "-",
    ]


def write_supervisor_blocked(
    action: dict[str, Any],
    artifact_dir: Path,
    reason: str,
    log_path: Path,
) -> None:
    blocked_path = artifact_dir / "blocked.md"
    if text_artifact_exists(blocked_path) or text_artifact_exists(artifact_dir / "final.md"):
        return
    blocked_path.write_text(
        "\n".join(
            [
                f"# Blocked: {action.get('title', 'Untitled')}",
                "",
                "The background prep worker did not produce a final artifact.",
                "",
                "## Supervisor reason",
                "",
                reason,
                "",
                "## Available action context",
                "",
                f"- Source: {action.get('source', 'unknown')}",
                f"- Reason: {action.get('reason', 'queued')}",
                f"- Next action: {action.get('next_action', 'review')}",
                f"- Worker log: {log_path}",
                "",
                "## Status",
                "",
                "- No external side effects were taken by the supervisor.",
                "- Albert needs to open this artifact or run a longer/manual prep pass.",
                "",
            ]
        )
    )


def action_has_terminal_artifact(action: dict[str, Any]) -> bool:
    artifact_dir = Path(str(action.get("artifact_dir", "")))
    final_path = artifact_dir / "final.md"
    blocked_path = artifact_dir / "blocked.md"
    return text_artifact_exists(final_path) or text_artifact_exists(blocked_path)


def select_actions(
    prepared_packet: dict[str, Any],
    ledger: dict[str, Any],
    limit: int,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    selected = []
    for action in prepared_packet.get("actions", []):
        if action.get("status") != "needs_draft":
            continue
        if action_has_terminal_artifact(action):
            continue
        if action_is_recently_launched(action, ledger, now=now):
            continue
        selected.append(action)
        if len(selected) >= limit:
            break
    return selected


def build_worker_prompt(action: dict[str, Any]) -> str:
    artifact_dir = Path(str(action.get("artifact_dir", "")))
    final_path = artifact_dir / "final.md"
    blocked_path = artifact_dir / "blocked.md"
    return "\n".join(
        [
            "You are a background command-center preparation worker.",
            "",
            f"Artifact directory: {artifact_dir}",
            f"Action title: {action.get('title', 'Untitled')}",
            f"Start with: {action.get('prompt_path') or artifact_dir / 'codex_prompt.md'}",
            "",
            "Goal:",
            "- First read codex_prompt.md, brief.md, evidence.md, risk.md, draft.md, and fire_plan.json if they exist.",
            f"- Prepare the action as far as possible before Albert reviews it.",
            f"- Only write final.md at {final_path} if you can produce a concrete, non-empty final artifact from real evidence.",
            f"- If evidence is insufficient, write {blocked_path} explaining exactly what is missing and do not create final.md.",
            "",
            "Approval boundary:",
            "- Do not send, submit, sign, schedule, delete, purchase, or mutate external systems.",
            "- Do not fabricate missing evidence, recipients, attachments, dates, or decisions.",
            "- Keep the final artifact ready for Albert's explicit final approval.",
            "",
            "Required output:",
            "- Write or update notes inside the artifact directory only.",
            "- You must create exactly one of final.md or blocked.md before exiting.",
            "- Only write final.md when the action is genuinely ready for final review.",
            "- Include a short risk/assumption section in final.md.",
            "",
        ]
    )


def launch_worker(
    action: dict[str, Any],
    now: datetime | None = None,
    wait_seconds: int = 0,
) -> dict[str, Any]:
    now = now or utc_now()
    artifact_dir = Path(str(action.get("artifact_dir", "")))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    prompt = build_worker_prompt(action)
    prompt_path = artifact_dir / "prep_worker_prompt.md"
    log_path = artifact_dir / "prep_worker.log"
    last_message_path = artifact_dir / "prep_worker_last_message.md"
    prompt_path.write_text(prompt)
    with log_path.open("ab") as log_file, prompt_path.open("rb") as prompt_file:
        process = subprocess.Popen(
            codex_command_args(artifact_dir, last_message_path),
            stdin=prompt_file,
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
        )
        job_status = "launched"
        returncode = None
        if wait_seconds > 0:
            try:
                returncode = process.wait(timeout=wait_seconds)
                outcome = artifact_outcome(artifact_dir)
                if outcome == "missing":
                    write_supervisor_blocked(
                        action,
                        artifact_dir,
                        "Codex exited without creating final.md or blocked.md.",
                        log_path,
                    )
                    outcome = artifact_outcome(artifact_dir)
                job_status = "completed" if outcome in {"final", "blocked"} else "exited_without_artifact"
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    returncode = process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    returncode = process.wait(timeout=5)
                write_supervisor_blocked(
                    action,
                    artifact_dir,
                    f"Codex did not finish within {wait_seconds} seconds, so the supervisor stopped it.",
                    log_path,
                )
                outcome = artifact_outcome(artifact_dir)
                job_status = "completed" if outcome in {"final", "blocked"} else "timed_out_without_artifact"
        else:
            outcome = "running"
    result = {
        "action_id": action.get("id"),
        "fingerprint": action.get("fingerprint"),
        "status": job_status,
        "pid": process.pid,
        "launched_at": now.isoformat(timespec="seconds"),
        "artifact_dir": str(artifact_dir),
        "prompt_path": str(prompt_path),
        "log_path": str(log_path),
        "last_message_path": str(last_message_path),
        "outcome": outcome,
    }
    if returncode is not None:
        result["returncode"] = returncode
        result["completed_at"] = utc_now().isoformat(timespec="seconds")
    return result


def tick(
    prepared_path: Path = DEFAULT_PREPARED_ACTIONS,
    ledger_path: Path = DEFAULT_JOB_LEDGER,
    limit: int = 1,
    dry_run: bool = False,
    wait_seconds: int = 0,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or utc_now()
    prepared_packet = read_json(prepared_path, {"actions": []})
    ledger = read_json(ledger_path, {"jobs": {}})
    jobs = ledger.setdefault("jobs", {})
    selected = select_actions(prepared_packet, ledger, limit=limit, now=now)
    launched = []
    errors = []
    if not dry_run:
        for action in selected:
            try:
                job = launch_worker(action, now=now, wait_seconds=wait_seconds)
                jobs[job_key(action)] = job
                launched.append(job)
            except Exception as exc:
                error = {
                    "action_id": action.get("id"),
                    "fingerprint": action.get("fingerprint"),
                    "status": "failed",
                    "error": str(exc),
                    "updated_at": now.isoformat(timespec="seconds"),
                }
                jobs[job_key(action)] = error
                errors.append(error)
        write_json(ledger_path, ledger)
    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "dry_run": dry_run,
        "candidate_count": len(selected),
        "candidates": [
            {
                "id": action.get("id"),
                "title": action.get("title"),
                "artifact_dir": action.get("artifact_dir"),
            }
            for action in selected
        ],
        "launched_count": len(launched),
        "launched": launched,
        "errors": errors,
        "ledger_path": str(ledger_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--prepared-actions", type=Path, default=DEFAULT_PREPARED_ACTIONS)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_JOB_LEDGER)
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--wait-seconds", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    result = tick(
        prepared_path=args.prepared_actions,
        ledger_path=args.ledger,
        limit=max(0, args.limit),
        dry_run=args.dry_run,
        wait_seconds=max(0, args.wait_seconds),
    )
    if args.as_json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    elif not args.quiet:
        print(
            "prep worker: "
            f"{result['candidate_count']} candidates / "
            f"{result['launched_count']} launched"
        )
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
