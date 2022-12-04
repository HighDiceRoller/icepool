from typing import Collection
import icepool
import pytest

from icepool import d

from collections import Counter

targets_to_test = [
    (),
    (1,),
    (2,),
    (4,),
    (6,),
    (1, 6),
    (1, 3, 6),
    (1, 1, 1),
    (1, 1, 3, 6),
    (1, 1, 3, 3, 6, 6),
]

wilds_to_test = [
    (),
    (1,),
    (2,),
    (6,),
    (1, 6),
    (1, 3, 6),
]


@pytest.mark.parametrize('target', targets_to_test)
@pytest.mark.parametrize('wilds', wilds_to_test)
def test_contains_subset(target: Collection, wilds: Collection):
    result = d(6).pool(4).contains_subset(target, wilds=wilds)

    def expected_func(rolls):
        wild_rolls = [x for x in rolls if x in wilds]
        non_wild_rolls = [x for x in rolls if x not in wilds]
        non_wild_match = Counter(non_wild_rolls) & Counter(target)
        return non_wild_match.total() + len(wild_rolls) >= len(target)

    expected = d(6).pool(4).expand().map(expected_func)
    assert result == expected


@pytest.mark.parametrize('target', targets_to_test)
@pytest.mark.parametrize('wilds', wilds_to_test)
def test_intersection_size(target, wilds):
    result = d(6).pool(4).intersection_size(target, wilds=wilds)

    def expected_func(rolls):
        wild_rolls = [x for x in rolls if x in wilds]
        non_wild_rolls = [x for x in rolls if x not in wilds]
        non_wild_match = Counter(non_wild_rolls) & Counter(target)
        return min(non_wild_match.total() + len(wild_rolls), len(target))

    expected = d(6).pool(4).expand().map(expected_func)
    assert result == expected