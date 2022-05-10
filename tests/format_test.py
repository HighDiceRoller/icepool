import _context

import icepool
import pytest

test_dice = [icepool.Die(), icepool.d6, icepool.d6.sub(lambda x: (x, x+1))]

# Test against errors only.

@pytest.mark.parametrize('die', test_dice)
def test_repr(die):
    repr(die)
    
@pytest.mark.parametrize('die', test_dice)
def test_str(die):
    str(die)

@pytest.mark.parametrize('die', test_dice)
@pytest.mark.parametrize('include_weights', [False, True])
@pytest.mark.parametrize('unpack_outcomes', [False, True])
def test_markdown(die, include_weights, unpack_outcomes):
    die.markdown(include_weights=include_weights, unpack_outcomes=unpack_outcomes)
    
@pytest.mark.parametrize('die', test_dice)
@pytest.mark.parametrize('include_weights', [False, True])
@pytest.mark.parametrize('unpack_outcomes', [False, True])
def test_csv(die, include_weights, unpack_outcomes):
    die.csv(include_weights=include_weights, unpack_outcomes=unpack_outcomes)
