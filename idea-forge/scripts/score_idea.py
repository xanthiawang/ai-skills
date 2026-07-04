#!/usr/bin/env python3
"""CLI: print the deterministic scoring scaffold for an idea note, then hand off to the LLM
judging in SKILL.md. Usage: python3 scripts/score_idea.py <note.md> [--notes-dir DIR] [--anchors YAML]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from idea_forge.prepare import prepare  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("note_path")
    ap.add_argument("--notes-dir")
    ap.add_argument("--anchors")
    args = ap.parse_args()
    scaffold = prepare(args.note_path, args.notes_dir,
                       args.anchors or prepare.__globals__["_DEFAULT_ANCHORS"])
    print(json.dumps(scaffold, indent=2, ensure_ascii=False))
    if scaffold["calibration"]["advisory"]:
        sys.stderr.write(
            "\n[ADVISORY] Calibration is advisory-only ("
            + str(scaffold["calibration"]["reason"])
            + "). Score and show the verdict, but do NOT auto-certify a survivor.\n")


if __name__ == "__main__":
    main()
