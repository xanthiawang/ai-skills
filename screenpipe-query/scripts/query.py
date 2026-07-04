#!/usr/bin/env python3
"""
Universal screenpipe query interface with natural language support.
"""

import json
import sys
import re
import argparse
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import urllib.request
import urllib.parse

DEFAULT_PORT = 3030
SCREENPIPE_API = f"http://localhost:{DEFAULT_PORT}"

# Common app aliases
APP_ALIASES = {
    "code": "Cursor",
    "editor": "Cursor",
    "terminal": "Terminal",
    "shell": "Terminal",
    "email": "Gmail",
    "mail": "Gmail",
    "chat": "Slack",
    "zoom": "zoom.us",
    "teams": "Microsoft Teams",
    "excel": "Microsoft Excel",
    "powerpoint": "Microsoft PowerPoint",
    "chrome": "Google Chrome",
    "browser": "Safari",
}

# Time patterns
TIME_PATTERNS = {
    r"this morning": lambda: (
        datetime.now().replace(hour=9, minute=0),
        datetime.now().replace(hour=12, minute=0),
    ),
    r"this afternoon": lambda: (
        datetime.now().replace(hour=12, minute=0),
        datetime.now().replace(hour=17, minute=0),
    ),
    r"this evening": lambda: (
        datetime.now().replace(hour=17, minute=0),
        datetime.now().replace(hour=21, minute=0),
    ),
    r"today": lambda: (datetime.now().replace(hour=0, minute=0), datetime.now()),
    r"yesterday": lambda: (
        (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0),
        (datetime.now() - timedelta(days=1)).replace(hour=23, minute=59),
    ),
    r"last (\d+) hours?": lambda h: (
        datetime.now() - timedelta(hours=int(h)),
        datetime.now(),
    ),
    r"last (\d+) days?": lambda d: (
        datetime.now() - timedelta(days=int(d)),
        datetime.now(),
    ),
}


def parse_natural_language(query: str) -> Dict:
    """Parse natural language query into API parameters."""
    params = {}
    query_lower = query.lower()

    # Extract time
    for pattern, time_func in TIME_PATTERNS.items():
        match = re.search(pattern, query_lower)
        if match:
            if match.groups():
                start, end = time_func(match.group(1))
            else:
                start, end = time_func()

            params["start_time"] = start.isoformat() + "Z"
            params["end_time"] = end.isoformat() + "Z"
            break

    # Extract app
    for alias, app_name in APP_ALIASES.items():
        if alias in query_lower:
            params["app_name"] = app_name
            break

    # Detect content type
    if any(
        word in query_lower
        for word in ["said", "conversation", "audio", "talking", "speaking"]
    ):
        params["content_type"] = "audio"
    elif any(word in query_lower for word in ["screen", "text", "typed", "wrote"]):
        params["content_type"] = "ocr"
    else:
        params["content_type"] = "all"

    # Extract search terms (remove time and app mentions)
    search_terms = query
    for pattern in TIME_PATTERNS.keys():
        search_terms = re.sub(pattern, "", search_terms, flags=re.IGNORECASE)
    for alias in APP_ALIASES.keys():
        search_terms = re.sub(
            r"\b" + alias + r"\b", "", search_terms, flags=re.IGNORECASE
        )

    search_terms = search_terms.strip()

    # Remove question words
    search_terms = re.sub(
        r"\b(what|when|where|who|how|did|was|were|is|are|in|on|at)\b",
        "",
        search_terms,
        flags=re.IGNORECASE,
    )
    search_terms = " ".join(search_terms.split())

    if search_terms and len(search_terms) > 2:
        params["q"] = search_terms

    # Default limit
    if "limit" not in params:
        params["limit"] = 50

    return params


def query_screenpipe(params: Dict) -> Dict:
    """Query screenpipe API."""
    query_string = urllib.parse.urlencode(params)
    url = f"{SCREENPIPE_API}/search?{query_string}"

    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Error querying screenpipe: {e}", file=sys.stderr)
        return {"data": [], "error": str(e)}


def format_results(results: Dict, verbose: bool = False) -> str:
    """Format results for display."""
    data = results.get("data", [])
    pagination = results.get("pagination", {})

    if not data:
        return "No results found."

    lines = [
        f"Found {pagination.get('total', len(data))} results (showing {len(data)}):\n"
    ]

    for i, item in enumerate(data, 1):
        content = item["content"]
        ts = datetime.fromisoformat(
            content["timestamp"].replace("Z", "+00:00")
        ).astimezone()
        time_str = ts.strftime("%I:%M:%S %p")

        lines.append(f"[{i}] {time_str}")

        if item["type"] == "OCR":
            app = content.get("app_name", "Unknown")
            window = content.get("window_name", "")
            text = content.get("text", "").strip()

            lines.append(f"    App: {app}")
            if window and window != app:
                lines.append(f"    Window: {window}")

            if verbose:
                lines.append(f"    Text: {text[:200]}")
            else:
                lines.append(f"    Text: {text[:100]}...")

        elif item["type"] == "Audio":
            device = content.get("device_name", "Unknown")
            trans = content.get("transcription", "").strip()
            speaker_id = content.get("speaker", {}).get("id", "Unknown")

            lines.append(f"    Device: {device}")
            lines.append(f"    Speaker: {speaker_id}")

            if verbose:
                lines.append(f"    Transcription: {trans}")
            else:
                lines.append(f"    Transcription: {trans[:100]}...")

        lines.append("")

    return "\n".join(lines)


def export_to_json(results: Dict, output_file: str):
    """Export results to JSON file."""
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results exported to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Query screenpipe recordings")
    parser.add_argument("query", nargs="*", help="Natural language query")
    parser.add_argument("--app", help="Filter by application")
    parser.add_argument("--window", help="Filter by window name")
    parser.add_argument("--type", choices=["all", "ocr", "audio"], help="Content type")
    parser.add_argument("--start", help="Start time (ISO 8601)")
    parser.add_argument("--end", help="End time (ISO 8601)")
    parser.add_argument("--limit", type=int, default=50, help="Max results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", help="Export to JSON file")
    parser.add_argument("--raw", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    # Build query parameters
    if args.query:
        # Natural language query
        query_str = " ".join(args.query)
        params = parse_natural_language(query_str)
    else:
        params = {}

    # Override with explicit parameters
    if args.app:
        params["app_name"] = args.app
    if args.window:
        params["window_name"] = args.window
    if args.type:
        params["content_type"] = args.type
    if args.start:
        params["start_time"] = args.start
    if args.end:
        params["end_time"] = args.end
    if args.limit:
        params["limit"] = args.limit

    if not params:
        print("Error: No query parameters specified", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    print(f"Query parameters: {json.dumps(params, indent=2)}", file=sys.stderr)

    # Execute query
    results = query_screenpipe(params)

    if "error" in results:
        print(f"Error: {results['error']}", file=sys.stderr)
        sys.exit(1)

    # Output results
    if args.raw:
        print(json.dumps(results, indent=2))
    elif args.json:
        export_to_json(results, args.json)
    else:
        print(format_results(results, verbose=args.verbose))


if __name__ == "__main__":
    main()
