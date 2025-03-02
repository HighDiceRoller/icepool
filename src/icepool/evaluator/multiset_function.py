__docformat__ = 'google'

import icepool
from icepool.evaluator.multiset_evaluator_base import MultisetDungeon, MultisetEvaluatorBase
from icepool.expression.base import MultisetExpressionBase
from icepool.expression.multiset_variable import MultisetVariable
from icepool.expression.multiset_tuple_variable import MultisetTupleVariable

import inspect
from functools import cached_property, update_wrapper

from icepool.order import Order
from icepool.typing import Q, T, U_co
from typing import Any, Callable, Collection, Generic, Hashable, Mapping, NamedTuple, Sequence, TypeAlias, overload

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

    I recommend to only use pure functions with `@multiset_function`.

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
        function: This should take in a fixed number of multiset variables and
            output an evaluator or tuple of evaluators. 
    """
    return MultisetFunctionEvaluator(wrapped)


class MultisetFunctionRawResult(Generic[T, U_co], NamedTuple):
    """A result of running an evaluator with `@multiset_function` parameters."""
    evaluator: MultisetEvaluatorBase[T, U_co]
    inner_inputs: tuple[MultisetExpressionBase[T, Any], ...]
    inner_kwargs: Mapping[str, Hashable]


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

            # TODO: anything needed for kwargs here?

        update_wrapper(self, wrapped)

    def prepare(
        self,
        inputs: 'tuple[MultisetExpressionBase[T, Q], ...]',
        kwargs: Mapping[str, Hashable],
    ):
        multiset_variables = [
            expression._variable_type(True, i, self._positional_names[i])
            for i, expression in enumerate(inputs)
        ]
        raw_result = self._wrapped(*multiset_variables, **kwargs)
        # TODO: cache? or is the cache done outside?
        if isinstance(raw_result, MultisetFunctionRawResult):
            return prepare_multiset_function(raw_result)
        else:
            return prepare_multiset_joint_function(raw_result)


def prepare_multiset_function(
    raw_result: 'MultisetFunctionRawResult[T, U_co]'
) -> 'tuple[MultisetDungeon, tuple[MultisetExpressionBase, ...]]':
    evaluator, inner_inputs, inner_kwargs = raw_result
    body_inputs: 'list[MultisetExpressionBase]' = []
    inner_inputs = tuple(input._detach(body_inputs) for input in inner_inputs)
    inner_dungeon, nested_body_inputs = evaluator.prepare(
        inner_inputs, inner_kwargs)
    combined_body_inputs = nested_body_inputs + tuple(body_inputs)
    return MultisetFunctionDungeon(len(body_inputs), inner_inputs,
                                   inner_dungeon,
                                   inner_kwargs), tuple(combined_body_inputs)


class MultisetFunctionDungeon(MultisetDungeon[T, U_co]):

    def __init__(self, body_inputs_len: int,
                 inner_inputs: tuple[MultisetExpressionBase[T, Any], ...],
                 inner_dungeon: MultisetDungeon[T, U_co],
                 inner_kwargs: Mapping[str, Hashable]):
        self.body_inputs_len = body_inputs_len
        self.inner_inputs = inner_inputs
        self.inner_dungeon = inner_dungeon
        self.inner_kwargs = inner_kwargs
        self.ascending_cache = {}
        self.descending_cache = {}

        if self.inner_dungeon.next_state_ascending is None:
            self.next_state_ascending = None
        if self.inner_dungeon.next_state_descending is None:
            self.next_state_descending = None

    def next_state_ascending(self, state, outcome, /, *counts,
                             **kwargs) -> Hashable:
        if state is None:
            inner_inputs = self.inner_inputs
            inner_state = None
        else:
            inner_inputs, inner_state = state
        nested_slice, body_slice, param_slice = self._count_slices
        nested_counts = counts[nested_slice]
        body_counts = counts[body_slice]
        param_counts = counts[param_slice]

        inner_inputs, inner_counts = zip(
            *(inner_input._apply_variables(outcome, body_counts, param_counts)
              for inner_input in inner_inputs))
        inner_state = self.inner_dungeon.next_state_ascending(
            inner_state, outcome, *nested_counts, *inner_counts,
            **self.inner_kwargs)

        return inner_inputs, inner_state

    def next_state_descending(self, state, outcome, /, *counts,
                              **kwargs) -> Hashable:
        if state is None:
            inner_inputs = self.inner_inputs
            inner_state = None
        else:
            inner_inputs, inner_state = state
        nested_slice, body_slice, param_slice = self._count_slices
        nested_counts = counts[nested_slice]
        body_counts = counts[body_slice]
        param_counts = counts[param_slice]

        inner_inputs, inner_counts = zip(
            *(inner_input._apply_variables(outcome, body_counts, param_counts)
              for inner_input in inner_inputs))
        inner_state = self.inner_dungeon.next_state_descending(
            inner_state, outcome, *nested_counts, *inner_counts,
            **self.inner_kwargs)

        return inner_inputs, inner_state

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
        nested_slice = slice(None, self.inner_dungeon.body_inputs_len)
        body_slice = slice(nested_slice.stop,
                           nested_slice.stop + self.body_inputs_len)
        param_slice = slice(body_slice.stop, None)
        return nested_slice, body_slice, param_slice

    @cached_property
    def _hash_key(self) -> Hashable:
        return (MultisetFunctionDungeon, self.body_inputs_len,
                self.inner_inputs, self.inner_dungeon,
                tuple(sorted(self.inner_kwargs.items())))

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
) -> 'tuple[MultisetDungeon, tuple[MultisetExpressionBase, ...]]':
    all_body_inputs_len: list[int] = []
    all_body_inputs = []
    all_inner_inputs = []
    all_inner_dungeon = []
    all_inner_kwargs = []
    for evaluator, inner_inputs, inner_kwargs in raw_result:
        body_inputs: 'list[MultisetExpressionBase]' = []
        inner_inputs = tuple(
            input._detach(body_inputs) for input in inner_inputs)
        inner_dungeon, nested_body_inputs = evaluator.prepare(
            inner_inputs, inner_kwargs)

        all_body_inputs_len.append(len(body_inputs))

        all_inner_inputs.append(inner_inputs)
        all_inner_dungeon.append(inner_dungeon)

        # TODO: all nested before all current, or interleaved?
        all_body_inputs += list(nested_body_inputs)
        all_body_inputs += body_inputs

        all_inner_kwargs.append(inner_kwargs)
    return MultisetFunctionJointDungeon(
        tuple(all_body_inputs_len), tuple(all_inner_inputs),
        tuple(all_inner_dungeon),
        tuple(all_inner_kwargs)), tuple(all_body_inputs)


class MultisetFunctionJointDungeon(MultisetDungeon[T, U_co]):

    def __init__(self, all_body_inputs_len: tuple[int, ...],
                 all_inner_inputs: tuple[tuple[MultisetExpressionBase[T, Any],
                                               ...], ...],
                 all_inner_dungeon: tuple[MultisetDungeon[T, U_co], ...],
                 all_inner_kwargs: tuple[Mapping[str, Hashable], ...]):
        self.body_inputs_len = sum(all_body_inputs_len)
        self.all_body_inputs_len = all_body_inputs_len
        self.all_inner_inputs = all_inner_inputs
        self.all_inner_dungeon = all_inner_dungeon
        self.all_inner_kwargs = all_inner_kwargs

        self.ascending_cache = {}
        self.descending_cache = {}

        for inner_dungeon in self.all_inner_dungeon:
            if inner_dungeon.next_state_ascending is None:
                self.next_state_ascending = None
            if inner_dungeon.next_state_descending is None:
                self.next_state_descending = None

    def next_state_ascending(self, state, outcome, /, *counts,
                             **kwargs) -> Hashable:
        raise NotImplementedError()

    def next_state_descending(self, state, outcome, /, *counts,
                              **kwargs) -> Hashable:
        raise NotImplementedError()

    def extra_outcomes(self, outcomes):
        return icepool.sorted_union(
            *(inner_dungeon.extra_outcomes(outcomes)
              for inner_dungeon in self.all_inner_dungeon))

    def final_outcome(self, final_state, **kwargs):
        raise NotImplementedError()

    @cached_property
    def _hash_key(self) -> Hashable:
        return (MultisetFunctionJointDungeon, self.all_body_inputs_len,
                self.all_inner_inputs, self.all_inner_dungeon,
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
