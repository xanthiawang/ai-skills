#!/usr/bin/env python3
"""Audit idea-forge calibration anchors without changing them.

Expected advisory gaps are not errors. The command exits nonzero only for malformed input or
when --fail-if-not-ready is requested by automation.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from idea_forge.anchors import anchor_gap_report, load_anchors, tier_counts  # noqa: E402
from idea_forge.harvest import harvest_anchors  # noqa: E402
from idea_forge.models import TIER_ORDINAL  # noqa: E402


DEFAULT_NOTES_DIR = "/Users/A.Y/Documents/Manual Library/Dendron/notes"


def _format_counts(counts):
    return ", ".join(f"{tier}={counts.get(tier, 0)}" for tier in TIER_ORDINAL)


def _report(anchors_path, notes_dir=None, min_anchors=12, min_per_tier=3):
    anchors = load_anchors(anchors_path)
    report = anchor_gap_report(anchors, min_anchors=min_anchors, min_per_tier=min_per_tier)
    harvested = harvest_anchors(notes_dir) if notes_dir else []
    return {
        "anchors_path": anchors_path,
        "ready": report["ready"],
        "advisory": report["advisory"],
        "n": report["n"],
        "counts": report["counts"],
        "missing_by_tier": report["missing_by_tier"],
        "reason": report["reason"],
        "harvested_n": len(harvested),
        "harvested_counts": tier_counts(harvested),
        "notes_dir": notes_dir,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--anchors", default="anchors/anchors.yaml")
    ap.add_argument("--notes-dir", default=DEFAULT_NOTES_DIR)
    ap.add_argument("--min-anchors", type=int, default=12)
    ap.add_argument("--min-per-tier", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-if-not-ready", action="store_true")
    args = ap.parse_args()

    report = _report(args.anchors, notes_dir=args.notes_dir,
                     min_anchors=args.min_anchors, min_per_tier=args.min_per_tier)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "READY" if report["ready"] else "ADVISORY-ONLY"
        print(f"Calibration status: {status}")
        print(f"Anchor file: {report['anchors_path']}")
        print(f"Live anchors: {report['n']} ({_format_counts(report['counts'])})")
        if report["reason"]:
            print(f"Gap: {report['reason']}")
        print(f"Harvested outcome anchors from vault: {report['harvested_n']} "
              f"({_format_counts(report['harvested_counts'])})")
        if report["advisory"]:
            print("Forward verdicts must remain advisory until the live anchors meet the gate.")

    if args.fail_if_not_ready and report["advisory"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
