import icepool
import pytest

from icepool import d6, die_map


def test_keep_highest_expression():

    result = (d6.pool(4) & [1, 2, 3, 4, 5, 6] * 4).highest(3).sum()

    def drop_lowest(*outcomes):
        return sum(outcomes) - min(outcomes)

    expected = die_map(drop_lowest, d6, d6, d6, d6)

    assert result == expected
