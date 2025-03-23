__docformat__ = 'google'

import icepool

from icepool.function import sorted_union
from icepool.order import ConflictingOrderError, Order, OrderReason, UnsupportedOrderError, merge_order_preferences

from abc import ABC, abstractmethod
from collections import defaultdict
from functools import cached_property
import itertools
import math

from icepool.typing import Q, T, U_co
from typing import (Any, Callable, Collection, Generic, Hashable, Iterator,
                    Literal, Mapping, MutableMapping, NamedTuple, Sequence,
                    Type, TypeAlias, cast, TYPE_CHECKING, overload)

if TYPE_CHECKING:
    from icepool.expression.multiset_expression_base import MultisetExpressionBase, MultisetExpressionPreparation, MultisetSourceBase
    from icepool.expression.multiset_param import MultisetParamBase
    from icepool.evaluator.multiset_function import MultisetFunctionRawResult
    from icepool import MultisetExpression


class MultisetEvaluatorPreparation(Generic[T, U_co], NamedTuple):
    dungeon: 'MultisetDungeon[T]'
    quest: 'MultisetQuest[T, U_co]'
    body_expressions: Sequence[MultisetExpressionBase[T, Any]]
    weight: int


class MultisetEvaluatorBase(ABC, Generic[T, U_co]):

    _cache: 'MutableMapping[Any, MultisetDungeon] | None' = None

    @abstractmethod
    def _prepare(
        self,
        param_types: 'Sequence[Type[MultisetParamBase]]',
        kwargs: Mapping[str, Hashable],
    ) -> 'Iterator[MultisetEvaluatorPreparation[T, U_co]]':
        """Prepares an evaluation.

        Args:
            param_types: The param types of the inputs. Used to determine the
                body expressions of `@multiset_function`.
            kwargs: `@multiset_function` determines how to forward these to
                the inner quests.

        Yields:
            A `MultisetEvaluatorPreparation`.
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
        input_exps = tuple(
            icepool.implicit_convert_to_expression(arg) for arg in args)

        # In this case we are inside a @multiset_function.
        if any(exp._has_param() for exp in input_exps):
            from icepool.evaluator.multiset_function import MultisetFunctionRawResult
            return MultisetFunctionRawResult(self, input_exps, kwargs)

        # Otherwise, we perform the evaluation.

        if self._cache is None:
            self._cache = {}

        final_data: 'MutableMapping[icepool.Die[U_co], int]' = defaultdict(int)

        param_types = [exp._param_type for exp in input_exps]
        for dungeon, quest, body_exps, eval_weight in self._prepare(
                param_types, kwargs):
            for preps in itertools.product(
                    *(exp._prepare() for exp in input_exps),
                    *(exp._prepare() for exp in body_exps)):
                (all_dungeonlets, all_broods, all_questlets, all_sources,
                 all_weights) = zip(*preps)

                # Replace dungeon with cached version if available.
                if dungeon.__hash__ is not None:
                    cache_key = (all_dungeonlets, all_broods, dungeon)
                    if cache_key in self._cache:
                        dungeon = self._cache[cache_key]
                    else:
                        self._cache[cache_key] = dungeon

                result = dungeon.evaluate(preps, quest, kwargs)
                net_weight = eval_weight * math.prod(all_weights)
                final_data[result] += net_weight

        return icepool.Die(final_data)

    __call__ = evaluate


class MultisetDungeon(Generic[T]):
    """Holds an evaluation's next_state function and caches."""

    ascending_cache: MutableMapping[Any, Mapping[Hashable, int]]
    """Maps (all_outcomes, inputs, initial_state) -> final_state -> int for next_state seeing outcomes in ascending order.
    
    Initialized in evaluate().
    """
    descending_cache: MutableMapping[Any, Mapping[Hashable, int]]
    """Maps (all_outcomes, inputs, initial_state) -> final_state -> int for next_state seeing outcomes in ascending order.
    
    Initialized in evaluate().
    """

    @abstractmethod
    def next_state(self, state: Hashable, order: Order, outcome: T, /,
                   *counts):
        """State transition function.

        This should produce a state given the previous state, an outcome,
        and the count of that outcome produced by each multiset input.

        Args:
            state: A hashable object indicating the state before rolling the
                current outcome. If this is the first outcome being considered,
                `state` will be `None`.
            order: The order in which outcomes are seen.
            outcome: The current outcome.
            *counts: One value (usually an `int`) for each input indicating how
                many of the current outcome were produced.

        Returns:
            A hashable object indicating the next state.
            The special value `icepool.Reroll` can be used to immediately remove
            the state from consideration, effectively performing a full reroll.

        Raises:
            UnsupportedOrderError if the given order is not supported.
        """

    __hash__: Callable[[], int] | None = None  # type: ignore
    """Subclasses may optionally be hashable; if so, intermediate calculations will be persistently cached."""

    def evaluate(self, preps: 'tuple[MultisetExpressionPreparation[T], ...]',
                 quest: 'MultisetQuest[T, U_co]',
                 kwargs: Mapping[str, Hashable]) -> 'icepool.Die[U_co]':
        """Runs evaluate_forward or evaluate_backward according to the input order versus the eval order."""

        if not hasattr(self, 'ascending_cache'):
            self.ascending_cache = {}
            self.descending_cache = {}

        pop_order, pop_order_reason = merge_order_preferences(
            (Order.Descending, OrderReason.Default),
            *itertools.chain.from_iterable((source.order_preference()
                                            for source in prep.sources)
                                           for prep in preps))

        all_outcomes = self.all_outcomes(quest, preps)

        try:
            all_sources, all_exp_state, eval_state = self.initial_state(
                quest, preps, -pop_order, all_outcomes, kwargs)
            final_states = self.evaluate_backward(pop_order, all_outcomes,
                                                  all_sources, all_exp_state,
                                                  eval_state)
            return quest.finalize_evaluation(final_states, kwargs)
        except UnsupportedOrderError:
            try:
                all_sources, all_exp_state, eval_state = self.initial_state(
                    quest, preps, pop_order, all_outcomes, kwargs)
                final_states = self.evaluate_forward(pop_order, all_outcomes,
                                                     all_sources,
                                                     all_exp_state, eval_state)
                return quest.finalize_evaluation(final_states, kwargs)
            except UnsupportedOrderError:
                raise ConflictingOrderError(
                    'Neither ascending nor descending order is compatable with the evaluation. '
                    +
                    f'Preferred input order was {pop_order.name} with reason {pop_order_reason.name}.'
                )

    def all_outcomes(
        self, quest: 'MultisetQuest[T, U_co]',
        preps: 'tuple[MultisetExpressionPreparation[T], ...]'
    ) -> tuple[T, ...]:
        source_outcomes = sorted_union(*itertools.chain.from_iterable(
            (source.outcomes() for source in prep.sources) for prep in preps))
        extra_outcomes = quest.extra_outcomes(source_outcomes)
        return sorted_union(source_outcomes, extra_outcomes)

    def initial_state(
        self, quest: 'MultisetQuest[T, U_co]',
        preps: 'tuple[MultisetExpressionPreparation[T], ...]', order: Order,
        outcomes: tuple[T, ...], kwargs: Mapping[str, Hashable]
    ) -> tuple['tuple[tuple[MultisetSourceBase[T, Any], ...], ...]',
               'tuple[tuple[Hashable, ...], ...]', Hashable]:
        all_sources = tuple(prep.sources for prep in preps)
        all_exp_state = tuple(
            tuple(
                questlet.initial_state(order, outcomes)
                for questlet in prep.questlets) for prep in preps)
        eval_state = quest.initial_state(order, outcomes, **kwargs)
        return all_sources, all_exp_state, eval_state

    def evaluate_backward(
            self, pop_order: Order, all_outcomes: tuple[T, ...],
            all_sources: 'tuple[tuple[MultisetSourceBase[T, Any], ...], ...]',
            all_exp_state: 'tuple[tuple[Hashable, ...], ...]',
            eval_state: Hashable) -> Mapping[Any, int]:
        """Internal algorithm for iterating so that next_state sees outcomes in backwards order.

        All intermediate return values are cached in the instance.

        Arguments:
            order: The order in which to send outcomes to `next_state()`.
            all_outcomes: All outcomes that will be seen. Elements will be
                popped of this.
            inputs: One or more `MultisetExpression`s to evaluate. Elements
                will be popped off this during recursion.

        Returns:
            A dict `{ state : weight }` describing the probability distribution
                over states.
        """
        # Since this is the backward evaluation, these are opposite of the
        # pop order.
        if pop_order > 0:
            cache = self.descending_cache
        else:
            cache = self.ascending_cache

        cache_key = (all_outcomes, all_sources, all_exp_state, eval_state)
        if cache_key in cache:
            return cache[cache_key]

        result: MutableMapping[Any, int] = defaultdict(int)

        if not all_outcomes:
            result = {eval_state: 1}
        else:
            outcome, prev_all_outcomes, iterators = pop_inputs(
                pop_order, all_outcomes, inputs)
            for p in itertools.product(*iterators):
                prev_inputs, counts, weights = zip(*p)
                prod_weight = math.prod(weights)
                prev = self.evaluate_backward(initial_state, pop_order,
                                              prev_all_outcomes, prev_inputs)
                for prev_state, prev_weight in prev.items():
                    state = self.next_state(prev_state, -pop_order, outcome,
                                            *counts)
                    if state is not icepool.Reroll:
                        result[state] += prev_weight * prod_weight

        cache[cache_key] = result
        return result

    def evaluate_forward(
        self, initial_state: Hashable, pop_order: Order,
        all_outcomes: tuple[T, ...],
        inputs: 'tuple[icepool.MultisetExpression[T], ...]'
    ) -> Mapping[Any, int]:
        """Internal algorithm for iterating in the less-preferred order.

        All intermediate return values are cached in the instance.

        Arguments:
            order: The order in which to send outcomes to `next_state()`.
            all_outcomes: All outcomes that will be seen. Elements will be
                popped off this.
            inputs: One or more `MultisetExpression`s to evaluate. Elements
                will be popped off this during recursion.

        Returns:
            A dict `{ state : weight }` describing the probability distribution
                over states.
        """
        if pop_order > 0:
            cache = self.ascending_cache
        else:
            cache = self.descending_cache

        cache_key = (all_outcomes, inputs, initial_state)
        if cache_key in cache:
            return cache[cache_key]

        result: MutableMapping[Any, int] = defaultdict(int)

        if all(not input.outcomes() for input in inputs) and not all_outcomes:
            result = {initial_state: 1}
        else:
            outcome, next_all_outcomes, iterators = pop_inputs(
                pop_order, all_outcomes, inputs)
            for p in itertools.product(*iterators):
                next_inputs, counts, weights = zip(*p)
                prod_weight = math.prod(weights)
                next_state = self.next_state(initial_state, pop_order, outcome,
                                             *counts)
                if next_state is not icepool.Reroll:
                    final_dist = self.evaluate_forward(next_state, pop_order,
                                                       next_all_outcomes,
                                                       next_inputs)
                    for final_state, weight in final_dist.items():
                        result[final_state] += weight * prod_weight

        cache[cache_key] = result
        return result


