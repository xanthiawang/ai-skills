"""Harvest calibration anchors organically from Albert's idea pipeline.

An anchor is an idea with a KNOWN outcome. Albert's `sci.ideas` notes already encode outcomes in
their stage: `published`/`active-paper` = it worked, `rejected` = it didn't, `dormant` = stalled.
So the calibration set is a *view over his own notes*, not a hand-maintained YAML — and it grows
as ideas graduate through the pipeline. Active/early stages (inbox, paper-idea, pilot, planned)
are the things being SCORED, not anchors, so they are skipped.

Publication record (the `top`-tier successes) is harvested separately from the CV bib; venue is
not knowable from a note's stage, so `published` maps to `field` here — upgrade to `top` by hand
for the ideas that actually hit Nature/Science.
"""
import glob
import os

from idea_forge.notes_io import parse_idea
from idea_forge.corpus_router import route
from idea_forge.models import Anchor, TIER_ORDINAL

# Only outcome-bearing stages become anchors.
STAGE_TIER = {
    "published": "field",      # graduated to a paper — solid outcome (mark 'top' by hand if Nature/Science)
    "active-paper": "field",   # deemed worth drafting
    "rejected": "failed",      # explicitly not worth pursuing = a killed idea
    "dormant": "incremental",  # stalled — not compelling enough to continue
}


def harvest_anchors(notes_dir, pattern="sci.ideas.*.md"):
    """Return blinded Anchor candidates from outcome-stage sci.ideas notes (skips the hub + active ideas)."""
    anchors = []
    for p in sorted(glob.glob(os.path.join(notes_dir, pattern))):
        if os.path.basename(p) == "sci.ideas.md":
            continue
        idea = parse_idea(p)
        tier = STAGE_TIER.get(idea.stage)
        if not tier:
            continue
        claim = idea.thesis or idea.content_for_judge()[:400]
        anchors.append(Anchor(
            id=os.path.basename(p)[:-3], title=idea.title, field=route(idea),
            claim=claim, known_tier=tier, tier_ordinal=TIER_ORDINAL[tier],
            failure_mode="", cutoff_date="",
            notes=f"harvested from sci.ideas stage '{idea.stage}'"))
    return anchors
