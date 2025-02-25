import pytest
import icepool


def test_die_sample():
    result = icepool.d6.sample()
    assert result >= 1
    assert result <= 6


def test_deck_sample():
    result = icepool.Deck({'A': 1, 'B': 2, 'C': 3}).sample()
    assert result in ['A', 'B', 'C']


def test_pool_sample():
    result = icepool.standard_pool([6, 6, 6, 8])[:-1].sample()
    assert all(x >= 1 for x in result)
    assert all(x <= 6 for x in result)


@pytest.mark.skip(
    reason="still need to figure out how to sample multiset tuples")
def test_deal_sample():
    a, b = icepool.Deck({'A': 1, 'B': 2, 'C': 3}).deal(3, 2).sample()
    assert all(x in ['A', 'B', 'C'] for x in a)
    assert all(x in ['A', 'B', 'C'] for x in b)
