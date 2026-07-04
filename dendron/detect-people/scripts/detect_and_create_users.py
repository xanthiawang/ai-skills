#!/usr/bin/env python3
"""
Detect people from screenpipe/journal data and create user.{name}.md entries.
Only creates entries when full name is available and context suggests professional interaction.

Enhanced with:
- Phonetic matching for audio-detected names (cross-check with existing users)
- Web search validation (flag unverifiable names)
- Duplicate detection and merging
"""

import json
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.parse
from typing import List, Dict, Optional, Tuple
import subprocess
import difflib


def normalize_name(name: str) -> str:
    """Convert name to slug format: 'Brian Athey' -> 'brian-athey'"""
    return name.lower().replace(" ", "-").replace(".", "")


def phonetic_similarity(name1: str, name2: str) -> float:
    """
    Calculate phonetic similarity between two names.
    Returns 0.0-1.0 score (higher = more similar).
    Uses combination of string similarity and phonetic patterns.
    """
    name1_lower = name1.lower()
    name2_lower = name2.lower()

    # Direct similarity
    similarity = difflib.SequenceMatcher(None, name1_lower, name2_lower).ratio()

    # Common audio transcription errors
    audio_variants = {
        "jin": ["gin", "jinn", "chin", "jean"],
        "yap": ["yep", "yapp", "yip"],
        "kejun": ["keijun", "kejung", "kaijun", "kejoon"],
        "albert": ["elbert", "alber"],
        "rich": ["rick", "richard"],
        "miller": ["millar", "miler"],
        "tony": ["toni", "tonny"],
        "david": ["davide", "dave"],
        "baker": ["backer", "bakar"],
    }

    # Check if names might be phonetic variants
    words1 = name1_lower.split()
    words2 = name2_lower.split()

    if len(words1) == len(words2):
        matches = 0
        for w1, w2 in zip(words1, words2):
            if w1 == w2:
                matches += 1
            else:
                # Check phonetic variants
                for key, variants in audio_variants.items():
                    if (w1 == key and w2 in variants) or (w2 == key and w1 in variants):
                        matches += 0.8
                        break

        phonetic_score = matches / len(words1)
        similarity = max(similarity, phonetic_score)

    return similarity


def get_existing_users(vault_path: Path) -> Dict[str, str]:
    """
    Get all existing user entries.
    Returns dict of {slug: full_name}
    """
    users = {}
    for user_file in vault_path.glob("user.*.md"):
        slug = user_file.stem.replace("user.", "")
        # Read the title from frontmatter
        try:
            content = user_file.read_text()
            title_match = re.search(r"^title:\s*(.+)$", content, re.MULTILINE)
            if title_match:
                full_name = title_match.group(1).strip()
                users[slug] = full_name
        except:
            continue
    return users


def find_similar_user(
    name: str, existing_users: Dict[str, str], threshold: float = 0.75
) -> Optional[Tuple[str, str, float]]:
    """
    Find existing user with similar name (phonetic matching).
    Returns (slug, full_name, similarity_score) or None.
    """
    best_match = None
    best_score = 0.0

    for slug, full_name in existing_users.items():
        score = phonetic_similarity(name, full_name)
        if score > best_score and score >= threshold:
            best_score = score
            best_match = (slug, full_name, score)

    return best_match


def check_user_exists(vault_path: Path, name_slug: str) -> bool:
    """Check if user.{slug}.md already exists."""
    return (vault_path / f"user.{name_slug}.md").exists()


