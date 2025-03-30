import pytest
from icepool import Deck, multiset_function


def test_bare_expression():
    deck = Deck(range(6), times=4)
    assert deck.deal(3).expand().equals(deck.deal((3, 4))[0].expand(),
                                        simplify=True)


def test_intersection_size():

    @multiset_function
    def intersection_size(hands):
        a, b = hands
        return (a & b).size()

    deck = Deck(range(20))
    assert intersection_size(deck.deal((5, 5))).probability(0) == 1


def test_union_size():

    @multiset_function
    def union_size(hands):
        a, b = hands
        return (a | b).size()

    deck = Deck(range(20))
    assert union_size(deck.deal((5, 5))).probability(10) == 1
