__docformat__ = 'google'

import icepool
from icepool.expression.multiset_expression import MultisetExpression

from functools import cached_property

from icepool.typing import Order, Outcome

from typing import Callable, Collection, Hashable, Mapping, Sequence, Type, TypeAlias, TypeVar


class BoundGeneratorExpression(MultisetExpression):
    """An independent, bound generator.

    These generators are always considered to operate independently. This is in
    contrast to `MultisetVariable`, where multiple appearances of the same
    variable are considered to be the same generator.
    """

    def __init__(self, generator: icepool.MultisetGenerator) -> None:
        if generator.arity != 1:
            raise ValueError('Bound generators must have an arity of 1.')
        self._generator = generator

    def next_state(self, state, outcome: Outcome, bound_counts: tuple[int, ...],
                   counts: tuple[int, ...]) -> tuple[Hashable, int]:
        # No state is needed, so we return the class name of the generator
        # for diagnostic purposes.
        return str(type(self._generator)), bound_counts[0]

    def order(self) -> Order:
        return Order.Any

    def shift_variables(self, shift: int) -> 'MultisetExpression':
        return self

    def bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return (self._generator,)

    @property
    def arity(self) -> int:
        return 0