def extract_people_from_text(text: str) -> List[Dict[str, str]]:
    """
    Extract full names from text.
    Returns list of {name, context} dicts.
    """
    people = []

    # Professional keywords - expanded to catch more interactions
    prof_keywords = [
        "professor",
        "dr.",
        "phd",
        "director",
        "chair",
        "scientist",
        "researcher",
        "postdoc",
        "faculty",
        "interview",
        "collaboration",
        "collaborator",
        "meeting",
        "met with",
        "discussed",
        "discussed with",
        "working with",
        "email",
        "called",
        "talked to",
        "spoke with",
    ]

    text_lower = text.lower()

    # Common false positive patterns (companies, UI elements, tech terms)
    excluded_first_words = {
        "Apple",
        "Microsoft",
        "Google",
        "Facebook",
        "Amazon",
        "Code",
        "File",
        "Folder",
        "Directory",
        "Window",
        "Tab",
        "Command",
        "Settings",
        "Button",
        "Menu",
        "Icon",
        "OTP",
        "API",
        "URL",
        "PDF",
        "CSV",
        "JSON",
        "HTML",
        "Next",
        "Pause",
        "Latest",
        "New",
        "Open",
        "Close",
        "Save",
        "Edit",
        "View",
        "Help",
        "Tools",
        "Format",
        "Insert",
        "Data",
        "Font",
        "Auto",
        "Email",
        "GitHub",
        "Stack",
        "Web",
        "Terminal",
        "System",
        "Display",
        "Assistant",
        "Associate",
        "Full",
        "Senior",
        "Junior",
        "Chief",
        "Head",
        "Final",
        "Draft",
        "Preliminary",
        "Interim",
        "Annual",
        "Monthly",
        "Weekly",
        "Execute",
        "Word",
        "Stanford",
        "Michigan",
        "Computational",
        "Biomedical",
    }

    excluded_last_words = {
        "File",
        "Files",
        "Code",
        "Tab",
        "Window",
        "Menu",
        "Button",
        "Institute",
        "University",
        "Department",
        "School",
        "Center",
        "Lab",
        "Apple",
        "Microsoft",
        "PowerPoint",
        "Excel",
        "Word",
        "Gmail",
        "Browser",
        "Settings",
        "Command",
        "Directory",
        "Folder",
        "OTP",
        "API",
        "Positions",
        "Engineering",
        "Professor",
        "Researcher",
        "Scientist",
        "Postdoc",
        "Student",
        "Fellow",
        "Medicine",
        "Medical",
        "Neuroscience",
        "Custom",
        "Count",
        "Proposal",
        "Cloud",
        "Not",
        "Data",
    }

    # Full name patterns that are definitely not people (job titles, institutions)
    excluded_full_names = {
        "Assistant Professor",
        "Associate Professor",
        "Full Professor",
        "Senior Scientist",
        "Junior Researcher",
        "Chief Officer",
        "Michigan Neuroscience",
        "Stanford Medical",
        "Computational Medicine",
        "Final Proposal",
        "Draft Document",
        "Word Count",
    }

    # UI/tech suffixes that indicate false positives
    ui_suffixes = ["Command", "Action", "Preview", "Review", "File", "Keep", "Items"]

    def is_likely_ui_element(word):
        """Check if word looks like a UI element (CamelCase, contains numbers, etc)"""
        if any(char.isdigit() for char in word):
            return True
        if len(word) > 15:  # Very long words are usually concatenated UI text
            return True
        # Check for CamelCase in middle of word (e.g., "FileKeep", "ActionItems")
        if sum(1 for c in word if c.isupper()) > 1:
            return True
        # Check for non-ASCII characters (OCR errors)
        if not word.isascii():
            return True
        return False

    def is_likely_ocr_error(name):
        """Check if name looks like an OCR error"""
        # Names with obvious misspellings or OCR artifacts
        ocr_errors = [
            "Emoii",
            "Endineerino",
            "Sereenpine",
            "Jinveop",
            "Videolapture",
            "Tor",
        ]
        if any(err in name for err in ocr_errors):
            return True

        # Check for mixed case weirdness (e.g., "VideolaPture")
        words = name.split()
        for word in words:
            # Count transitions from lower to upper case
            transitions = sum(
                1
                for i in range(len(word) - 1)
                if word[i].islower() and word[i + 1].isupper()
            )
            if transitions > 1:  # More than one camelCase transition = likely OCR error
                return True

        return False

    # Look for capital First Last patterns
    words = text.split()
    for i, word in enumerate(words):
        if not word or len(word) < 3:
            continue

        # Must be alphabetic and capitalized
        if not (word[0].isupper() and word.isalpha()):
            continue

        # Skip if word looks like UI element
        if is_likely_ui_element(word):
            continue

        # Skip excluded first words
        if word in excluded_first_words:
            continue

        # Check next word
        if i + 1 < len(words):
            next_word = words[i + 1]

            # Validate next word
            if not next_word or len(next_word) < 3:
                continue
            if not (next_word[0].isupper() and next_word.isalpha()):
                continue

            # Skip if next word looks like UI element
            if is_likely_ui_element(next_word):
                continue

            # Skip excluded last words
            if next_word in excluded_last_words:
                continue

            # Skip if next word is a UI suffix
            if next_word in ui_suffixes:
                continue

            # Found potential full name
            full_name = f"{word} {next_word}"

            # Skip excluded full names (job titles, institutions)
            if full_name in excluded_full_names:
                continue

            # Skip likely OCR errors
            if is_likely_ocr_error(full_name):
                continue

            # Check if near professional context
            context_start = max(0, i - 15)
            context_end = min(len(words), i + 15)
            context_words = " ".join(words[context_start:context_end]).lower()

            has_prof_context = any(kw in context_words for kw in prof_keywords)

            if has_prof_context:
                people.append(
                    {
                        "name": full_name,
                        "context": " ".join(
                            words[max(0, i - 20) : min(len(words), i + 30)]
                        ),
                    }
                )

    return people


