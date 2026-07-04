import pytest
from idea_forge.models import (TIER_ORDINAL, KILLING_FLAWS, Anchor,
                               validate_judge_output, adversary_kills)


def test_tier_ordinal():
    assert TIER_ORDINAL == {"top": 4, "field": 3, "failed": 2, "incremental": 1}


def test_blinded_card_strips_identity():
    a = Anchor(id="x", title="Famous Nature Paper", field="bio", claim="C claim",
               known_tier="top", tier_ordinal=4, failure_mode="", cutoff_date="2020-01-01")
    card = a.blinded_card()
    assert card["claim"] == "C claim"
    assert card["field"] == "bio"
    assert "title" not in card and "known_tier" not in card and "tier_ordinal" not in card


def test_validate_judge_output_ok():
    d = {"novelty": {"score": 8}, "feasibility": {"score": 6}, "impact": {"score": 9},
         "tier_potential": "top"}
    assert validate_judge_output(d)["tier_potential"] == "top"


def test_validate_judge_output_bad_range():
    with pytest.raises(ValueError):
        validate_judge_output({"novelty": {"score": 18}, "feasibility": {"score": 6},
                               "impact": {"score": 9}, "tier_potential": "top"})


def test_validate_judge_output_bad_tier():
    with pytest.raises(ValueError):
        validate_judge_output({"novelty": {"score": 80}, "feasibility": {"score": 60},
                               "impact": {"score": 90}, "tier_potential": "nobel"})


def test_adversary_kills_only_grounded():
    assert adversary_kills({"flaw_type": "genuine_scoop", "citation": "doi:x"}) is True
    assert adversary_kills({"flaw_type": "speculative_concern", "citation": "doi:x"}) is False
    assert adversary_kills({"flaw_type": "genuine_scoop", "citation": ""}) is False  # ungrounded
