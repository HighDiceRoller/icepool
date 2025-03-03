__docformat__ = 'google'

import icepool
from icepool.order import ConflictingOrderError, Order, OrderReason, merge_order_preferences

from abc import ABC, abstractmethod
from collections import defaultdict
from functools import cached_property
import itertools
import math

from icepool.typing import Q, T, U_co
from typing import (Any, Callable, Collection, Generic, Hashable, Iterator,
                    Mapping, MutableMapping, Sequence, TypeAlias, cast,
                    TYPE_CHECKING, overload)

if TYPE_CHECKING:
    from icepool.expression.base import MultisetExpressionBase
    from icepool.generator.alignment import Alignment
    from icepool import MultisetExpression


def _initialize_inputs(
    inputs: 'tuple[MultisetExpressionBase[T, Q], ...]'
) -> 'tuple[Iterator[tuple[MultisetExpressionBase[T, Q], int]], ...]':
    return tuple(expression._generate_initial() for expression in inputs)


class MultisetEvaluatorBase(ABC, Generic[T, U_co]):

    @abstractmethod
    def prepare(
        self,
        inputs: 'tuple[MultisetExpressionBase[T, Q], ...]',
        kwargs: Mapping[str, Hashable],
    ) -> 'tuple[MultisetDungeon, tuple[MultisetExpressionBase, ...]]':
        """Prepares an evaluation.
        
        In the future this will likely allow yielding multiple results.
        """

    def evaluate(
        self, *args: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
        **kwargs: Hashable
    ) -> 'icepool.Die[U_co] | tuple[MultisetEvaluatorBase[T, U_co], tuple[MultisetExpressionBase[T, Any], ...], Mapping[str, Hashable]]':
        """Evaluates input expression(s).

        You can call the `MultisetEvaluator` object directly for the same effect,
        e.g. `sum_evaluator(input)` is an alias for `sum_evaluator.evaluate(input)`.

        Most evaluators will expect a fixed number of input multisets.
        The union of the outcomes of the input(s) must be totally orderable.

        Args:
            *args: Each may be one of the following:
                * A `MultisetExpression`.
                * A mappable mapping outcomes to the number of those outcomes.
                * A sequence of outcomes.

        Returns:
            A `Die` representing the distribution of the final outcome if no
            arg contains a parameter. Otherwise returns information
            needed to construct a multiset function.
        """

        # Convert arguments to expressions.
        inputs = tuple(
            icepool.implicit_convert_to_expression(arg) for arg in args)

        # In this case we are inside a @multiset_function.
        if any(input.has_parameters() for input in inputs):
            return self, inputs, kwargs

        # Otherwise, we perform the evaluation.

        if not all(expression._is_resolvable() for expression in inputs):
            return icepool.Die([])

        final_data: 'MutableMapping[icepool.Die[U_co], int]' = defaultdict(int)
        iterators = _initialize_inputs(inputs)
        for p in itertools.product(*iterators):
            sub_inputs, sub_weights = zip(*p)
            dungeon, body_inputs = self.prepare(sub_inputs, kwargs)
            # TODO: get cached dungeon
            prod_weight = math.prod(sub_weights)
            outcomes = icepool.sorted_union(*(expression.outcomes()
                                              for expression in sub_inputs))
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

    direct_kwargs: 'Mapping[str, Hashable]' = {}
    """These will be sent to next_state_ascending, next_state_descending, and final_outcome.
    
    This allows to (sometimes) avoid wrapping these in another function just to
    feed them kwargs.
    """

    body_input_len: int
    """The number of body inputs for a @multiset_function. 0 if not a @multiset_function."""

    @abstractmethod
    def next_state_ascending(self, state: Hashable, outcome: T, /, *counts,
                             **kwargs: Hashable) -> Hashable:
        """The next_state function to use when going in ascending order.
        
        This method may be set to None in subclasses.
        """

    @abstractmethod
    def next_state_descending(self, state: Hashable, outcome: T, /, *counts,
                              **kwargs: Hashable) -> Hashable:
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

    def evaluation_order(self) -> Order:
        """Which evaluation orders are supported."""
        if self.next_state_ascending is not None and self.next_state_descending is not None:
            return Order.Any
        elif self.next_state_ascending is not None:
            return Order.Ascending
        elif self.next_state_descending is not None:
            return Order.Descending
        else:
            raise ConflictingOrderError('No evaluation order is supported.')

    def _select_order(
        self, inputs: 'Sequence[MultisetExpressionBase[T, Any]]'
    ) -> tuple[Order, Order]:
        """Selects a iteration order.

        Note that we prefer the input order to be opposite the eval order.

        Returns:
            * The input (pop) order to use.
            * The eval (next_state) order to use.
        """
        eval_order = self.evaluation_order()

        if not inputs:
            # No inputs.
            return Order(-eval_order), eval_order

        input_order, input_order_reason = merge_order_preferences(
            *(input.order_preference() for input in inputs))

        if input_order is None:
            input_order = Order.Any
            input_order_reason = OrderReason.NoPreference

        # No mandatory evaluation order, go with preferred algorithm.
        # Note that this has order *opposite* the pop order.
        if eval_order == Order.Any:
            eval_order = Order(-input_order or Order.Ascending)
            return Order(-eval_order), eval_order

        # Mandatory evaluation order.
        if input_order == Order.Any:
            return Order(-eval_order), eval_order
        else:
            return input_order, eval_order

    def evaluate_backward(self, eval_order: Order,
                          extra_outcomes: 'Alignment[T]',
                          inputs: 'tuple[MultisetExpressionBase[T, Q], ...]',
                          kwargs: Mapping[str, Hashable]) -> Mapping[Any, int]:
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
        if eval_order > 0:
            cache = self.ascending_cache
            next_state_function = cast(Callable, self.next_state_ascending)
        else:
            cache = self.descending_cache
            next_state_function = cast(Callable, self.next_state_descending)

        cache_key = (extra_outcomes, inputs, None)
        if cache_key in cache:
            return cache[cache_key]

        result: MutableMapping[Any, int] = defaultdict(int)

        if all(not input.outcomes()
               for input in inputs) and not extra_outcomes.outcomes():
            result = {None: 1}
        else:
            outcome, prev_extra_outcomes, iterators = MultisetDungeon._pop_inputs(
                Order(-eval_order), extra_outcomes, inputs)
            for p in itertools.product(*iterators):
                prev_inputs, counts, weights = zip(*p)
                prod_weight = math.prod(weights)
                prev = self.evaluate_backward(eval_order, prev_extra_outcomes,
                                              prev_inputs, kwargs)
                for prev_state, prev_weight in prev.items():
                    state = next_state_function(prev_state, outcome, *counts,
                                                **kwargs)
                    if state is not icepool.Reroll:
                        result[state] += prev_weight * prod_weight

        cache[cache_key] = result
        return result

    def evaluate_forward(self,
                         eval_order: Order,
                         extra_outcomes: 'Alignment[T]',
                         inputs: 'tuple[icepool.MultisetExpression[T], ...]',
                         kwargs: Mapping[str, Hashable],
                         initial_state: Hashable = None) -> Mapping[Any, int]:
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
        if eval_order > 0:
            cache = self.ascending_cache
            next_state_function = cast(Callable, self.next_state_ascending)
        else:
            cache = self.descending_cache
            next_state_function = cast(Callable, self.next_state_descending)

        cache_key = (extra_outcomes, inputs, initial_state)
        if cache_key in cache:
            return cache[cache_key]

        result: MutableMapping[Any, int] = defaultdict(int)

        if all(not input.outcomes()
               for input in inputs) and not extra_outcomes.outcomes():
            result = {initial_state: 1}
        else:
            outcome, next_extra_outcomes, iterators = MultisetDungeon._pop_inputs(
                eval_order, extra_outcomes, inputs)
            for p in itertools.product(*iterators):
                next_inputs, counts, weights = zip(*p)
                prod_weight = math.prod(weights)
                next_state = next_state_function(initial_state, outcome,
                                                 *counts, **kwargs)
                if next_state is not icepool.Reroll:
                    final_dist = self.evaluate_forward(eval_order,
                                                       next_extra_outcomes,
                                                       next_inputs, kwargs,
                                                       next_state)
                    for final_state, weight in final_dist.items():
                        result[final_state] += weight * prod_weight

        cache[cache_key] = result
        return result

    def evaluate(self, extra_outcomes: 'Alignment[T]',
                 inputs: 'tuple[icepool.MultisetExpression[T], ...]',
                 kwargs: Mapping[str, Hashable]) -> 'icepool.Die[U_co]':
        """Runs evaluate_forward or evaluate_backward according to the input order versus the eval order."""
        input_order, eval_order = self._select_order(inputs)
        if input_order == eval_order:
            final_states = self.evaluate_forward(eval_order, extra_outcomes,
                                                 inputs, kwargs)
        else:
            final_states = self.evaluate_backward(eval_order, extra_outcomes,
                                                  inputs, kwargs)

        final_outcomes = []
        final_weights = []
        for state, weight in final_states.items():
            outcome = self.final_outcome(state)
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
