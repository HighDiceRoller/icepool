import _context

from hdroller import Die
import pytest

def test_dict():
    d = {}
    d[Die.d6] = 100
    assert d[Die.d6] == 100
