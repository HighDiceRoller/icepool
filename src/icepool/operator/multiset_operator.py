__docformat__ = 'google'

import icepool
from icepool.generator.pop_order import PopOrderReason, merge_pop_orders
from icepool.multiset_expression import MultisetExpression, InitialMultisetGeneration, PopMultisetGeneration

import itertools
import math

from icepool.typing import T, U, ImplicitConversionError, Order, Outcome, T
from typing import Any, Callable, Collection, Generic, Hashable, Iterable, Iterator, Literal, Mapping, Self, Sequence, Type, TypeAlias, TypeVar, cast, overload

from abc import abstractmethod


class MultisetOperator(MultisetExpression[T]):
    """Internal node of an expression taking one or more counts and producing a single count."""

    @abstractmethod
    def _copy(
        self, copy_children: 'Iterable[MultisetExpression[T]]'
    ) -> 'MultisetExpression[T]':
        """Creates a copy of self with the given children.
        
        I considered using `copy.copy` but this doesn't play well with
        incidental members such as in `@cached_property`.
        """

    @abstractmethod
    def _transform_next(
            self, next_children: 'Iterable[MultisetExpression[T]]', outcome: T,
            counts: 'tuple[int, ...]') -> 'tuple[MultisetExpression[T], int]':
        """Produce the next state of this expression.

        Args:
            next_children: The children of the result are to be set to this.
            outcome: The outcome being processed.
            counts: One count per child.

        Returns:
            An expression representing the next state and the count produced by this expression.

        Raises:
            UnboundMultisetExpressionError if this is called on an expression with free variables.
        """

    def outcomes(self) -> Sequence[T]:
        return icepool.sorted_union(*(child.outcomes()
                                      for child in self._children))

    def output_arity(self) -> int:
        """Transforms only output 1 count. For multiple outputs, use @multiset_function."""
        return 1

    def _is_resolvable(self) -> bool:
        return all(child._is_resolvable() for child in self._children)

    def _generate_initial(self) -> InitialMultisetGeneration:
        for t in itertools.product(*(child._generate_initial()
                                     for child in self._children)):
            next_children, weights = zip(*t)
            next_self = self._copy(next_children)
            yield next_self, math.prod(weights)

    def _generate_min(self, min_outcome: T) -> PopMultisetGeneration:
        for t in itertools.product(*(child._generate_min(min_outcome)
                                     for child in self._children)):
            next_children, counts, weights = zip(*t)
            next_self, count = self._transform_next(next_children, min_outcome,
                                                    counts)
            yield next_self, (count, ), math.prod(weights)

    def _generate_max(self, max_outcome: T) -> PopMultisetGeneration:
        for t in itertools.product(*(child._generate_min(max_outcome)
                                     for child in self._children)):
            next_children, counts, weights = zip(*t)
            next_self, count = self._transform_next(next_children, max_outcome,
                                                    counts)
            yield next_self, (count, ), math.prod(weights)

    def _local_preferred_pop_order(
            self) -> tuple[Order | None, PopOrderReason]:
        return merge_pop_orders(*(child._local_preferred_pop_order()
                                  for child in self._children))

    def _free_arity(self) -> int:
        return max(child._free_arity() for child in self._children)

    def denominator(self) -> int:
        return math.prod(child.denominator() for child in self._children)

    def _unbind(self, next_index: int) -> 'tuple[MultisetExpression, int]':
        unbound_children = []
        for child in self._children:
            unbound_child, next_index = child._unbind(next_index)
            unbound_children.append(unbound_child)
        unbound_expression = self._copy(unbound_children)
        return unbound_expression, next_index
