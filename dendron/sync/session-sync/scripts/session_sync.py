#!/usr/bin/env python3
"""Emit sync manifests from high-signal Claude/Codex transcript events.

The script is intentionally deterministic. It does not ask an LLM to summarize
or infer missing facts; it extracts short evidence snippets from user-typed
messages and local file-touch metadata, then leaves routing confidence visible
for the vault-updater.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

HOME = Path.home()
DEFAULT_VAULT = HOME / "Documents/Manual Library/Dendron/notes"
CLAUDE_DIR = HOME / ".claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron-notes"
CODEX_DIR = HOME / ".codex/sessions"
AI_SKILLS_DIR = HOME / "programs/ai-skills"
SESSION_INDEX = AI_SKILLS_DIR / "dendron/command-center/scripts/session_index.py"

NOISE_RE = re.compile(
    r"^\s*("
    r"Base directory for this skill|"
    r"Based on these recent user messages|"
    r"<EXTREMELY_IMPORTANT>|"
    r"<task-notification>|"
    r"<system-reminder>|"
    r"<local-command-stdout>|"
    r"\[Request interrupted|"
    r"Caveat: The messages"
    r")",
    re.IGNORECASE,
)

CORRECTION_RE = re.compile(
    r"^\s*(no[,\.\s]|nope|actually\b|wrong\b|that's not|that is not|"
    r"instead\b|don't\b|stop\b|undo\b|revert\b|why did you)",
    re.IGNORECASE,
)

RECORD_RE = re.compile(
    r"\b(record this|remember this|save this|update working memory|"
    r"add to working memory|carry forward|park this|log this)\b",
    re.IGNORECASE,
)

AGENT_SYSTEM_RE = re.compile(
    r"\b(codex|claude|cc|agent|agents?\.md|command center|command-center|"
    r"dendron|sync|memory|working memory|transcript|session|notes?)\b",
    re.IGNORECASE,
)

DECISION_RE = re.compile(
    r"\b(decid(e|ed|ing)|decision|go with|use .+ instead|should be done|"
    r"more reliable|default to|enforced|implement it)\b",
    re.IGNORECASE,
)

FOLLOWUP_RE = re.compile(
    r"\b(todo|follow up|next step|need to|needs to|should|please implement|"
    r"fix|blocked|awaiting)\b",
    re.IGNORECASE,
)

PATH_RE = re.compile(r"(/[A-Za-z0-9_ .@%+=:,~/-]{8,})")


@dataclass
class SessionCandidate:
    source: str
    session_id: str
    path: Path
    cwd: str | None
    mtime: float
    size: int


@dataclass
class Signal:
    note: str
    section: str
    content: str
    confidence: float
    evidence: list[dict[str, str]]
    create_title: str | None = None
    create_desc: str | None = None


@dataclass
class ParsedSession:
    candidate: SessionCandidate
    user_messages: list[tuple[str, str]] = field(default_factory=list)
    assistant_messages: list[tuple[str, str]] = field(default_factory=list)
    touched_files: set[str] = field(default_factory=set)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_from_mtime(mtime: float) -> str:
    return datetime.fromtimestamp(mtime, timezone.utc).isoformat().replace("+00:00", "Z")


def clean_snippet(text: str, limit: int = 240) -> str:
    one_line = re.sub(r"\s+", " ", text).strip()
    if len(one_line) <= limit:
        return one_line
    return one_line[: limit - 1].rstrip() + "..."


def is_user_noise(text: str) -> bool:
    if not text or not text.strip():
        return True
    if NOISE_RE.match(text):
        return True
    if "Base directory for this skill" in text[:200]:
        return True
    if "<EXTREMELY_IMPORTANT>" in text[:500]:
        return True
    s = text.lstrip()
    if s.startswith("[{") and "tool_use_id" in s[:160]:
        return True
    return False


def read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return fallback
    except json.JSONDecodeError:
        return fallback


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def text_from_claude_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            parts.append(str(block.get("text") or ""))
        elif block.get("type") == "tool_use":
            name = block.get("name") or ""
            parts.append(f"[tool_use: {name}]")
    return "\n".join(p for p in parts if p)


def extract_paths(value: Any) -> set[str]:
    paths: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"file_path", "path", "notebook_path"} and isinstance(item, str):
                paths.add(item)
            else:
                paths.update(extract_paths(item))
    elif isinstance(value, list):
        for item in value:
            paths.update(extract_paths(item))
    elif isinstance(value, str):
        for match in PATH_RE.findall(value):
            paths.add(match.rstrip(".,);]'\""))
    return paths


def parse_claude(candidate: SessionCandidate) -> ParsedSession:
    parsed = ParsedSession(candidate=candidate)
    with candidate.path.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = rec.get("timestamp") or ""
            role = rec.get("type") or rec.get("role") or ""
            msg = rec.get("message") or {}
            content = msg.get("content") if isinstance(msg, dict) else None
            if role == "user":
                text = text_from_claude_content(content)
                if not is_user_noise(text):
                    parsed.user_messages.append((ts, text))
            elif role == "assistant":
                text = text_from_claude_content(content)
                if text:
                    parsed.assistant_messages.append((ts, text))
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            name = str(block.get("name") or "")
                            if name in {"Write", "Edit", "MultiEdit", "NotebookEdit"}:
                                parsed.touched_files.update(extract_paths(block.get("input")))
    return parsed


def text_from_codex_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if isinstance(block, dict):
            text = block.get("text")
            if text:
                parts.append(str(text))
    return "\n".join(parts)


def parse_codex(candidate: SessionCandidate) -> ParsedSession:
    parsed = ParsedSession(candidate=candidate)
    with candidate.path.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = rec.get("timestamp") or ""
            if rec.get("type") == "response_item":
                payload = rec.get("payload") or {}
                if not isinstance(payload, dict):
                    continue
                role = payload.get("role") or ""
                if role == "user":
                    text = text_from_codex_content(payload.get("content"))
                    if not is_user_noise(text):
                        parsed.user_messages.append((ts, text))
                elif role == "assistant":
                    text = text_from_codex_content(payload.get("content"))
                    if text:
                        parsed.assistant_messages.append((ts, text))
                elif payload.get("type") == "function_call":
                    name = str(payload.get("name") or "")
                    if "apply_patch" in name:
                        parsed.touched_files.update(extract_paths(payload.get("arguments")))
    return parsed


def discover_claude(vault: Path) -> Iterable[SessionCandidate]:
    if not CLAUDE_DIR.exists():
        return []
    items: list[SessionCandidate] = []
    for path in CLAUDE_DIR.glob("*.jsonl"):
        stat = path.stat()
        items.append(
            SessionCandidate(
                source="claude",
                session_id=path.stem,
                path=path,
                cwd=str(vault),
                mtime=stat.st_mtime,
                size=stat.st_size,
            )
        )
    return items


def discover_codex() -> Iterable[SessionCandidate]:
    if not CODEX_DIR.exists():
        return []
    items: list[SessionCandidate] = []
    for path in CODEX_DIR.rglob("rollout-*.jsonl"):
        session_id = path.stem
        cwd: str | None = None
        try:
            with path.open(encoding="utf-8") as fh:
                for line in fh:
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if rec.get("type") == "session_meta":
                        payload = rec.get("payload") or {}
                        if isinstance(payload, dict):
                            session_id = payload.get("id") or payload.get("session_id") or session_id
                            cwd = payload.get("cwd")
                        break
        except OSError:
            continue
        stat = path.stat()
        items.append(
            SessionCandidate(
                source="codex",
                session_id=session_id,
                path=path,
                cwd=cwd,
                mtime=stat.st_mtime,
                size=stat.st_size,
            )
        )
    return items


def in_prefix(path_text: str | None, prefix: Path) -> bool:
    if not path_text:
        return False
    try:
        path = Path(path_text).expanduser().resolve()
        return path == prefix.resolve() or prefix.resolve() in path.parents
    except OSError:
        return False


def select_candidates(
    all_candidates: Iterable[SessionCandidate],
    state: dict[str, Any],
    cwd_prefix: Path,
    quiet_seconds: int,
    bootstrap_hours: int,
    max_sessions: int,
) -> list[SessionCandidate]:
    now = time.time()
    processed = state.get("processed_files") or {}
    first_run_cutoff = now - bootstrap_hours * 3600
    selected: list[SessionCandidate] = []
    for cand in all_candidates:
        if cand.mtime > now - quiet_seconds:
            continue
        if cand.source == "codex" and not in_prefix(cand.cwd, cwd_prefix):
            continue
        key = str(cand.path)
        prior = processed.get(key)
        if prior:
            if prior.get("mtime") == cand.mtime and prior.get("size") == cand.size:
                continue
        elif cand.mtime < first_run_cutoff:
            continue
        selected.append(cand)
    selected.sort(key=lambda c: c.mtime)
    return selected[-max_sessions:]


def evidence_for(parsed: ParsedSession, ts: str, snippet: str, kind: str) -> list[dict[str, str]]:
    return [
        {
            "type": f"{parsed.candidate.source}_transcript",
            "subject": f"{kind}: {snippet}",
            "date": ts or iso_from_mtime(parsed.candidate.mtime),
            "session_id": parsed.candidate.session_id,
            "path": str(parsed.candidate.path),
        }
    ]


def tool_note_exists(vault: Path) -> bool:
    return (vault / "tool.agent-session-capture.md").exists()


def is_managed_agent_file(path_text: str, vault: Path) -> bool:
    if path_text.startswith(str(AI_SKILLS_DIR)):
        return True
    if path_text in {
        str(vault / "AGENTS.md"),
        str(vault.parent / "AGENTS.md"),
        str(vault.parent / "CLAUDE.md"),
    }:
        return True
    if path_text.startswith(str(vault / ".scripts/sync_agent_instructions.py")):
        return True
    return False


def bullet_for(parsed: ParsedSession, ts: str, label: str, snippet: str) -> str:
    when = (ts or iso_from_mtime(parsed.candidate.mtime))[:19].replace("T", " ")
    sid = parsed.candidate.session_id[:12]
    return f"- {when} [{parsed.candidate.source}:{sid}] {label}: \"{snippet}\""


def signals_from_session(parsed: ParsedSession, vault: Path) -> list[Signal]:
    signals: list[Signal] = []
    for ts, text in parsed.user_messages:
        snippet = clean_snippet(text)
        lower = text.lower()
        is_agent_system = bool(AGENT_SYSTEM_RE.search(text))
        if RECORD_RE.search(text):
            signals.append(
                Signal(
                    note="_working-memory.md",
                    section="## Agent Session Capture",
                    content=bullet_for(parsed, ts, "Explicit capture request", snippet),
                    confidence=0.84,
                    evidence=evidence_for(parsed, ts, snippet, "explicit_capture"),
                )
            )
        if CORRECTION_RE.search(text):
            target = "tool.agent-session-capture.md" if is_agent_system else "_working-memory.md"
            section = "## Recent Session Signals" if target.startswith("tool.") else "## Agent Session Capture"
            signals.append(
                Signal(
                    note=target,
                    section=section,
                    content=bullet_for(parsed, ts, "User correction", snippet),
                    confidence=0.76,
                    evidence=evidence_for(parsed, ts, snippet, "correction"),
                    create_title="Agent Session Capture" if target.startswith("tool.") else None,
                    create_desc="Important Claude/Codex transcript signals promoted during sync" if target.startswith("tool.") else None,
                )
            )
        if is_agent_system and (DECISION_RE.search(text) or FOLLOWUP_RE.search(text)):
            label = "Agent-system decision" if DECISION_RE.search(text) else "Agent-system follow-up"
            signals.append(
                Signal(
                    note="tool.agent-session-capture.md",
                    section="## Recent Session Signals",
                    content=bullet_for(parsed, ts, label, snippet),
                    confidence=0.82 if DECISION_RE.search(text) else 0.72,
                    evidence=evidence_for(parsed, ts, snippet, "agent_system_signal"),
                    create_title="Agent Session Capture",
                    create_desc="Important Claude/Codex transcript signals promoted during sync",
                )
            )

    interesting_files = sorted(p for p in parsed.touched_files if is_managed_agent_file(p, vault))
    if interesting_files:
        shown = ", ".join(Path(p).name for p in interesting_files[:6])
        if len(interesting_files) > 6:
            shown += f", +{len(interesting_files) - 6} more"
        ts = parsed.user_messages[-1][0] if parsed.user_messages else ""
        snippet = f"Touched managed files: {shown}"
        signals.append(
            Signal(
                note="tool.agent-session-capture.md",
                section="## Recent Session Signals",
                content=bullet_for(parsed, ts, "Managed files changed", snippet),
                confidence=0.7,
                evidence=evidence_for(parsed, ts, snippet, "managed_file_touch"),
                create_title="Agent Session Capture",
                create_desc="Important Claude/Codex transcript signals promoted during sync",
            )
        )
    return signals


def coalesce_signals(signals: list[Signal], vault: Path) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[Signal]] = {}
    for signal in signals:
        grouped.setdefault((signal.note, signal.section), []).append(signal)

    changes: list[dict[str, Any]] = []
    for (note, section), group in sorted(grouped.items()):
        unique_lines = list(dict.fromkeys(sig.content for sig in group))
        content = "\n".join(unique_lines)
        confidence = min(sig.confidence for sig in group)
        evidence: list[dict[str, str]] = []
        for sig in group:
            evidence.extend(sig.evidence)
        if note == "tool.agent-session-capture.md" and not tool_note_exists(vault):
            body = (
                "## Recent Session Signals\n\n"
                f"{content}\n\n"
                "## Notes\n\n"
                "- Generated from Claude Code and Codex transcripts by `/sync agent-session`.\n"
                "- Entries are evidence snippets, not full transcript summaries.\n"
            )
            changes.append(
                {
                    "note": None,
                    "action": "create_note",
                    "suggested_path": note,
                    "frontmatter": {
                        "title": group[0].create_title or "Agent Session Capture",
                        "desc": group[0].create_desc or "Important Claude/Codex transcript signals promoted during sync",
                    },
                    "content": body,
                    "confidence": confidence,
                    "evidence": evidence,
                }
            )
            continue
        changes.append(
            {
                "note": note,
                "action": "append",
                "section": section,
                "content": content + "\n",
                "confidence": confidence,
                "evidence": evidence,
            }
        )
    return changes


def update_session_index() -> None:
    if not SESSION_INDEX.exists():
        return
    subprocess.run(
        [sys.executable, str(SESSION_INDEX), "update"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def build_manifest(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    vault = args.vault.resolve()
    state_path = args.state or vault / ".cache/sync-state/session-sync-state.json"
    state = read_json(state_path, {"processed_files": {}})
    if args.update_index:
        update_session_index()
    candidates = list(discover_claude(vault)) + list(discover_codex())
    selected = select_candidates(
        candidates,
        state,
        args.cwd_prefix.resolve(),
        args.quiet_minutes * 60,
        args.bootstrap_hours,
        args.max_sessions,
    )

    parsed_sessions: list[ParsedSession] = []
    signals: list[Signal] = []
    for cand in selected:
        try:
            parsed = parse_claude(cand) if cand.source == "claude" else parse_codex(cand)
        except OSError:
            continue
        parsed_sessions.append(parsed)
        signals.extend(signals_from_session(parsed, vault))

    changes = coalesce_signals(signals, vault)
    generated_at = utc_now().isoformat().replace("+00:00", "Z")
    manifest = {
        "source": "agent-session",
        "generated_at": generated_at,
        "changes": changes,
        "summary": {
            "sessions_seen": len(candidates),
            "sessions_scanned": len(parsed_sessions),
            "signals_found": len(signals),
            "changes": len(changes),
            "quiet_minutes": args.quiet_minutes,
            "bootstrap_hours": args.bootstrap_hours,
        },
    }

    next_state = {
        "updated_at": generated_at,
        "processed_files": dict(state.get("processed_files") or {}),
    }
    for cand in selected:
        next_state["processed_files"][str(cand.path)] = {
            "source": cand.source,
            "session_id": cand.session_id,
            "mtime": cand.mtime,
            "size": cand.size,
            "last_seen": generated_at,
        }
    return manifest, next_state


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--cwd-prefix", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--quiet-minutes", type=int, default=5)
    parser.add_argument("--bootstrap-hours", type=int, default=48)
    parser.add_argument("--max-sessions", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--no-update-index", action="store_false", dest="update_index")
    parser.set_defaults(update_index=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    vault = args.vault.resolve()
    if args.state is None:
        args.state = vault / ".cache/sync-state/session-sync-state.json"
    if args.manifest is None:
        stamp = utc_now().strftime("%Y-%m-%dT%H%M%SZ")
        args.manifest = vault / f".cache/sync-state/agent-session-manifest-{stamp}.json"

    manifest, next_state = build_manifest(args)
    if args.dry_run:
        print(json.dumps(manifest, indent=2, ensure_ascii=False) if args.as_json else manifest["summary"])
        return 0

    write_json(args.manifest, manifest)
    write_json(args.state, next_state)
    if args.as_json:
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
    else:
        print(
            f"agent-session sync: scanned {manifest['summary']['sessions_scanned']} sessions, "
            f"found {manifest['summary']['signals_found']} signals, wrote {args.manifest}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
