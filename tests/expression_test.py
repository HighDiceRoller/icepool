import icepool
import pytest

from icepool import d6, map


def test_keep_highest_expression():

    result = (d6.pool(4) & [1, 2, 3, 4, 5, 6] * 4).highest(3).sum()

    def drop_lowest(*outcomes):
        return sum(outcomes) - min(outcomes)

    expected = map(drop_lowest, d6, d6, d6, d6)

    assert result == expected


def test_disjoint_union_keep_negative_counts():
    assert (d6.pool(4).disjoint_union(d6.pool(2)[-1, -1],
                                      keep_negative_counts=False).sum()
            < 0).mean() == 0
    assert (d6.pool(4).disjoint_union(d6.pool(2)[-1, -1],
                                      keep_negative_counts=True).sum()
            < 0).mean() > 0


def test_difference_keep_negative_counts():
    assert (d6.pool(4).difference(d6.pool(2), keep_negative_counts=False).sum()
            < 0).mean() == 0
    assert (d6.pool(4).difference(d6.pool(2), keep_negative_counts=True).sum()
            < 0).mean() > 0


def test_intersection_keep_negative_counts():
    assert (d6.pool(4).intersection(d6.pool(2)[-1, -1],
                                    keep_negative_counts=False).sum()
            < 0).mean() == 0
    assert (d6.pool(4).intersection(d6.pool(2)[-1, -1],
                                    keep_negative_counts=True).sum()
            < 0).mean() > 0


def test_union_keep_negative_counts():
    assert (d6.pool(4)[-1, -1, -1, -1].union(d6.pool(2)[-1, -1],
                                             keep_negative_counts=False).sum()
            < 0).mean() == 0
    assert (d6.pool(4)[-1, -1, -1, -1].union(d6.pool(2)[-1, -1],
                                             keep_negative_counts=True).sum()
            < 0).mean() > 0
