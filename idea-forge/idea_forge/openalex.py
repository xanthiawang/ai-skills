"""OpenAlex retrieval fallback for idea-forge.

Keyless and generously rate-limited, unlike anonymous Semantic Scholar (429-prone).
Mirrors semantic_scholar.search()'s return shape: list of dicts with
title / year / abstract / citationCount, so callers can swap sources freely.
"""
import os
import requests

BASE = "https://api.openalex.org"
SELECT = "title,publication_year,doi,cited_by_count,abstract_inverted_index"
MAILTO = os.environ.get("OPENALEX_MAILTO", "xanthiaw12@gmail.com")


class OpenAlexError(Exception):
    pass


def _headers():
    return {"User-Agent": f"idea-forge (mailto:{MAILTO})"}


def _deinvert(inv):
    if not inv:
        return None
    pos = {p: w for w, ps in inv.items() for p in ps}
    return " ".join(pos[i] for i in sorted(pos))


def _to_s2_shape(work):
    return {
        "title": work.get("title"),
        "year": work.get("publication_year"),
        "abstract": _deinvert(work.get("abstract_inverted_index")),
        "citationCount": work.get("cited_by_count"),
        "doi": work.get("doi"),
    }


def search(query, limit=10, session=None):
    sess = session or requests
    try:
        r = sess.get(f"{BASE}/works",
                     params={"search": query, "per-page": limit, "select": SELECT},
                     headers=_headers(), timeout=20)
        r.raise_for_status()
    except Exception as e:
        raise OpenAlexError(str(e)) from e
    return [_to_s2_shape(w) for w in r.json().get("results", [])]


def search_with_s2_fallback(query, limit=10, session=None):
    """Try Semantic Scholar first (richer metadata), fall back to OpenAlex on error."""
    from . import semantic_scholar as ss
    try:
        out = ss.search(query, limit=limit, session=session)
        if out:
            return out, "semantic_scholar"
    except ss.SemanticScholarError:
        pass
    return search(query, limit=limit, session=session), "openalex"
