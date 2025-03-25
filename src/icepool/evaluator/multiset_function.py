__docformat__ = 'google'

import itertools
import math
import icepool
from icepool.evaluator.multiset_evaluator_base import MultisetEvaluatorBase, MultisetDungeon, MultisetQuest
from icepool.expression.multiset_expression_base import MultisetDungeonlet, MultisetExpressionBase, MultisetQuestlet, MultisetSourceBase
from icepool.expression.multiset_param import MultisetParam, MultisetParamBase, MultisetTupleParam

import inspect
from functools import cached_property, update_wrapper

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
    inner_exps: tuple[MultisetExpressionBase[T, Any], ...]
    inner_kwargs: Mapping[str, Hashable]

    def prepare_inner(
        self
    ) -> Iterator[tuple['MultisetDungeon[T]', 'MultisetQuest[T, U_co]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        yield from self.evaluator._prepare(self.inner_exps, self.inner_kwargs)


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
    outer_exps: tuple[MultisetExpressionBase[T, Any],
                      ...], raw_result: 'MultisetFunctionRawResult[T, U_co]'
) -> Iterator[tuple['MultisetDungeon[T]', 'MultisetQuest[T, U_co]',
                    'tuple[MultisetSourceBase[T, Any], ...]', int]]:
    for t in itertools.product(*(exp._prepare() for exp in outer_exps)):
        outer_dungeonlet_flats, outer_questlet_flats, outer_sources, outer_weights = zip(
            *t)
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
        outer_dungeonlet_flats:
        'tuple[tuple[MultisetDungeonlet[T, Any], ...], ...]',
        inner_dungeon: MultisetDungeon[T],
    ):
        self.dungeonlet_flats = outer_dungeonlet_flats + inner_dungeon.dungeonlet_flats
        self.inner_dungeon = inner_dungeon

    # does next_statelet_flats also need to be overriden?
    def next_state(self, state, order, outcome, /, *param_counts):
        inner_statelet_flats, inner_state = state
        inner_statelet_flats = self.inner_dungeon.next_statelet_flats(
            inner_statelet_flats, order, outcome, source_counts)
        inner_state = self.inner_dungeon.next_state(state, order, outcome,
                                                    *counts)
        return inner_statelet_flats, inner_state

    # TODO: __hash__?


class MultisetFunctionQuest(MultisetQuest[T, U_co]):

    def __init__(
        self,
        outer_questlet_flats: 'tuple[tuple[MultisetQuestlet[T], ...], ...]',
        inner_quest: MultisetQuest[T, U_co],
        inner_kwargs: Mapping[str, Hashable],
    ):
        self.questlet_flats = outer_questlet_flats + inner_quest.questlet_flats
        self.inner_quest = inner_quest
        self.inner_kwargs = inner_kwargs

    def extra_outcomes(self, outcomes):
        return self.inner_quest.extra_outcomes(outcomes)

    def initial_state(self, order, outcomes, /, **kwargs):
        inner_statelet_flats = self.inner_quest.initial_statelet_flats(
            order, outcomes)
        inner_state = self.inner_quest.initial_state(order, outcomes,
                                                     **self.inner_kwargs)
        return inner_statelet_flats, inner_state

    def final_outcome(self, final_state, order, outcomes, **kwargs):
        inner_statelet_flats, inner_state = final_state
        return self.inner_quest.final_outcome(inner_state, order, outcomes,
                                              **self.inner_kwargs)


def prepare_multiset_joint_function(
    raw_result: 'tuple[MultisetFunctionRawResult[T, U_co], ...]'
) -> Iterator[tuple['MultisetDungeon[T]', 'MultisetQuest[T, U_co]',
                    'tuple[MultisetSourceBase[T, Any], ...]', int]]:
    for t in itertools.product(*(raw.iter_infos() for raw in raw_result)):
        (all_nested_body_inputs, all_body_inputs, all_inner_expressions,
         all_inner_dungeon, all_inner_quest, all_inner_kwargs,
         all_weight) = zip(*t)
        all_nested_body_inputs_len = tuple(
            len(x) for x in all_nested_body_inputs)
        all_body_inputs_len = tuple(len(x) for x in all_body_inputs)
        all_combined_body_inputs = (
            *itertools.chain.from_iterable(all_nested_body_inputs),
            *itertools.chain.from_iterable(all_body_inputs))
        dungeon = MultisetFunctionJointDungeon(all_nested_body_inputs_len,
                                               all_body_inputs_len,
                                               all_inner_dungeon)
        quest = MultisetFunctionJointQuest(all_inner_expressions,
                                           all_inner_quest, all_inner_kwargs)
        yield dungeon, quest, all_combined_body_inputs, math.prod(all_weight)