class MultisetQuest(Generic[T, U_co]):

    @abstractmethod
    def extra_outcomes(self, outcomes: Sequence[T]) -> Collection[T]:
        """Extra outcomes that should be seen.
        
        Args:
            outcomes: The union of the outcomes of the input expressions.
        """

    @abstractmethod
    def initial_state(self, order: Order, outcomes: Sequence[T], /, **kwargs):
        """The initial evaluation state.
        TODO: Should this get cardinalities?

        Args:
            order: The order in which `next_state` will see outcomes.
            outcomes: All outcomes that will be seen by `next_state` in sorted order.
            kwargs: Any keyword arguments that were passed to `evaluate()`.

        Raises:
            UnsupportedOrderError if the given order is not supported.
        """

    @abstractmethod
    def final_outcome(
            self, final_state: Hashable, order: Order, outcomes: tuple[T, ...],
            /, **kwargs: Hashable
    ) -> 'U_co | icepool.Die[U_co] | icepool.RerollType':
        """Generates a final outcome from a final state."""

    def finalize_evaluation(
            self, final_states: Mapping[Any, int], order: Order,
            outcomes: tuple[T, ...],
            kwargs: Mapping[str, Hashable]) -> 'icepool.Die[U_co]':
        final_outcomes = []
        final_weights = []
        for state, weight in final_states.items():
            outcome = self.final_outcome(state, order, outcomes, **kwargs)
            if outcome is None:
                raise TypeError(
                    "None is not a valid final outcome.\n"
                    "This may have been a result of not supplying any input with an outcome."
                )
            if outcome is not icepool.Reroll:
                final_outcomes.append(outcome)
                final_weights.append(weight)

        return icepool.Die(final_outcomes, final_weights)


def pop_inputs(
    order: Order, all_outcomes: tuple[T, ...],
    inputs: 'tuple[MultisetExpressionBase[T, Q], ...]'
) -> 'tuple[T, tuple[T, ...], tuple[Iterator[tuple[MultisetExpressionBase, Any, int]], ...]]':
    """Pops a single outcome from the inputs.

    Args:
        order: The order in which to pop. Descending order pops from the top
        and ascending from the bottom.
        all_outcomes: All outcomes that will be seen.
        inputs: The inputs to pop from.

    Returns:
        * The popped outcome.
        * The remaining extra outcomes.
        * A tuple of iterators over the resulting inputs, counts, and weights.
    """
    if order < 0:
        outcome = all_outcomes[-1]
        next_all_outcomes = all_outcomes[:-1]

        return outcome, next_all_outcomes, tuple(
            input._generate_max(outcome) for input in inputs)
    else:
        outcome = all_outcomes[0]
        next_all_outcomes = all_outcomes[1:]

        return outcome, next_all_outcomes, tuple(
            input._generate_min(outcome) for input in inputs)
