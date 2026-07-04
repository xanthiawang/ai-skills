#!/usr/bin/env python3
"""
Extract a single keyframe screenshot at a specific timestamp.
Called by Cursor Agent after identifying important moments in timeline.

Usage:
    python extract_keyframe_at_time.py --date 2026-01-31 --timestamp "2026-01-31T19:30:00" --output journal_2026-01-31_moment_1
"""

import argparse
import json
import os
import sys
from pathlib import Path
import requests
from datetime import datetime
import base64


def extract_keyframe(date: str, timestamp: str, output_name: str, vault_path: Path):
    """Extract a single keyframe at the specified timestamp."""

    screenpipe_url = "http://localhost:3030"

    # Parse timestamp
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as e:
        print(f"❌ Invalid timestamp format: {timestamp}")
        print(f"   Expected: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SS-HH:MM")
        sys.exit(1)

    # Query screenpipe for frames around this timestamp (±30 seconds)
    start_time = dt.replace(second=max(0, dt.second - 30)).isoformat()
    end_time = dt.replace(second=min(59, dt.second + 30)).isoformat()

    print(f"🔍 Searching for frame near {timestamp}...")

    params = {
        "start_time": start_time,
        "end_time": end_time,
        "limit": 10,
        "content_type": "ocr",
        "include_frames": "true",
    }

    try:
        response = requests.get(f"{screenpipe_url}/search", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error querying screenpipe: {e}")
        sys.exit(1)

    if not data.get("data"):
        print(f"❌ No frames found near {timestamp}")
        sys.exit(1)

    # Find frame closest to target timestamp
    target_ts = dt.timestamp()
    best_frame = None
    min_diff = float("inf")

    for item in data["data"]:
        if "content" in item and "frame" in item["content"]:
            item_ts = datetime.fromisoformat(
                item["content"]["timestamp"].replace("Z", "+00:00")
            ).timestamp()
            diff = abs(item_ts - target_ts)
            if diff < min_diff:
                min_diff = diff
                best_frame = item["content"]["frame"]

    if not best_frame:
        print(f"❌ No valid frame found")
        sys.exit(1)

    # Save keyframe as PNG
    assets_dir = vault_path / "assets"
    assets_dir.mkdir(exist_ok=True)

    output_path = assets_dir / f"{output_name}.png"

    try:
        # Decode base64 frame
        frame_data = base64.b64decode(best_frame)
        output_path.write_bytes(frame_data)
        print(f"✅ Saved: {output_path}")
    except Exception as e:
        print(f"❌ Error saving frame: {e}")
        sys.exit(1)

    # Create video symlink (will be handled by link_video_keyframes.py separately)
    print(
        f"📹 Note: Run link_video_keyframes.py to create video symlink for this keyframe"
    )

    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Extract keyframe at specific timestamp"
    )
    parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD)")
    parser.add_argument("--timestamp", required=True, help="Timestamp (ISO format)")
    parser.add_argument(
        "--output", required=True, help="Output name (without extension)"
    )
    parser.add_argument("--vault", default=None, help="Vault path (optional)")

    args = parser.parse_args()

    # Default vault path
    if args.vault:
        vault_path = Path(args.vault)
    else:
        vault_path = Path.home() / "Documents" / "Manual Library" / "Dendron" / "notes"

    if not vault_path.exists():
        print(f"❌ Vault not found: {vault_path}")
        sys.exit(1)

    extract_keyframe(args.date, args.timestamp, args.output, vault_path)


if __name__ == "__main__":
    main()
