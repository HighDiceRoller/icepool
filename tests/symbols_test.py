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


def test_sub():
    assert die - 'ac' == Die(['-ac', '-c', 'b - c', 'ab - c']).map(Symbols)
    assert +(die - 'ac') == Die(['', '', 'b', 'ab']).map(Symbols)


def test_and():
    assert die & 'abb' == Die(['', 'a', 'ab', 'ab']).map(Symbols)


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


def test_ordering():
    assert Symbols('a') > Symbols('')
    assert Symbols('a') > Symbols('bb')
    assert Symbols('-a') < Symbols('bb')
    assert Symbols('a') < Symbols('ab')


def test_getitem_missing_does_not_add_symbol():
    symbols = Symbols('a')
    assert symbols['b'] == 0
    assert symbols['ab'] == Symbols('a')
    assert list(symbols) == ['a']


def test_count_subset_missing_does_not_add_symbol():
    symbols = Symbols('a')
    assert symbols.count_subset('b') == 0
    assert list(symbols) == ['a']
