__docformat__ = 'google'

from icepool.evaluator.multiset_evaluator_base import MultisetDungeon, MultisetEvaluatorBase
from icepool.expression.base import MultisetExpressionBase
from icepool.expression.multiset_variable import MultisetVariable
from icepool.expression.multiset_tuple_variable import MultisetTupleVariable

import inspect
from functools import cached_property, update_wrapper

from icepool.order import Order
from icepool.typing import Q, T, U_co
from typing import Any, Callable, Collection, Hashable, Mapping, Sequence, TypeAlias, overload

MV: TypeAlias = MultisetVariable | MultisetTupleVariable


@overload
def multiset_function(wrapped: Callable[[MV], MultisetEvaluatorBase[T, U_co]
                                        | tuple[MultisetEvaluatorBase[T, U_co],
                                                ...]],
                      /) -> MultisetEvaluatorBase[T, U_co]:
    ...


@overload
def multiset_function(wrapped: Callable[[MV, MV],
                                        MultisetEvaluatorBase[T, U_co]
                                        | tuple[MultisetEvaluatorBase[T, U_co],
                                                ...]],
                      /) -> MultisetEvaluatorBase[T, U_co]:
    ...


@overload
def multiset_function(wrapped: Callable[[MV, MV, MV],
                                        MultisetEvaluatorBase[T, U_co]
                                        | tuple[MultisetEvaluatorBase[T, U_co],
                                                ...]],
                      /) -> MultisetEvaluatorBase[T, U_co]:
    ...


@overload
def multiset_function(wrapped: Callable[[MV, MV, MV, MV],
                                        MultisetEvaluatorBase[T, U_co]
                                        | tuple[MultisetEvaluatorBase[T, U_co],
                                                ...]],
                      /) -> MultisetEvaluatorBase[T, U_co]:
    ...


def multiset_function(wrapped: Callable[..., MultisetEvaluatorBase[T, U_co]
                                        | tuple[MultisetEvaluatorBase[T, U_co],
                                                ...]],
                      /) -> MultisetEvaluatorBase[T, U_co]:
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


class MultisetFunctionEvaluator(MultisetEvaluatorBase[T, U_co]):

    def __init__(
        self, wrapped: Callable[..., MultisetEvaluatorBase[T, U_co]
                                | tuple[MultisetEvaluatorBase[T, U_co], ...]]):
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
        wrapped_result = self._wrapped(*multiset_variables, **kwargs)
        # TODO: cache? or is the cache done outside?
        if isinstance(wrapped_result, tuple):
            return prepare_multiset_function(wrapped_result)
        else:
            return prepare_multiset_joint_function(wrapped_result)


def prepare_multiset_function(
    wrapped_result:
    'tuple[MultisetEvaluatorBase[T, U_co], tuple[MultisetExpressionBase[T, Any], ...], Mapping[str, Hashable]]'
) -> 'tuple[MultisetDungeon, tuple[MultisetExpressionBase, ...]]':
    evaluator, inner_inputs, inner_kwargs = wrapped_result
    body_inputs: 'list[MultisetExpressionBase]' = []
    inner_inputs = tuple(input._detach(body_inputs) for input in inner_inputs)
    inner_dungeon, nested_body_inputs = evaluator.prepare(
        inner_inputs, inner_kwargs)
    all_body_inputs = nested_body_inputs + tuple(body_inputs)
    return MultisetFunctionDungeon(len(body_inputs), inner_inputs,
                                   inner_dungeon,
                                   inner_kwargs), tuple(all_body_inputs)


def prepare_multiset_joint_function(
    wrapped_result:
    'tuple[tuple[MultisetEvaluatorBase[T, U_co], tuple[MultisetExpressionBase[T, Any], ...], Mapping[str, Hashable]], ...]'
) -> 'MultisetDungeon':
    raise NotImplementedError()


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


class MultisetFunctionJointDungeon(MultisetDungeon[T, U_co]):

    def __init__(
        self, wrapped_result:
        'tuple[tuple[MultisetEvaluatorBase[T, U_co], tuple[MultisetExpressionBase[T, Any], ...], Mapping[str, Hashable]], ...]'
    ):
        # In this joint case we forward directly.
        self.direct_kwargs = {}
        self.all_inner_kwargs = ()  # TODO
        raise NotImplementedError()

    @cached_property
    def _hash_key(self) -> Hashable:
        raise NotImplementedError()

    @cached_property
    def _hash(self) -> int:
        return hash(self._hash_key)

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other) -> bool:
        if not isinstance(other, MultisetFunctionDungeon):
            return False
        return self._hash_key == other._hash_key
