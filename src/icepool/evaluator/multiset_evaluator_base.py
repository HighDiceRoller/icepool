__docformat__ = 'google'

import icepool
from icepool.order import ConflictingOrderError, Order, OrderReason, UnsupportedOrderError, merge_order_preferences

from abc import ABC, abstractmethod
from collections import defaultdict
from functools import cached_property
import itertools
import math

from icepool.typing import Q, T, U_co
from typing import (Any, Callable, Collection, Generic, Hashable, Iterator,
                    Literal, Mapping, MutableMapping, Sequence, TypeAlias,
                    cast, TYPE_CHECKING, overload)

if TYPE_CHECKING:
    from icepool.expression.multiset_expression_base import MultisetExpressionBase
    from icepool.evaluator.multiset_function import MultisetFunctionRawResult
    from icepool.generator.alignment import Alignment
    from icepool import MultisetExpression


class MultisetEvaluatorBase(ABC, Generic[T, U_co]):

    _cache: 'MutableMapping[MultisetDungeon, MultisetDungeon] | None' = None

    @abstractmethod
    def _prepare(
        self,
        inputs: 'tuple[MultisetExpressionBase[T, Q], ...]',
        kwargs: Mapping[str, Hashable],
    ) -> 'Iterator[tuple[MultisetDungeon, tuple[MultisetExpressionBase, ...], int]]':
        """Prepares an evaluation.

        Args:
            inputs: This is just for the benefit of `@multiset_function`
                so it can know whether the arguments are single multisets or
                multiset tuples.
            kwargs: Used as part of the dungeon's cache key.
                `@multiset_function` also determines how to forward these to
                the inner evaluators.

        Yields:
            dungeon, body_inputs, weight
        """

    def evaluate(
        self, *args: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
        **kwargs: Hashable
    ) -> 'icepool.Die[U_co] | MultisetFunctionRawResult[T, U_co]':
        """Evaluates input expression(s).

        You can call the evaluator object directly for the same effect,
        e.g. `sum_evaluator(input)` is an alias for `sum_evaluator.evaluate(input)`.

        Positional arguments are multisets. Most evaluators will expect a 
        fixed number of input multisets of these. The union of the outcomes of
        the input(s) must be totally orderable.

        Non-multiset arguments can be provided as keyword arguments.

        Args:
            *args: Each may be one of the following:
                * A `MultisetExpression`.
                * A mappable mapping outcomes to the number of those outcomes.
                * A sequence of outcomes.

        Returns:
            A `Die` representing the distribution of the final outcome if no
            arg contains a parameter. Otherwise returns information
            needed to construct a `@multiset_function`.
        """

        # Convert arguments to expressions.
        inputs = tuple(
            icepool.implicit_convert_to_expression(arg) for arg in args)

        # In this case we are inside a @multiset_function.
        if any(input.has_parameters() for input in inputs):
            from icepool.evaluator.multiset_function import MultisetFunctionRawResult
            return MultisetFunctionRawResult(self, inputs, kwargs)

        # Otherwise, we perform the evaluation.

        if not all(expression._is_resolvable() for expression in inputs):
            return icepool.Die([])

        if self._cache is None:
            self._cache = {}

        final_data: 'MutableMapping[icepool.Die[U_co], int]' = defaultdict(int)
        for p in itertools.product(*(expression._prepare()
                                     for expression in inputs)):
            sub_inputs, sub_weights = zip(*p)
            for dungeon, body_inputs, dungeon_weight in self._prepare(
                    sub_inputs, kwargs):
                # TODO: initialize body_inputs inside prepare

                # replace dungeon with cached version if available
                if dungeon in self._cache:
                    dungeon = self._cache[dungeon]
                else:
                    self._cache[dungeon] = dungeon

                prod_weight = math.prod(sub_weights) * dungeon_weight
                outcomes = icepool.sorted_union(
                    *(expression.outcomes() for expression in sub_inputs))
                extra_outcomes = icepool.Alignment(
                    dungeon.extra_outcomes(outcomes))
                sub_result = dungeon.evaluate(extra_outcomes,
                                              body_inputs + sub_inputs, kwargs)
                final_data[sub_result] += prod_weight

        return icepool.Die(final_data)

    __call__ = evaluate


