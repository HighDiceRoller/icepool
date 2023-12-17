import icepool
import pytest

from icepool import Die, Symbols

die = Die(['', 'a', 'ab', 'aab']).map(Symbols)


def test_marginals_getitem():
    assert die.marginals['a'] == Die([0, 1, 1, 2])
    assert die.marginals['b'] == Die([0, 0, 1, 1])
    assert die.marginals['ab'] == die


def test_marginals_getattr():
    assert die.marginals.a == Die([0, 1, 1, 2])
    assert die.marginals.b == Die([0, 0, 1, 1])
    assert die.marginals.ab == die


def test_add_new():
    assert die + 'c' == Die(['c', 'ac', 'abc', 'aabc']).map(Symbols)


def test_add_existing():
    assert die + 'b' == Die(['b', 'ab', 'abb', 'aabb']).map(Symbols)


def test_mul():
    assert die * 2 == Die(['', 'aa', 'aabb', 'aaaabb']).map(Symbols)


def test_floordiv():
    assert die // 2 == Die(['', '', '', 'a']).map(Symbols)


def test_issubset():
    assert Symbols('ab').issubset('abc')
    assert not Symbols('ab').issubset('ac')


def test_issuperset():
    assert Symbols('ab').issuperset('a')
    assert not Symbols('ab').issuperset('ac')
