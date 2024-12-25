__docformat__ = 'google'

import bisect
from functools import cached_property
import itertools
import random
import icepool
from icepool.collection.counts import Counts

from icepool.generator.pop_order import PopOrderReason
from icepool.typing import T, U, ImplicitConversionError, Order, Outcome, T
from typing import Any, Callable, Collection, Generic, Hashable, Iterable, Iterator, Literal, Mapping, Self, Sequence, Type, TypeAlias, TypeVar, cast, overload

from abc import ABC, abstractmethod


def implicit_convert_to_expression(
    arg: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
) -> 'MultisetExpression[T]':
    """Implcitly converts the argument to a `MultisetExpression`.

    Args:
        arg: The argument must either already be a `MultisetExpression`;
            or a `Mapping` or `Collection`.
    """
    if isinstance(arg, MultisetExpression):
        return arg
    elif isinstance(arg, (Mapping, Sequence)):
        return icepool.Pool(arg)
    else:
        raise ImplicitConversionError(
            f'Argument of type {arg.__class__.__name__} cannot be implicitly converted to a Pool.'
        )


class MultisetExpression(ABC, Generic[T]):
    """Abstract base class representing an expression that operates on multisets.

    Expression methods can be applied to `MultisetGenerator`s to do simple
    evaluations. For joint evaluations, try `multiset_function`.

    Use the provided operations to build up more complicated
    expressions, or to attach a final evaluator.

    Operations include:

    | Operation                   | Count / notes                               |
    |:----------------------------|:--------------------------------------------|
    | `additive_union`, `+`       | `l + r`                                     |
    | `difference`, `-`           | `l - r`                                     |
    | `intersection`, `&`         | `min(l, r)`                                 |
    | `union`, `\\|`               | `max(l, r)`                                 |
    | `symmetric_difference`, `^` | `abs(l - r)`                                |
    | `multiply_counts`, `*`      | `count * n`                                 |
    | `divide_counts`, `//`       | `count // n`                                |
    | `modulo_counts`, `%`        | `count % n`                                 |
    | `keep_counts`               | `count if count >= n else 0` etc.           |
    | unary `+`                   | same as `keep_counts_ge(0)`                 |
    | unary `-`                   | reverses the sign of all counts             |
    | `unique`                    | `min(count, n)`                             |
    | `keep_outcomes`             | `count if outcome in t else 0`              |
    | `drop_outcomes`             | `count if outcome not in t else 0`          |
    | `map_counts`                | `f(outcome, *counts)`                       |
    | `keep`, `[]`                | less capable than `KeepGenerator` version   |
    | `highest`                   | less capable than `KeepGenerator` version   |
    | `lowest`                    | less capable than `KeepGenerator` version   |

    | Evaluator                      | Summary                                                                    |
    |:-------------------------------|:---------------------------------------------------------------------------|
    | `issubset`, `<=`               | Whether the left side's counts are all <= their counterparts on the right  |
    | `issuperset`, `>=`             | Whether the left side's counts are all >= their counterparts on the right  |
    | `isdisjoint`                   | Whether the left side has no positive counts in common with the right side |
    | `<`                            | As `<=`, but `False` if the two multisets are equal                        |
    | `>`                            | As `>=`, but `False` if the two multisets are equal                        |
    | `==`                           | Whether the left side has all the same counts as the right side            |
    | `!=`                           | Whether the left side has any different counts to the right side           |
    | `expand`                       | All elements in ascending order                                            |
    | `sum`                          | Sum of all elements                                                        |
    | `count`                        | The number of elements                                                     |
    | `any`                          | Whether there is at least 1 element                                        |
    | `highest_outcome_and_count`    | The highest outcome and how many of that outcome                           |
    | `all_counts`                   | All counts in descending order                                             |
    | `largest_count`                | The single largest count, aka x-of-a-kind                                  |
    | `largest_count_and_outcome`    | Same but also with the corresponding outcome                               |
    | `count_subset`, `//`           | The number of times the right side is contained in the left side           |
    | `largest_straight`             | Length of longest consecutive sequence                                     |
    | `largest_straight_and_outcome` | Same but also with the corresponding outcome                               |
    | `all_straights`                | Lengths of all consecutive sequences in descending order                   |
    """

    _children: 'tuple[MultisetExpression[T], ...]'
    """A tuple of child expressions. These are assumed to the positional arguments of the constructor."""

    @abstractmethod
    def outcomes(self) -> Sequence[T]:
        """The possible outcomes that could be generated, in ascending order."""

    @abstractmethod
    def output_arity(self) -> int:
        """The number of multisets/counts generated. Must be constant."""

    @abstractmethod
    def _is_resolvable(self) -> bool:
        """`True` iff the generator is capable of producing an overall outcome.

        For example, a dice `Pool` will return `False` if it contains any dice
        with no outcomes.
        """

    @abstractmethod
    def _generate_initial(self) -> Iterator[tuple['MultisetExpression', int]]:
        """Initialize the expression before any outcomes are emitted.

        Yields:
            * Each possible initial expression.
            * The weight for selecting that initial expression.
        
        Unitary expressions can just yield `(self, 1)` and return.
        """

    @abstractmethod
    def _generate_min(
        self, min_outcome: T
    ) -> Iterator[tuple['MultisetExpression', Sequence, int]]:
        """Pops the min outcome from this expression if it matches the argument.

        Yields:
            * Ax expression with the min outcome popped.
            * A tuple of counts for the min outcome.
            * The weight for this many of the min outcome appearing.

            If the argument does not match the min outcome, or this expression
            has no outcomes, only a single tuple is yielded:

            * `self`
            * A tuple of zeros.
            * weight = 1.

        Raises:
            UnboundMultisetExpressionError if this is called on an expression with free variables.
        """

    @abstractmethod
    def _generate_max(
        self, max_outcome: T
    ) -> Iterator[tuple['MultisetExpression', Sequence, int]]:
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
    def _preferred_pop_order(self) -> tuple[Order | None, PopOrderReason]:
        """Returns the preferred pop order of the expression, along with the priority of that pop order.

        Greater priorities strictly outrank lower priorities.
        An order of `None` represents conflicting orders and can occur in the 
        argument and/or return value.
        """

    @abstractmethod
    def order(self) -> Order:
        """Any ordering that is required by this expression.

        This should check any previous expressions for their order, and
        raise a ValueError for any incompatibilities.

        Returns:
            The required order.
        """

    @abstractmethod
    def _free_arity(self) -> int:
        """The minimum number of multisets/counts that must be provided to this expression.

        Any excess multisets/counts that are provided will be ignored.

        This does not include bound generators.
        """

    @abstractmethod
    def denominator(self) -> int:
        """The total weight of all paths through this generator.
        
        Raises:
            UnboundMultisetExpressionError if this is called on an expression with free variables.
        """

    @abstractmethod
    def _unbind(self, next_index: int) -> 'tuple[MultisetExpression, int]':
        """Replaces bound generators within this expression with free variables.

        Bound generators are replaced with free variables with index equal to
        their position in _bound_generators().

        Variables that are already free have their indexes shifted by the
        number of bound genrators.

        Args:
            next_index: The index of the next bound generator.

        Returns:
            The transformed expression and the new next_index.
        """

    @property
    @abstractmethod
    def _local_hash_key(self) -> Hashable:
        """A hash key that logically identifies this object among MultisetExpressions.

        Does not include the hash for children.

        Used to implement `equals()` and `__hash__()`
        """

    def min_outcome(self) -> T:
        return self.outcomes()[0]

    def max_outcome(self) -> T:
        return self.outcomes()[-1]

    @cached_property
    def _hash_key(self) -> Hashable:
        """A hash key that logically identifies this object among MultisetExpressions.

        Used to implement `equals()` and `__hash__()`
        """
        return (self._local_hash_key, ) + tuple(child._hash_key
                                                for child in self._children)

    def equals(self, other) -> bool:
        """Whether this expression is logically equal to another object."""
        if not isinstance(other, MultisetExpression):
            return False
        return self._hash_key == other._hash_key

    @cached_property
    def _hash(self) -> int:
        return hash(self._hash_key)

    def __hash__(self) -> int:
        return self._hash

    # Sampling.

    def sample(self) -> tuple[tuple, ...]:
        """EXPERIMENTAL: A single random sample from this generator.

        This uses the standard `random` package and is not cryptographically
        secure.

        Returns:
            A sorted tuple of outcomes for each output of this generator.
        """
        if not self.outcomes():
            raise ValueError('Cannot sample from an empty set of outcomes.')

        preferred_pop_order, pop_order_reason = self._preferred_pop_order()

        if preferred_pop_order is not None and preferred_pop_order > 0:
            outcome = self.min_outcome()
            generated = tuple(self._generate_min(outcome))
        else:
            outcome = self.max_outcome()
            generated = tuple(self._generate_max(outcome))

        cumulative_weights = tuple(
            itertools.accumulate(g.denominator() * w for g, _, w in generated))
        denominator = cumulative_weights[-1]
        # We don't use random.choices since that is based on floats rather than ints.
        r = random.randrange(denominator)
        index = bisect.bisect_right(cumulative_weights, r)
        popped_generator, counts, _ = generated[index]
        head = tuple((outcome, ) * count for count in counts)
        if popped_generator.outcomes():
            tail = popped_generator.sample()
            return tuple(tuple(sorted(h + t)) for h, t, in zip(head, tail))
        else:
            return head

    def _compare(
        self,
        right: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
        operation_class: Type['icepool.evaluator.ComparisonEvaluator'],
        *,
        truth_value_callback: 'Callable[[], bool] | None' = None
    ) -> 'icepool.Die[bool] | icepool.MultisetEvaluator[T, bool]':
        if isinstance(right, MultisetExpression):
            evaluator = icepool.evaluator.ExpressionEvaluator(
                self, right, evaluator=operation_class())
        elif isinstance(right, (Mapping, Sequence)):
            right_expression = icepool.implicit_convert_to_expression(right)
            evaluator = icepool.evaluator.ExpressionEvaluator(
                self, right_expression, evaluator=operation_class())
        else:
            raise TypeError('Operand not comparable with expression.')

        if evaluator._free_arity == 0:
            if truth_value_callback is not None:

                def data_callback() -> Counts[bool]:
                    die = cast('icepool.Die[bool]', evaluator.evaluate())
                    if not isinstance(die, icepool.Die):
                        raise TypeError('Did not resolve to a die.')
                    return die._data

                return icepool.DieWithTruth(data_callback,
                                            truth_value_callback)
            else:
                return evaluator.evaluate()
        else:
            return evaluator

    def __eq__(  # type: ignore
            self,
            other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
            /) -> 'icepool.Die[bool] | icepool.MultisetEvaluator[T, bool]':
        try:

            def truth_value_callback() -> bool:
                if not isinstance(other, MultisetExpression):
                    return False
                return self._hash_key == other._hash_key

            return self._compare(other,
                                 icepool.evaluator.IsEqualSetEvaluator,
                                 truth_value_callback=truth_value_callback)
        except TypeError:
            return NotImplemented

    def __ne__(  # type: ignore
            self,
            other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
            /) -> 'icepool.Die[bool] | icepool.MultisetEvaluator[T, bool]':
        try:

            def truth_value_callback() -> bool:
                if not isinstance(other, MultisetExpression):
                    return False
                return self._hash_key != other._hash_key

            return self._compare(other,
                                 icepool.evaluator.IsNotEqualSetEvaluator,
                                 truth_value_callback=truth_value_callback)
        except TypeError:
            return NotImplemented
