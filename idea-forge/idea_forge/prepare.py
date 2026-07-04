"""Assemble the deterministic scoring scaffold for one idea note.

Ties the plumbing together so the interactive skill (or a future batch mode) always does the
same deterministic prep before the LLM judging: parse (any structure) → route + grounding →
population for Pareto → calibration/advisory gate. The LLM steps (judge/adversary/evolution)
then run on top of this scaffold per SKILL.md.
"""
import os

from idea_forge.notes_io import parse_idea, load_population
from idea_forge.corpus_router import route, CORPUS_BY_ROUTE, GROUNDING_CONFIDENCE
from idea_forge.anchors import load_anchors, anchor_gap_report

_PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_ANCHORS = os.path.join(_PKG_ROOT, "anchors", "anchors.yaml")


def calibration_status(anchors_path=_DEFAULT_ANCHORS, min_anchors=12, min_per_tier=3):
    """Whether forward verdicts can be trusted, or the system must run advisory-only."""
    try:
        anchors = load_anchors(anchors_path)
    except FileNotFoundError:
        return {"advisory": True, "n": 0, "counts": {}, "reason": "no anchors file"}
    report = anchor_gap_report(anchors, min_anchors=min_anchors, min_per_tier=min_per_tier)
    return {
        "advisory": report["advisory"],
        "n": report["n"],
        "counts": report["counts"],
        "missing_by_tier": report["missing_by_tier"],
        "reason": report["reason"],
    }


def prepare(note_path, notes_dir=None, anchors_path=_DEFAULT_ANCHORS):
    idea = parse_idea(note_path)
    notes_dir = notes_dir or os.path.dirname(os.path.abspath(note_path))
    r = route(idea)
    pop = load_population(notes_dir)
    return {
        "id": idea.id,
        "title": idea.title,
        "stage": idea.stage,
        "has_template": idea.has_template,
        "content_for_judge": idea.content_for_judge(),
        "route": r,
        "corpora": CORPUS_BY_ROUTE[r],
        "grounding_confidence": GROUNDING_CONFIDENCE[r],
        "population_size": len(pop),
        "calibration": calibration_status(anchors_path),
    }
