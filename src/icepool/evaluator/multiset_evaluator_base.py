__docformat__ = 'google'

import icepool

from icepool.function import sorted_union
from icepool.order import ConflictingOrderError, Order, OrderReason, UnsupportedOrder, merge_order_preferences

from abc import ABC, abstractmethod
from collections import defaultdict
from functools import cached_property
import itertools
import math

from icepool.typing import Q, T, U_co
from typing import (Any, Callable, Collection, Generic, Hashable, Iterator,
                    Literal, Mapping, MutableMapping, MutableSequence,
                    NamedTuple, Sequence, Type, TypeAlias, cast, TYPE_CHECKING,
                    overload)

if TYPE_CHECKING:
    from icepool.expression.multiset_expression_base import MultisetExpressionBase, MultisetSourceBase, Dungeonlet, Questlet
    from icepool.expression.multiset_param import MultisetParamBase
    from icepool.evaluator.multiset_function import MultisetFunctionRawResult
    from icepool import MultisetExpression


class MultisetEvaluatorBase(ABC, Generic[T, U_co]):

    _cache: 'MutableMapping[Any, Dungeon] | None' = None

    @abstractmethod
    def _prepare(
        self,
        input_exps: 'tuple[MultisetExpressionBase[T, Any], ...]',
        kwargs: Mapping[str, Hashable],
    ) -> Iterator[tuple['Dungeon[T]', 'Quest[T, U_co]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        """Prepares an evaluation.

        Args:
            input_exps: The input expressions to the evaluation.
            kwargs: Keyword arguments, which are not expresions.

        Yields:
            dungeon, quest, sources, weight
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
        if any(exp._has_param for exp in input_exps):
            from icepool.evaluator.multiset_function import MultisetFunctionRawResult
            return MultisetFunctionRawResult(self, input_exps, kwargs)

        # Otherwise, we perform the evaluation.

        if self._cache is None:
            self._cache = {}

        final_data: 'MutableMapping[icepool.Die[U_co], int]' = defaultdict(int)

        for dungeon, quest, sources, weight in self._prepare(
                input_exps, kwargs):

            # Replace dungeon with cached version if available.
            if dungeon.__hash__ is not None:
                if dungeon in self._cache:
                    dungeon = self._cache[dungeon]
                else:
                    self._cache[dungeon] = dungeon

            result: 'icepool.Die[U_co]' = dungeon.evaluate(
                quest, sources, kwargs)
            final_data[result] += weight

        return icepool.Die(final_data)

    __call__ = evaluate


class Dungeon(Generic[T]):
    """Holds an evaluation's next_state function and caches."""

    dungeonlet_flats: 'tuple[tuple[Dungeonlet[T, Any], ...], ...]'

    ascending_cache: 'MutableMapping[Room[T], Mapping[tuple[tuple[Hashable, ...], ...], Mapping[Hashable, int]]]'
    """Maps room -> final_state -> int for next_state seeing outcomes in ascending order.
    
    Initialized in evaluate().
    """
    descending_cache: 'MutableMapping[Room[T], Mapping[tuple[tuple[Hashable, ...], ...], Mapping[Hashable, int]]]'
    """Maps room -> final_state -> int for next_state seeing outcomes in ascending order.
    
    Initialized in evaluate().
    """

    @abstractmethod
    def next_state_main(self, state: Hashable, order: Order, outcome: T,
                        source_counts: Iterator,
                        param_counts: Sequence) -> Hashable:
        """Main state transition function.
        
        Args:
            state: The state of the dungeon.
            order: The order in which outcomes are seen.
            outcome: The current outcome.
            source_counts: The counts produced by sources. This is an iterator
                that will be consumed in order.
            param_counts: The counts produced by parameters at this level.

        Returns:
            The next state, or icepool.Reroll to drop this branch of evaluation.
        """

    def evaluate(self, quest: 'Quest[T, U_co]',
                 sources: 'tuple[MultisetSourceBase[T, Any], ...]',
                 kwargs: Mapping[str, Hashable]) -> 'icepool.Die[U_co]':
        """Runs evaluate_forward or evaluate_backward according to the input order versus the eval order."""

        if not hasattr(self, 'ascending_cache'):
            self.ascending_cache = {}
            self.descending_cache = {}

        if not all(source.is_resolvable() for source in sources):
            return icepool.Die([])

        pop_order, pop_order_reason = merge_order_preferences(
            (Order.Descending, OrderReason.Default),
            *(source.order_preference() for source in sources))

        source_outcomes = sorted_union(*(source.outcomes()
                                         for source in sources))
        extra_outcomes = quest.extra_outcomes(source_outcomes)
        all_outcomes = sorted_union(source_outcomes, extra_outcomes)

        try:
            room, sizes = self.initial_room(quest, sources, -pop_order,
                                            all_outcomes, kwargs)
            final_states = self.evaluate_backward(pop_order, room)
            return quest.finalize_evaluation(final_states, -pop_order,
                                             all_outcomes, sizes, kwargs)
        except UnsupportedOrder:
            try:
                if pop_order_reason is OrderReason.Default:
                    # Flip the pop order.
                    room, sizes = self.initial_room(quest, sources, pop_order,
                                                    all_outcomes, kwargs)
                    final_states = self.evaluate_backward(-pop_order, room)
                    return quest.finalize_evaluation(final_states, pop_order,
                                                     all_outcomes, sizes,
                                                     kwargs)
                else:
                    # Use the alternate algorithm.
                    room, sizes = self.initial_room(quest, sources, pop_order,
                                                    all_outcomes, kwargs)
                    final_states = self.evaluate_forward(pop_order, room)
                    return quest.finalize_evaluation(final_states, pop_order,
                                                     all_outcomes, sizes,
                                                     kwargs)
            except UnsupportedOrder:
                raise ConflictingOrderError(
                    'Neither ascending nor descending order is compatable with the evaluation. '
                    +
                    f'Preferred input order was {pop_order.name} with reason {pop_order_reason.name}.'
                )

    def initial_room(
            self, quest: 'Quest[T, U_co]',
            sources: 'tuple[MultisetSourceBase, ...]', order: Order,
            outcomes: tuple[T, ...],
            kwargs: Mapping[str, Hashable]) -> 'tuple[Room[T], tuple]':
        source_counts = (source.size() for source in sources)
        initial_statelets, sizes = quest.initial_statelets(
            order, outcomes, source_counts, ())
        initial_state_main = quest.initial_state_main(order, outcomes,
                                                      source_counts, sizes,
                                                      kwargs)
        return Room(outcomes, sources, initial_statelets,
                    initial_state_main), sizes

    def evaluate_backward(
        self, pop_order: Order, room: 'Room'
    ) -> Mapping[tuple[tuple[Hashable, ...], ...], Mapping[Hashable, int]]:
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

        if room in cache:
            return cache[room]

        result: MutableMapping[tuple[tuple[Hashable, ...], ...],
                               MutableMapping[Hashable, int]] = defaultdict(
                                   lambda: defaultdict(int))

        if room.is_done():
            result = {
                room.initial_statelet_flats: {
                    room.initial_state_main: 1
                }
            }
        else:
            eval_order = -pop_order
            for outcome, source_counts, prev_outcomes, prev_sources, weight in room.pop(
                    pop_order):
                prev_room = Room(prev_outcomes, prev_sources,
                                 room.initial_statelet_flats,
                                 room.initial_state_main)
                prev = self.evaluate_backward(pop_order, prev_room)

                for prev_statelet_flats, prev_main in prev.items():
                    source_counts_iter = iter(source_counts)
                    statelet_flats, counts = self.next_statelet_flats_and_counts(
                        prev_statelet_flats, eval_order, outcome,
                        source_counts_iter, ())
                    subresult = result[statelet_flats]
                    remaining_source_counts = tuple(source_counts_iter)
                    for prev_state_main, prev_weight in prev_main.items():
                        state_main = self.next_state_main(
                            prev_state_main, eval_order, outcome,
                            iter(remaining_source_counts), counts)
                        if state_main is not icepool.Reroll:
                            subresult[state_main] += prev_weight * weight
        cache[room] = result
        return result

    def evaluate_forward(
        self, pop_order: Order, room: 'Room'
    ) -> Mapping[tuple[tuple[Hashable, ...], ...], Mapping[Hashable, int]]:
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

        if room in cache:
            return cache[room]

        result: MutableMapping[tuple[tuple[Hashable, ...], ...],
                               MutableMapping[Hashable, int]] = defaultdict(
                                   lambda: defaultdict(int))

        if room.is_done():
            result = {
                room.initial_statelet_flats: {
                    room.initial_state_main: 1
                }
            }
        else:
            for outcome, source_counts, next_outcomes, next_sources, weight in room.pop(
                    pop_order):
                source_counts_iter = iter(source_counts)
                next_statelet_flats, counts = self.next_statelet_flats_and_counts(
                    room.initial_statelet_flats, pop_order, outcome,
                    source_counts_iter, ())
                next_state_main = self.next_state_main(room.initial_state_main,
                                                       pop_order, outcome,
                                                       source_counts_iter,
                                                       counts)
                if next_state_main is not icepool.Reroll:
                    next_room = Room(next_outcomes, next_sources,
                                     next_statelet_flats, next_state_main)
                    final = self.evaluate_forward(pop_order, next_room)
                    for final_statelet_flats, final_main in final.items():
                        subresult = result[final_statelet_flats]
                        for final_state_main, final_weight in final_main.items(
                        ):
                            subresult[
                                final_state_main] += weight * final_weight

        cache[room] = result
        return result

    def next_statelet_flats_and_counts(
        self, statelet_flats: 'tuple[tuple[Hashable, ...], ...]', order: Order,
        outcome: T, source_counts: Iterator, param_counts: Sequence
    ) -> 'tuple[tuple[tuple[Hashable, ...], ...], tuple]':
        """Helper function to advance dungeonlet_flats.
        
        Returns:
            next_statelet_flats, output_counts
        """
        next_flats = []
        output_counts: MutableSequence = []
        for dungeonlets, statelets in zip(self.dungeonlet_flats,
                                          statelet_flats):
            next_statelets = []
            countlets: MutableSequence = []
            for dungeonlet, statelet in zip(dungeonlets, statelets):
                child_counts = [countlets[i] for i in dungeonlet.child_indexes]
                next_statelet, countlet = dungeonlet.next_state(
                    statelet, order, outcome, child_counts, source_counts,
                    param_counts)
                next_statelets.append(next_statelet)
                countlets.append(countlet)
            next_flats.append(tuple(next_statelets))
            output_counts.append(countlets[-1])
        return tuple(next_flats), tuple(output_counts)


class Room(Generic[T], NamedTuple):
    outcomes: tuple[T, ...]
    sources: 'tuple[MultisetSourceBase[T, Any], ...]'
    initial_statelet_flats: tuple[tuple[Hashable, ...], ...]
    initial_state_main: Hashable

    def is_done(self) -> bool:
        return not self.outcomes

    def pop(
        self, order: Order
    ) -> Iterator[tuple[T, tuple[Any, ...], tuple[T, ...],
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        """Pops the next outcome from the sources.

        Args:
            order: The order in which to pop. Descending order pops from the top
            and ascending from the bottom.
        
        Yields:
            * The popped outcome.
            * The source_counts of the popped outcome.
            * The remaining outcomes.
            * The remaining sources.
            * weight for this result.
        """
        if order < 0:
            outcome = self.outcomes[-1]
            outcomes = self.outcomes[:-1]
        else:
            outcome = self.outcomes[0]
            outcomes = self.outcomes[1:]

        for t in itertools.product(*(source.pop(order, outcome)
                                     for source in self.sources)):
            sources, source_counts, weights = zip(*t)
            weight = math.prod(weights)
            yield outcome, source_counts, outcomes, sources, weight


class Quest(Generic[T, U_co]):
    questlet_flats: 'tuple[tuple[Questlet[T, Any], ...], ...]'

    @abstractmethod
    def extra_outcomes(self, outcomes: Sequence[T]) -> Collection[T]:
        """Extra outcomes that should be seen.
        
        Args:
            outcomes: The union of the outcomes of the input expressions.
        """

    @abstractmethod
    def initial_state_main(self, order: Order, outcomes: tuple[T, ...],
                           source_counts: Iterator, param_counts: Sequence,
                           kwargs: Mapping[str, Hashable]) -> Hashable:
        """The initial evaluation state.

        Args:
            order: The order in which `next_state` will see outcomes.
            outcomes: All outcomes that will be seen by `next_state` in sorted order.
            kwargs: Any keyword arguments that were passed to `evaluate()`.

        Raises:
            UnsupportedOrder if the given order is not supported.
        """

    @abstractmethod
    def final_outcome(
        self, final_state: Hashable, order: Order, outcomes: tuple[T, ...],
        sizes: tuple, kwargs: Mapping[str, Hashable]
    ) -> 'U_co | icepool.Die[U_co] | icepool.RerollType':
        """Generates a final outcome from a final state."""

    def initial_statelets(self, order: Order, outcomes: tuple[T, ...],
                          source_counts: Iterator, param_counts: Sequence):
        statelet_flats = []
        output_counts: MutableSequence = []
        for questlets in self.questlet_flats:
            statelets = []
            countlets: MutableSequence = []
            for questlet in questlets:
                child_counts = [countlets[i] for i in questlet.child_indexes]
                next_statelet, countlet = questlet.initial_state(
                    order, outcomes, child_counts, source_counts, param_counts)
                statelets.append(next_statelet)
                countlets.append(countlet)
            statelet_flats.append(tuple(statelets))
            output_counts.append(countlets[-1])
        return tuple(statelet_flats), tuple(output_counts)

    def finalize_evaluation(
            self, final_states: Mapping[tuple[tuple[Hashable, ...], ...],
                                        Mapping[Hashable, int]], order: Order,
            outcomes: tuple[T, ...], sizes: tuple,
            kwargs: Mapping[str, Hashable]) -> 'icepool.Die[U_co]':
        final_outcomes = []
        final_weights = []
        for _, main_states in final_states.items():
            for state, weight in main_states.items():
                outcome = self.final_outcome(state, order, outcomes, sizes,
                                             kwargs)
                if outcome is None:
                    raise TypeError(
                        "None is not a valid final outcome.\n"
                        "This may have been a result of not supplying any input with an outcome."
                    )
                if outcome is not icepool.Reroll:
                    final_outcomes.append(outcome)
                    final_weights.append(weight)

        return icepool.Die(final_outcomes, final_weights)
