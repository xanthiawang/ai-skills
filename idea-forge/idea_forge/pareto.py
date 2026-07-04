def dominates(a, b):
    """a Pareto-dominates b iff a >= b on every axis and a > b on at least one."""
    return all(x >= y for x, y in zip(a, b)) and any(x > y for x, y in zip(a, b))


def pareto_front(pop):
    ids = list(pop)
    return [i for i in ids
            if not any(dominates(pop[j], pop[i]) for j in ids if j != i)]
