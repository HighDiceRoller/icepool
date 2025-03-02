__docformat__ = 'google'

import icepool
from icepool.order import Order, OrderReason, merge_order_preferences

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
    def prepare(self, order: Order,
                kwargs: Mapping[str, Hashable]) -> 'MultisetDungeon':
        """Prepares an evaluation.
        
        In the future this will likely allow yielding multiple results.
        """

    @abstractmethod
    def order(self) -> Order:
        """Which outcome orderings the evaluator supports.
        Returns:
            * Order.Ascending (= 1)
                if outcomes are to be seen in ascending order.
            * Order.Descending (= -1)
                if outcomes are to be seen in descending order.
            * Order.Any (= 0)
                if outcomes can be seen in any order.
        """

    def final_outcome(self, final_state: Hashable,
                      /) -> 'U_co | icepool.Die[U_co] | icepool.RerollType':
        """Optional method to generate a final output outcome from a final state.

        By default, the final outcome is equal to the final state.
        Note that `None` is not a valid outcome for a `Die`,
        and if there are no outcomes, `final_outcome` will be immediately
        be callled with `final_state=None`.
        Subclasses that want to handle this case should explicitly define what
        happens.

        Args:
            final_state: A state after all outcomes have been processed.

        Returns:
            A final outcome that will be used as part of constructing the result `Die`.
            As usual for `Die()`, this could itself be a `Die` or `icepool.Reroll`.
        """
        # If not overriden, the final_state should have type U_co.
        return cast(U_co, final_state)

    def extra_outcomes(self, outcomes: Sequence[T]) -> Collection[T]:
        """Optional method to specify extra outcomes that should be seen as inputs to `next_state()`.

        These will be seen by `next_state` even if they do not appear in the
        input(s). The default implementation returns `()`, or no additional
        outcomes.

        If you want `next_state` to see consecutive `int` outcomes, you can set
        `extra_outcomes = icepool.MultisetEvaluator.consecutive`.
        See `consecutive()` below.

        Args:
            outcomes: The outcomes that could be produced by the inputs, in
            ascending order.
        """
        return ()

    def evaluate(self, *args:
                 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
                 **kwargs: Hashable) -> 'icepool.Die[U_co]':
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
            arg contains a free variable. Otherwise, returns a new evaluator.
        """

        # Convert arguments to expressions.
        inputs = tuple(
            icepool.implicit_convert_to_expression(arg) for arg in args)

        # In this case we are inside a @multiset_function, and we create a
        # corresponding MultisetFunctionEvaluator.
        if any(input.has_free_variables() for input in inputs):
            raise NotImplementedError()

        # Otherwise, we perform the evaluation.

        if not all(expression._is_resolvable() for expression in inputs):
            return icepool.Die([])

        input_order, eval_order = self._select_order(*inputs)

        dungeon = self.prepare(eval_order, kwargs)

        # TODO: get cached dungeon

        final_states: MutableMapping[Any, int] = defaultdict(int)
        iterators = _initialize_inputs(inputs)
        for p in itertools.product(*iterators):
            sub_inputs, sub_weights = zip(*p)
            # TODO: inputs = self.bound_inputs() + sub_inputs
            prod_weight = math.prod(sub_weights)
            outcomes = icepool.sorted_union(*(expression.outcomes()
                                              for expression in sub_inputs))
            extra_outcomes = icepool.Alignment(self.extra_outcomes(outcomes))
            sub_final_states = dungeon.evaluate(
                input_order,
                extra_outcomes,
                sub_inputs,
            )
            for sub_state, sub_weight in sub_final_states.items():
                final_states[sub_state] += sub_weight * prod_weight

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

    __call__ = evaluate

    def _select_order(
            self, *inputs:
        'MultisetExpressionBase[T, Any]') -> tuple[Order, Order]:
        """Selects a iteration order.

        Note that we prefer the input order to be opposite the eval order.

        Returns:
            * The input (pop) order to use.
            * The eval (next_state) order to use.
        """
        eval_order = self.order()

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


class MultisetDungeon(Generic[T, U_co], Hashable):
    """Holds values that are constant within a single evaluation, along with a cache."""

    eval_order: Order
    """The order in which next_state sees outcomes."""
    cache: 'MutableMapping[tuple[Alignment, tuple[MultisetExpressionBase[T, Any], ...], Hashable], Mapping[U_co, int]]'
    """Maps (extra_outcomes, inputs, initial_state) -> final_state -> int."""

    def __init__(self, next_state_function: Callable[..., Hashable],
                 eval_order: Order, kwargs: Mapping[str, Hashable]):
        """Constructor.
        
        Args:
            next_state: The `next_state()` function to use.
            final_outcome: The `final_outcome()` function to use.
            kwargs: These will be sent to `next_state()` and `final_outcome()`.
        """
        self.next_state_function = next_state_function
        self.eval_order = eval_order
        self.kwargs = kwargs
        self.cache = {}

    @cached_property
    def _hash_key(self):
        return (self.next_state_function, tuple(sorted(self.kwargs.items())))

    @cached_property
    def _hash(self) -> int:
        return hash(self._hash_key)

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other) -> bool:
        if not isinstance(other, MultisetDungeon):
            return False
        return self._hash_key == other._hash_key

    def evaluate_backward(
        self, extra_outcomes: 'Alignment[T]',
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
        cache_key = (extra_outcomes, inputs, None)
        if cache_key in self.cache:
            return self.cache[cache_key]

        result: MutableMapping[Any, int] = defaultdict(int)

        if all(not input.outcomes()
               for input in inputs) and not extra_outcomes.outcomes():
            result = {None: 1}
        else:
            outcome, prev_extra_outcomes, iterators = MultisetDungeon._pop_inputs(
                Order(-self.eval_order), extra_outcomes, inputs)
            for p in itertools.product(*iterators):
                prev_inputs, counts, weights = zip(*p)
                prod_weight = math.prod(weights)
                prev = self.evaluate_backward(prev_extra_outcomes, prev_inputs)
                for prev_state, prev_weight in prev.items():
                    state = self.next_state_function(prev_state, outcome,
                                                     *counts)
                    if state is not icepool.Reroll:
                        result[state] += prev_weight * prod_weight

        self.cache[cache_key] = result
        return result

    def evaluate_forward(self,
                         extra_outcomes: 'Alignment[T]',
                         inputs: 'tuple[icepool.MultisetExpression[T], ...]',
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
        cache_key = (extra_outcomes, inputs, initial_state)
        if cache_key in self.cache:
            return self.cache[cache_key]

        result: MutableMapping[Any, int] = defaultdict(int)

        if all(not input.outcomes()
               for input in inputs) and not extra_outcomes.outcomes():
            result = {initial_state: 1}
        else:
            outcome, next_extra_outcomes, iterators = MultisetDungeon._pop_inputs(
                self.eval_order, extra_outcomes, inputs)
            for p in itertools.product(*iterators):
                next_inputs, counts, weights = zip(*p)
                prod_weight = math.prod(weights)
                next_state = self.next_state_function(initial_state, outcome,
                                                      *counts)
                if next_state is not icepool.Reroll:
                    final_dist = self.evaluate_forward(next_extra_outcomes,
                                                       next_inputs, next_state)
                    for final_state, weight in final_dist.items():
                        result[final_state] += weight * prod_weight

        self.cache[cache_key] = result
        return result

    def evaluate(
        self, input_order: Order, extra_outcomes: 'Alignment[T]',
        inputs: 'tuple[icepool.MultisetExpression[T], ...]'
    ) -> Mapping[Any, int]:
        """Runs evaluate_forward or evaluate_backward according to the input order versus the eval order."""
        if input_order == self.eval_order:
            return self.evaluate_forward(extra_outcomes, inputs)
        else:
            return self.evaluate_backward(extra_outcomes, inputs)

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
