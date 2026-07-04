from idea_forge.pareto import dominates, pareto_front


def test_dominates_true():
    assert dominates((80, 70, 90), (60, 70, 85)) is True


def test_dominates_false_tradeoff():
    assert dominates((80, 40, 90), (60, 90, 85)) is False


def test_dominates_false_equal():
    assert dominates((70, 70, 70), (70, 70, 70)) is False


def test_pareto_front_drops_dominated():
    pop = {"a": (80, 70, 90), "b": (60, 70, 85), "c": (50, 95, 40)}
    assert set(pareto_front(pop)) == {"a", "c"}