class MultisetDungeon(Generic[T, U_co], Hashable):
    """Holds values that are constant within a single evaluation, along with a cache."""

    ascending_cache: 'MutableMapping[tuple[Alignment, tuple[MultisetExpressionBase[T, Any], ...], Hashable], Mapping[U_co, int]]'
    """Maps (extra_outcomes, inputs, initial_state) -> final_state -> int for next_state_ascending_function."""
    descending_cache: 'MutableMapping[tuple[Alignment, tuple[MultisetExpressionBase[T, Any], ...], Hashable], Mapping[U_co, int]]'
    """Maps (extra_outcomes, inputs, initial_state) -> final_state -> int for next_state_descending_function."""

    @abstractmethod
    def initial_state(self, order: Order, outcomes: Sequence[T], /, **kwargs):
        """
        TODO: Should this get cardinalities?

        Args:
            order: The order in which next_state will see outcomes.
            outcomes: All outcomes that will be seen by next_state in sorted order.
            kwargs: Any keyword arguments that were passed to `evaluate()`.

        Raises:
            UnsupportedOrderError if the given order is not supported.
        """

    @abstractmethod
    def next_state_ascending(self, state: Hashable, outcome: T, /,
                             *counts) -> Hashable:
        """The next_state function to use when going in ascending order.
        
        This method may be set to None in subclasses.
        """

    @abstractmethod
    def next_state_descending(self, state: Hashable, outcome: T, /,
                              *counts) -> Hashable:
        """The next_state function to use when going in descending order.
        
        This method may be set to None in subclasses.
        """

    @abstractmethod
    def extra_outcomes(self, outcomes: Sequence[T]) -> Collection[T]:
        """Extra outcomes that should be seen."""

    @abstractmethod
    def final_outcome(
            self, final_state: Hashable, /, **kwargs: Hashable
    ) -> 'U_co | icepool.Die[U_co] | icepool.RerollType':
        """Generates a final outcome from a final state."""

    def evaluate_backward(
        self, input_order: Order, extra_outcomes: 'Alignment[T]',
        initial_state: Hashable,
        inputs: 'tuple[MultisetExpressionBase[T, Q], ...]'
    ) -> Mapping[Any, int]:
        """Internal algorithm for iterating so that next_state sees outcomes in backwards order.

        All intermediate return values are cached in the instance.

        Arguments:
            order: The order in which to send outcomes to `next_state()`.
            extra_outcomes: As `extra_outcomes()`. Elements will be popped off this
                during recursion.
            inputs: One or more `MultisetExpression`s to evaluate. Elements
                will be popped off this during recursion.

        Returns:
            A dict `{ state : weight }` describing the probability distribution
                over states.
        """
        # Since this is the backward evaluation, these are opposite of the
        # input order.
        if input_order > 0:
            cache = self.descending_cache
            next_state_function = self.next_state_descending
        else:
            cache = self.ascending_cache
            next_state_function = self.next_state_ascending

        if next_state_function is None:
            raise UnsupportedOrderError()

        cache_key = (extra_outcomes, inputs, initial_state)
        if cache_key in cache:
            return cache[cache_key]

        result: MutableMapping[Any, int] = defaultdict(int)

        if all(not input.outcomes()
               for input in inputs) and not extra_outcomes.outcomes():
            result = {initial_state: 1}
        else:
            outcome, prev_extra_outcomes, iterators = MultisetDungeon._pop_inputs(
                input_order, extra_outcomes, inputs)
            for p in itertools.product(*iterators):
                prev_inputs, counts, weights = zip(*p)
                prod_weight = math.prod(weights)
                prev = self.evaluate_backward(input_order, prev_extra_outcomes,
                                              initial_state, prev_inputs)
                for prev_state, prev_weight in prev.items():
                    state = next_state_function(prev_state, outcome, *counts)
                    if state is not icepool.Reroll:
                        result[state] += prev_weight * prod_weight

        cache[cache_key] = result
        return result

    def evaluate_forward(
        self, input_order: Order, extra_outcomes: 'Alignment[T]',
        initial_state: Hashable,
        inputs: 'tuple[icepool.MultisetExpression[T], ...]'
    ) -> Mapping[Any, int]:
        """Internal algorithm for iterating in the less-preferred order.

        All intermediate return values are cached in the instance.

        Arguments:
            order: The order in which to send outcomes to `next_state()`.
            extra_outcomes: As `extra_outcomes()`. Elements will be popped off this
                during recursion.
            inputs: One or more `MultisetExpression`s to evaluate. Elements
                will be popped off this during recursion.

        Returns:
            A dict `{ state : weight }` describing the probability distribution
                over states.
        """
        if input_order > 0:
            cache = self.ascending_cache
            next_state_function = self.next_state_ascending
        else:
            cache = self.descending_cache
            next_state_function = self.next_state_descending

        if next_state_function is None:
            raise UnsupportedOrderError()

        cache_key = (extra_outcomes, inputs, initial_state)
        if cache_key in cache:
            return cache[cache_key]

        result: MutableMapping[Any, int] = defaultdict(int)

        if all(not input.outcomes()
               for input in inputs) and not extra_outcomes.outcomes():
            result = {initial_state: 1}
        else:
            outcome, next_extra_outcomes, iterators = MultisetDungeon._pop_inputs(
                input_order, extra_outcomes, inputs)
            for p in itertools.product(*iterators):
                next_inputs, counts, weights = zip(*p)
                prod_weight = math.prod(weights)
                next_state = next_state_function(initial_state, outcome,
                                                 *counts)
                if next_state is not icepool.Reroll:
                    final_dist = self.evaluate_forward(input_order,
                                                       next_extra_outcomes,
                                                       next_state, next_inputs)
                    for final_state, weight in final_dist.items():
                        result[final_state] += weight * prod_weight

        cache[cache_key] = result
        return result

    def evaluate(self, extra_outcomes: 'Alignment[T]',
                 inputs: 'tuple[icepool.MultisetExpression[T], ...]',
                 kwargs: Mapping[str, Hashable]) -> 'icepool.Die[U_co]':
        """Runs evaluate_forward or evaluate_backward according to the input order versus the eval order."""

        input_order, input_order_reason = merge_order_preferences(
            (Order.Descending, OrderReason.Default),
            *(input.order_preference() for input in inputs))

        try:
            initial_state = self.initial_state(-input_order,
                                               extra_outcomes.outcomes(),
                                               **kwargs)
            final_states = self.evaluate_backward(input_order, extra_outcomes,
                                                  initial_state, inputs)
            return self._finalize_evaluation(final_states, kwargs)
        except UnsupportedOrderError:
            try:
                initial_state = self.initial_state(input_order,
                                                   extra_outcomes.outcomes(),
                                                   **kwargs)
                final_states = self.evaluate_forward(input_order,
                                                     extra_outcomes,
                                                     initial_state, inputs)
                return self._finalize_evaluation(final_states, kwargs)
            except UnsupportedOrderError:
                raise ConflictingOrderError(
                    'Neither ascending nor descending order is compatable with the evaluation. '
                    +
                    f'Preferred input order was {input_order.name} with reason {input_order_reason.name}.'
                )

    def _finalize_evaluation(
            self, final_states: Mapping[Any, int],
            kwargs: Mapping[str, Hashable]) -> 'icepool.Die[U_co]':
        final_outcomes = []
        final_weights = []
        for state, weight in final_states.items():
            outcome = self.final_outcome(state, **kwargs)
            if outcome is None:
                raise TypeError(
                    "None is not a valid final outcome.\n"
                    "This may have been a result of not supplying any input with an outcome."
                )
            if outcome is not icepool.Reroll:
                final_outcomes.append(outcome)
                final_weights.append(weight)

        return icepool.Die(final_outcomes, final_weights)

    @staticmethod
    def _pop_inputs(
        order: Order, extra_outcomes: 'Alignment[T]',
        inputs: 'tuple[MultisetExpressionBase[T, Q], ...]'
    ) -> 'tuple[T, Alignment[T], tuple[Iterator[tuple[MultisetExpressionBase, Any, int]], ...]]':
        """Pops a single outcome from the inputs.

        Args:
            order: The order in which to pop. Descending order pops from the top
            and ascending from the bottom.
            extra_outcomes: Any extra outcomes to use.
            inputs: The inputs to pop from.

        Returns:
            * The popped outcome.
            * The remaining extra outcomes.
            * A tuple of iterators over the resulting inputs, counts, and weights.
        """
        extra_outcomes_and_inputs = (extra_outcomes, ) + inputs
        if order < 0:
            outcome = max(input.max_outcome()
                          for input in extra_outcomes_and_inputs
                          if input.outcomes())

            next_extra_outcomes, _, _ = next(
                extra_outcomes._generate_max(outcome))

            return outcome, next_extra_outcomes, tuple(
                input._generate_max(outcome) for input in inputs)
        else:
            outcome = min(input.min_outcome()
                          for input in extra_outcomes_and_inputs
                          if input.outcomes())

            next_extra_outcomes, _, _ = next(
                extra_outcomes._generate_min(outcome))

            return outcome, next_extra_outcomes, tuple(
                input._generate_min(outcome) for input in inputs)
