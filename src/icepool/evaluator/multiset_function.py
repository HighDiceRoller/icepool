__docformat__ = 'google'

import itertools
import math
import icepool
from icepool.evaluator.multiset_evaluator_base import MultisetEvaluatorBase, Dungeon, Quest
from icepool.expression.multiset_expression_base import Dungeonlet, MultisetExpressionBase, Questlet, MultisetSourceBase
from icepool.expression.multiset_param import MultisetParam, MultisetTupleParam

import inspect
from functools import update_wrapper

from icepool.function import sorted_union
from icepool.order import Order
from icepool.typing import Q, T, MaybeHashKeyed, U_co
from typing import Any, Callable, Generic, Hashable, Iterator, Mapping, MutableSequence, NamedTuple, Sequence, TypeAlias, overload

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
        return a.keep_outcomes(target).size()

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
    ) -> Iterator[tuple['Dungeon[T]', 'Quest[T, U_co]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        yield from self.evaluator._prepare(self.body_exps, self.inner_kwargs)


class MultisetFunctionEvaluator(MultisetEvaluatorBase[T, U_co]):
    _positional_names: Sequence[str]

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
    ) -> Iterator[tuple['Dungeon[T]', 'Quest[T, U_co]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        multiset_variables = [
            exp._make_param(i, self._positional_names[i])
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
) -> Iterator[tuple['Dungeon[T]', 'Quest[T, U_co]',
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


class MultisetFunctionDungeon(Dungeon[T], MaybeHashKeyed):

    def __init__(
        self,
        dungeonlet_flats: 'tuple[tuple[Dungeonlet[T, Any], ...], ...]',
        inner_dungeon: Dungeon[T],
    ):
        self.dungeonlet_flats = dungeonlet_flats
        self.inner_dungeon = inner_dungeon
        self.calls = (inner_dungeon, )

        if self.inner_dungeon.__hash__ is None:
            self.__hash__ = None  # type: ignore

    def next_state_main(self, state, order: Order, outcome: T,
                        *param_counts) -> Hashable:
        return self.inner_dungeon.next_state_main(state, order, outcome,
                                                  *param_counts[0])

    @property
    def hash_key(self):
        if self.__hash__ is None:
            return None
        return MultisetFunctionDungeon, self.dungeonlet_flats, self.inner_dungeon


class MultisetFunctionQuest(Quest[T, U_co]):

    def __init__(
        self,
        questlet_flats: 'tuple[tuple[Questlet[T, Any], ...], ...]',
        inner_quest: Quest[T, U_co],
        inner_kwargs: Mapping[str, Hashable],
    ):
        self.questlet_flats = questlet_flats
        self.inner_quest = inner_quest
        self.calls = (inner_quest, )
        self.inner_kwargs = inner_kwargs

    def extra_outcomes(self, outcomes):
        return self.inner_quest.extra_outcomes(outcomes)

    def initial_state_main(self, order: Order, outcomes: tuple[T, ...],
                           *param_sizes, **kwargs: Hashable) -> Hashable:
        # The kwargs have already been bound to inner_kwargs.
        return self.inner_quest.initial_state_main(order, outcomes,
                                                   *param_sizes[0],
                                                   **self.inner_kwargs)

    def final_outcome(self, final_state, order: Order, outcomes: tuple[T, ...],
                      *param_sizes, **kwargs):
        return self.inner_quest.final_outcome(final_state, order, outcomes,
                                              *param_sizes[0],
                                              **self.inner_kwargs)


def prepare_multiset_joint_function(
    outer_exps: tuple[MultisetExpressionBase[T, Any], ...],
    raw_result: tuple['MultisetFunctionRawResult[T, Any]', ...],
) -> Iterator[tuple['Dungeon[T]', 'Quest[T, Any]',
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


class MultisetFunctionJointDungeon(Dungeon[T], MaybeHashKeyed):

    def __init__(
        self,
        dungeonlet_flats: 'tuple[tuple[Dungeonlet[T, Any], ...], ...]',
        inner_dungeons: tuple[Dungeon[T], ...],
    ):
        self.dungeonlet_flats = dungeonlet_flats
        self.inner_dungeons = inner_dungeons
        self.calls = inner_dungeons

        if any(dungeon.__hash__ is None for dungeon in inner_dungeons):
            self.__hash__ = None  # type: ignore

    def next_state_main(self, state, order: Order, outcome: T,
                        *param_counts) -> Hashable:
        next_state: MutableSequence[Hashable] = []
        inner_dungeon: Dungeon[T]
        inner_param_tree: tuple
        for inner_state, inner_dungeon, inner_param_tree in zip(
                state, self.inner_dungeons, param_counts):
            next_inner_state = inner_dungeon.next_state_main(
                inner_state, order, outcome, *inner_param_tree)
            if next_inner_state is icepool.Reroll:
                return icepool.Reroll
            next_state.append(next_inner_state)
        return tuple(next_state)

    @property
    def hash_key(self):
        if self.__hash__ is None:
            return None
        return MultisetFunctionJointDungeon, self.dungeonlet_flats, self.inner_dungeons


class MultisetFunctionJointQuest(Quest[T, Any]):

    def __init__(
        self,
        questlet_flats: 'tuple[tuple[Questlet[T, Any], ...], ...]',
        inner_quests: tuple[Quest[T, Any], ...],
        inner_kwargses: tuple[Mapping[str, Hashable], ...],
    ):
        self.questlet_flats = questlet_flats
        self.inner_quests = inner_quests
        self.calls = inner_quests
        self.inner_kwargses = inner_kwargses

    def extra_outcomes(self, outcomes):
        return sorted_union(*(quest.extra_outcomes(outcomes)
                              for quest in self.inner_quests))

    def initial_state_main(self, order: Order, outcomes: tuple[T, ...],
                           *param_sizes, **kwargs: Hashable) -> Hashable:

        return tuple(
            inner_quest.initial_state_main(order, outcomes, *inner_param_sizes,
                                           **inner_kwargs)
            for inner_quest, inner_kwargs, inner_param_sizes in zip(
                self.inner_quests, self.inner_kwargses, param_sizes))

    def final_outcome(self, final_state, order: Order, outcomes: tuple[T, ...],
                      *param_sizes, **kwargs: Hashable):
        # The kwargs have already been bound to inner_kwargses.
        result = tuple(
            quest.final_outcome(inner_main_state, order, outcomes, *
                                inner_param_sizes, **inner_kwargs)
            for quest, inner_main_state, inner_param_sizes, inner_kwargs in
            zip(self.inner_quests, final_state, param_sizes,
                self.inner_kwargses))
        if any(x is icepool.Reroll for x in result):
            return icepool.Reroll
        return result
