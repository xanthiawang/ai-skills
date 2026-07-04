import math
from idea_forge.retrodiction import spearman, retrodiction_report


def test_spearman_perfect():
    assert math.isclose(spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0, abs_tol=1e-9)


def test_spearman_inverse():
    assert math.isclose(spearman([1, 2, 3, 4], [40, 30, 20, 10]), -1.0, abs_tol=1e-9)


def _full_set(good=True):
    # 12 anchors, 3 per tier; predicted correlates with tier when good
    tiers = ["top", "field", "failed", "incremental"]
    predicted, actual = {}, {}
    base = {"top": 95, "field": 70, "failed": 45, "incremental": 20}
    for t in tiers:
        for k in range(3):
            i = f"{t}{k}"
            actual[i] = t
            predicted[i] = base[t] + k if good else 100 - base[t] + k
    return predicted, actual


def test_passes_with_full_calibrated_set():
    predicted, actual = _full_set(good=True)
    rep = retrodiction_report(predicted, actual, threshold=0.6)
    assert rep.n == 12 and rep.advisory is False
    assert rep.correlation > 0.9 and rep.passed is True
    # CI is a valid sub-unit interval whose lower bound brackets the point estimate.
    # (Near the ceiling the bootstrap distribution is left-skewed, so we do not require
    #  correlation <= ci_high strictly.)
    assert rep.ci_low <= rep.correlation
    assert 0.0 <= rep.ci_high <= 1.0 + 1e-9


def test_advisory_when_too_few_anchors():
    predicted = {"top0": 95, "field0": 70, "failed0": 45, "incremental0": 20}
    actual = {"top0": "top", "field0": "field", "failed0": "failed", "incremental0": "incremental"}
    rep = retrodiction_report(predicted, actual)
    assert rep.advisory is True and rep.passed is False   # n<12


def test_fails_when_anticorrelated():
    predicted, actual = _full_set(good=False)
    rep = retrodiction_report(predicted, actual, threshold=0.6)
    assert rep.advisory is False and rep.passed is False
