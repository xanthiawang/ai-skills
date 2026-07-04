#!/usr/bin/env python3
"""
Generate daily journal from screenpipe with AI-powered analysis.
Uses Claude to produce human-quality journal entries.
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
import subprocess

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


def extract_work_context(text: str) -> str:
    """Infer activity from OCR content."""
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

    return None


def group_by_content(items: list, config: dict) -> dict:
    """Group activities by content and time."""
    hourly_content = defaultdict(lambda: defaultdict(list))

    for item in items:
        ts = datetime.fromisoformat(item["content"]["timestamp"].replace("Z", "+00:00"))
        local_ts = ts.astimezone()
        hour = local_ts.hour

        if item["type"] == "OCR":
            text = item["content"].get("text", "").strip()
            if len(text) < 30:
                continue

            context = extract_work_context(text)
            if context:
                hourly_content[hour][context].append(text[:300])

        elif item["type"] == "Audio":
            trans = item["content"].get("transcription", "").strip()
            if len(trans) > 20:
                hourly_content[hour]["Conversation"].append(trans[:200])

    return hourly_content


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
            sleep_periods.append((timestamps[i], timestamps[i + 1]))

    return sleep_periods


def find_day_boundaries(target_date: datetime, config: dict) -> tuple:
    """Find intelligent day boundaries based on sleep patterns."""
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
        return (
            target_date.replace(hour=0, minute=0, second=0),
            target_date.replace(hour=23, minute=59, second=59),
        )

    sleep_periods = detect_sleep_periods(data, config)
    print(f"Detected {len(sleep_periods)} sleep periods", file=sys.stderr)

    default_wake_hour = config.get("sleep_detection", {}).get("default_wake_hour", 6)

    if not sleep_periods:
        start_boundary = target_date.replace(hour=default_wake_hour, minute=0, second=0)
        end_boundary = (target_date + timedelta(days=1)).replace(
            hour=default_wake_hour, minute=0, second=0
        )
        print(
            f"No sleep detected, using {default_wake_hour} AM boundaries",
            file=sys.stderr,
        )
        return (start_boundary, end_boundary)

    # Find wake-up time on target date
    target_midnight = target_date.replace(hour=0, minute=0, second=0)
    target_next_midnight = target_midnight + timedelta(days=1)

    wake_up_time = None
    next_sleep_time = None

    for sleep_start, sleep_end in sleep_periods:
        if target_midnight <= sleep_end < target_next_midnight:
            if wake_up_time is None or sleep_end < wake_up_time:
                wake_up_time = sleep_end

    if wake_up_time:
        for sleep_start, sleep_end in sleep_periods:
            if sleep_start > wake_up_time:
                next_sleep_time = sleep_start
                break

    start_boundary = (
        wake_up_time
        if wake_up_time
        else target_date.replace(hour=default_wake_hour, minute=0, second=0)
    )
    end_boundary = (
        next_sleep_time
        if next_sleep_time
        else (target_date + timedelta(days=1)).replace(
            hour=default_wake_hour, minute=0, second=0
        )
    )

    print(f"Day boundaries: {start_boundary} → {end_boundary}", file=sys.stderr)
    return (start_boundary, end_boundary)


def prepare_ai_context(hourly_content: dict, date: datetime) -> str:
    """Prepare structured data for AI analysis."""
    context_parts = []

    for hour in sorted(hourly_content.keys()):
        hour_12 = hour % 12 or 12
        period = "PM" if hour >= 12 else "AM"
        hour_data = hourly_content[hour]

        if not hour_data:
            continue

        context_parts.append(f"\n=== {hour_12}:00 {period} ===\n")

        for activity, items in sorted(
            hour_data.items(), key=lambda x: len(x[1]), reverse=True
        ):
            context_parts.append(f"\n[{activity}]")
            # Sample of content
            for text in items[:5]:
                clean = " ".join(text.split())[:150]
                context_parts.append(f"  {clean}")

    return "\n".join(context_parts)


def call_claude_for_analysis(context: str, date: datetime, keyframes: list) -> dict:
    """Use Claude to analyze the day and generate journal content."""

    keyframe_desc = (
        "\n".join([f"- {kf['hour']}:00: {kf['context'][:100]}" for kf in keyframes[:5]])
        if keyframes
        else "No keyframes extracted"
    )

    prompt = f"""You are analyzing screen activity data from {date.strftime('%Y-%m-%d')} to generate a daily journal entry.

SCREEN ACTIVITY DATA:
{context}

KEYFRAMES AVAILABLE:
{keyframe_desc}

Generate a journal entry in this EXACT structure:

## Day Summary

[2-3 sentences: What did you work on? Be specific about projects, not just categories. Example: "Built screenpipe journal automation system. UMich faculty interview preparation. Email correspondence about protein clock collaboration."]

## Timeline

