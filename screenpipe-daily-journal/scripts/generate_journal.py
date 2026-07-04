#!/usr/bin/env python3
"""
Generate daily journal from screenpipe - content-focused, not app-focused.
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


def extract_work_context(text: str, window: str = None) -> str:
    """Extract what the user was actually working on from OCR text ONLY.

    CRITICAL: Screenpipe's metadata (app_name, window_name) is UNRELIABLE.
    We IGNORE the 'window' parameter completely and infer activity from OCR content patterns.

    Example OCR patterns:
    - "def function_name" → Coding
    - "Terminal" + "$ commands" → Terminal work
    - Email UI elements → Email
    - Browser with URLs → Web browsing
    """
    # Common patterns - infer from OCR content only
    text_lower = text.lower()

    # Terminal/shell work - look for command prompts
    if any(pattern in text for pattern in ["$ ", "~ %", "›", "❯", "bash", "zsh"]):
        if "python" in text_lower or ".py" in text:
            return "Terminal - Python development"
        elif "git" in text_lower:
            return "Terminal - Git operations"
        return "Terminal work"

    # Code editor - look for code patterns
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
        # Try to identify language
        if "def " in text_lower and ":" in text:
            return "Coding - Python"
        elif "function" in text_lower or "const " in text_lower:
            return "Coding - JavaScript"
        return "Coding/development"

    # Browser - look for URL patterns
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

    # Project/file names
    if "proj." in text_lower:
        for word in text.split():
            if "proj." in word.lower():
                return f"Working on {word}"

    # Meeting notes
    if "meet." in text.lower() or "meeting" in text_lower:
        if "umich" in text_lower or "michigan" in text_lower:
            return "Faculty interview prep (UMich)"
        return "Meeting notes"

    # Dendron/notes
    if "dendron" in text_lower or ".md" in text:
        if "journal" in text_lower:
            return "Journal generation"
        elif "skill" in text_lower:
            return "Skills development"
        return "Note-taking"

    # Research
    if (
        "paper" in text_lower
        or "zotero" in text_lower
        or "doi" in text_lower
        or "pubmed" in text_lower
    ):
        return "Research/reading papers"

    # Email - look for email UI elements
    if any(
        pattern in text_lower
        for pattern in ["inbox", "compose", "reply", "subject:", "from:", "to:"]
    ):
        if "donghyun" in text_lower:
            return "Email correspondence (Donghyun)"
        return "Email"

    # Communication apps - look for app-specific UI
    if "slack" in text_lower or "channel" in text_lower:
        return "Slack - Team communication"
    if "zoom" in text_lower or "meeting id" in text_lower:
        return "Zoom meeting"
    if "teams" in text_lower:
        return "Microsoft Teams"
    if "whatsapp" in text_lower:
        return "WhatsApp"

    # Document editing - look for UI elements
    if any(
        pattern in text_lower
        for pattern in ["autosave", "font", "paragraph", "formatting"]
    ):
        if "slide" in text_lower:
            return "Presentation editing"
        return "Document editing"

    # NO FALLBACK TO SCREENPIPE METADATA - it's unreliable
    # If we can't infer from OCR, return None
    return None


def group_by_content(items: list, config: dict) -> dict:
    """Group activities by actual content, not apps."""
    hourly_content = defaultdict(lambda: defaultdict(list))

    for item in items:
        ts = datetime.fromisoformat(item["content"]["timestamp"].replace("Z", "+00:00"))
        local_ts = ts.astimezone()
        hour = local_ts.hour

        if item["type"] == "OCR":
            text = item["content"].get("text", "").strip()
            # NOTE: We deliberately IGNORE app_name and window_name metadata
            # because screenpipe's metadata is unreliable. We infer from OCR content only.

            # Skip very short text (likely noise)
            if len(text) < 30:
                continue

            # Extract what they were working on FROM OCR CONTENT ONLY
            context = extract_work_context(text)
            if context:
                hourly_content[hour][context].append(text[:200])

        elif item["type"] == "Audio":
            trans = item["content"].get("transcription", "").strip()
            if len(trans) > 20:
                hourly_content[hour]["Conversation"].append(trans)

    return hourly_content


def generate_insights(hourly_content: dict) -> list:
    """Generate insights from content."""
    insights = []

    # What they spent most time on
    all_activities = Counter()
    for hour_data in hourly_content.values():
        for activity, items in hour_data.items():
            all_activities[activity] += len(items)

    if all_activities:
        top = all_activities.most_common(3)
        activities = [act for act, _ in top if act != "Conversation"]
        if activities:
            insights.append(f"Main focus: {', '.join(activities)}")

    # Collaboration level
    total_convs = sum(
        len(hour_data.get("Conversation", [])) for hour_data in hourly_content.values()
    )
    if total_convs > 20:
        insights.append(f"High collaboration day ({total_convs} conversations)")
    elif total_convs > 0:
        insights.append(f"Some collaboration ({total_convs} conversations)")

    return insights


def format_journal(date: datetime, hourly_content: dict, config: dict) -> str:
    """Format journal with content focus."""
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

    # Insights
    insights = generate_insights(hourly_content)
    if insights:
        journal.append("## 🔑 Key Insights\n")
        for insight in insights:
            journal.append(f"- {insight}")
        journal.append("")

    # Timeline - content focused
    journal.append("## ⏱️ Timeline\n")

    for hour in sorted(hourly_content.keys()):
        hour_12 = hour % 12 or 12
        period = "PM" if hour >= 12 else "AM"
        hour_data = hourly_content[hour]

        if not hour_data:
            continue

        journal.append(f"### {hour_12}:00 {period}\n")

        # List what they worked on (not apps)
        for activity, items in sorted(
            hour_data.items(), key=lambda x: len(x[1]), reverse=True
        ):
            if activity == "Conversation":
                # Show conversations
                for conv in items[:2]:
                    journal.append(f'- 🎤 "{conv}"')
            else:
                # Show work activities
                journal.append(f"**{activity}**")
                # Add some context if available
                if items and len(items[0]) > 50:
                    sample = " ".join(items[0].split())[:120]
                    journal.append(f"  _{sample}_")

        journal.append("")

    # Knowledge base additions
    journal.append("## 📝 Knowledge Base Additions\n")

    # Extract important info
    contacts = set()
    decisions = []
    research = []

    for hour_data in hourly_content.values():
        for activity, items in hour_data.items():
            for text in items:
                text_lower = text.lower()

                # Find names/contacts
                if "@" in text or "email" in text_lower:
                    words = text.split()
                    for i, word in enumerate(words):
                        if word[0].isupper() and len(word) > 3 and i > 0:
                            if words[i - 1].lower() in ["with", "from", "to", "email"]:
                                contacts.add(word)

                # Find decisions
                if any(
                    phrase in text_lower
                    for phrase in ["decided", "chose", "selected", "going with"]
                ):
                    decisions.append(text[:100])

                # Find research items
                if any(
                    word in text_lower
                    for word in ["paper", "research", "study", "doi", "arxiv"]
                ):
                    research.append(text[:100])

    journal.append("### New Contacts\n")
    if contacts:
        for contact in list(contacts)[:5]:
            journal.append(f"- {contact}")
    journal.append("\n### Key Decisions\n")
    if decisions:
        for decision in decisions[:3]:
            journal.append(f"- {decision}...")
    journal.append("\n### Research & Development\n")
    if research:
        for item in research[:3]:
            journal.append(f"- {item}...")

    journal.append("\n## ✅ Inferred Tasks\n")
    journal.append("### From Audio/Text\n")

    # Task detection
    tasks = set()
    for hour_data in hourly_content.values():
        for activity, items in hour_data.items():
            for text in items:
                text_lower = text.lower()

                # Look for task patterns
                task_patterns = [
                    ("need to", r"need to (.+?)[\.\,]"),
                    ("should", r"should (.+?)[\.\,]"),
                    ("will", r"will (.+?)[\.\,]"),
                    ("going to", r"going to (.+?)[\.\,]"),
                    ("plan to", r"plan to (.+?)[\.\,]"),
                ]

                for pattern, regex in task_patterns:
                    if pattern in text_lower:
                        import re

                        matches = re.findall(regex, text_lower)
                        for match in matches:
                            if 10 < len(match) < 80:
                                task = match.strip().capitalize()
                                tasks.add(task)

    for task in list(tasks)[:8]:
        journal.append(f"- [ ] {task}")

    if not tasks:
        journal.append("- No explicit tasks detected")

    journal.append("\n### From Work Context\n")
    journal.append("- [ ] Continue ongoing projects\n")

    # Manual sections
    journal.extend(
        [
            "\n## Task created\n",
            "- [ ] \n",
            "## Task done\n",
            "\n",
            "## Read\n",
            "\n",
            "## Thought\n",
        ]
    )

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

    # Query screenpipe
    start_time = target_date.replace(hour=0, minute=0, second=0).isoformat() + "Z"
    end_time = target_date.replace(hour=23, minute=59, second=59).isoformat() + "Z"

    print(f"Querying screenpipe for {target_date.date()}...", file=sys.stderr)
    result = query_screenpipe(start_time, end_time, limit=2000)
    data = result.get("data", [])

    if not data:
        print(f"No data found for {target_date.date()}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(data)} items", file=sys.stderr)

    # Group by content
    hourly_content = group_by_content(data, config)

    # Generate journal
    journal_content = format_journal(target_date, hourly_content, config)

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(journal_content)
        print(f"Journal written to {args.output}", file=sys.stderr)
    else:
        print(journal_content)


if __name__ == "__main__":
    main()
