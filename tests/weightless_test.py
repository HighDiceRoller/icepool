import icepool
import pytest

from icepool import d6, Deck

test_generators = [
    d6.pool(3),
    Deck([1, 2, 2, 3, 3, 3, 4, 4, 4, 4]).deal(4),
]


@pytest.mark.parametrize('generator', test_generators)
def test_weightless_expand(generator):
    standard_expand = generator.expand()
    weightless_expand = generator.weightless().expand()
    assert len(weightless_expand) == len(standard_expand)
    assert weightless_expand.denominator() == len(standard_expand)
