#!/usr/bin/env python3
"""
Extract candidate names from screenpipe data with MINIMAL filtering.
The AI agent will do the intelligent validation.
"""

import json
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.parse
from typing import List, Dict


def extract_candidate_names(text: str, context_window: int = 30) -> List[Dict]:
    """
    Extract potential names with minimal filtering.
    Returns list of {name, context} dicts.
    Let AI decide what's real.
    """
    candidates = []
    words = text.split()

    # Look for capitalized word pairs (basic pattern for names)
    for i, word in enumerate(words):
        if not word or len(word) < 2:
            continue

        # Must start with capital letter and be mostly alphabetic
        if not (
            word[0].isupper() and sum(c.isalpha() for c in word) >= len(word) * 0.7
        ):
            continue

        # Check next word
        if i + 1 < len(words):
            next_word = words[i + 1]

            if not next_word or len(next_word) < 2:
                continue

            # Next word should also be capitalized and alphabetic
            if (
                next_word[0].isupper()
                and sum(c.isalpha() for c in next_word) >= len(next_word) * 0.7
            ):
                candidate_name = f"{word} {next_word}"

                # Get surrounding context
                context_start = max(0, i - context_window)
                context_end = min(len(words), i + context_window + 2)
                context = " ".join(words[context_start:context_end])

                candidates.append({"name": candidate_name, "context": context})

    return candidates


def main():
    vault_path = Path.home() / "Documents/Manual Library/Dendron/notes"

    # Date to process
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    date = datetime.strptime(date_str, "%Y-%m-%d")

    # Query screenpipe for full calendar day
    start = date.replace(hour=0, minute=0, second=0).isoformat() + "Z"
    end = date.replace(hour=23, minute=59, second=59).isoformat() + "Z"

    url = f"http://localhost:3030/search?start_time={start}&end_time={end}&limit=1000"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.load(response)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    items = data.get("data", [])

    # Extract candidates from OCR and Audio separately
    ocr_candidates = {}
    audio_candidates = {}

    for item in items:
        if item["type"] == "OCR":
            text = item["content"].get("text", "")
            candidates = extract_candidate_names(text)

            for candidate in candidates:
                name = candidate["name"]
                if name not in ocr_candidates:
                    ocr_candidates[name] = {
                        "context": candidate["context"],
                        "source": "OCR",
                        "count": 1,
                    }
                else:
                    ocr_candidates[name]["count"] += 1

        elif item["type"] == "Audio":
            text = item["content"].get("transcription", "")
            candidates = extract_candidate_names(text)

            for candidate in candidates:
                name = candidate["name"]
                if name not in audio_candidates:
                    audio_candidates[name] = {
                        "context": candidate["context"],
                        "source": "Audio",
                        "count": 1,
                    }
                else:
                    audio_candidates[name]["count"] += 1

    # Get existing users
    existing_users = []
    for user_file in vault_path.glob("user.*.md"):
        try:
            content = user_file.read_text()
            title_match = re.search(r"^title:\s*(.+)$", content, re.MULTILINE)
            if title_match:
                existing_users.append(
                    {
                        "slug": user_file.stem.replace("user.", ""),
                        "name": title_match.group(1).strip(),
                    }
                )
        except:
            continue

    # Output JSON for AI agent
    output = {
        "date": date_str,
        "candidates": {
            "ocr": [
                {"name": name, **info}
                for name, info in sorted(
                    ocr_candidates.items(), key=lambda x: x[1]["count"], reverse=True
                )
            ],
            "audio": [
                {"name": name, **info}
                for name, info in sorted(
                    audio_candidates.items(), key=lambda x: x[1]["count"], reverse=True
                )
            ],
        },
        "existing_users": existing_users,
        "stats": {
            "ocr_candidates": len(ocr_candidates),
            "audio_candidates": len(audio_candidates),
            "existing_users": len(existing_users),
        },
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
