#!/usr/bin/env python3
"""
Generate daily journal from screenpipe - improved with specific details and AI handoff context.
"""

import json
import sys
import os
import argparse
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path
import urllib.request
import urllib.parse
import re

DEFAULT_PORT = 3030
SCREENPIPE_API = f"http://localhost:{DEFAULT_PORT}"


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


def query_screenpipe(start_time: str, end_time: str, limit: int = 2000) -> dict:
    """Query screenpipe API."""
    params = urllib.parse.urlencode(
        {"start_time": start_time, "end_time": end_time, "limit": limit}
    )

    url = f"{SCREENPIPE_API}/search?{params}"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Error querying screenpipe: {e}", file=sys.stderr)
        return {"data": []}


def extract_specific_details(text: str, activity: str) -> str:
    """Extract specific actionable details from text."""
    text = " ".join(text.split())  # Clean whitespace

    # For email, try to extract who/what
    if "email" in activity.lower():
        # Look for names
        words = text.split()
        for i, word in enumerate(words):
            if word and word[0].isupper() and len(word) > 3:
                if i > 0 and words[i - 1].lower() in [
                    "from",
                    "to",
                    "with",
                    "email",
                    "dear",
                ]:
                    return f"Correspondence with {word}"

    # For meetings, extract meeting name or attendees
    if "meeting" in activity.lower() or "interview" in activity.lower():
        # Look for proper nouns
        if "umich" in text.lower() or "michigan" in text.lower():
            return "UMich faculty interview materials"

    # For code, try to find function names or file names
    if "code" in activity.lower() or "development" in activity.lower():
        # Look for .py, .js, etc files
        file_pattern = r"(\w+\.\w{2,4})"
        matches = re.findall(file_pattern, text)
        if matches:
            return f"Working on {matches[0]}"

    # Default: return first meaningful phrase
    if len(text) > 50:
        return text[:150] + "..."

    return text


def identify_key_moment(items: list, hour: int) -> dict:
    """Identify if this hour has a key moment worth embedding as screenshot."""
    # Key moments are:
    # 1. Long, content-rich text (>200 chars)
    # 2. Important contexts (meetings, emails with names, code with specifics)
    # 3. Not utility screens

    for text in items:
        if len(text) > 200:
            # This is substantial content
            # Check if it has useful info
            if any(
                word in text.lower()
                for word in [
                    "interview",
                    "meeting",
                    "email",
                    "project",
                    "research",
                    "draft",
                    "review",
                ]
            ):
                return {
                    "has_moment": True,
                    "text": text[:200],
                    "reason": "Substantial work content",
                }

    return {"has_moment": False}


def format_timeline(hourly_content: dict, date: datetime) -> list:
    """Format timeline with specific details and embedded key moments."""
    timeline = []

    for hour in sorted(hourly_content.keys()):
        hour_12 = hour % 12 or 12
        period = "PM" if hour >= 12 else "AM"
        hour_data = hourly_content[hour]

        if not hour_data:
            continue

        # Check if this hour has a key moment
        all_texts = []
        for items in hour_data.values():
            all_texts.extend(items)

        key_moment = identify_key_moment(all_texts, hour)

        # Format hour header
        timeline.append(f"### {hour_12}:00 {period}\n")

        # If key moment, embed screenshot
        # (Note: actual screenshot would need to be extracted separately)
        if key_moment["has_moment"]:
            timeline.append(
                f'_![Key moment](assets/journal_{date.strftime("%Y-%m-%d")}_hour_{hour}.png)_\n'
            )

        # List activities with specific details
        for activity, items in sorted(
            hour_data.items(), key=lambda x: len(x[1]), reverse=True
        ):
            if activity == "Conversation":
                # Only include if substantive
                for conv in items:
                    if len(conv) > 30 and not any(
                        skip in conv.lower() for skip in ["hello", "test", "um", "uh"]
                    ):
                        timeline.append(f'- 🎤 "{conv[:100]}..."')
            else:
                timeline.append(f"**{activity}**")

                # Extract specific details
                details = []
                for text in items[:3]:  # Top 3 text samples
                    detail = extract_specific_details(text, activity)
                    if detail and len(detail) > 20:
                        details.append(detail)

                if details:
                    for detail in details[:2]:  # Max 2 details per activity
                        timeline.append(f"- {detail}")
                else:
                    # Fallback to first text snippet
                    if items:
                        clean = " ".join(items[0].split())[:120]
                        timeline.append(f"- {clean}...")

        timeline.append("")

    return timeline


def extract_open_questions(hourly_content: dict) -> list:
    """Extract open questions, blockers, and next steps."""
    open_items = []

    # Look for question markers
    for hour_data in hourly_content.values():
        for activity, items in hour_data.items():
            for text in items:
                text_lower = text.lower()

                # Patterns that indicate open questions
                if "?" in text:
                    clean = " ".join(text.split())
                    open_items.append({"type": "question", "text": clean[:150]})

                # Patterns for blockers
                if any(
                    word in text_lower
                    for word in ["blocked", "stuck", "issue", "problem", "error"]
                ):
                    clean = " ".join(text.split())
                    open_items.append({"type": "blocker", "text": clean[:150]})

                # Patterns for next steps
                if any(
                    phrase in text_lower
                    for phrase in ["need to", "next step", "todo", "should"]
                ):
                    clean = " ".join(text.split())
                    open_items.append({"type": "next", "text": clean[:150]})

    return open_items[:5]  # Limit to top 5


