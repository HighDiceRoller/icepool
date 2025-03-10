__docformat__ = 'google'

import itertools
import math
import icepool
from icepool.evaluator.multiset_evaluator_base import MultisetDungeon, MultisetEvaluatorBase
from icepool.expression.multiset_expression_base import MultisetExpressionBase
from icepool.expression.multiset_variable import MultisetVariable
from icepool.expression.multiset_tuple_variable import MultisetTupleVariable

import inspect
from functools import cached_property, update_wrapper

from icepool.order import Order
from icepool.typing import Q, T, U_co
from typing import Any, Callable, Collection, Generic, Hashable, Iterator, Mapping, NamedTuple, Sequence, TypeAlias, overload

MV: TypeAlias = MultisetVariable | MultisetTupleVariable


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


class MultisetFunctionRawResult(Generic[T, U_co]):
    """A result of running an evaluator with `@multiset_function` parameters."""
    evaluator: MultisetEvaluatorBase[T, U_co]
    inner_inputs: tuple[MultisetExpressionBase[T, Any], ...]
    inner_kwargs: Mapping[str, Hashable]

    def __init__(self, evaluator: MultisetEvaluatorBase[T, U_co],
                 inner_inputs: tuple[MultisetExpressionBase[T, Any], ...],
                 inner_kwargs: Mapping[str, Hashable]):
        self.evaluator = evaluator
        self.inner_inputs = inner_inputs
        self.inner_kwargs = inner_kwargs

    def iter_infos(
        self
    ) -> Iterator[tuple[tuple[MultisetExpressionBase, ...], tuple[
            MultisetExpressionBase, ...], tuple[MultisetExpressionBase, ...],
                        MultisetDungeon, Mapping[str, Hashable], int]]:
        body_inputs: 'list[MultisetExpressionBase]' = []
        inner_expressions = tuple(
            input._detach(body_inputs) for input in self.inner_inputs)
        for inner_dungeon, nested_body_inputs, weight in self.evaluator._prepare(
                inner_expressions, self.inner_kwargs):
            yield (nested_body_inputs, tuple(body_inputs), inner_expressions,
                   inner_dungeon, self.inner_kwargs, weight)


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
        inputs: 'tuple[MultisetExpressionBase[T, Q], ...]',
        kwargs: Mapping[str, Hashable],
    ):
        multiset_variables = [
            expression._variable_type(True, i, self._positional_names[i])
            for i, expression in enumerate(inputs)
        ]
        raw_result = self._wrapped(*multiset_variables, **kwargs)
        if isinstance(raw_result, MultisetFunctionRawResult):
            yield from prepare_multiset_function(raw_result)
        else:
            yield from prepare_multiset_joint_function(raw_result)


def prepare_multiset_function(
    raw_result: 'MultisetFunctionRawResult[T, U_co]'
) -> 'Iterator[tuple[MultisetDungeon, tuple[MultisetExpressionBase, ...], int]]':
    for (nested_body_inputs, body_inputs, inner_expressions, inner_dungeon,
         inner_kwargs, weight) in raw_result.iter_infos():
        yield MultisetFunctionDungeon(
            len(nested_body_inputs), len(body_inputs), inner_expressions,
            inner_dungeon,
            inner_kwargs), nested_body_inputs + body_inputs, weight


class MultisetFunctionDungeon(MultisetDungeon[T, U_co]):

    def __init__(self, nested_body_inputs_len: int, body_inputs_len: int,
                 inner_expressions: tuple[MultisetExpressionBase[T, Any], ...],
                 inner_dungeon: MultisetDungeon[T, U_co],
                 inner_kwargs: Mapping[str, Hashable]):
        # TODO: do we actually need these lengths?
        # Though this question might be obviated by expression._prepare().
        self.nested_body_inputs_len = nested_body_inputs_len
        self.body_inputs_len = body_inputs_len
        self.inner_expressions = inner_expressions
        self.inner_dungeon = inner_dungeon
        # TODO: can we avoid storing inner_kwargs?
        # Would this require delaying inner dungeon creation further?
        self.inner_kwargs = inner_kwargs
        self.ascending_cache = {}
        self.descending_cache = {}

    def initial_state(self, order, outcomes, /, **kwargs):
        return self.inner_expressions, self.inner_dungeon.initial_state(
            order, outcomes, **self.inner_kwargs)

    def next_state(self, state, order, outcome, /, *counts):
        inner_expressions, inner_state = state
        nested_slice, body_slice, param_slice = self._count_slices
        nested_counts = counts[nested_slice]
        body_counts = counts[body_slice]
        param_counts = counts[param_slice]

        inner_expressions, inner_counts = zip(
            *(inner_expression._apply_variables(outcome, body_counts,
                                                param_counts)
              for inner_expression in inner_expressions))
        inner_state = self.inner_dungeon.next_state(inner_state, order,
                                                    outcome, *nested_counts,
                                                    *inner_counts)

        return inner_expressions, inner_state

    def extra_outcomes(self, outcomes):
        return self.inner_dungeon.extra_outcomes(outcomes)

    def final_outcome(self, final_state, **kwargs):
        if final_state is None:
            return self.inner_dungeon.final_outcome(None, **self.inner_kwargs)
        else:
            _, inner_state = final_state
        return self.inner_dungeon.final_outcome(inner_state,
                                                **self.inner_kwargs)

    @cached_property
    def _count_slices(self) -> 'tuple[slice, slice, slice]':
        nested_slice = slice(0, self.nested_body_inputs_len)
        body_slice = slice(nested_slice.stop,
                           nested_slice.stop + self.body_inputs_len)
        param_slice = slice(body_slice.stop, None)
        return nested_slice, body_slice, param_slice

    @cached_property
    def _hash_key(self) -> Hashable:
        return (MultisetFunctionDungeon, self.inner_expressions,
                self.inner_dungeon, tuple(sorted(self.inner_kwargs.items())))

    @cached_property
    def _hash(self) -> int:
        return hash(self._hash_key)

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other) -> bool:
        if not isinstance(other, MultisetFunctionDungeon):
            return False
        return self._hash_key == other._hash_key


