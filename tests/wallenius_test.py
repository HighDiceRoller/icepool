import icepool
import pytest

from icepool import Wallenius, Die


def test_wallenius_singleton_dict():
    data = {1: 1, 2: 2, 3: 3, 4: 4}

    base = Die(data)
    expected = base.map(lambda x: base.remove(x).map(lambda y: (x, y))).map(
        lambda x: tuple(sorted(x)))

    assert Wallenius(data).deal(2).expand() == expected


def test_wallenius_singleton_list():
    data = [(1, 1), (2, 2), (3, 3), (4, 4)]

    base = Die({k: v for k, v in data})
    expected = base.map(lambda x: base.remove(x).map(lambda y: (x, y))).map(
        lambda x: tuple(sorted(x)))

    assert Wallenius(data).deal(2).expand() == expected


def test_wallenius_weighted_dict():
    data = {1: (1, 2), 2: (2, 2), 3: (3, 2), 4: (4, 2)}

    base = Die({x: 2 * x for x in [1, 2, 3, 4]})
    expected = base.map(lambda x: base.remove(x, x).map(lambda y: (x, y))).map(
        lambda x: tuple(sorted(x)))

    assert Wallenius(data).deal(2).expand().simplify() == expected.simplify()


def test_wallenius_weighted_list():
    data = [(1, 1), (2, 2), (3, 3), (4, 4), (1, 1), (2, 2), (3, 3), (4, 4)]

    base = Die({x: 2 * x for x in [1, 2, 3, 4]})
    expected = base.map(lambda x: base.remove(x, x).map(lambda y: (x, y))).map(
        lambda x: tuple(sorted(x)))

    assert Wallenius(data).deal(2).expand().simplify() == expected.simplify()
