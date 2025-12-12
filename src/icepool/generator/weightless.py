__docformat__ = 'google'

from icepool.generator.multiset_generator import MultisetGenerator, MultisetSource

from icepool.order import UnsupportedOrder
from icepool.typing import ImplicitConversionError, T


class WeightlessGenerator(MultisetGenerator[T]):
    """EXPERIMENTAL: A generator wrapper that sets all weights to 1.
    
    This only works properly if the wrapped generator never takes multiple paths
    to the same output multiset.
    """

    def __init__(self, wrapped: MultisetGenerator[T], /):
        self._wrapped = wrapped

    def _make_source(self):
        return WeightlessSource(self._wrapped._make_source())

    @property
    def _static_keepable(self) -> bool:
        return False

    @property
    def hash_key(self):
        return WeightlessGenerator, self._wrapped.hash_key


class WeightlessSource(MultisetSource[T]):

    def __init__(self, wrapped: MultisetSource[T], /):
        self._wrapped = wrapped

    def outcomes(self):
        return self._wrapped.outcomes()

    def pop(self, order, outcome):
        seen_counts = set()
        for source, count, weight in self._wrapped.pop(order, outcome):
            if count in seen_counts:
                raise UnsupportedOrder(
                    'weightless cannot handle calls to pop() that produce the same count multiple times.'
                )
            seen_counts.add(count)
            yield WeightlessSource(source), count, 1

    def size(self):
        return self._wrapped.size()

    def order_preference(self):
        return self._wrapped.order_preference()

    def is_resolvable(self):
        return self._wrapped.is_resolvable()

    @property
    def hash_key(self):
        return WeightlessSource, self._wrapped.hash_key