def infer_tasks(hourly_content: dict) -> list:
    """Infer actionable tasks from content."""
    tasks = set()

    for hour_data in hourly_content.values():
        for activity, items in hour_data.items():
            for text in items:
                text_lower = text.lower()

                # Task patterns
                patterns = [
                    (r"need to (.+?)[\.;,]", "need to"),
                    (r"should (.+?)[\.;,]", "should"),
                    (r"will (.+?)[\.;,]", "will"),
                    (r"going to (.+?)[\.;,]", "going to"),
                    (r"must (.+?)[\.;,]", "must"),
                    (r"email (.+?)[\.;,]", "email"),
                    (r"send (.+?)[\.;,]", "send"),
                    (r"schedule (.+?)[\.;,]", "schedule"),
                ]

                for pattern, prefix in patterns:
                    matches = re.findall(pattern, text_lower, re.IGNORECASE)
                    for match in matches:
                        if 10 < len(match) < 80:
                            task = match.strip().capitalize()
                            tasks.add(f"{prefix.capitalize()} {task}")

    return list(tasks)[:10]


def detect_sleep_periods(data: list, config: dict) -> list:
    """
    Detect sleep periods by finding large gaps in activity.
    Returns list of (sleep_start, sleep_end) datetime tuples.
    """
    if not data:
        return []

    min_gap_hours = config.get("sleep_detection", {}).get("min_gap_hours", 3.0)

    # Extract all timestamps
    timestamps = []
    for item in data:
        if "content" in item and "timestamp" in item["content"]:
            ts_str = item["content"]["timestamp"]
            try:
                # Handle both formats: with and without microseconds
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

    # Find gaps larger than min_gap_hours
    sleep_periods = []
    for i in range(len(timestamps) - 1):
        gap = (timestamps[i + 1] - timestamps[i]).total_seconds() / 3600
        if gap >= min_gap_hours:
            # This is likely a sleep period
            sleep_periods.append((timestamps[i], timestamps[i + 1]))

    return sleep_periods


def find_day_boundaries(target_date: datetime, config: dict) -> tuple:
    """
    Find intelligent day boundaries based on sleep patterns.

    Strategy:
    - Query wider window (previous day 6 AM to next day 12 PM)
    - Detect sleep periods (gaps > 3 hours)
    - Find the wake-up time on target_date
    - Find the next sleep period after wake-up
    - If no clear sleep, use 6 AM cutoff as fallback

    Returns: (start_datetime, end_datetime)
    """
    # Query wider window to detect sleep patterns
    query_start = (target_date - timedelta(days=1)).replace(hour=6, minute=0, second=0)
    query_end = (target_date + timedelta(days=1)).replace(hour=12, minute=0, second=0)

    print(
        f"Analyzing activity patterns from {query_start.date()} to {query_end.date()}...",
        file=sys.stderr,
    )

    result = query_screenpipe(
        query_start.isoformat() + "Z", query_end.isoformat() + "Z", limit=3000
    )
    data = result.get("data", [])

    if not data:
        # Fallback to midnight if no data
        return (
            target_date.replace(hour=0, minute=0, second=0),
            target_date.replace(hour=23, minute=59, second=59),
        )

    # Detect sleep periods
    sleep_periods = detect_sleep_periods(data, config)

    print(f"Detected {len(sleep_periods)} sleep periods", file=sys.stderr)

    default_wake_hour = config.get("sleep_detection", {}).get("default_wake_hour", 6)
    late_night_cutoff = config.get("sleep_detection", {}).get(
        "late_night_cutoff_hour", 6
    )

    if not sleep_periods:
        # No clear sleep detected, use default boundaries
        # But shift to default_wake_hour as more natural boundary than midnight
        start_boundary = target_date.replace(hour=default_wake_hour, minute=0, second=0)
        end_boundary = (target_date + timedelta(days=1)).replace(
            hour=default_wake_hour, minute=0, second=0
        )
        print(
            f"No sleep detected, using {default_wake_hour} AM boundaries",
            file=sys.stderr,
        )
        return (start_boundary, end_boundary)

    # Find the wake-up time on target_date (first sleep end after target_date midnight)
    target_midnight = target_date.replace(hour=0, minute=0, second=0)
    target_next_midnight = target_midnight + timedelta(days=1)

    wake_up_time = None
    next_sleep_time = None

    for sleep_start, sleep_end in sleep_periods:
        # Find wake-up (sleep end) that falls within target date range
        # Consider late-night work: if wake up is before 6 AM on target_date,
        # it might be continuation from previous day
        if target_midnight <= sleep_end < target_next_midnight:
            # This wake-up is on target_date
            if wake_up_time is None or sleep_end < wake_up_time:
                wake_up_time = sleep_end

        # If sleep_end is in early morning (before late_night_cutoff) on target_date,
        # this is likely late-night work from previous day
        if (
            sleep_end.date() == target_date.date()
            and sleep_end.hour < late_night_cutoff
        ):
            # Check if there was activity before this sleep
            prev_day_evening = (target_date - timedelta(days=1)).replace(
                hour=18, minute=0
            )
            if sleep_start >= prev_day_evening:
                # Continuous work from previous evening through early morning
                # Include this in the journal
                wake_up_time = prev_day_evening
                print(
                    f"Detected late-night session: {prev_day_evening} → {sleep_end}",
                    file=sys.stderr,
                )

    # Find next sleep after wake-up
    if wake_up_time:
        for sleep_start, sleep_end in sleep_periods:
            if sleep_start > wake_up_time:
                next_sleep_time = sleep_start
                break

    # Determine boundaries
    if wake_up_time is None:
        # Fallback: use default_wake_hour on target_date
        start_boundary = target_date.replace(hour=default_wake_hour, minute=0, second=0)
    else:
        start_boundary = wake_up_time

    if next_sleep_time is None:
        # No clear next sleep, use default_wake_hour next day
        end_boundary = (target_date + timedelta(days=1)).replace(
            hour=default_wake_hour, minute=0, second=0
        )
    else:
        end_boundary = next_sleep_time

    print(f"Day boundaries: {start_boundary} → {end_boundary}", file=sys.stderr)
    print(
        f"Duration: {(end_boundary - start_boundary).total_seconds() / 3600:.1f} hours",
        file=sys.stderr,
    )

    return (start_boundary, end_boundary)