class MultisetFunctionJointDungeon(MultisetDungeon[T]):

    def __init__(self, all_nested_body_inputs_len: tuple[int, ...],
                 all_body_inputs_len: tuple[int, ...],
                 all_inner_dungeon: tuple[MultisetDungeon[T]]):
        self.all_inner_dungeon = all_inner_dungeon

        pos = 0
        nested_body_slices = []
        body_slices = []
        for nested_len in all_nested_body_inputs_len:
            nested_body_slice = slice(pos, pos + nested_len)
            pos += nested_len
            nested_body_slices.append(nested_body_slice)
        for body_len in all_body_inputs_len:
            body_slice = slice(pos, pos + body_len)
            pos += body_len
            body_slices.append(body_slice)

        param_slice = slice(pos, None)
        self.count_slices = tuple(nested_body_slices), tuple(
            body_slices), param_slice

    def next_state(self, state, order, outcome, /, *counts):
        all_inner_expressions, all_inner_states = state

        next_all_inner_expressions = []
        next_all_inner_states = []

        nested_body_slices, body_slices, param_slice = self.count_slices
        param_counts = counts[param_slice]

        for (inner_expressions, inner_state, nested_body_slice, body_slice,
             inner_dungeon) in zip(all_inner_expressions, all_inner_states,
                                   nested_body_slices, body_slices,
                                   self.all_inner_dungeon):
            nested_counts = counts[nested_body_slice]
            body_counts = counts[body_slice]

            inner_expressions, inner_counts = zip(
                *(inner_expression._apply_variables(outcome, body_counts,
                                                    param_counts)
                  for inner_expression in inner_expressions))
            inner_state = inner_dungeon.next_state(inner_state, order, outcome,
                                                   *nested_counts,
                                                   *inner_counts)
            next_all_inner_expressions.append(inner_expressions)
            next_all_inner_states.append(inner_state)

        return tuple(next_all_inner_expressions), tuple(next_all_inner_states)

    # TODO: hash? must involve inner expressions if so


class MultisetFunctionJointQuest(MultisetQuest[T, U_co]):

    def __init__(
            self,
            all_inner_expressions: tuple[tuple[MultisetExpressionBase[T, Any],
                                               ...], ...],
            all_inner_quest: tuple[MultisetQuest[T, U_co], ...],
            all_inner_kwargs: tuple[Mapping[str, Hashable], ...]):
        self.all_inner_expressions = all_inner_expressions
        self.all_inner_quest = all_inner_quest
        self.all_inner_kwargs = all_inner_kwargs

    def initial_state(self, order, outcomes, /, **kwargs):
        all_inner_expressions = self.all_inner_expressions
        all_inner_states = tuple(
            inner_quest.initial_state(order, outcomes, **inner_kwargs)
            for inner_quest, inner_kwargs in zip(self.all_inner_quest,
                                                 self.all_inner_kwargs))

        return all_inner_expressions, all_inner_states

    def extra_outcomes(self, outcomes):
        return icepool.sorted_union(*(inner_quest.extra_outcomes(outcomes)
                                      for inner_quest in self.all_inner_quest))

    def final_outcome(self, final_state, order, outcomes, **kwargs):
        if final_state is None:
            result = tuple(
                inner_quest.final_outcome(None, **inner_kwargs)
                for inner_quest, inner_kwargs in zip(self.all_inner_quest,
                                                     self.all_inner_kwargs))
        else:
            result = tuple(
                inner_quest.final_outcome(inner_final_state, **inner_kwargs)
                for inner_quest, inner_final_state, inner_kwargs, in zip(
                    self.all_inner_quest, final_state[1],
                    self.all_inner_kwargs))
        if icepool.Reroll in result:
            return icepool.Reroll
        else:
            return result