def search_person_info(name: str) -> Optional[Dict]:
    """
    Search for person's information via web search.
    Returns dict with bio info or None if not found/verifiable.
    """
    try:
        # Use DuckDuckGo instant answer API (no auth required)
        query = urllib.parse.quote(f"{name} professor researcher scientist")
        url = f"https://api.duckduckgo.com/?q={query}&format=json"

        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.load(response)

        # Check if we got meaningful results
        abstract = data.get("Abstract", "")
        heading = data.get("Heading", "")

        if abstract and len(abstract) > 50:
            return {
                "name": heading or name,
                "bio": abstract[:500],
                "source": data.get("AbstractURL", ""),
                "verified": True,
            }

        # Try alternative: check if name appears in search results
        # This is a simple heuristic - if we can't find info, likely not a real person or typo
        return None

    except Exception as e:
        print(f"  ⚠️  Web search failed for '{name}': {e}", file=sys.stderr)
        return None


def create_user_entry(
    vault_path: Path,
    name: str,
    context: str,
    date: str,
    source: str = "OCR",
    web_info: Optional[Dict] = None,
) -> bool:
    """
    Create user.{slug}.md entry for a person.
    Includes web search results if available, flags if unverifiable.
    """
    slug = normalize_name(name)
    filepath = vault_path / f"user.{slug}.md"

    if filepath.exists():
        print(f"User entry already exists: {slug}", file=sys.stderr)
        return False

    # Generate ID
    entry_id = f"user-{slug}-001"
    timestamp = int(datetime.now().timestamp() * 1000)

    # Determine verification status
    if web_info and web_info.get("verified"):
        verification = "✅ Verified via web search"
        bio_section = f"""{web_info.get('bio', '')}

**Source**: {web_info.get('source', 'N/A')}"""
    else:
        verification = (
            f"⚠️ UNVERIFIED - Could not find on internet (detected from {source})"
        )
        if source == "Audio":
            verification += "\n⚠️ **Audio-detected name** - likely has transcription errors. Check for similar existing users."
        bio_section = "_[Could not verify via web search - may be typo, OCR error, or private individual]_"

    # Create entry
    content = f"""---
id: {entry_id}
title: {name}
desc: ''
updated: {timestamp}
created: {timestamp}
---

## Verification Status

{verification}

## Contact Info

- 🏢 Institution: _[To be filled]_
- 📧 Email: _[To be filled]_

## Role & Expertise

{bio_section}

## Context

**How we connected**: Detected from journal/screenpipe

**Date**: {date}

**Detection source**: {source}

**Context**: {context[:200]}...

## Notes

_[Add notes about interactions]_
"""

    filepath.write_text(content)
    print(f"✓ Created user entry: user.{slug}.md", file=sys.stderr)
    return True


