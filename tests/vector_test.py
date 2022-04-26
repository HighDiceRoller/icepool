import _context

import icepool
import pytest

def test_cartesian_product():
    result = icepool.cartesian_product(icepool.d6, icepool.d6)
    assert result.ndim() == 2
    assert result.covariance(0, 1) == 0.0
    result_sum = result.sub(lambda a, b: a + b)
    assert result_sum.equals(2 @ icepool.d6)

def test_cartesian_product_cast():
    result = icepool.cartesian_product(icepool.d6, 2)
    assert result.ndim() == 2
    assert result.covariance(0, 1) == 0.0
    result_sum = result.sub(lambda a, b: a + b)
    assert result_sum.equals(icepool.d6 + 2)