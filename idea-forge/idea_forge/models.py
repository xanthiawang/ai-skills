from dataclasses import dataclass, field

TIER_ORDINAL = {"top": 4, "field": 3, "failed": 2, "incremental": 1}
FLAW_TYPES = {"genuine_scoop", "decisive_confound", "feasibility_blocker", "speculative_concern"}
KILLING_FLAWS = {"genuine_scoop", "decisive_confound", "feasibility_blocker"}
AXES = ("novelty", "feasibility", "impact")


@dataclass
class IdeaNote:
    id: str
    path: str
    title: str
    thesis: str
    prior_work: str
    contribution: str
    empirical_claim: str
    stage: str
    sections: dict = field(default_factory=dict)
    raw_body: str = ""   # full note body (sans frontmatter + idea-forge block) — universal fallback

    @property
    def has_template(self):
        """True if any of the structured template sections were populated."""
        return any([self.thesis, self.prior_work, self.contribution, self.empirical_claim])

    def content_for_judge(self):
        """What the judge should read: structured sections if present, else the raw body."""
        if self.has_template:
            parts = [f"{k}: {v}" for k, v in
                     (("thesis", self.thesis), ("prior_work", self.prior_work),
                      ("contribution", self.contribution), ("empirical_claim", self.empirical_claim))
                     if v]
            return "\n".join(parts)
        return self.raw_body


@dataclass
class Anchor:
    id: str
    title: str
    field: str            # "bio" | "cs"
    claim: str
    known_tier: str       # top | field | failed | incremental
    tier_ordinal: int
    failure_mode: str = ""  # scooped | infeasible | poorly-executed | low-leverage | venue-timing | ""
    cutoff_date: str = ""   # ISO date; retrieval must not go past this when grounding the anchor
    notes: str = ""
    label_status: str = ""  # e.g. proposed_from_venue | validated_by_albert
    source_bib_key: str = ""
    source_doi: str = ""
    source_path: str = ""

    def blinded_card(self):
        """The idea stripped of everything that reveals which paper it is."""
        return {"card_id": self.id, "field": self.field, "claim": self.claim}


@dataclass
class RetrodictionReport:
    correlation: float
    n: int
    ci_low: float
    ci_high: float
    passed: bool
    advisory: bool
    threshold: float
    detail: list


def validate_judge_output(d):
    for ax in AXES:
        if ax not in d or "score" not in d[ax]:
            raise ValueError(f"missing axis {ax}")
        s = d[ax]["score"]
        if not (isinstance(s, (int, float)) and 0 <= s <= 10):
            raise ValueError(f"{ax} score out of [0,10]: {s}")
    if d.get("tier_potential") not in TIER_ORDINAL:
        raise ValueError(f"bad tier_potential: {d.get('tier_potential')}")
    return d


def adversary_kills(d):
    """A kill requires a killing flaw type AND grounding (citation or concrete mechanism)."""
    if d.get("flaw_type") not in KILLING_FLAWS:
        return False
    return bool(d.get("citation") or d.get("mechanism"))
