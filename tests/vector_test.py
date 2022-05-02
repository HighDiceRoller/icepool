import _context

import icepool
import pytest

def test_cartesian_product():
    result = icepool.Die((icepool.d6, icepool.d6))
    assert result.covariance(0, 1) == 0.0
    result_sum = result.sub(lambda x: sum(x))
    assert result_sum.equals(2 @ icepool.d6)

def test_cartesian_product_cast():
    result = icepool.Die((icepool.d6, 2))
    assert result.covariance(0, 1) == 0.0
    result_sum = result.sub(lambda x: sum(x))
    assert result_sum.equals(icepool.d6 + 2)