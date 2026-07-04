#!/usr/bin/env python3
"""
Extract raw data from screenpipe for journal generation.
This script provides structured data - formatting is done by the Cursor Agent.
"""

import json
import sys
import argparse
import sqlite3
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
from pathlib import Path
import urllib.request
import urllib.parse

DEFAULT_PORT = 3030
SCREENPIPE_API = f"http://localhost:{DEFAULT_PORT}"
SCREENPIPE_DB = Path.home() / ".screenpipe/db.sqlite"


def load_config():
    """Load configuration."""
    config_path = Path.home() / ".screenpipe/journal_config.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)

    return {
        "screenpipe_port": 3030,
        "journal_path": str(Path.home() / "Documents/Manual Library/Dendron/notes"),
        "focus_apps": ["Cursor", "Zotero", "Terminal", "Safari", "Google Chrome"],
        "ignore_windows": ["screenpipe", "Settings", "Keepass", "1Password"],
        "sleep_detection": {
            "min_gap_hours": 3.0,
            "default_wake_hour": 6,
            "late_night_cutoff_hour": 6,
        },
    }


def query_screenpipe_sqlite(start_time: str, end_time: str, limit: int = 2000) -> dict:
    """Query the local screenpipe SQLite DB when the HTTP API is blocked."""
    if not SCREENPIPE_DB.exists():
        print(f"Screenpipe SQLite DB not found: {SCREENPIPE_DB}", file=sys.stderr)
        return {"data": []}

    items = []
    try:
        conn = sqlite3.connect(f"file:{SCREENPIPE_DB}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

        if "ocr_text" in tables:
            ocr_rows = conn.execute(
                """
                SELECT
                    f.timestamp,
                    f.name AS frame_name,
                    COALESCE(o.app_name, f.app_name, '') AS app_name,
                    COALESCE(o.window_name, f.window_name, '') AS window_name,
                    COALESCE(o.focused, f.focused, 1) AS focused,
                    COALESCE(f.browser_url, '') AS browser_url,
                    o.text
                FROM ocr_text o
                JOIN frames f ON f.id = o.frame_id
                WHERE datetime(f.timestamp) >= datetime(?)
                  AND datetime(f.timestamp) < datetime(?)
                  AND length(COALESCE(o.text, '')) >= 1
                ORDER BY datetime(f.timestamp)
                LIMIT ?
                """,
                (start_time, end_time, limit),
            ).fetchall()
        else:
            ocr_rows = conn.execute(
                """
                WITH frame_text AS (
                    SELECT
                        f.id,
                        f.timestamp,
                        f.name AS frame_name,
                        COALESCE(f.app_name, '') AS app_name,
                        COALESCE(f.window_name, '') AS window_name,
                        COALESCE(f.focused, 1) AS focused,
                        COALESCE(f.browser_url, '') AS browser_url,
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
                WHERE length(COALESCE(text, '')) >= 1
                ORDER BY datetime(timestamp)
                LIMIT ?
                """,
                (start_time, end_time, limit),
            ).fetchall()
        for row in ocr_rows:
            items.append(
                {
                    "type": "OCR",
                    "content": {
                        "timestamp": row["timestamp"],
                        "text": row["text"] or "",
                        "app_name": row["app_name"] or "",
                        "window_name": row["window_name"] or "",
                        "focused": bool(row["focused"]),
                        "browser_url": row["browser_url"] or "",
                        "frame_name": row["frame_name"] or "",
                    },
                }
            )

        audio_rows = conn.execute(
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
              AND length(COALESCE(a.transcription, '')) >= 1
            ORDER BY datetime(a.timestamp)
            LIMIT ?
            """,
            (start_time, end_time, limit),
        ).fetchall()
        for row in audio_rows:
            items.append(
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
            )
        conn.close()
    except Exception as exc:
        print(f"Error querying screenpipe SQLite fallback: {exc}", file=sys.stderr)
        return {"data": []}

    items.sort(key=lambda item: item.get("content", {}).get("timestamp", ""))
    return {"data": items[:limit]}


def query_screenpipe(start_time: str, end_time: str, limit: int = 2000) -> dict:
    """Query screenpipe API, falling back to the local SQLite store."""
    params = urllib.parse.urlencode(
        {"start_time": start_time, "end_time": end_time, "limit": limit}
    )

    url = f"{SCREENPIPE_API}/search?{params}"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Error querying screenpipe HTTP API: {e}", file=sys.stderr)
        print("Falling back to local screenpipe SQLite DB", file=sys.stderr)
        return query_screenpipe_sqlite(start_time, end_time, limit=limit)


def extract_work_context(text: str) -> str:
    """Infer activity type from OCR content."""
    text_lower = text.lower()

    # Terminal/shell work
    if any(pattern in text for pattern in ["$ ", "~ %", "›", "❯", "bash", "zsh"]):
        if "python" in text_lower or ".py" in text:
            return "Terminal - Python development"
        elif "git" in text_lower:
            return "Terminal - Git operations"
        return "Terminal work"

    # Code editor
    if any(
        keyword in text_lower
        for keyword in [
            "def ",
            "class ",
            "import ",
            "function",
            "const ",
            "let ",
            "var ",
        ]
    ):
        if "def " in text_lower and ":" in text:
            return "Coding - Python"
        elif "function" in text_lower or "const " in text_lower:
            return "Coding - JavaScript"
        return "Coding/development"

    # Browser activities
    if any(
        pattern in text_lower
        for pattern in ["http://", "https://", ".com", ".org", ".edu"]
    ):
        if "github" in text_lower:
            return "GitHub - Code review"
        elif "gmail" in text_lower or "mail.google" in text_lower:
            return "Email (Gmail)"
        elif any(search in text_lower for search in ["google", "search", "wikipedia"]):
            return "Web research"
        return "Web browsing"

    # Meeting notes
    if "meet." in text_lower or "meeting" in text_lower:
        return "Meeting notes"

    # Journal/notes
    if "dendron" in text_lower or ".md" in text:
        if "journal" in text_lower:
            return "Journal generation"
        elif "skill" in text_lower:
            return "Skills development"
        return "Note-taking"

    # Research
    if any(
        word in text_lower for word in ["paper", "zotero", "doi", "pubmed", "arxiv"]
    ):
        return "Research/reading papers"

    # Email
    if any(
        pattern in text_lower
        for pattern in ["inbox", "compose", "reply", "subject:", "from:", "to:"]
    ):
        return "Email"

    # Communication
    if "slack" in text_lower:
        return "Slack - Team communication"
    if "zoom" in text_lower:
        return "Zoom meeting"
    if "teams" in text_lower:
        return "Microsoft Teams"

    # Document editing
    if any(
        pattern in text_lower
        for pattern in ["autosave", "font", "paragraph", "formatting"]
    ):
        if "slide" in text_lower:
            return "Presentation editing"
        return "Document editing"

    return "General work"


def detect_sleep_periods(data: list, config: dict) -> list:
    """Detect sleep periods by finding large gaps in activity."""
    if not data:
        return []

    min_gap_hours = config.get("sleep_detection", {}).get("min_gap_hours", 3.0)

    timestamps = []
    for item in data:
        if "content" in item and "timestamp" in item["content"]:
            ts_str = item["content"]["timestamp"]
            try:
                if "." in ts_str:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                else:
                    ts = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ")
                timestamps.append(ts)
            except Exception:
                continue

    if len(timestamps) < 2:
        return []

    timestamps.sort()

    sleep_periods = []
    for i in range(len(timestamps) - 1):
        gap = (timestamps[i + 1] - timestamps[i]).total_seconds() / 3600
        if gap >= min_gap_hours:
            sleep_periods.append(
                {
                    "start": timestamps[i].isoformat(),
                    "end": timestamps[i + 1].isoformat(),
                    "duration_hours": round(gap, 1),
                }
            )

    return sleep_periods


def find_day_boundaries(target_date: datetime, config: dict) -> tuple:
    """Find intelligent day boundaries based on sleep patterns."""
    query_start = (target_date - timedelta(days=1)).replace(hour=6, minute=0, second=0)
    query_end = (target_date + timedelta(days=1)).replace(hour=12, minute=0, second=0)

    result = query_screenpipe(
        query_start.isoformat() + "Z", query_end.isoformat() + "Z", limit=3000
    )
    data = result.get("data", [])

    if not data:
        return (
            target_date.replace(hour=0, minute=0, second=0),
            target_date.replace(hour=23, minute=59, second=59),
        )

    sleep_periods = detect_sleep_periods(data, config)
    default_wake_hour = config.get("sleep_detection", {}).get("default_wake_hour", 6)

    if not sleep_periods:
        start_boundary = target_date.replace(
            hour=default_wake_hour, minute=0, second=0, tzinfo=timezone.utc
        )
        end_boundary = (target_date + timedelta(days=1)).replace(
            hour=default_wake_hour, minute=0, second=0, tzinfo=timezone.utc
        )
        return (start_boundary, end_boundary)

    # Find wake-up time on target date
    # Make target_date timezone-aware for comparison
    target_midnight = target_date.replace(
        hour=0, minute=0, second=0, tzinfo=timezone.utc
    )
    target_next_midnight = target_midnight + timedelta(days=1)

    wake_up_time = None
    next_sleep_time = None

    for sp in sleep_periods:
        sleep_end = datetime.fromisoformat(sp["end"])
        # Ensure timezone-aware
        if sleep_end.tzinfo is None:
            sleep_end = sleep_end.replace(tzinfo=timezone.utc)

        if target_midnight <= sleep_end < target_next_midnight:
            if wake_up_time is None or sleep_end < wake_up_time:
                wake_up_time = sleep_end

    if wake_up_time:
        for sp in sleep_periods:
            sleep_start = datetime.fromisoformat(sp["start"])
            # Ensure timezone-aware
            if sleep_start.tzinfo is None:
                sleep_start = sleep_start.replace(tzinfo=timezone.utc)
            if sleep_start > wake_up_time:
                next_sleep_time = sleep_start
                break

    start_boundary = (
        wake_up_time
        if wake_up_time
        else target_date.replace(
            hour=default_wake_hour, minute=0, second=0, tzinfo=timezone.utc
        )
    )
    end_boundary = (
        next_sleep_time
        if next_sleep_time
        else (target_date + timedelta(days=1)).replace(
            hour=default_wake_hour, minute=0, second=0, tzinfo=timezone.utc
        )
    )

    return (start_boundary, end_boundary)


def extract_raw_data(date: datetime, config: dict) -> dict:
    """Extract structured raw data from screenpipe."""
    # Use 6 AM to 6 AM boundaries in local time
    # Convert local time to UTC for API queries
    from datetime import datetime as dt
    import time

    # Get local timezone offset
    local_tz = dt.now().astimezone().tzinfo

    # Start at 6 AM on target date (local time)
    start_local = date.replace(hour=6, minute=0, second=0, microsecond=0)
    start_local = start_local.replace(tzinfo=local_tz)

    # End at 6 AM next day (local time)
    end_local = (date + timedelta(days=1)).replace(
        hour=6, minute=0, second=0, microsecond=0
    )
    end_local = end_local.replace(tzinfo=local_tz)

    # Convert to UTC for API
    start_time = start_local.astimezone(timezone.utc)
    end_time = end_local.astimezone(timezone.utc)

    # Convert to naive UTC for API (screenpipe expects naive UTC times)
    start_naive = start_time.replace(tzinfo=None)
    end_naive = end_time.replace(tzinfo=None)

    # Query screenpipe with higher limit for full day
    result = query_screenpipe(
        start_naive.isoformat() + "Z", end_naive.isoformat() + "Z", limit=10000
    )
    data = result.get("data", [])

    # Still detect sleep periods for context (but don't use them to exclude data)
    sleep_periods = detect_sleep_periods(data, config)

    if not data:
        return {"error": f"No data found for {date.date()}"}

    # Group by hour
    hourly_data = defaultdict(lambda: {"ocr": [], "audio": [], "activities": Counter()})

    for item in data:
        ts = datetime.fromisoformat(item["content"]["timestamp"].replace("Z", "+00:00"))
        local_ts = ts.astimezone()
        hour = local_ts.hour

        if item["type"] == "OCR":
            text = item["content"].get("text", "").strip()
            if len(text) < 30:
                continue

            activity = extract_work_context(text)
            hourly_data[hour]["activities"][activity] += 1
            hourly_data[hour]["ocr"].append(
                {
                    "text": text[:300],
                    "timestamp": local_ts.isoformat(),
                    "activity": activity,
                }
            )

        elif item["type"] == "Audio":
            trans = item["content"].get("transcription", "").strip()
            if len(trans) > 20:
                hourly_data[hour]["audio"].append(
                    {"text": trans[:200], "timestamp": local_ts.isoformat()}
                )

    # Convert to serializable format
    formatted_hourly = {}
    for hour, hour_data in hourly_data.items():
        formatted_hourly[hour] = {
            "ocr": hour_data["ocr"],
            "audio": hour_data["audio"],
            "activities": dict(hour_data["activities"]),
        }

    # Find keyframes
    vault_path = config.get("journal_path", "")
    keyframes = []
    if vault_path:
        assets_dir = Path(vault_path) / "assets"
        pattern = f"journal_{date.strftime('%Y-%m-%d')}_moment_*.png"

        import re

        for img in sorted(assets_dir.glob(pattern)):
            match = re.search(r"moment_(\d+)\.png", img.name)
            if match:
                moment_num = match.group(1)
                video_path = img.with_suffix(".mp4")
                keyframes.append(
                    {
                        "number": moment_num,
                        "image": f"assets/{img.name}",
                        "video": (
                            f"assets/{video_path.name}" if video_path.exists() else None
                        ),
                    }
                )

    return {
        "date": date.strftime("%Y-%m-%d"),
        "day_boundaries": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "duration_hours": round((end_time - start_time).total_seconds() / 3600, 1),
        },
        "sleep_periods": sleep_periods,
        "total_items": len(data),
        "hourly_data": formatted_hourly,
        "keyframes": keyframes,
        "summary_stats": {
            "total_hours_active": len(hourly_data),
            "total_ocr_items": sum(len(h["ocr"]) for h in hourly_data.values()),
            "total_audio_items": sum(len(h["audio"]) for h in hourly_data.values()),
            "top_activities": dict(
                Counter(
                    activity
                    for h in hourly_data.values()
                    for activity in h["activities"].keys()
                ).most_common(10)
            ),
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extract raw data from screenpipe for journal generation"
    )
    parser.add_argument("date", nargs="?", help='Date (YYYY-MM-DD) or "today"')
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output"
    )

    args = parser.parse_args()

    config = load_config()

    # Parse date
    if not args.date or args.date == "today":
        target_date = datetime.now()
    else:
        target_date = datetime.strptime(args.date, "%Y-%m-%d")

    # Extract raw data
    print(f"Extracting data for {target_date.date()}...", file=sys.stderr)
    raw_data = extract_raw_data(target_date, config)

    if "error" in raw_data:
        print(raw_data["error"], file=sys.stderr)
        sys.exit(1)

    print(
        f"Extracted {raw_data['total_items']} items across {raw_data['summary_stats']['total_hours_active']} hours",
        file=sys.stderr,
    )

    # Output
    json_output = json.dumps(raw_data, indent=2 if args.pretty else None)

    if args.output:
        with open(args.output, "w") as f:
            f.write(json_output)
        print(f"Raw data written to {args.output}", file=sys.stderr)
    else:
        print(json_output)


if __name__ == "__main__":
    main()
