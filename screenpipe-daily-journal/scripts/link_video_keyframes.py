#!/usr/bin/env python3
"""
Create symlinks to screenpipe video files for key moments instead of extracting frames.
Saves storage and allows viewing video context.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
import urllib.request


def link_video_keyframes(date_str: str, output_dir: Path):
    """Create symlinks to MP4 videos for key moments."""

    date = datetime.strptime(date_str, "%Y-%m-%d")
    start = date.replace(hour=0, minute=0).isoformat() + "Z"
    end = date.replace(hour=23, minute=59).isoformat() + "Z"

    # Query screenpipe
    url = f"http://localhost:3030/search?start_time={start}&end_time={end}&content_type=ocr&limit=500&min_length=150"

    with urllib.request.urlopen(url, timeout=30) as response:
        data = json.load(response)

    items = data.get("data", [])

    # Filter and sort
    candidates = []
    for item in items:
        content = item["content"]
        text = content.get("text", "").strip()
        app = content.get("app_name", "")

        # Skip utility windows
        if app in ["screenpipe", "Bartender 5", "Wispr Flow", "Settings"]:
            continue

        if len(text) < 150:
            continue

        video_path = content.get("file_path")
        if not video_path or not Path(video_path).exists():
            continue

        candidates.append(
            {
                "text_len": len(text),
                "app": app,
                "window": content.get("window_name", ""),
                "text": text[:200],
                "video": video_path,
                "offset": content.get("offset_index", 0),
                "timestamp": content.get("timestamp"),
            }
        )

    # Take top 5
    candidates = sorted(candidates, key=lambda x: x["text_len"], reverse=True)[:5]

    # Create symlinks
    output_dir.mkdir(parents=True, exist_ok=True)

    keyframes = []
    for i, item in enumerate(candidates, 1):
        video_path = Path(item["video"])

        # Create symlink with descriptive name
        link_name = f"journal_{date_str}_moment_{i}.mp4"
        link_path = output_dir / link_name

        # Remove existing symlink if present
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()

        # Create symlink
        link_path.symlink_to(video_path)

        ts = datetime.fromisoformat(
            item["timestamp"].replace("Z", "+00:00")
        ).astimezone()
        time_str = ts.strftime("%I:%M %p")

        keyframes.append(
            {
                "time": time_str,
                "title": item["window"] or item["app"],
                "filename": link_name,
                "text": item["text"],
                "offset": item["offset"],
            }
        )

        print(
            f"✓ Linked: {link_name} -> {video_path.name} (offset: {item['offset']})",
            file=sys.stderr,
        )

    # Output markdown
    print("\n## Key Moments\n")
    for kf in keyframes:
        print(f"### [{kf['time']}] {kf['title']}\n")
        print(f'<video width="800" controls>')
        print(
            f"  <source src=\"assets/{kf['filename']}#t={kf['offset']*2}\" type=\"video/mp4\">"
        )
        print(f"</video>\n")
        text_clean = " ".join(kf["text"].split())[:150]
        print(f"{text_clean}...\n")


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    assets_dir = Path.home() / "Documents/Manual Library/Dendron/notes/assets"

    link_video_keyframes(date_arg, assets_dir)
