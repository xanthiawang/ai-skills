#!/usr/bin/env python3
"""
Screenpipe Intelligence Pipeline - Phase 1: Preprocessor

Converts raw screenpipe data into structured, deduplicated sessions.
- Fetches OCR + audio via localhost:3030 API
- Deduplicates consecutive OCR frames (>85% similarity = skip)
- Groups frames into activity sessions (same app + content window)
- Extracts entities (people, projects, URLs, DOIs) via regex
- Caches hourly blocks to .cache/cc-screenpipe-YYYY-MM-DD-HH.json

Usage:
    python3 preprocess_screenpipe.py [--date 2026-03-11] [--hours 6-23] [--force]
"""

import argparse
import difflib
import json
import os
import re
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SCREENPIPE_API = "http://localhost:3030"
SCREENPIPE_API_KEY = os.environ.get("SCREENPIPE_API_KEY", "")
SCREENPIPE_DB = Path.home() / ".screenpipe/db.sqlite"
VAULT_PATH = Path.home() / "Documents" / "Manual Library" / "Dendron" / "notes"
CACHE_DIR = VAULT_PATH / ".cache"
DEDUP_THRESHOLD = 0.85
SESSION_GAP_SECONDS = 300  # 5 min gap = new session
MIN_TEXT_LENGTH = 30

# Patterns for entity extraction
PEOPLE_PATTERN = re.compile(r"\b[A-Z][a-z]{1,15} [A-Z][a-z]{1,20}\b")
DOI_PATTERN = re.compile(r"10\.\d{4,}/[\S]+")
URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+")
ARXIV_PATTERN = re.compile(r"arXiv:\d{4}\.\d{4,}")

# Apps/windows to ignore (case-insensitive substring match)
# These are overlays, system chrome, or background processes whose OCR
# is either noise or a duplicate of the real foreground app's content.
IGNORE_APPS = {
    "screenpipe",
    "1password",
    "keepass",
    "system preferences",
    "system settings",
    "notification center",
    "loginwindow",
    "wallpaper",
    "dock",
    "spotlight",
    "control center",
    "windowmanager",
    "windowserver",
    "coreservices",
    "offscreen",
    "cluely",          # AI overlay — OCR is always bleed-through from underlying app
    "bartender",       # menu bar manager overlay
    "istat menus",     # system monitor overlay
}


def get_local_tz():
    """Get the local timezone."""
    return datetime.now().astimezone().tzinfo


_screenpipe_offline = False  # circuit breaker: skip queries after first failure


