__docformat__ = 'google'

import itertools
import math
import icepool
from icepool.evaluator.multiset_evaluator_base import MultisetEvaluatorBase, MultisetDungeon, MultisetQuest
from icepool.expression.multiset_expression_base import MultisetDungeonlet, MultisetExpressionBase, MultisetQuestlet, MultisetSourceBase
from icepool.expression.multiset_param import MultisetParam, MultisetParamBase, MultisetTupleParam

import inspect
from functools import cached_property, update_wrapper

from icepool.function import sorted_union
from icepool.order import Order
from icepool.typing import Q, T, U_co
from typing import Any, Callable, Collection, Generic, Hashable, Iterator, Mapping, NamedTuple, Sequence, Type, TypeAlias, overload

MV: TypeAlias = MultisetParam | MultisetTupleParam


@overload
def multiset_function(wrapped: Callable[[
    MV
], 'MultisetFunctionRawResult[T, U_co] | tuple[MultisetFunctionRawResult[T, U_co], ...]'],
                      /) -> 'MultisetEvaluatorBase[T, U_co]':
    ...


@overload
def multiset_function(wrapped: Callable[[
    MV, MV
], 'MultisetFunctionRawResult[T, U_co] | tuple[MultisetFunctionRawResult[T, U_co], ...]'],
                      /) -> 'MultisetEvaluatorBase[T, U_co]':
    ...


@overload
def multiset_function(wrapped: Callable[[
    MV, MV, MV
], 'MultisetFunctionRawResult[T, U_co] | tuple[MultisetFunctionRawResult[T, U_co], ...]'],
                      /) -> 'MultisetEvaluatorBase[T, U_co]':
    ...


@overload
def multiset_function(wrapped: Callable[[
    MV, MV, MV, MV
], 'MultisetFunctionRawResult[T, U_co] | tuple[MultisetFunctionRawResult[T, U_co], ...]'],
                      /) -> 'MultisetEvaluatorBase[T, U_co]':
    ...


def multiset_function(wrapped: Callable[
    ...,
    'MultisetFunctionRawResult[T, U_co] | tuple[MultisetFunctionRawResult[T, U_co], ...]'],
                      /) -> 'MultisetEvaluatorBase[T, U_co]':
    """EXPERIMENTAL: A decorator that turns a function into a multiset evaluator.

    The provided function should take in arguments representing multisets,
    do a limited set of operations on them (see `MultisetExpression`), and
    finish off with an evaluation. You can return a tuple to perform a joint
    evaluation.

    For example, to create an evaluator which computes the elements each of two
    multisets has that the other doesn't:
    ```python
    @multiset_function
    def two_way_difference(a, b):
        return (a - b).expand(), (b - a).expand()
    ```

    You can send non-multiset variables as keyword arguments
    (recommended to be defined as keyword-only).
    ```python
    @multiset_function
    def count_outcomes(a, *, target):
        return a.keep_outcomes(target).count()

    count_outcomes(a, target=[5, 6])
    ```

    While in theory `@multiset_function` implements late binding similar to
    ordinary Python functions, I recommend using only pure functions.

    Be careful when using control structures: you cannot branch on the value of
    a multiset expression or evaluation, so e.g.

    ```python
    @multiset_function
    def bad(a, b)
        if a == b:
            ...
    ```

    is not allowed.

    `multiset_function` has considerable overhead, being effectively a
    mini-language within Python. For better performance, you can try
    implementing your own subclass of `MultisetEvaluator` directly.

    Args:
        function: This should take in multiset expressions as positional
            arguments, and non-multiset variables as keyword arguments.
    """
    return MultisetFunctionEvaluator(wrapped)


