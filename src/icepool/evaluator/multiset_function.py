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

    Any globals inside `function` are currently effectively bound at the time
    `multiset_function` is invoked. Note that this is different than how
    ordinary Python closures behave. For example,

    ```python
    target = [1, 2, 3]

    @multiset_function
    def count_intersection(a):
        return (a & target).count()

    print(count_intersection(d6.pool(3)))

    target = [1]
    print(count_intersection(d6.pool(3)))
    ```

    would produce the same thing both times. This behavior may change in the 
    future; I recommend to use only pure functions with `@mulitset_function`
    (i.e. not producing any side effects, nor being affected by them).

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

        update_wrapper(self, wrapped)

    def prepare(
        self,
        inputs: 'tuple[MultisetExpressionBase[T, Q], ...]',
        kwargs: Mapping[str, Hashable],
    ) -> 'MultisetDungeon':
        multiset_variables = [
            expression._variable_type(True, i, self._positional_names[i])
            for i, expression in enumerate(inputs)
        ]
        wrapped_result = self._wrapped(*multiset_variables, **kwargs)
        # TODO: cache? or is the cache done outside?
        if isinstance(wrapped_result, tuple):
            return MultisetFunctionDungeon(wrapped_result)
        else:
            return MultisetFunctionJointDungeon(wrapped_result)


class MultisetFunctionDungeon(MultisetDungeon[T, U_co]):
    next_state_ascending = None  # type: ignore
    next_state_descending = None  # type: ignore
    extra_outcomes = None  # type: ignore
    final_outcome = None  # type: ignore

    def __init__(
        self, wrapped_result:
        'tuple[MultisetEvaluatorBase[T, U_co], tuple[MultisetExpressionBase[T, Any], ...], Mapping[str, Hashable]]'
    ):
        evaluator, inner_inputs, inner_kwargs = wrapped_result
        non_parameters: 'list[MultisetExpressionBase]' = []
        self.inner_inputs = tuple(
            input._unbind(non_parameters) for input in inner_inputs)
        self.inner_dungeon = evaluator.prepare(self.inner_inputs, inner_kwargs)
        self.next_state_ascending = self.inner_dungeon.next_state_ascending  # type: ignore
        self.next_state_descending = self.inner_dungeon.next_state_descending  # type: ignore
        self.extra_outcomes = self.inner_dungeon.extra_outcomes  # type: ignore
        self.final_outcome = self.inner_dungeon.final_outcome  # type: ignore
        self.kwargs = inner_kwargs
        self.ascending_cache = {}
        self.descending_cache = {}

    @cached_property
    def _hash_key(self) -> Hashable:
        # TODO: is this enough?
        return (MultisetFunctionDungeon, self.inner_dungeon, self.inner_inputs,
                tuple(sorted(self.kwargs.items())))

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
        self.kwargs = {}
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
