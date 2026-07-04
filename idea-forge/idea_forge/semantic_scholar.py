import os
import requests

BASE = "https://api.semanticscholar.org/graph/v1"
FIELDS = "title,year,abstract,citationCount"


class SemanticScholarError(Exception):
    pass


def _headers():
    key = os.environ.get("S2_API_KEY")
    return {"x-api-key": key} if key else {}


def _get(path, params, session):
    sess = session or requests
    try:
        r = sess.get(f"{BASE}{path}", params=params, headers=_headers(), timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise SemanticScholarError(str(e)) from e


def search(query, limit=10, session=None):
    return _get("/paper/search",
                {"query": query, "limit": limit, "fields": FIELDS}, session).get("data", [])


def related(paper_id, limit=10, session=None):
    data = _get(f"/paper/{paper_id}/citations",
                {"limit": limit, "fields": FIELDS}, session)
    return [row.get("citingPaper", {}) for row in data.get("data", [])]
