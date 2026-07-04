from idea_forge.corpus_router import route, CORPUS_BY_ROUTE, GROUNDING_CONFIDENCE
from idea_forge.models import IdeaNote


def _idea(thesis, contribution=""):
    return IdeaNote(id="i", path="p", title="t", thesis=thesis, prior_work="",
                    contribution=contribution, empirical_claim="", stage="inbox", sections={})


def test_routes_bio():
    i = _idea("A senescence assay linking methylation clocks to lifespan in mice")
    assert route(i) == "bio"
    assert GROUNDING_CONFIDENCE[route(i)] == "high"


def test_routes_cs():
    i = _idea("A benchmark for multi-agent LLM verification and memory topology")
    assert route(i) == "cs"
    assert "arxiv" in CORPUS_BY_ROUTE["cs"] and GROUNDING_CONFIDENCE["cs"] == "low"


def test_tie_defaults_bio():
    assert route(_idea("")) == "bio"