def prepare_multiset_joint_function(
    raw_result: 'tuple[MultisetFunctionRawResult[T, U_co], ...]'
) -> 'Iterator[tuple[MultisetDungeon, tuple[MultisetExpressionBase, ...], int]]':
    for t in itertools.product(*(raw.iter_infos() for raw in raw_result)):
        (all_nested_body_inputs, all_body_inputs, all_inner_expressions,
         all_inner_dungeon, all_inner_kwargs, all_weight) = zip(*t)
        all_nested_body_inputs_len = tuple(
            len(x) for x in all_nested_body_inputs)
        all_body_inputs_len = tuple(len(x) for x in all_body_inputs)
        all_combined_body_inputs = (
            *itertools.chain.from_iterable(all_nested_body_inputs),
            *itertools.chain.from_iterable(all_body_inputs))
        yield MultisetFunctionJointDungeon(
            all_nested_body_inputs_len, all_body_inputs_len,
            all_inner_expressions, all_inner_dungeon,
            all_inner_kwargs), all_combined_body_inputs, math.prod(all_weight)


class MultisetFunctionJointDungeon(MultisetDungeon[T, U_co]):

    def __init__(
            self, all_nested_body_inputs_len: tuple[int, ...],
            all_body_inputs_len: tuple[int, ...],
            all_inner_expressions: tuple[tuple[MultisetExpressionBase[T, Any],
                                               ...], ...],
            all_inner_dungeon: tuple[MultisetDungeon[T, U_co], ...],
            all_inner_kwargs: tuple[Mapping[str, Hashable], ...]):
        self.all_nested_body_inputs_len = all_nested_body_inputs_len
        self.all_body_inputs_len = all_body_inputs_len
        self.all_inner_expressions = all_inner_expressions
        self.all_inner_dungeon = all_inner_dungeon
        self.all_inner_kwargs = all_inner_kwargs

        self.ascending_cache = {}
        self.descending_cache = {}

    def initial_state(self, order, outcomes, /, **kwargs):
        all_inner_expressions = self.all_inner_expressions
        all_inner_states = tuple(
            inner_dungeon.initial_state(order, outcomes, **inner_kwargs)
            for inner_dungeon, inner_kwargs in zip(self.all_inner_dungeon,
                                                   self.all_inner_kwargs))

        return all_inner_expressions, all_inner_states

    def next_state(self, state, order, outcome, /, *counts):
        all_inner_expressions, all_inner_states = state

        next_all_inner_expressions = []
        next_all_inner_states = []

        nested_body_slices, body_slices, param_slice = self._count_slices
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

    def extra_outcomes(self, outcomes):
        return icepool.sorted_union(
            *(inner_dungeon.extra_outcomes(outcomes)
              for inner_dungeon in self.all_inner_dungeon))

    def final_outcome(self, final_state, **kwargs):
        if final_state is None:
            result = tuple(
                inner_dungeon.final_outcome(None, **inner_kwargs)
                for inner_dungeon, inner_kwargs in zip(self.all_inner_dungeon,
                                                       self.all_inner_kwargs))
        else:
            result = tuple(
                inner_dungeon.final_outcome(inner_final_state, **inner_kwargs)
                for inner_dungeon, inner_final_state, inner_kwargs, in zip(
                    self.all_inner_dungeon, final_state[1],
                    self.all_inner_kwargs))
        if icepool.Reroll in result:
            return icepool.Reroll
        else:
            return result

    @cached_property
    def _count_slices(
            self) -> tuple[tuple[slice, ...], tuple[slice, ...], slice]:
        pos = 0
        nested_body_slices = []
        body_slices = []
        for nested_len in self.all_nested_body_inputs_len:
            nested_body_slice = slice(pos, pos + nested_len)
            pos += nested_len
            nested_body_slices.append(nested_body_slice)
        for body_len in self.all_body_inputs_len:
            body_slice = slice(pos, pos + body_len)
            pos += body_len
            body_slices.append(body_slice)

        param_slice = slice(pos, None)
        return tuple(nested_body_slices), tuple(body_slices), param_slice

    @cached_property
    def _hash_key(self) -> Hashable:
        return (MultisetFunctionJointDungeon, self.all_inner_expressions,
                self.all_inner_dungeon,
                tuple(
                    tuple(sorted(inner_kwargs.items()))
                    for inner_kwargs in self.all_inner_kwargs))

    @cached_property
    def _hash(self) -> int:
        return hash(self._hash_key)

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other) -> bool:
        if not isinstance(other, MultisetFunctionJointDungeon):
            return False
        return self._hash_key == other._hash_key
