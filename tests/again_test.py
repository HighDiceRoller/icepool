import icepool
import pytest

from icepool import Again, d6


def test_again_plus_6():
    x = Again + 6
    assert x.evaluate(d6) == d6 + 6