class MultisetFunctionRawResult(Generic[T, U_co], NamedTuple):
    """A result of running an evaluator with `@multiset_function` parameters."""
    evaluator: MultisetEvaluatorBase[T, U_co]
    body_exps: tuple[MultisetExpressionBase[T, Any], ...]
    inner_kwargs: Mapping[str, Hashable]

    def prepare_inner(
        self
    ) -> Iterator[tuple['MultisetDungeon[T]', 'MultisetQuest[T, U_co]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        yield from self.evaluator._prepare(self.body_exps, self.inner_kwargs)


class MultisetFunctionEvaluator(MultisetEvaluatorBase[T, U_co]):

    def __init__(self, wrapped: Callable[
        ...,
        'MultisetFunctionRawResult[T, U_co] | tuple[MultisetFunctionRawResult[T, U_co], ...]']
                 ):
        self._wrapped = wrapped
        wrapped_parameters = inspect.signature(wrapped,
                                               follow_wrapped=False).parameters
        self._positional_names = []
        for index, parameter in enumerate(wrapped_parameters.values()):

            if parameter.kind in [
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ]:
                self._positional_names.append(parameter.name)

        update_wrapper(self, wrapped)

    def _prepare(
        self,
        input_exps: tuple[MultisetExpressionBase[T, Any], ...],
        kwargs: Mapping[str, Hashable],
    ) -> Iterator[tuple['MultisetDungeon[T]', 'MultisetQuest[T, U_co]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        multiset_variables = [
            exp._param_type(i, self._positional_names[i])
            for i, exp in enumerate(input_exps)
        ]
        raw_result = self._wrapped(*multiset_variables, **kwargs)
        if isinstance(raw_result, MultisetFunctionRawResult):
            yield from prepare_multiset_function(input_exps, raw_result)
        else:
            yield from prepare_multiset_joint_function(input_exps, raw_result)


def prepare_multiset_function(
    outer_exps: tuple[MultisetExpressionBase[T, Any], ...],
    raw_result: 'MultisetFunctionRawResult[T, U_co]',
) -> Iterator[tuple['MultisetDungeon[T]', 'MultisetQuest[T, U_co]',
                    'tuple[MultisetSourceBase[T, Any], ...]', int]]:
    for outer in itertools.product(*(exp._prepare() for exp in outer_exps)):
        outer_dungeonlet_flats, outer_questlet_flats, outer_sources, outer_weights = zip(
            *outer)
        outer_sources = tuple(itertools.chain.from_iterable(outer_sources))
        outer_weight = math.prod(outer_weights)

        for inner_dungeon, inner_quest, inner_sources, inner_weight in raw_result.prepare_inner(
        ):
            dungeon = MultisetFunctionDungeon(outer_dungeonlet_flats,
                                              inner_dungeon)
            quest = MultisetFunctionQuest(outer_questlet_flats, inner_quest,
                                          raw_result.inner_kwargs)
            yield dungeon, quest, outer_sources + inner_sources, outer_weight * inner_weight


class MultisetFunctionDungeon(MultisetDungeon[T]):

    def __init__(
        self,
        dungeonlet_flats: 'tuple[tuple[MultisetDungeonlet[T, Any], ...], ...]',
        inner_dungeon: MultisetDungeon[T],
    ):
        self.dungeonlet_flats = dungeonlet_flats
        self.inner_dungeon = inner_dungeon

    def next_state(self, state, order: Order, outcome: T,
                   source_counts: Iterator,
                   param_counts: Sequence) -> Hashable:
        statelet_flats, inner_state = state

        next_statelet_flats, param_counts = self.next_statelet_flats_and_counts(
            self.dungeonlet_flats, statelet_flats, order, outcome,
            source_counts, param_counts)

        next_inner_state = self.inner_dungeon.next_state(
            inner_state, order, outcome, source_counts, param_counts)
        if next_inner_state is icepool.Reroll:
            return icepool.Reroll
        return next_statelet_flats, next_inner_state

    # TODO: __hash__?


class MultisetFunctionQuest(MultisetQuest[T, U_co]):

    def __init__(
        self,
        questlet_flats: 'tuple[tuple[MultisetQuestlet[T], ...], ...]',
        inner_quest: MultisetQuest[T, U_co],
        inner_kwargs: Mapping[str, Hashable],
    ):
        self.questlet_flats = questlet_flats
        self.inner_quest = inner_quest
        self.inner_kwargs = inner_kwargs

    def extra_outcomes(self, outcomes):
        return self.inner_quest.extra_outcomes(outcomes)

    def initial_state(self, order, outcomes, kwargs):
        # The kwargs have already been bound to inner_kwargs.
        statelet_flats = tuple(
            tuple(
                questlet.initial_state(order, outcomes) for questlet in flat)
            for flat in self.questlet_flats)
        inner_state = self.inner_quest.initial_state(order, outcomes,
                                                     self.inner_kwargs)
        return statelet_flats, inner_state

    def final_outcome(self, final_state, order, outcomes, kwargs):
        # The kwargs have already been bound to inner_kwargs.
        statelet_flats, inner_state = final_state
        return self.inner_quest.final_outcome(inner_state, order, outcomes,
                                              self.inner_kwargs)


def prepare_multiset_joint_function(
    outer_exps: tuple[MultisetExpressionBase[T, Any], ...],
    raw_result: tuple['MultisetFunctionRawResult[T, U_co]', ...],
) -> Iterator[tuple['MultisetDungeon[T]', 'MultisetQuest[T, U_co]',
                    'tuple[MultisetSourceBase[T, Any], ...]', int]]:
    for outer in itertools.product(*(exp._prepare() for exp in outer_exps)):
        outer_dungeonlet_flats, outer_questlet_flats, outer_sources, outer_weights = zip(
            *outer)
        outer_sources = tuple(itertools.chain.from_iterable(outer_sources))
        outer_weight = math.prod(outer_weights)

    inner_kwargses = tuple(raw.inner_kwargs for raw in raw_result)
    for inner in itertools.product(*(raw.prepare_inner()
                                     for raw in raw_result)):
        (inner_dungeons, inner_quests, all_inner_sources,
         inner_weights) = zip(*inner)
        dungeon = MultisetFunctionJointDungeon(outer_dungeonlet_flats,
                                               inner_dungeons)
        quest = MultisetFunctionJointQuest(outer_questlet_flats, inner_quests,
                                           inner_kwargses)
        sources = outer_sources + tuple(
            itertools.chain.from_iterable(all_inner_sources))
        weight = outer_weight * math.prod(inner_weights)
        yield dungeon, quest, sources, weight


class MultisetFunctionJointDungeon(MultisetDungeon[T]):

    def __init__(
        self,
        dungeonlet_flats: 'tuple[tuple[MultisetDungeonlet[T, Any], ...], ...]',
        inner_dungeons: tuple[MultisetDungeon[T], ...],
    ):
        self.dungeonlet_flats = dungeonlet_flats
        self.inner_dungeons = inner_dungeons

    def next_state(self, state, order: Order, outcome: T,
                   source_counts: Iterator,
                   param_counts: Sequence) -> Hashable:
        statelet_flats, inner_states = state

        next_statelet_flats, param_counts = self.next_statelet_flats_and_counts(
            self.dungeonlet_flats, statelet_flats, order, outcome,
            source_counts, param_counts)

        next_inner_states = tuple(
            dungeon.next_state(inner_state, order, outcome, source_counts,
                               param_counts)
            for dungeon, inner_state in zip(self.inner_dungeons, inner_states))

        if any(x is icepool.Reroll for x in next_inner_states):
            return icepool.Reroll

        return next_statelet_flats, next_inner_states

    # TODO: __hash__?


class MultisetFunctionJointQuest(MultisetQuest[T, U_co]):

    def __init__(
        self,
        questlet_flats: 'tuple[tuple[MultisetQuestlet[T], ...], ...]',
        inner_quests: tuple[MultisetQuest[T, U_co], ...],
        inner_kwargses: tuple[Mapping[str, Hashable], ...],
    ):
        self.questlet_flats = questlet_flats
        self.inner_quests = inner_quests
        self.inner_kwargses = inner_kwargses

    def extra_outcomes(self, outcomes):
        return sorted_union(*(quest.extra_outcomes(outcomes)
                              for quest in self.inner_quests))

    def initial_state(self, order, outcomes, kwargs):
        # The kwargs have already been bound to inner_kwargses.
        statelet_flats = tuple(
            tuple(
                questlet.initial_state(order, outcomes) for questlet in flat)
            for flat in self.questlet_flats)
        inner_state = tuple(
            quest.initial_state(order, outcomes, inner_kwargs) for quest,
            inner_kwargs in zip(self.inner_quests, self.inner_kwargses))
        return statelet_flats, inner_state

    def final_outcome(self, final_state, order, outcomes, kwargs):
        # The kwargs have already been bound to inner_kwargses.
        statelet_flats, inner_states = final_state
        result = tuple(
            quest.final_outcome(inner_state, order, outcomes, inner_kwargs)
            for quest, inner_state, inner_kwargs in zip(
                self.inner_quests, inner_states, self.inner_kwargses))
        if any(x is icepool.Reroll for x in result):
            return icepool.Reroll
        return result
