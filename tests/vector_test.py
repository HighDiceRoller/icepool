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

def test_vector_add():
    result = icepool.Die((icepool.d8, 1)) + icepool.Die((0, icepool.d6))
    expected = icepool.Die((icepool.d8, icepool.d6 + 1))
    assert result.equals(expected)

def test_vector_matmul():
    result = 2 @ icepool.Die((icepool.d6, icepool.d8))
    expected = icepool.Die((2 @ icepool.d6, 2 @ icepool.d8))
    assert result.equals(expected)
    
def test_binary_op_mismatch_outcome_len():
    with pytest.raises(ValueError):
        result = icepool.d6 + icepool.Die((icepool.d6, icepool.d8))
