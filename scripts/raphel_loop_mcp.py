#!/usr/bin/env python3
"""Dependency-free MCP server for durable Cursor Agent loops."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import signal
import subprocess
import sys
import textwrap
import time
import uuid
from pathlib import Path
from typing import Any


SERVER_NAME = "raphel-loop"
PROTOCOL_VERSION = "2025-06-18"
DEFAULT_MODEL = "gpt-5.5-extra-high"
STATE_DIR = Path(
    os.environ.get(
        "RAPHEL_LOOP_STATE_DIR",
        str(Path.home() / ".local" / "state" / "raphel-loop" / "jobs"),
    )
)
FORBIDDEN_MODEL_PARTS = ("max",)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def validate_model(model: str, allow_costly_model: bool = False) -> None:
    lowered = model.lower()
    if not allow_costly_model and any(part in lowered for part in FORBIDDEN_MODEL_PARTS):
        raise ValueError(
            "Refusing Cursor MAX model variant. Use gpt-5.5-extra-high by default, "
            "or pass allow_costly_model=true only after Albert explicitly approves."
        )


def validate_workspace(workspace: str) -> Path:
    path = Path(workspace).expanduser().resolve()
    if not path.exists():
        raise ValueError(f"Workspace does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"Workspace is not a directory: {path}")
    return path


def job_paths(job_id: str) -> dict[str, Path]:
    job_dir = STATE_DIR / job_id
    return {
        "dir": job_dir,
        "state": job_dir / "state.json",
        "runner_log": job_dir / "runner.log",
        "agent_log": job_dir / "cursor-agent.jsonl",
        "stop": job_dir / "STOP",
    }


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)


def tail_file(path: Path, limit: int = 6000) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()
    return data[-limit:].decode("utf-8", errors="replace")


def parse_status(output: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return "continue"
    match = re.fullmatch(r"RAPHEL_STATUS:\s*(done|continue)", lines[-1], re.IGNORECASE)
    return match.group(1).lower() if match else "continue"


def pid_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def active_job_for_workspace(workspace: Path) -> str | None:
    ensure_state_dir()
    for state_path in STATE_DIR.glob("*/state.json"):
        try:
            state = read_json(state_path)
        except Exception:
            continue
        if Path(str(state.get("workspace", ""))).resolve() != workspace:
            continue
        if state.get("status") not in {"starting", "running"}:
            continue
        pid = state.get("runner_pid")
        if isinstance(pid, int) and not pid_is_running(pid):
            state["status"] = "failed"
            state["error"] = "runner process is no longer alive"
            state["updated_at"] = utc_now()
            write_json_atomic(state_path, state)
            continue
        return str(state.get("job_id"))
    return None


def make_prompt(task: str, max_iterations: int) -> str:
    return textwrap.dedent(
        f"""
    [TASK]
    {task}

    [RAPHEL LOOP CONTRACT]
    You are the only Cursor Agent invocation for this raphel-loop job. Do not
    expect to be called again. Run the loop internally inside this single
    invocation:

    1. Inspect the workspace and task requirements.
    2. Work on the next concrete step.
    3. Verify with the real commands/files/tests needed for this task.
    4. If verification shows more work remains, continue from step 2.
    5. Stop only when the task is genuinely complete, blocked by a concrete
       external condition, or you have completed {max_iterations} internal
       work/verify cycles.

    Do not stop midway just because the task is long. If blocked, explain the
    blocking condition and still end with RAPHEL_STATUS: continue.

    Before your final response, verify the actual files/tests/commands needed
    for the task. Then call the `raphel_loop_checkpoint` MCP tool. If the tool
    returns RAPHEL_DECISION: continue_work, do not stop; continue the next
    concrete step and call the checkpoint again before trying to stop.

    End with exactly one marker line:
    RAPHEL_STATUS: done
    if the task is complete and verified, or:
    RAPHEL_STATUS: continue
    if more work remains.

    If continuing, include a concise RAPHEL_NEXT section with the next concrete
    step. Do not use MAX models.
    """
    ).strip()


def run_cursor_once(state: dict[str, Any], prompt: str, paths: dict[str, Path]) -> str:
    cmd = [
        "cursor-agent",
        "-p",
        "--output-format",
        "text",
        "--model",
        state["model"],
        "--force",
        "--trust",
        prompt,
    ]
    timeout_sec = int(state["cursor_timeout_sec"])
    started = utc_now()
    proc = subprocess.run(
        cmd,
        cwd=state["workspace"],
        text=True,
        capture_output=True,
        timeout=timeout_sec,
        check=False,
    )
    output = proc.stdout
    if proc.stderr:
        output += "\n[stderr]\n" + proc.stderr
    record = {
        "iteration": state["iteration"],
        "started_at": started,
        "finished_at": utc_now(),
        "returncode": proc.returncode,
        "output": output,
    }
    with paths["agent_log"].open("a", encoding="utf-8") as handle:
        json.dump(record, handle, sort_keys=True)
        handle.write("\n")
    return output


def run_job(job_id: str) -> int:
    paths = job_paths(job_id)
    try:
        state = read_json(paths["state"])
        state["status"] = "running"
        state["runner_pid"] = os.getpid()
        state["started_at"] = state.get("started_at") or utc_now()
        write_json_atomic(paths["state"], state)

        if paths["stop"].exists():
            state["status"] = "stopped"
            state["finished_at"] = utc_now()
            write_json_atomic(paths["state"], state)
            return 0

        state["iteration"] = 1
        state["updated_at"] = utc_now()
        write_json_atomic(paths["state"], state)
        prompt = make_prompt(state["task"], int(state["max_iterations"]))

        try:
            output = run_cursor_once(state, prompt, paths)
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or "") + "\n[timeout]\n" + str(exc)
            state["status"] = "failed"
            state["error"] = f"cursor-agent timed out after {state['cursor_timeout_sec']} seconds"
            state["last_output_tail"] = output[-6000:]
            state["finished_at"] = utc_now()
            write_json_atomic(paths["state"], state)
            return 1

        state["last_output_tail"] = output[-6000:]
        state["last_status_marker"] = parse_status(output)
        state["updated_at"] = utc_now()
        if state["last_status_marker"] == "done":
            state["status"] = "done"
            state["finished_at"] = utc_now()
            write_json_atomic(paths["state"], state)
            return 0

        state["status"] = "needs_followup"
        state["finished_at"] = utc_now()
        write_json_atomic(paths["state"], state)
        return 2
    except Exception as exc:
        paths["dir"].mkdir(parents=True, exist_ok=True)
        with paths["runner_log"].open("a", encoding="utf-8") as handle:
            handle.write(f"{utc_now()} runner failure: {exc}\n")
        if paths["state"].exists():
            state = read_json(paths["state"])
            state["status"] = "failed"
            state["error"] = str(exc)
            state["finished_at"] = utc_now()
            write_json_atomic(paths["state"], state)
        return 1


def start_cursor_loop(args: dict[str, Any]) -> dict[str, Any]:
    task = str(args.get("task", "")).strip()
    if not task:
        raise ValueError("task is required")
    workspace = validate_workspace(str(args.get("workspace") or os.getcwd()))
    model = str(args.get("model") or DEFAULT_MODEL)
    allow_costly_model = bool(args.get("allow_costly_model", False))
    validate_model(model, allow_costly_model)
    allow_concurrent = bool(args.get("allow_concurrent", False))
    active_job = active_job_for_workspace(workspace)
    if active_job and not allow_concurrent:
        raise ValueError(
            f"Workspace already has active raphel-loop job {active_job}. "
            "Pass allow_concurrent=true only if the jobs cannot edit the same files."
        )

    max_iterations = int(args.get("max_iterations", 12))
    if max_iterations < 1 or max_iterations > 100:
        raise ValueError("max_iterations must be between 1 and 100")
    cursor_timeout_sec = int(args.get("cursor_timeout_sec", 7200))
    if cursor_timeout_sec < 60:
        raise ValueError("cursor_timeout_sec must be at least 60")

    ensure_state_dir()
    job_id = f"{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    paths = job_paths(job_id)
    paths["dir"].mkdir(parents=True, exist_ok=False)
    state = {
        "job_id": job_id,
        "task": task,
        "workspace": str(workspace),
        "model": model,
        "max_iterations": max_iterations,
        "cursor_timeout_sec": cursor_timeout_sec,
        "iteration": 0,
        "status": "starting",
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "agent_log": str(paths["agent_log"]),
        "runner_log": str(paths["runner_log"]),
        "allow_concurrent": allow_concurrent,
    }
    write_json_atomic(paths["state"], state)

    with paths["runner_log"].open("a", encoding="utf-8") as log:
        proc = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--run-job", job_id],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    state["runner_pid"] = proc.pid
    state["status"] = "running"
    state["updated_at"] = utc_now()
    write_json_atomic(paths["state"], state)
    return summarize_job(job_id, include_tail=False)


def summarize_job(job_id: str, include_tail: bool = True) -> dict[str, Any]:
    paths = job_paths(job_id)
    if not paths["state"].exists():
        raise ValueError(f"Unknown raphel-loop job: {job_id}")
    state = read_json(paths["state"])
    pid = state.get("runner_pid")
    if state.get("status") in {"starting", "running"} and isinstance(pid, int) and not pid_is_running(pid):
        state["status"] = "failed"
        state["error"] = "runner process is no longer alive"
        state["updated_at"] = utc_now()
        write_json_atomic(paths["state"], state)
    state["state_path"] = str(paths["state"])
    state["job_dir"] = str(paths["dir"])
    if include_tail:
        state["runner_log_tail"] = tail_file(paths["runner_log"])
        state["agent_log_tail"] = tail_file(paths["agent_log"])
    return state


def stop_job(job_id: str) -> dict[str, Any]:
    paths = job_paths(job_id)
    if not paths["state"].exists():
        raise ValueError(f"Unknown raphel-loop job: {job_id}")
    paths["stop"].write_text(utc_now() + "\n", encoding="utf-8")
    state = read_json(paths["state"])
    pid = state.get("runner_pid")
    if isinstance(pid, int) and state.get("status") == "running":
        try:
            os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except PermissionError:
            os.kill(pid, signal.SIGTERM)
    state["status"] = "stop_requested"
    state["updated_at"] = utc_now()
    write_json_atomic(paths["state"], state)
    return summarize_job(job_id)


def checkpoint_dir() -> Path:
    path = STATE_DIR / "_checkpoints"
    path.mkdir(parents=True, exist_ok=True)
    return path


def raphel_loop_checkpoint(args: dict[str, Any]) -> dict[str, Any]:
    status = str(args.get("status", "")).strip().lower()
    summary = str(args.get("summary", "")).strip()
    verification = str(args.get("verification", "")).strip()
    remaining_work = str(args.get("remaining_work", "")).strip()
    next_step = str(args.get("next_step", "")).strip()

    if status not in {"done", "continue", "blocked"}:
        raise ValueError("status must be one of: done, continue, blocked")
    if not summary:
        raise ValueError("summary is required")

    finish_allowed = status == "done" and bool(verification) and not remaining_work
    if finish_allowed:
        instruction = (
            "RAPHEL_DECISION: finish_allowed. You may now provide the final response. "
            "Keep it concise and include the verification that proves completion."
        )
    else:
        finish_allowed = False
        if status == "done" and not verification:
            reason = "You marked done without verification."
        elif status == "done" and remaining_work:
            reason = "You marked done while remaining_work is non-empty."
        elif status == "blocked":
            reason = "You reported a blocker; final response may only explain the concrete blocker."
        else:
            reason = "More work remains."
        instruction = (
            "RAPHEL_DECISION: continue_work. Do not stop yet. "
            f"{reason} Continue with the next concrete step: {next_step or remaining_work or 'inspect, implement, and verify the next unfinished item'}."
        )

    payload = {
        "created_at": utc_now(),
        "status": status,
        "summary": summary,
        "verification": verification,
        "remaining_work": remaining_work,
        "next_step": next_step,
        "finish_allowed": finish_allowed,
        "instruction": instruction,
    }
    path = checkpoint_dir() / f"{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}.json"
    write_json_atomic(path, payload)
    payload["checkpoint_path"] = str(path)
    return payload


TOOLS = [
    {
        "name": "raphel_loop_checkpoint",
        "description": "Call before Cursor Agent stops. Returns whether finishing is allowed or whether the agent must continue working.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["done", "continue", "blocked"],
                    "description": "Use done only when complete and verified; continue when more work remains; blocked only for concrete external blockers.",
                },
                "summary": {"type": "string"},
                "verification": {"type": "string"},
                "remaining_work": {"type": "string"},
                "next_step": {"type": "string"},
            },
            "required": ["status", "summary"],
        },
    },
    {
        "name": "start_cursor_loop",
        "description": "Start one Cursor Agent invocation with an internal raphel work/verify loop until RAPHEL_STATUS: done or follow-up is needed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string"},
                "workspace": {"type": "string"},
                "model": {"type": "string", "default": DEFAULT_MODEL},
                "max_iterations": {"type": "integer", "default": 12},
                "cursor_timeout_sec": {"type": "integer", "default": 7200},
                "allow_costly_model": {"type": "boolean", "default": False},
                "allow_concurrent": {"type": "boolean", "default": False},
            },
            "required": ["task"],
        },
    },
    {
        "name": "cursor_loop_status",
        "description": "Read status, logs, and the latest output tail for a raphel-loop job.",
        "inputSchema": {
            "type": "object",
            "properties": {"job_id": {"type": "string"}},
            "required": ["job_id"],
        },
    },
    {
        "name": "cursor_loop_stop",
        "description": "Request a raphel-loop job to stop.",
        "inputSchema": {
            "type": "object",
            "properties": {"job_id": {"type": "string"}},
            "required": ["job_id"],
        },
    },
]


def content_response(payload: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(payload, indent=2, sort_keys=True)}]}


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "raphel_loop_checkpoint":
        return content_response(raphel_loop_checkpoint(arguments))
    if name == "start_cursor_loop":
        return content_response(start_cursor_loop(arguments))
    if name == "cursor_loop_status":
        return content_response(summarize_job(str(arguments.get("job_id", ""))))
    if name == "cursor_loop_stop":
        return content_response(stop_job(str(arguments.get("job_id", ""))))
    raise ValueError(f"Unknown tool: {name}")


def read_message(framing: dict[str, Any]) -> dict[str, Any] | None:
    """Read one JSON-RPC message from stdin.

    Supports both stdio transports:
    - MCP spec: newline-delimited JSON (one compact JSON object per line). This
      is what real MCP clients (cursor-agent, Claude, the SDKs) send.
    - Legacy LSP-style ``Content-Length`` header framing (kept for backward
      compatibility with any caller that used the original hand-rolled framing).

    The framing is auto-detected from the first non-blank line and remembered in
    ``framing['mode']`` so responses are written back over the same transport.
    """
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        stripped = line.strip()
        if not stripped:
            # Blank line outside of a header block: ignore and keep reading.
            continue
        if stripped[:15].lower() == b"content-length:":
            framing["mode"] = "lsp"
            headers: dict[str, str] = {}
            key, _, value = line.decode("ascii", errors="replace").partition(":")
            headers[key.lower().strip()] = value.strip()
            while True:
                hline = sys.stdin.buffer.readline()
                if not hline or hline in (b"\r\n", b"\n"):
                    break
                k, _, v = hline.decode("ascii", errors="replace").partition(":")
                headers[k.lower().strip()] = v.strip()
            length = int(headers.get("content-length", "0"))
            if length <= 0:
                return None
            body = sys.stdin.buffer.read(length)
            return json.loads(body.decode("utf-8"))
        # Newline-delimited JSON: the line itself is a full message.
        if framing.get("mode") is None:
            framing["mode"] = "ndjson"
        try:
            return json.loads(stripped.decode("utf-8"))
        except json.JSONDecodeError:
            # Partial / non-JSON line; skip and keep reading.
            continue


def write_message(payload: dict[str, Any], framing: dict[str, Any]) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    if framing.get("mode") == "lsp":
        sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
        sys.stdout.buffer.write(body)
    else:
        # Default: newline-delimited JSON (MCP stdio transport).
        sys.stdout.buffer.write(body + b"\n")
    sys.stdout.buffer.flush()


def handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    msg_id = message.get("id")
    if msg_id is None:
        return None
    try:
        if method == "initialize":
            result = {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": "0.1.0"},
            }
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = message.get("params") or {}
            result = call_tool(str(params.get("name", "")), params.get("arguments") or {})
        elif method == "resources/list":
            result = {"resources": []}
        elif method == "prompts/list":
            result = {"prompts": []}
        elif method == "ping":
            result = {}
        else:
            raise ValueError(f"Unsupported method: {method}")
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32000, "message": str(exc)},
        }


def serve() -> int:
    ensure_state_dir()
    framing: dict[str, Any] = {"mode": None}
    while True:
        message = read_message(framing)
        if message is None:
            return 0
        response = handle_request(message)
        if response is not None:
            write_message(response, framing)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-job")
    parser.add_argument("--start")
    parser.add_argument("--workspace")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-iterations", type=int, default=12)
    parser.add_argument("--cursor-timeout-sec", type=int, default=7200)
    parser.add_argument("--allow-costly-model", action="store_true")
    parser.add_argument("--allow-concurrent", action="store_true")
    parser.add_argument("--status")
    parser.add_argument("--stop")
    args = parser.parse_args(argv)
    if args.run_job:
        return run_job(args.run_job)
    if args.start:
        payload = start_cursor_loop(
            {
                "task": args.start,
                "workspace": args.workspace or os.getcwd(),
                "model": args.model,
                "max_iterations": args.max_iterations,
                "cursor_timeout_sec": args.cursor_timeout_sec,
                "allow_costly_model": args.allow_costly_model,
                "allow_concurrent": args.allow_concurrent,
            }
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    if args.status:
        print(json.dumps(summarize_job(args.status), indent=2, sort_keys=True))
        return 0
    if args.stop:
        print(json.dumps(stop_job(args.stop), indent=2, sort_keys=True))
        return 0
    return serve()


if __name__ == "__main__":
    raise SystemExit(main())
