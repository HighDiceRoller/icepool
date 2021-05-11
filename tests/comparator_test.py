import _context

from hdroller import Die
import pytest

def lt_test():
    assert (Die.d6 < Die.d6) == pytest.approx(15 / 36)

def gt_test():
    assert (Die.d6 > Die.d6) == pytest.approx(15 / 36)

def leq_test():
    assert (Die.d6 <= Die.d6) == pytest.approx(21 / 36)

def geq_test():
    assert (Die.d6 >= Die.d6) == pytest.approx(21 / 36)