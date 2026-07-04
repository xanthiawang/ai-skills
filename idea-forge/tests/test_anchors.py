from pathlib import Path
from idea_forge.anchors import (
    anchor_gap_report,
    blinded_cards,
    load_anchors,
    save_anchors,
    tier_counts,
)

FIX = Path(__file__).parent / "fixtures" / "fixture_anchors.yaml"


def test_load_and_derive_ordinal():
    anchors = load_anchors(str(FIX))
    assert len(anchors) == 3
    assert {a.tier_ordinal for a in anchors} == {4, 3, 1}


def test_blinded_cards_hide_identity():
    cards = blinded_cards(load_anchors(str(FIX)))
    joined = str(cards)
    assert "T1" not in joined and "top" not in joined and "known_tier" not in joined
    assert all(set(c) == {"card_id", "field", "claim"} for c in cards)


def test_tier_counts():
    counts = tier_counts(load_anchors(str(FIX)))
    assert counts["top"] == 1 and counts["field"] == 1 and counts["incremental"] == 1


def test_roundtrip(tmp_path):
    p = tmp_path / "a.yaml"
    save_anchors(str(p), load_anchors(str(FIX)))
    assert len(load_anchors(str(p))) == 3


def test_metadata_roundtrip(tmp_path):
    p = tmp_path / "meta.yaml"
    p.write_text(
        "- id: a1\n"
        "  title: T\n"
        "  field: bio\n"
        "  claim: c\n"
        "  known_tier: top\n"
        "  label_status: proposed_from_venue\n"
        "  source_bib_key: ying2024\n"
        "  source_doi: 10.1038/example\n"
        "  source_path: /tmp/source.bib\n")
    out = tmp_path / "out.yaml"
    save_anchors(str(out), load_anchors(str(p)))
    a = load_anchors(str(out))[0]
    assert a.label_status == "proposed_from_venue"
    assert a.source_bib_key == "ying2024"
    assert a.source_doi == "10.1038/example"
    assert a.source_path == "/tmp/source.bib"


def test_anchor_gap_report_keeps_unbalanced_set_advisory():
    anchors = load_anchors(str(FIX))
    report = anchor_gap_report(anchors)
    assert report["advisory"] is True
    assert report["missing_by_tier"]["failed"] == 3
    assert report["reason"]


def test_anchor_gap_report_ready_when_full(tmp_path):
    rows = []
    for tier in ("top", "field", "failed", "incremental"):
        for k in range(3):
            rows.append(
                f"- id: {tier}{k}\n"
                "  title: T\n"
                "  field: bio\n"
                "  claim: c\n"
                f"  known_tier: {tier}\n")
    p = tmp_path / "full.yaml"
    p.write_text("".join(rows))
    report = anchor_gap_report(load_anchors(str(p)))
    assert report["ready"] is True
    assert report["advisory"] is False
    assert report["reason"] is None