def generate_journal(date: datetime, config: dict) -> str:
    """Generate complete journal entry."""
    # Find intelligent day boundaries based on sleep patterns
    start_time, end_time = find_day_boundaries(date, config)

    # Query screenpipe with intelligent boundaries
    print(
        f"Querying screenpipe for {date.date()} (intelligent boundaries)...",
        file=sys.stderr,
    )
    result = query_screenpipe(
        start_time.isoformat() + "Z", end_time.isoformat() + "Z", limit=2000
    )
    data = result.get("data", [])

    if not data:
        print(f"No data found for {date.date()}", file=sys.stderr)
        return ""

    print(f"Found {len(data)} items", file=sys.stderr)

    # Group by content
    from generate_journal import group_by_content, extract_work_context

    hourly_content = group_by_content(data, config)

    # Build journal
    dendron_date = date.strftime("%Y.%m.%d")

    journal = [
        "---",
        f"id: daily.journal.{dendron_date}",
        f"title: '{dendron_date}'",
        "desc: ''",
        f"updated: {int(datetime.now().timestamp() * 1000)}",
        f"created: {int(date.timestamp() * 1000)}",
        "traitIds:",
        "  - journalNote",
        "---\n",
    ]

    # Day Summary - brief, scannable
    journal.append("## Day Summary\n")

    all_activities = Counter()
    for hour_data in hourly_content.values():
        for activity, items in hour_data.items():
            if activity != "Conversation":
                all_activities[activity] += len(items)

    if all_activities:
        top = all_activities.most_common(3)
        for activity, _ in top:
            journal.append(f"{activity}.\n")
    journal.append("")

    # Timeline
    journal.append("## Timeline\n")
    timeline = format_timeline(hourly_content, date)
    journal.extend(timeline)

    # State & Open Questions
    journal.append("## State & Open Questions\n")
    open_items = extract_open_questions(hourly_content)

    if open_items:
        for item in open_items:
            journal.append(f"**{item['type'].title()}**: {item['text']}...\n")
    else:
        journal.append(
            "_[Add manually: What's in progress? What's blocked? What's next?]_\n"
        )
    journal.append("")

    # Tasks
    journal.append("## Tasks\n")
    journal.append("### Inferred from Today\n")

    tasks = infer_tasks(hourly_content)
    if tasks:
        for task in tasks:
            journal.append(f"- [ ] {task}")
    else:
        journal.append("- [ ]")

    journal.append("\n### Completed Today\n")
    journal.append("- [x] \n")
    journal.append("\n## Notes\n")

    return "\n".join(journal)


def main():
    parser = argparse.ArgumentParser(
        description="Generate daily journal from screenpipe"
    )
    parser.add_argument("date", nargs="?", help='Date (YYYY-MM-DD) or "today"')
    parser.add_argument("--output", "-o", help="Output file path")

    args = parser.parse_args()

    config = load_config()

    # Parse date
    if not args.date or args.date == "today":
        target_date = datetime.now()
    else:
        target_date = datetime.strptime(args.date, "%Y-%m-%d")

    # Generate journal
    journal_content = generate_journal(target_date, config)

    if not journal_content:
        sys.exit(1)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(journal_content)
        print(f"Journal written to {args.output}", file=sys.stderr)
    else:
        print(journal_content)


if __name__ == "__main__":
    main()
