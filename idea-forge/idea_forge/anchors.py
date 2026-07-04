import yaml
from idea_forge.models import Anchor, TIER_ORDINAL


def _anchor_kwargs(row):
    tier = row["known_tier"]
    return dict(
        id=row["id"], title=row["title"], field=row["field"], claim=row["claim"],
        known_tier=tier, tier_ordinal=row.get("tier_ordinal", TIER_ORDINAL[tier]),
        failure_mode=row.get("failure_mode", ""), cutoff_date=row.get("cutoff_date", ""),
        notes=row.get("notes", ""), label_status=row.get("label_status", ""),
        source_bib_key=row.get("source_bib_key", ""), source_doi=row.get("source_doi", ""),
        source_path=row.get("source_path", ""))


def load_anchors(path):
    with open(path) as f:
        raw = yaml.safe_load(f) or []
    out = []
    for r in raw:
        out.append(Anchor(**_anchor_kwargs(r)))
    return out


def save_anchors(path, anchors):
    data = [dict(id=a.id, title=a.title, field=a.field, claim=a.claim,
                 known_tier=a.known_tier, tier_ordinal=a.tier_ordinal,
                 failure_mode=a.failure_mode, cutoff_date=a.cutoff_date, notes=a.notes,
                 label_status=a.label_status, source_bib_key=a.source_bib_key,
                 source_doi=a.source_doi, source_path=a.source_path)
            for a in anchors]
    with open(path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def blinded_cards(anchors):
    return [a.blinded_card() for a in anchors]


def tier_counts(anchors):
    counts = {}
    for a in anchors:
        counts[a.known_tier] = counts.get(a.known_tier, 0) + 1
    return counts


def anchor_gap_report_from_counts(counts, n, min_anchors=12, min_per_tier=3):
    """Shared calibration-readiness check used by runtime gates and audit tooling."""
    missing_by_tier = {
        tier: max(0, min_per_tier - counts.get(tier, 0))
        for tier in TIER_ORDINAL
    }
    total_ready = n >= min_anchors
    tiers_ready = all(v == 0 for v in missing_by_tier.values())
    ready = total_ready and tiers_ready
    reasons = []
    if not total_ready:
        reasons.append(f"need >={min_anchors} anchors (have {n})")
    missing = {k: v for k, v in missing_by_tier.items() if v}
    if missing:
        reasons.append(
            "need >={0} per tier; missing {1}".format(
                min_per_tier,
                ", ".join(f"{tier}:{count}" for tier, count in missing.items())))
    return {
        "ready": ready,
        "advisory": not ready,
        "n": n,
        "counts": dict(counts),
        "missing_by_tier": missing_by_tier,
        "reason": None if ready else "; ".join(reasons),
    }


def anchor_gap_report(anchors, min_anchors=12, min_per_tier=3):
    return anchor_gap_report_from_counts(
        tier_counts(anchors), len(anchors), min_anchors=min_anchors,
        min_per_tier=min_per_tier)