def main():
    # Get vault path from config or default
    vault_path = Path.home() / "Documents/Manual Library/Dendron/notes"

    # Date to process
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    date = datetime.strptime(date_str, "%Y-%m-%d")

    # Query screenpipe - use 0:00 to 23:59 to ensure we capture the full calendar day
    # This ensures 0-6 AM is always included
    start = date.replace(hour=0, minute=0, second=0).isoformat() + "Z"
    end = date.replace(hour=23, minute=59, second=59).isoformat() + "Z"

    url = f"http://localhost:3030/search?start_time={start}&end_time={end}&limit=1000"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.load(response)
    except Exception as e:
        print(f"Error querying screenpipe: {e}", file=sys.stderr)
        return

    items = data.get("data", [])

    # Get existing users for phonetic matching
    existing_users = get_existing_users(vault_path)
    print(f"\nFound {len(existing_users)} existing user entries", file=sys.stderr)

    # Extract people from OCR and audio separately
    ocr_people = {}
    audio_people = {}

    for item in items:
        if item["type"] == "OCR":
            text = item["content"].get("text", "")
            people = extract_people_from_text(text)

            for person in people:
                name = person["name"]
                if name not in ocr_people:
                    ocr_people[name] = {"context": person["context"], "source": "OCR"}

        elif item["type"] == "Audio":
            text = item["content"].get("transcription", "")
            people = extract_people_from_text(text)

            for person in people:
                name = person["name"]
                if name not in audio_people:
                    audio_people[name] = {
                        "context": person["context"],
                        "source": "Audio",
                    }

    # Process people
    print(
        f"\nDetected {len(ocr_people)} from OCR, {len(audio_people)} from Audio",
        file=sys.stderr,
    )

    processed = set()

    # Process OCR-detected people (more reliable)
    for name, info in ocr_people.items():
        slug = normalize_name(name)

        if slug in processed:
            continue

        if check_user_exists(vault_path, slug):
            print(f"  ✓ {name} - already exists (user.{slug}.md)", file=sys.stderr)
            processed.add(slug)
        else:
            print(f"  ➜ {name} (from OCR) - creating entry...", file=sys.stderr)

            # Perform web search
            web_info = search_person_info(name)

            if web_info:
                print(f"    ✅ Verified via web search", file=sys.stderr)
                create_user_entry(
                    vault_path, name, info["context"], date_str, "OCR", web_info
                )
                processed.add(slug)
            else:
                print(
                    f"    ⚠️  Could not verify on internet - may be typo or private individual",
                    file=sys.stderr,
                )
                # Check if similar user exists
                similar = find_similar_user(name, existing_users)
                if similar:
                    similar_slug, similar_name, score = similar
                    print(
                        f"    💡 Similar existing user: {similar_name} (score: {score:.2f})",
                        file=sys.stderr,
                    )
                    print(
                        f"       Consider if this is a duplicate/typo", file=sys.stderr
                    )

                # Check if name looks like OCR error
                def looks_suspicious(name):
                    words = name.split()
                    for word in words:
                        # Mixed case weirdness
                        transitions = sum(
                            1
                            for i in range(len(word) - 1)
                            if word[i].islower() and word[i + 1].isupper()
                        )
                        if transitions > 1:
                            return True
                        # Very short words
                        if len(word) < 3:
                            return True
                    return False

                if looks_suspicious(name):
                    print(
                        f"    ❌ Name looks suspicious (likely OCR error) - NOT creating entry",
                        file=sys.stderr,
                    )
                    processed.add(slug)
                else:
                    # Create entry with warning flag
                    create_user_entry(
                        vault_path, name, info["context"], date_str, "OCR", web_info
                    )
                    processed.add(slug)

    # Process audio-detected people (less reliable - check against existing users first)
    for name, info in audio_people.items():
        slug = normalize_name(name)

        if slug in processed:
            continue

        # First, check for phonetic match with existing users
        similar = find_similar_user(name, existing_users, threshold=0.70)

        if similar:
            similar_slug, similar_name, score = similar
            print(
                f"  🔗 {name} (from Audio) - likely refers to existing user: {similar_name} (score: {score:.2f})",
                file=sys.stderr,
            )
            print(
                f"     → Linking to user.{similar_slug}.md instead of creating new entry",
                file=sys.stderr,
            )
            processed.add(slug)
            continue

        if check_user_exists(vault_path, slug):
            print(f"  ✓ {name} - already exists (user.{slug}.md)", file=sys.stderr)
            processed.add(slug)
        else:
            print(
                f"  ⚠️  {name} (from Audio) - audio transcription may have errors",
                file=sys.stderr,
            )

            # Perform web search
            web_info = search_person_info(name)

            if web_info:
                print(
                    f"    ✅ Verified via web search - creating entry", file=sys.stderr
                )
                create_user_entry(
                    vault_path, name, info["context"], date_str, "Audio", web_info
                )
            else:
                print(f"    ❌ Could not verify on internet", file=sys.stderr)
                print(
                    f"    → Likely a transcription error. NOT creating entry.",
                    file=sys.stderr,
                )
                print(f"    💡 Check manually if needed: '{name}'", file=sys.stderr)

            processed.add(slug)


if __name__ == "__main__":
    main()