def query_screenpipe_sqlite(
    start_time: str,
    end_time: str,
    content_type: str = "ocr",
    limit: int = 5000,
    min_length: int = MIN_TEXT_LENGTH,
) -> list:
    """Read screenpipe's local SQLite DB when the HTTP API is unavailable."""
    if not SCREENPIPE_DB.exists():
        print(f"Screenpipe SQLite DB not found: {SCREENPIPE_DB}", file=sys.stderr)
        return []

    try:
        conn = sqlite3.connect(f"file:{SCREENPIPE_DB}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if content_type == "audio":
            rows = conn.execute(
                """
                SELECT
                    a.timestamp,
                    a.transcription,
                    a.speaker_id,
                    COALESCE(s.name, 'Unknown') AS speaker_name,
                    CASE
                        WHEN a.start_time IS NOT NULL AND a.end_time IS NOT NULL
                        THEN a.end_time - a.start_time
                        ELSE NULL
                    END AS duration_seconds
                FROM audio_transcriptions a
                LEFT JOIN speakers s ON s.id = a.speaker_id
                WHERE datetime(a.timestamp) >= datetime(?)
                  AND datetime(a.timestamp) < datetime(?)
                  AND length(COALESCE(a.transcription, '')) >= ?
                ORDER BY datetime(a.timestamp)
                LIMIT ?
                """,
                (start_time, end_time, min_length, limit),
            ).fetchall()
            conn.close()
            return [
                {
                    "type": "Audio",
                    "content": {
                        "timestamp": row["timestamp"],
                        "transcription": row["transcription"] or "",
                        "speaker": {
                            "id": row["speaker_id"],
                            "name": row["speaker_name"] or "Unknown",
                        },
                        "duration_seconds": row["duration_seconds"],
                    },
                }
                for row in rows
            ]

        if content_type == "accessibility":
            rows = conn.execute(
                """
                SELECT
                    id,
                    timestamp,
                    name AS frame_name,
                    COALESCE(app_name, '') AS app_name,
                    COALESCE(window_name, '') AS window_name,
                    COALESCE(browser_url, '') AS browser_url,
                    COALESCE(focused, 1) AS focused,
                    COALESCE(accessibility_text, full_text, '') AS text
                FROM frames
                WHERE datetime(timestamp) >= datetime(?)
                  AND datetime(timestamp) < datetime(?)
                  AND length(COALESCE(accessibility_text, full_text, '')) >= ?
                ORDER BY datetime(timestamp)
                LIMIT ?
                """,
                (start_time, end_time, min_length, limit),
            ).fetchall()
            item_type = "UI"
        elif "ocr_text" not in tables:
            rows = conn.execute(
                """
                WITH frame_text AS (
                    SELECT
                        f.id,
                        f.timestamp,
                        f.name AS frame_name,
                        COALESCE(f.app_name, '') AS app_name,
                        COALESCE(f.window_name, '') AS window_name,
                        COALESCE(f.browser_url, '') AS browser_url,
                        COALESCE(f.focused, 1) AS focused,
                        COALESCE(
                            NULLIF(f.full_text, ''),
                            NULLIF(f.accessibility_text, ''),
                            GROUP_CONCAT(e.text, char(10)),
                            ''
                        ) AS text
                    FROM frames f
                    LEFT JOIN elements e
                      ON e.frame_id = f.id
                     AND e.text IS NOT NULL
                     AND e.text != ''
                     AND e.source IN ('ocr', 'accessibility')
                    WHERE datetime(f.timestamp) >= datetime(?)
                      AND datetime(f.timestamp) < datetime(?)
                    GROUP BY f.id
                )
                SELECT *
                FROM frame_text
                WHERE length(COALESCE(text, '')) >= ?
                ORDER BY datetime(timestamp)
                LIMIT ?
                """,
                (start_time, end_time, min_length, limit),
            ).fetchall()
            item_type = "OCR"
        else:
            rows = conn.execute(
                """
                SELECT
                    f.id,
                    f.timestamp,
                    f.name AS frame_name,
                    COALESCE(o.app_name, f.app_name, '') AS app_name,
                    COALESCE(o.window_name, f.window_name, '') AS window_name,
                    COALESCE(f.browser_url, '') AS browser_url,
                    COALESCE(o.focused, f.focused, 1) AS focused,
                    o.text
                FROM ocr_text o
                JOIN frames f ON f.id = o.frame_id
                WHERE datetime(f.timestamp) >= datetime(?)
                  AND datetime(f.timestamp) < datetime(?)
                  AND length(COALESCE(o.text, '')) >= ?
                ORDER BY datetime(f.timestamp)
                LIMIT ?
                """,
                (start_time, end_time, min_length, limit),
            ).fetchall()
            item_type = "OCR"

        conn.close()
        return [
            {
                "type": item_type,
                "content": {
                    "timestamp": row["timestamp"],
                    "text": row["text"] or "",
                    "app_name": row["app_name"] or "",
                    "window_name": row["window_name"] or "",
                    "browser_url": row["browser_url"] or "",
                    "focused": bool(row["focused"]),
                    "frame_name": row["frame_name"] or f"frame-{row['id']}",
                },
            }
            for row in rows
        ]
    except Exception as exc:
        print(f"Warning: screenpipe SQLite fallback failed: {exc}", file=sys.stderr)
        return []


def query_screenpipe(
    start_time: str,
    end_time: str,
    content_type: str = "ocr",
    limit: int = 5000,
    min_length: int = MIN_TEXT_LENGTH,
) -> list:
    """Query screenpipe API for content in a time window."""
    global _screenpipe_offline
    if _screenpipe_offline:
        return query_screenpipe_sqlite(
            start_time,
            end_time,
            content_type=content_type,
            limit=limit,
            min_length=min_length,
        )

    params = {
        "start_time": start_time,
        "end_time": end_time,
        "content_type": content_type,
        "limit": limit,
        "min_length": min_length,
    }
    url = f"{SCREENPIPE_API}/search?{urlencode(params)}"

    try:
        req = Request(url)
        if SCREENPIPE_API_KEY:
            req.add_header("Authorization", f"Bearer {SCREENPIPE_API_KEY}")
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        return data.get("data", [])
    except (URLError, TimeoutError, OSError) as e:
        _screenpipe_offline = True
        if "Connection refused" in str(e) or "timed out" in str(e):
            print(
                "Screenpipe HTTP unavailable — using local SQLite fallback",
                file=sys.stderr,
            )
        else:
            print(
                f"Warning: screenpipe HTTP query failed: {e}; using SQLite fallback",
                file=sys.stderr,
            )
        return query_screenpipe_sqlite(
            start_time,
            end_time,
            content_type=content_type,
            limit=limit,
            min_length=min_length,
        )


def load_vault_entities() -> dict:
    """Load known people and project names from vault filenames."""
    people = set()
    projects = set()

    for f in VAULT_PATH.glob("user.*.md"):
        name = f.stem.replace("user.", "")
        # Convert slug to display name parts for matching
        parts = name.split("-")
        if len(parts) >= 2 and not parts[0].isdigit():
            # "tony-wyss-coray" -> "Tony Wyss Coray"
            display = " ".join(p.capitalize() for p in parts)
            people.add(display)
            # Also add shorter forms
            if len(parts) == 2:
                people.add(f"{parts[0].capitalize()} {parts[1].capitalize()}")

    for f in VAULT_PATH.glob("proj.*.md"):
        name = f.stem
        # "proj.2025.disaggregase" -> "disaggregase"
        parts = name.split(".")
        if len(parts) >= 3:
            proj_name = ".".join(parts[2:])
            projects.add(proj_name)

    return {"people": people, "projects": projects}


def similarity(a: str, b: str) -> float:
    """Quick similarity ratio between two strings using SequenceMatcher."""
    if not a or not b:
        return 0.0
    # For performance, compare first 500 chars
    return difflib.SequenceMatcher(None, a[:500], b[:500]).ratio()


# Apps that are overlays / always-visible and should lose ties
# Apps that are overlays but may still have useful content (e.g. Wispr Flow
# captures dictation). These get a scoring penalty but aren't fully ignored.
OVERLAY_APPS = {"wispr flow", "raycast", "alfred"}

# Content signatures: regex patterns that indicate a specific app is the real source
APP_CONTENT_SIGNATURES = {
    "Cursor": [
        re.compile(r"(def |class |import |function |const |let |var |=>)"),
        re.compile(r"\.(py|ts|tsx|js|jsx|md|json|yaml|toml)\b"),
        re.compile(r"(Workspace|Explorer|Source Control|Extensions)"),
    ],
    "Google Chrome": [
        re.compile(r"https?://"),
        re.compile(r"(gmail|google\.com|github\.com|arxiv|biorxiv)"),
    ],
    "Google Chrome Beta": [
        re.compile(r"https?://"),
        re.compile(r"(gmail|google\.com|github\.com|arxiv|biorxiv)"),
    ],
    "iTerm2": [
        re.compile(r"(\$ |~ %|❯|›|bash|zsh|pip |python3? |git )"),
    ],
    "Terminal": [
        re.compile(r"(\$ |~ %|❯|›|bash|zsh|pip |python3? |git )"),
    ],
    "WeChat": [
        re.compile(r"[\u4e00-\u9fff]{3,}"),  # 3+ consecutive CJK chars
        re.compile(r"(微信|朋友圈|聊天)"),
    ],
    "Slack": [
        re.compile(r"(#[a-z_-]+|Thread|Channel|DM)"),
    ],
    "zoom.us": [
        re.compile(r"(You are on a call|Participants|Meeting|Mute|Share Screen)"),
    ],
}


def score_app_match(app_name: str, text: str) -> float:
    """Score how well OCR text matches what you'd expect from this app."""
    score = 0.0
    app_lower = app_name.lower()

    # Overlays get a penalty
    if app_lower in OVERLAY_APPS:
        score -= 2.0

    # Check content signatures
    for sig_app, patterns in APP_CONTENT_SIGNATURES.items():
        if sig_app.lower() in app_lower or app_lower in sig_app.lower():
            for pat in patterns:
                if pat.search(text[:500]):
                    score += 1.0

    # Window name relevance: if window_name appears in text, boost
    # (handled at caller level since we need the frame)

    return score


def collapse_same_timestamp(frames: list) -> list:
    """Collapse multiple frames at the same timestamp into one, picking the best app.

    Screenpipe captures the entire screen and attributes the same OCR text to every
    visible window. This function groups by timestamp (second resolution), identifies
    duplicate text, and keeps only the most likely active app per unique text.
    """
    if not frames:
        return []

    # Group by timestamp (second resolution)
    by_ts = defaultdict(list)
    for frame in frames:
        ts = frame.get("timestamp", "")[:19]  # truncate to seconds
        by_ts[ts].append(frame)

    collapsed = []
    for ts, group in sorted(by_ts.items()):
        if len(group) == 1:
            collapsed.append(group[0])
            continue

        # Cluster frames by text similarity within this timestamp
        clusters = []  # list of (representative_frame, [all_apps])
        for frame in group:
            text = frame.get("text", "")
            matched = False
            for cluster in clusters:
                rep_text = cluster[0].get("text", "")
                if similarity(text, rep_text) > 0.70:
                    cluster[1].append(frame)
                    matched = True
                    break
            if not matched:
                clusters.append((frame, [frame]))

        # For each cluster, pick the best app
        for rep, members in clusters:
            if len(members) == 1:
                collapsed.append(members[0])
                continue

            # Score each member's app against the shared text
            text = rep.get("text", "")
            best = max(members, key=lambda f: score_app_match(f.get("app_name", ""), text))
            collapsed.append(best)

    collapsed.sort(key=lambda f: f.get("timestamp", ""))
    return collapsed


def dedup_frames(frames: list) -> list:
    """Remove near-duplicate OCR frames: first collapse same-timestamp duplicates,
    then dedup consecutive-in-time similar frames within each app."""
    if not frames:
        return []

    # Phase A: Collapse same-timestamp multi-app duplicates
    frames = collapse_same_timestamp(frames)

    # Phase B: Per-app temporal dedup
    by_app = defaultdict(list)
    for frame in frames:
        app = frame.get("app_name", "Unknown")
        by_app[app].append(frame)

    deduped_by_app = {}
    for app, app_frames in by_app.items():
        app_frames.sort(key=lambda f: f.get("timestamp", ""))
        kept = [app_frames[0]]
        for frame in app_frames[1:]:
            sim = similarity(frame.get("text", ""), kept[-1].get("text", ""))
            if sim > DEDUP_THRESHOLD:
                continue
            kept.append(frame)
        deduped_by_app[app] = kept

    all_deduped = []
    for kept in deduped_by_app.values():
        all_deduped.extend(kept)
    all_deduped.sort(key=lambda f: f.get("timestamp", ""))
    return all_deduped


def group_into_sessions(frames: list) -> list:
    """Group frames into activity sessions per-app, then consolidate nearby same-app sessions."""
    if not frames:
        return []

    # Step 1: Group frames by app
    by_app = defaultdict(list)
    for frame in frames:
        by_app[frame.get("app_name", "Unknown")].append(frame)

    # Step 2: Within each app, group consecutive-in-time frames into sessions
    raw_sessions = []
    for app, app_frames in by_app.items():
        app_frames.sort(key=lambda f: f.get("timestamp", ""))
        current = {
            "frames": [app_frames[0]],
            "app": app,
            "window": app_frames[0].get("window_name", ""),
        }
        for frame in app_frames[1:]:
            ts_curr = parse_timestamp(frame.get("timestamp", ""))
            ts_prev = parse_timestamp(current["frames"][-1].get("timestamp", ""))
            gap = (ts_curr - ts_prev).total_seconds() if ts_curr and ts_prev else 999

            # Browser URL change = new session within same browser
            url_changed = (
                frame.get("browser_url", "") != current["frames"][-1].get("browser_url", "")
                and frame.get("browser_url")
            )

            if gap > SESSION_GAP_SECONDS or url_changed:
                raw_sessions.append(current)
                current = {
                    "frames": [frame],
                    "app": app,
                    "window": frame.get("window_name", ""),
                }
            else:
                current["frames"].append(frame)
        raw_sessions.append(current)

    # Step 3: Finalize and sort sessions by start time
    sessions = [finalize_session(s) for s in raw_sessions]
    sessions = [s for s in sessions if s is not None and s["frame_count"] > 0]
    sessions.sort(key=lambda s: s["start"])
    return sessions


def finalize_session(session: dict) -> dict:
    """Convert raw session frames into structured session output."""
    frames = session["frames"]
    timestamps = [parse_timestamp(f.get("timestamp", "")) for f in frames]
    timestamps = [t for t in timestamps if t]

    if not timestamps:
        return None

    start = min(timestamps)
    end = max(timestamps)
    duration = (end - start).total_seconds() / 60

    # Get activity type from content
    all_text = " ".join(f.get("text", "") for f in frames)
    activity = classify_activity(session["app"], all_text)

    # Key content: first and last frame text (transitions), truncated
    key_content = []
    if frames:
        first_text = frames[0].get("text", "")[:200]
        if first_text:
            key_content.append(first_text)
        if len(frames) > 1:
            last_text = frames[-1].get("text", "")[:200]
            if last_text and last_text != first_text:
                key_content.append(last_text)

    # Browser URL from first frame with one
    browser_url = None
    for f in frames:
        if f.get("browser_url"):
            browser_url = f["browser_url"]
            break

    # Entity extraction
    entities = extract_entities(all_text)

    return {
        "start": start.strftime("%H:%M:%S"),
        "end": end.strftime("%H:%M:%S"),
        "app": session["app"],
        "window": session.get("window", ""),
        "activity": activity,
        "duration_minutes": round(duration, 1),
        "key_content": key_content,
        "browser_url": browser_url,
        "entities": entities,
        "frame_count": len(frames),
    }


def classify_activity(app_name: str, text: str) -> str:
    """Classify activity type from app name and content."""
    app = (app_name or "").lower()
    text_lower = text.lower()

    if "cursor" in app or "code" in app:
        if "python" in text_lower or ".py" in text:
            return "Coding - Python"
        if "javascript" in text_lower or ".js" in text or ".tsx" in text:
            return "Coding - JavaScript/TypeScript"
        return "Coding"
    if "terminal" in app or "iterm" in app or "warp" in app:
        if "git" in text_lower:
            return "Terminal - Git"
        return "Terminal"
    if "chrome" in app or "safari" in app or "firefox" in app or "arc" in app:
        if "gmail" in text_lower or "mail.google" in text_lower:
            return "Email (Gmail)"
        if "github.com" in text_lower:
            return "GitHub"
        if any(s in text_lower for s in ["arxiv", "biorxiv", "pubmed", "nature.com"]):
            return "Research browsing"
        if "calendar.google" in text_lower:
            return "Google Calendar"
        return "Web browsing"
    if "slack" in app:
        return "Slack"
    if "mattermost" in app:
        return "Mattermost"
    if "zoom" in app:
        return "Video call (Zoom)"
    if "zotero" in app:
        return "Reference management"
    if "finder" in app:
        return "File management"
    if "preview" in app or "pdf" in text_lower:
        return "Document viewing"
    if "wechat" in app or "微信" in text:
        return "WeChat"
    if "figma" in app:
        return "Design (Figma)"
    if "obsidian" in app or "dendron" in text_lower:
        return "Note-taking"

    return "General"


def extract_entities(text: str) -> dict:
    """Extract people, projects, URLs, DOIs from text."""
    entities = {
        "people": [],
        "projects": [],
        "urls": [],
        "dois": [],
    }

    # People: find Title Case names
    names = set(PEOPLE_PATTERN.findall(text))
    # Filter common false positives
    false_positives = {
        "Google Chrome",
        "Microsoft Teams",
        "Visual Studio",
        "App Store",
        "System Preferences",
        "System Settings",
        "New Tab",
        "Home Page",
        "Sign In",
        "Log In",
        "Stack Overflow",
        "Open Source",
        "United States",
        "Read More",
        "Learn More",
        "Click Here",
        "Next Page",
        "Page Down",
        "Last Modified",
        "Privacy Policy",
        "Terms Service",
        "All Rights",
    }
    entities["people"] = sorted(names - false_positives)

    # DOIs
    entities["dois"] = list(set(DOI_PATTERN.findall(text)))

    # URLs (limit to interesting ones)
    urls = set(URL_PATTERN.findall(text))
    interesting_domains = [
        "arxiv.org",
        "biorxiv.org",
        "pubmed",
        "nature.com",
        "science.org",
        "github.com",
        "doi.org",
    ]
    entities["urls"] = sorted(
        u for u in urls if any(d in u for d in interesting_domains)
    )[:10]

    # arXiv IDs
    arxiv_ids = ARXIV_PATTERN.findall(text)
    if arxiv_ids:
        entities["arxiv"] = list(set(arxiv_ids))

    return entities


def parse_timestamp(ts_str: str) -> datetime | None:
    """Parse various timestamp formats from screenpipe."""
    if not ts_str:
        return None
    try:
        # Handle timezone offset formats
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def process_hour(
    date: datetime, hour: int, force: bool = False
) -> dict | None:
    """Process one hour of screenpipe data. Returns cached if available."""
    date_str = date.strftime("%Y-%m-%d")
    cache_file = CACHE_DIR / f"cc-screenpipe-{date_str}-{hour:02d}.json"

    # Check cache (skip for current hour)
    now = datetime.now()
    is_current_hour = (
        date.date() == now.date() and hour == now.hour
    )

    if cache_file.exists() and not force and not is_current_hour:
        try:
            with open(cache_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    # Build time window in local time, convert to UTC for API
    local_tz = get_local_tz()
    start_local = date.replace(hour=hour, minute=0, second=0, microsecond=0)
    start_local = start_local.replace(tzinfo=local_tz)
    end_local = start_local + timedelta(hours=1)

    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)

    # Query accessibility (UI-tree) — preferred since 0.3.291. Cleaner text than OCR
    # (proper word boundaries, structure, control glyphs). Falls back to OCR per-frame
    # when accessibility tree wasn't captured for that frame.
    ax_items = query_screenpipe(
        start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        content_type="accessibility",
        limit=5000,
        min_length=MIN_TEXT_LENGTH,
    )

    # Query OCR — fallback for frames without accessibility-tree capture
    ocr_items = query_screenpipe(
        start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        content_type="ocr",
        limit=5000,
        min_length=MIN_TEXT_LENGTH,
    )

    # Query Audio
    audio_items = query_screenpipe(
        start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        content_type="audio",
        limit=500,
        min_length=10,
    )

    # Merge accessibility + OCR items, preferring accessibility for the same frame
    # (keyed by frame_name when present, else timestamp+app). Accessibility records
    # come back as type="UI" with the same content shape as OCR.
    seen_keys = set()
    merged_items = []
    for item in ax_items:
        content = item.get("content", {})
        key = content.get("frame_name") or (
            content.get("timestamp", "") + "|" + content.get("app_name", "")
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        merged_items.append(("ax", item))
    for item in ocr_items:
        content = item.get("content", {})
        key = content.get("frame_name") or (
            content.get("timestamp", "") + "|" + content.get("app_name", "")
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        merged_items.append(("ocr", item))

    # Parse merged items into frames with full metadata
    raw_frames = []
    for source, item in merged_items:
        content = item.get("content", {})
        text = content.get("text", "").strip()
        if len(text) < MIN_TEXT_LENGTH:
            continue

        app_name = content.get("app_name", "")
        window_name = content.get("window_name", "")

        # Skip ignored apps/windows
        combined = (app_name + " " + window_name).lower()
        if any(ign in combined for ign in IGNORE_APPS):
            continue

        # Skip unfocused windows (accessibility records don't always include focused;
        # only filter when the field is explicitly False)
        if content.get("focused") is False:
            continue

        raw_frames.append(
            {
                "text": text,
                "timestamp": content.get("timestamp", ""),
                "app_name": app_name,
                "window_name": window_name,
                "browser_url": content.get("browser_url", ""),
                "focused": content.get("focused", True),
                "source": source,  # "ax" or "ocr"
            }
        )

    # Sort by timestamp
    raw_frames.sort(key=lambda f: f.get("timestamp", ""))

    # Dedup
    deduped = dedup_frames(raw_frames)

    # Group into sessions
    sessions = group_into_sessions(deduped)
    sessions = [s for s in sessions if s is not None]

    # Parse audio segments
    audio_segments = []
    for item in audio_items:
        content = item.get("content", {})
        text = content.get("transcription", "").strip()
        if len(text) < 10:
            continue

        speaker = content.get("speaker") or {}
        ts = parse_timestamp(content.get("timestamp", ""))

        audio_segments.append(
            {
                "timestamp": ts.strftime("%H:%M:%S") if ts else "",
                "text": text,
                "speaker": {
                    "id": speaker.get("id"),
                    "name": speaker.get("name", "Unknown"),
                },
                "duration_seconds": content.get("duration_seconds"),
            }
        )

    result = {
        "date": date_str,
        "hour": hour,
        "sessions": sessions,
        "audio_segments": audio_segments,
        "stats": {
            "raw_frames": len(raw_frames),
            "after_dedup": len(deduped),
            "compression_ratio": (
                round(len(deduped) / len(raw_frames), 3) if raw_frames else 0
            ),
            "session_count": len(sessions),
            "audio_count": len(audio_segments),
        },
    }

    # Cache result
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def process_day(
    date: datetime, hours: tuple[int, int] = (6, 23), force: bool = False
) -> dict:
    """Process an entire day of screenpipe data."""
    start_hour, end_hour = hours
    all_sessions = []
    all_audio = []
    total_raw = 0
    total_deduped = 0

    for hour in range(start_hour, end_hour + 1):
        result = process_hour(date, hour, force=force)
        if result:
            all_sessions.extend(result.get("sessions", []))
            all_audio.extend(result.get("audio_segments", []))
            stats = result.get("stats", {})
            total_raw += stats.get("raw_frames", 0)
            total_deduped += stats.get("after_dedup", 0)

    # Cross-reference entities with vault
    vault_entities = load_vault_entities()
    known_people = vault_entities["people"]
    known_projects = vault_entities["projects"]

    # Enrich entity lists: flag known people/projects
    for session in all_sessions:
        entities = session.get("entities", {})
        people = entities.get("people", [])
        enriched_people = []
        for name in people:
            is_known = any(
                name.lower() in kp.lower() or kp.lower() in name.lower()
                for kp in known_people
            )
            enriched_people.append(
                {"name": name, "known": is_known}
            )
        entities["people"] = enriched_people

    return {
        "date": date.strftime("%Y-%m-%d"),
        "hours_range": f"{start_hour}-{end_hour}",
        "sessions": all_sessions,
        "audio_segments": all_audio,
        "stats": {
            "raw_frames": total_raw,
            "after_dedup": total_deduped,
            "compression_ratio": (
                round(total_deduped / total_raw, 3) if total_raw else 0
            ),
            "total_sessions": len(all_sessions),
            "total_audio": len(all_audio),
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess screenpipe data: dedup, session-group, entity-extract"
    )
    parser.add_argument(
        "--date",
        default="today",
        help='Date to process (YYYY-MM-DD or "today")',
    )
    parser.add_argument(
        "--hours",
        default="0-23",
        help="Hour range to process (e.g., 6-18, default: 0-23)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-processing even if cached",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output JSON file path (default: stdout)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only print stats, not full data",
    )

    args = parser.parse_args()

    # Parse date
    if args.date == "today":
        target_date = datetime.now()
    else:
        target_date = datetime.strptime(args.date, "%Y-%m-%d")

    # Parse hour range
    parts = args.hours.split("-")
    start_hour = int(parts[0])
    end_hour = int(parts[1]) if len(parts) > 1 else start_hour

    print(
        f"Processing {target_date.date()} hours {start_hour}-{end_hour}...",
        file=sys.stderr,
    )

    result = process_day(target_date, (start_hour, end_hour), force=args.force)

    stats = result["stats"]
    print(
        f"Done: {stats['raw_frames']} raw → {stats['after_dedup']} deduped "
        f"({stats['compression_ratio']:.1%} kept) → {stats['total_sessions']} sessions, "
        f"{stats['total_audio']} audio segments",
        file=sys.stderr,
    )

    if args.stats_only:
        output = json.dumps(result["stats"], indent=2)
    else:
        output = json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
