from unittest.mock import MagicMock
import pytest
from idea_forge.semantic_scholar import search, SemanticScholarError


def _resp(json_data):
    m = MagicMock()
    m.json.return_value = json_data
    m.raise_for_status = MagicMock()
    return m


def test_search_parses():
    sess = MagicMock()
    sess.get.return_value = _resp({"data": [{"paperId": "p1", "title": "T", "year": 2024,
                                             "abstract": "a", "citationCount": 5}]})
    out = search("q", limit=1, session=sess)
    assert out[0]["paperId"] == "p1" and out[0]["citationCount"] == 5


def test_network_error_raises():
    sess = MagicMock()
    sess.get.side_effect = Exception("boom")
    with pytest.raises(SemanticScholarError):
        search("q", session=sess)
