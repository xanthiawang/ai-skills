#!/usr/bin/env python3
"""
Thin Honcho adapter — gated by env var so it auto-no-ops when the
service isn't running.

Usage:
    honcho_adapter.py write --session <id> --peer <name> --role user --text "..."
    honcho_adapter.py query --peer <name> --question "What does this person care about?"
    honcho_adapter.py mirror-session <session_id>   # backfill one Claude jsonl into honcho

Set HONCHO_BASE_URL=http://localhost:8000 to enable. With no env var, every
call is a silent no-op so accidental imports during sessions don't 500.

This is the A/B mirror layer: it writes a copy of every turn that mentions
a person into honcho, then lets you compare honcho's emergent peer model
against your static `user.*.md` rolodex after a week of traffic.

The dependency is `honcho-ai` from PyPI. Install with:
    pip install honcho-ai
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

WORKSPACE = "albert-command-center"
SESSION_DIR = Path(
    "/Users/A.Y/.claude/projects/-Users-A-Y-Documents-Manual-Library-Dendron-notes"
)
VAULT_DIR = Path("/Users/A.Y/Documents/Manual Library/Dendron/notes")


def _enabled() -> bool:
    return bool(os.environ.get("HONCHO_BASE_URL"))


def _client():
    """Lazy import — honcho-ai isn't installed until Albert opts in."""
    if not _enabled():
        return None
    try:
        from honcho import Honcho  # type: ignore
    except ImportError:
        print(
            "honcho-ai not installed. Run: pip install honcho-ai",
            file=sys.stderr,
        )
        return None
    return Honcho(
        workspace_id=WORKSPACE,
        base_url=os.environ["HONCHO_BASE_URL"],
        api_key=os.environ.get("HONCHO_API_KEY", "local-no-auth"),
    )


def cmd_write(args) -> int:
    h = _client()
    if h is None:
        print("(honcho disabled — set HONCHO_BASE_URL to enable)", file=sys.stderr)
        return 0
    peer = h.peer(args.peer)
    session = h.session(args.session)
    if args.role == "user":
        session.add_messages([peer.message(args.text)])
    else:
        # Honcho models the agent as a peer too — name it `assistant` by convention.
        assistant = h.peer("assistant")
        session.add_messages([assistant.message(args.text)])
    print(f"Wrote turn (peer={args.peer}, session={args.session}, role={args.role})", file=sys.stderr)
    return 0


def cmd_query(args) -> int:
    h = _client()
    if h is None:
        print("(honcho disabled)", file=sys.stderr)
        return 0
    peer = h.peer(args.peer)
    response = peer.chat(args.question)
    print(response)
    return 0


# Heuristic: detect when a turn is "about" a person in Albert's rolodex.
# Match against existing user.*.md filenames (firstname-lastname).
def known_peers() -> set[str]:
    out = set()
    for fp in VAULT_DIR.glob("user.*.md"):
        slug = fp.stem.replace("user.", "")
        out.add(slug)
    return out


PEER_NAME_RE = re.compile(r"\b([A-Z][a-z]+(?:[ -][A-Z][a-z]+){0,2})\b")


def detect_peer(text: str, known: set[str]) -> str | None:
    """Return the most-mentioned known peer in the text, if any."""
    counts: dict[str, int] = {}
    for m in PEER_NAME_RE.finditer(text):
        slug = m.group(1).lower().replace(" ", "-")
        if slug in known:
            counts[slug] = counts.get(slug, 0) + 1
    if not counts:
        return None
    return max(counts, key=counts.get)


def cmd_mirror_session(args) -> int:
    """Backfill a Claude jsonl session into honcho."""
    h = _client()
    if h is None:
        print("(honcho disabled — set HONCHO_BASE_URL to enable)", file=sys.stderr)
        return 1

    fp = SESSION_DIR / f"{args.session_id}.jsonl"
    if not fp.exists():
        print(f"No such session: {fp}", file=sys.stderr)
        return 1

    known = known_peers()
    session = h.session(args.session_id)
    user_peer = h.peer("albert")
    assistant_peer = h.peer("assistant")
    n = 0

    with fp.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = rec.get("type") or rec.get("role") or ""
            msg = rec.get("message") or {}
            content = msg.get("content") if isinstance(msg, dict) else None
            if isinstance(content, list):
                content = " ".join(
                    b.get("text", "") for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                )
            if not isinstance(content, str) or not content.strip():
                continue

            # Decide which peer this turn is about.
            mentioned = detect_peer(content, known)
            messages = []
            if role == "user":
                messages.append(user_peer.message(content[:2000]))
                if mentioned:
                    h.peer(mentioned)  # ensure peer exists; co-presence implicit in workspace
            else:
                messages.append(assistant_peer.message(content[:2000]))

            session.add_messages(messages)
            n += 1

    print(f"Mirrored {n} turns from {args.session_id} → honcho", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    sub = ap.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("write")
    w.add_argument("--session", required=True)
    w.add_argument("--peer", required=True)
    w.add_argument("--role", default="user", choices=["user", "assistant"])
    w.add_argument("--text", required=True)

    q = sub.add_parser("query")
    q.add_argument("--peer", required=True)
    q.add_argument("--question", required=True)

    m = sub.add_parser("mirror-session")
    m.add_argument("session_id")

    args = ap.parse_args()
    return {"write": cmd_write, "query": cmd_query, "mirror-session": cmd_mirror_session}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
