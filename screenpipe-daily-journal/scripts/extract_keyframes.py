#!/usr/bin/env python3
"""
Extract keyframes from screenpipe videos and embed in journal.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import urllib.request


def extract_frame_from_video(video_path: str, offset: int, output_path: str) -> bool:
    """Extract single frame from video using ffmpeg."""
    if not Path(video_path).exists():
        return False

    # Calculate timestamp (0.5 FPS = 2 seconds per frame)
    timestamp = offset * 2

    cmd = [
        "ffmpeg",
        "-ss",
        str(timestamp),
        "-i",
        video_path,
        "-frames:v",
        "1",
        "-y",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        return result.returncode == 0 and Path(output_path).exists()
    except:
        return False


def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    date = datetime.strptime(date_arg, "%Y-%m-%d")

    # Query screenpipe
    start = date.replace(hour=0, minute=0).isoformat() + "Z"
    end = date.replace(hour=23, minute=59).isoformat() + "Z"

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

        if app in ["screenpipe", "Bartender 5", "Wispr Flow", "Settings"]:
            continue

        if len(text) < 150:
            continue

        candidates.append(
            {
                "text_len": len(text),
                "app": app,
                "window": content.get("window_name", ""),
                "text": text[:200],
                "video": content.get("file_path"),
                "offset": content.get("offset_index", 0),
                "timestamp": content.get("timestamp"),
            }
        )

    # Take top 5
    candidates = sorted(candidates, key=lambda x: x["text_len"], reverse=True)[:5]

    # Extract frames
    assets_dir = Path.home() / "Documents/Manual Library/Dendron/notes/assets"
    assets_dir.mkdir(exist_ok=True)

    keyframes = []
    for i, item in enumerate(candidates, 1):
        if not item["video"]:
            continue

        filename = f"journal_{date_arg}_moment_{i}.png"
        output_path = assets_dir / filename

        success = extract_frame_from_video(
            item["video"], item["offset"], str(output_path)
        )

        if success:
            ts = datetime.fromisoformat(
                item["timestamp"].replace("Z", "+00:00")
            ).astimezone()
            time_str = ts.strftime("%I:%M %p")

            keyframes.append(
                {
                    "time": time_str,
                    "title": item["window"] or item["app"],
                    "filename": filename,
                    "text": item["text"],
                }
            )
            print(f"✓ Extracted: {filename}", file=sys.stderr)

    # Output markdown
    print("\n## 📸 Key Moments\n")
    for kf in keyframes:
        print(f"### [{kf['time']}] {kf['title']}")
        print(f"![Screenshot](assets/{kf['filename']})")
        text_clean = " ".join(kf["text"].split())[:150]
        print(f"{text_clean}...\n")


if __name__ == "__main__":
    main()
