import _context

import icepool
import pytest

test_dice = [icepool.Die([]), icepool.d6, icepool.d6.sub(lambda x: (x, x+1))]

# Test against errors only.

@pytest.mark.parametrize('die', test_dice)
def test_repr(die):
    repr(die)
    
@pytest.mark.parametrize('die', test_dice)
def test_str(die):
    str(die)
    
format_specs = [
    '',
    'md:q==|q<=|q>=',
    'md:p==|p<=|p>=',
    'md:%==|%>=|%>=',
    'csv:q==|q<=|q>=',
    'csv:p==|p<=|p>=',
    'csv:%==|%>=|%>=',
]

@pytest.mark.parametrize('die', test_dice)
@pytest.mark.parametrize('format_spec', format_specs)
def test_format_spec(die, format_spec):
    f'{die:{format_spec}}'

