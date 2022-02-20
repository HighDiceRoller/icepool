import _context

import hdroller
import pytest

def test_d_syntax():
    assert hdroller.d6.weights() == (1,) * 6
    assert hdroller.d6.probability(0) == 0.0
    assert hdroller.d6.probability(1) == pytest.approx(1.0 / 6.0)
    assert hdroller.d6.probability(6) == pytest.approx(1.0 / 6.0)
    assert hdroller.d6.probability(7) == 0.0

def test_coin():
    b = hdroller.bernoulli(1, 2)
    c = hdroller.coin(1, 2)

    assert b.pmf() == pytest.approx([0.5, 0.5])
    assert c.pmf() == pytest.approx([0.5, 0.5])

def test_list_no_min_outcome():
    result = hdroller.Die(2, 3, 3, 4, 4, 4, 5, 5, 6)
    expected = 2 @ hdroller.d3
    assert result.equals(expected)

def test_zero_outcomes():
    die = hdroller.Die(weights=[0, 1, 1, 1, 1, 1, 1], min_outcome=0)
    other = hdroller.d6
    assert die.has_zero_weights()
    assert not die.equals(other)

def test_d6s():
    d6 = hdroller.d6
    assert d6.equals(hdroller.d(6))
    assert d6.equals(hdroller.Die(d6))
    assert d6.equals(hdroller.Die(hdroller.d3, hdroller.d3+3))
    assert d6.equals(hdroller.Die({1:1, 2:1, 3:1, 4:1, 5:1, 6:1}))
    assert d6.equals(hdroller.Die(1, 2, 3, 4, 5, 6))

def test_return_self():
    die = hdroller.d6
    assert hdroller.Die(die) is die

denominator_method_test_args = [
    ((), None),
    ((hdroller.d5, hdroller.d7), None),
    ((hdroller.d6, hdroller.d8), None),
    ((hdroller.d6, hdroller.d8, hdroller.d10), None),
    ((hdroller.d6, hdroller.d8, hdroller.d10, hdroller.d12), (4, 3, 2, 1)),
    ((hdroller.d6, hdroller.d8, hdroller.d10, hdroller.d12), (3, 4, 5, 6)),
]

@pytest.mark.parametrize('args,weights', denominator_method_test_args)
def test_denominator_method(args, weights):
    prod = hdroller.Die(*args, weights=weights, denominator_method='prod')
    lcm = hdroller.Die(*args, weights=weights, denominator_method='lcm')
    lcm_weighted = hdroller.Die(*args, weights=weights, denominator_method='lcm_weighted')
    assert prod.reduce().equals(lcm.reduce())
    assert prod.reduce().equals(lcm_weighted.reduce())
    assert prod.denominator() >= lcm.denominator()
    assert lcm.denominator() >= lcm_weighted.denominator()

def test_denominator_lcm_weighted():
    result = hdroller.Die(hdroller.d6, hdroller.d8, hdroller.d10, hdroller.d12, weights=(3, 4, 5, 6), denominator_method='lcm_weighted')
    assert result.denominator() == 36
