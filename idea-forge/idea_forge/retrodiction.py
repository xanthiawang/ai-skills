import random
from idea_forge.models import RetrodictionReport, TIER_ORDINAL
from idea_forge.anchors import anchor_gap_report_from_counts


def _rank(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(x, y):
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    rx, ry = _rank(x), _rank(y)
    n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx) ** 0.5
    vy = sum((b - my) ** 2 for b in ry) ** 0.5
    return 0.0 if vx == 0 or vy == 0 else cov / (vx * vy)


def bootstrap_ci(x, y, n_boot=1000, seed=0):
    rng = random.Random(seed)
    n = len(x)
    if n < 2:
        return (0.0, 0.0)
    stats = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        stats.append(spearman([x[i] for i in idx], [y[i] for i in idx]))
    stats.sort()
    lo = stats[int(0.025 * n_boot)]
    hi = stats[min(int(0.975 * n_boot), n_boot - 1)]
    return (lo, hi)


def retrodiction_report(predicted, actual_tier, threshold=0.6,
                        min_anchors=12, min_per_tier=3, seed=0):
    ids = [i for i in predicted if i in actual_tier]
    pred = [predicted[i] for i in ids]
    act = [TIER_ORDINAL[actual_tier[i]] for i in ids]
    corr = spearman(pred, act)
    lo, hi = bootstrap_ci(pred, act, seed=seed)
    counts = {}
    for i in ids:
        counts[actual_tier[i]] = counts.get(actual_tier[i], 0) + 1
    gap = anchor_gap_report_from_counts(counts, len(ids), min_anchors, min_per_tier)
    advisory = gap["advisory"]
    passed = (not advisory) and corr >= threshold
    detail = [(i, TIER_ORDINAL[actual_tier[i]], predicted[i]) for i in ids]
    return RetrodictionReport(correlation=corr, n=len(ids), ci_low=lo, ci_high=hi,
                              passed=passed, advisory=advisory, threshold=threshold,
                              detail=detail)