[Group activities by time blocks (hour or multi-hour sessions). For EACH block include:
- Hour header (### HH:00 AM/PM)
- Activity headers (**Activity Name**)
- SPECIFIC DETAILS: What you did/decided, not just what you touched
- Decisions made: prefix with "Decision:"
- Blockers: prefix with "Blocked:"
- Important quotes: use 🎤 for audio transcriptions (only if meaningful)
- If keyframe available, embed: ![Context description](assets/journal_{date.strftime("%Y-%m-%d")}_moment_N.png)]

## State & Open Questions

[Structured by project/area:
**Project/Area Name**
- Status: [current state]
- Blocker: [what's blocking progress, if any]
- Next: [next concrete step]

Only include active projects.]

## Tasks

### Inferred from Today
[Extract REAL tasks from the content. Each task must be:
- Actionable (starts with verb)
- Specific (mentions what/who)
- Sensible (not OCR garbage)
Format: - [ ] Task description
Skip if no clear tasks found]

### Completed Today
[Leave empty or add [x] tasks if explicitly mentioned as done]

## Notes
[Optional: Meta-observations, patterns, or insights about the day]

CRITICAL RULES:
1. Write like a human competent professional - clear, specific, concrete
2. Focus on WHAT you did/decided, not just WHAT app you used
3. Include decisions and blockers when you see them
4. Filter audio quotes - only include meaningful ones, not every utterance
5. Tasks must make sense - filter out OCR garbage
6. Be specific: "Drafted email to Brian Athey" not "Worked on email"
7. Short sentences are fine. No fancy prose.
8. Skip empty sections rather than filling with placeholders

Return ONLY the markdown content for these sections, no preamble."""

    try:
        # Call Claude via API
        result = subprocess.run(
            [
                "curl",
                "-s",
                "https://api.anthropic.com/v1/messages",
                "-H",
                "content-type: application/json",
                "-H",
                f"x-api-key: {os.environ.get('ANTHROPIC_API_KEY', '')}",
                "-H",
                "anthropic-version: 2023-06-01",
                "-d",
                json.dumps(
                    {
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 4096,
                        "messages": [{"role": "user", "content": prompt}],
                    }
                ),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            response = json.loads(result.stdout)
            content = response.get("content", [{}])[0].get("text", "")
            return {"success": True, "content": content}
        else:
            print(f"Claude API error: {result.stderr}", file=sys.stderr)
            return {"success": False, "error": result.stderr}

    except Exception as e:
        print(f"Error calling Claude: {e}", file=sys.stderr)
        return {"success": False, "error": str(e)}


def find_keyframes(date: datetime, vault_path: str) -> list:
    """Find existing keyframes for this date."""
    assets_dir = Path(vault_path) / "assets"
    keyframes = []

    pattern = f"journal_{date.strftime('%Y-%m-%d')}_moment_*.png"

    for img in assets_dir.glob(pattern):
        # Extract moment number
        match = re.search(r"moment_(\d+)\.png", img.name)
        if match:
            moment_num = match.group(1)
            # Try to read context from nearby files
            keyframes.append(
                {
                    "number": moment_num,
                    "path": f"assets/{img.name}",
                    "hour": 0,  # Would need to extract from screenshot metadata
                    "context": "",
                }
            )

    return sorted(keyframes, key=lambda x: x["number"])


def generate_journal(date: datetime, config: dict) -> str:
    """Generate complete journal entry with AI analysis."""
    # Find intelligent day boundaries
    start_time, end_time = find_day_boundaries(date, config)

    # Query screenpipe
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

    # Group content
    hourly_content = group_by_content(data, config)

    # Find keyframes
    vault_path = config.get("journal_path", "")
    keyframes = find_keyframes(date, vault_path) if vault_path else []

    # Prepare context for AI
    context = prepare_ai_context(hourly_content, date)

    # Call Claude for analysis
    print("Analyzing with Claude...", file=sys.stderr)
    ai_result = call_claude_for_analysis(context, date, keyframes)

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

    if ai_result["success"]:
        journal.append(ai_result["content"])
    else:
        # Fallback to basic format if AI fails
        journal.extend(
            [
                "## Day Summary\n",
                "_[AI analysis unavailable - add summary manually]_\n",
                "\n## Timeline\n",
                "_[AI analysis unavailable - review raw data]_\n",
            ]
        )

    return "\n".join(journal)


def main():
    parser = argparse.ArgumentParser(
        description="Generate daily journal from screenpipe with AI analysis"
    )
    parser.add_argument("date", nargs="?", help='Date (YYYY-MM-DD) or "today"')
    parser.add_argument("--output", "-o", help="Output file path")

    args = parser.parse_args()

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "Warning: ANTHROPIC_API_KEY not set. AI analysis will fail.",
            file=sys.stderr,
        )

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
