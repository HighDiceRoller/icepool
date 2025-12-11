__docformat__ = 'google'

from icepool.generator.multiset_generator import MultisetGenerator, MultisetSource
from icepool.generator.keep import KeepGenerator

from icepool.typing import ImplicitConversionError, T


class WeightlessGenerator(MultisetGenerator[T]):
    """EXPERIMENTAL: A generator wrapper that sets all weights to 1.
    
    This only works properly if the wrapped generator never takes multiple paths
    to the same output multiset.
    """

    def __init__(self, base: KeepGenerator[T]):
        if base.has_negative_keeps() or base.has_zero_keeps():
            raise ValueError(
                'Generators with non-positive keeps cannot be made weightless.'
            )
        self._base = base

    def _make_source(self):
        return WeightlessSource(self._base._make_source())

    @property
    def _static_keepable(self) -> bool:
        return False

    @property
    def hash_key(self):
        return WeightlessGenerator, self._base.hash_key


class WeightlessSource(MultisetSource[T]):

    def __init__(self, base: MultisetSource[T]):
        self._base = base

    def outcomes(self):
        return self._base.outcomes()

    def pop(self, order, outcome):
        for source, count, weight in self._base.pop(order, outcome):
            yield WeightlessSource(source), count, 1

    def size(self):
        return self._base.size()

    def order_preference(self):
        return self._base.order_preference()

    def is_resolvable(self):
        return self._base.is_resolvable()

    @property
    def hash_key(self):
        return WeightlessSource, self._base.hash_key
