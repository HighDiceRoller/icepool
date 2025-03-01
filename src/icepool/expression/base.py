__docformat__ = 'google'

import icepool
from icepool.collection.counts import Counts
from icepool.order import Order, OrderReason, merge_order_preferences
from icepool.population.keep import highest_slice, lowest_slice

import bisect
from functools import cached_property
import itertools
import operator
import random

from icepool.typing import Q, T, U, Expandable, ImplicitConversionError, T
from types import EllipsisType
from typing import (Any, Callable, Collection, Generic, Hashable, Iterator,
                    Literal, Mapping, Sequence, Type, TypeAlias, TypeVar, cast,
                    overload)

from abc import ABC, abstractmethod


class MultisetBindingError(TypeError):
    """Indicates a bound multiset variable was found where a free variable was expected, or vice versa."""


C = TypeVar('C', bound='MultisetExpressionBase')
"""Type variable representing a subclass of `MultisetExpressionBase`."""


class MultisetExpressionBase(ABC, Generic[T, Q], Hashable):
    _children: 'tuple[MultisetExpressionBase[T, Any], ...]'
    """A tuple of child expressions. These are assumed to the positional arguments of the constructor."""

    @property
    @abstractmethod
    def _variable_type(self) -> type:
        """Returns the corresponding multiset variable type."""
        ...

    @abstractmethod
    def _generate_initial(
            self) -> Iterator[tuple['MultisetExpressionBase[T, Q]', int]]:
        """Initialize the expression before any outcomes are emitted.

        Yields:
            * Each possible initial expression.
            * The weight for selecting that initial expression.
        
        Unitary expressions can just yield `(self, 1)` and return.
        """

    @abstractmethod
    def _generate_min(self: C, min_outcome: T) -> Iterator[tuple[C, Q, int]]:
        """Pops the min outcome from this expression if it matches the argument.

        Yields:
            * Ax expression with the min outcome popped.
            * A tuple of counts for the min outcome.
            * The weight for this many of the min outcome appearing.

            If the argument does not match the min outcome, or this expression
            has no outcomes, only a single tuple is yielded:

            * `self`
            * Zero count.
            * weight = 1.

        Raises:
            UnboundMultisetExpressionError if this is called on an expression with free variables.
        """

    @abstractmethod
    def _generate_max(self: C, max_outcome: T) -> Iterator[tuple[C, Q, int]]:
        """Pops the max outcome from this expression if it matches the argument.

        Yields:
            * An expression with the max outcome popped.
            * A tuple of counts for the max outcome.
            * The weight for this many of the max outcome appearing.

            If the argument does not match the max outcome, or this expression
            has no outcomes, only a single tuple is yielded:

            * `self`
            * A tuple of zeros.
            * weight = 1.

        Raises:
            UnboundMultisetExpressionError if this is called on an expression with free variables.
        """

    @abstractmethod
    def _unbind(
        self,
        bound_inputs: 'list[MultisetExpressionBase]' = []
    ) -> 'MultisetExpressionBase[T, Q]':
        """Removes bound subexpressions, replacing them with variables.

        Args:
            bound_inputs: The list of bound subexpressions. Bound subexpressions
                will be added to this list.

        Returns:
            A copy of this expression with any fully-bound subexpressions
            replaced with variables. The `index` of each variable is equal to
            the position of the expression they replaced in `bound_inputs`.
        """

    @abstractmethod
    def _apply_variables(
        self, outcome: T, bound_counts: tuple[int, ...],
        free_counts: tuple[int,
                           ...]) -> 'tuple[MultisetExpressionBase[T, Q], Q]':
        """Advances the state of this expression given counts emitted from variables and returns a count.
        
        Args:
            outcome: The current outcome being processed.
            bound_counts: The counts emitted by bound expressions.
            free_counts: The counts emitted by arguments to the
                `@mulitset_function`.

        Returns:
            An expression representing the next state and the count produced by
            this expression.
        """

    @abstractmethod
    def outcomes(self) -> Sequence[T]:
        """The possible outcomes that could be generated, in ascending order."""

    @abstractmethod
    def _is_resolvable(self) -> bool:
        """`True` iff the generator is capable of producing an overall outcome.

        For example, a dice `Pool` will return `False` if it contains any dice
        with no outcomes.
        """

    @abstractmethod
    def local_order_preference(self) -> tuple[Order, OrderReason]:
        """Any ordering that is preferred or required by this expression node."""

    @abstractmethod
    def has_free_variables(self) -> bool:
        """Whether this expression contains any free variables, i.e. parameters to a @multiset_function."""

    @abstractmethod
    def denominator(self) -> int:
        """The total weight of all paths through this generator.
        
        Raises:
            UnboundMultisetExpressionError if this is called on an expression with free variables.
        """

    @property
    @abstractmethod
    def _local_hash_key(self) -> Hashable:
        """A hash key that logically identifies this object among MultisetExpressions.

        Does not include the hash for children.

        Used to implement `equals()` and `__hash__()`
        """

    @property
    def _can_keep(self) -> bool:
        """Whether the expression supports enhanced keep operations."""
        return False

    def min_outcome(self) -> T:
        return self.outcomes()[0]

    def max_outcome(self) -> T:
        return self.outcomes()[-1]

    @cached_property
    def _hash_key(self) -> Hashable:
        """A hash key that logically identifies this object among MultisetExpressions.

        Used to implement `equals()` and `__hash__()`
        """
        return (self._local_hash_key,
                tuple(child._hash_key for child in self._children))

    def equals(self, other) -> bool:
        """Whether this expression is logically equal to another object."""
        if not isinstance(other, MultisetExpressionBase):
            return False
        return self._hash_key == other._hash_key

    @cached_property
    def _hash(self) -> int:
        return hash(self._hash_key)

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other, /) -> bool:
        return self.equals(other)

    def __ne__(self, other, /) -> bool:
        return not self.equals(other)

    def _iter_nodes(self) -> 'Iterator[MultisetExpressionBase]':
        """Iterates over the nodes in this expression in post-order (leaves first)."""
        for child in self._children:
            yield from child._iter_nodes()
        yield self

    def order_preference(self) -> tuple[Order, OrderReason]:
        return merge_order_preferences(*(node.local_order_preference()
                                         for node in self._iter_nodes()))
