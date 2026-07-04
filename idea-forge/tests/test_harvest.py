from idea_forge.harvest import harvest_anchors
from idea_forge.models import TIER_ORDINAL


def _note(p, stage_key, stage_val, body="## Concept\nDo a thing about aging cells.\n"):
    p.write_text(f"---\nid: {p.stem}\ntitle: {p.stem}\n{stage_key}: {stage_val}\n---\n\n{body}")


def test_harvest_maps_outcome_stages_and_skips_active(tmp_path):
    _note(tmp_path / "sci.ideas.a.md", "stage", "rejected")
    _note(tmp_path / "sci.ideas.b.md", "stage", "paper-idea")       # active -> skipped
    _note(tmp_path / "sci.ideas.c.md", "status", "dormant")          # note: uses status: key
    _note(tmp_path / "sci.ideas.d.md", "stage", "published")
    (tmp_path / "sci.ideas.md").write_text("---\ntitle: hub\n---\nindex\n")  # hub -> skipped

    anchors = harvest_anchors(str(tmp_path))
    tiers = {a.id: a.known_tier for a in anchors}
    assert tiers == {"sci.ideas.a": "failed", "sci.ideas.c": "incremental",
                     "sci.ideas.d": "field"}
    # blinded card carries the idea content, not the outcome; ordinal derived from tier
    a = next(x for x in anchors if x.id == "sci.ideas.a")
    assert "aging cells" in a.claim
    assert a.known_tier == "failed" and a.tier_ordinal == TIER_ORDINAL["failed"]
