import itertools
import icepool
import icepool.evaluator

from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.expression.multiset_variable import MultisetVariable as MV

import inspect
from functools import cached_property, update_wrapper

from typing import Any, Callable, Collection, Hashable, TypeAlias, overload

from icepool.order import Order, OrderReason, merge_order_preferences
from icepool.typing import T, U_co

NestedTupleOrEvaluator: TypeAlias = MultisetEvaluator[T, U_co] | tuple[
    'NestedTupleOrEvaluator[T, U_co]', ...]

NestedTupleOrOutcome: TypeAlias = U_co | tuple['NestedTupleOrOutcome[U_co]',
                                               ...]


def replace_tuples_with_joint_evaluator(
        arg: NestedTupleOrEvaluator[T, U_co],
        /) -> MultisetEvaluator[T, NestedTupleOrOutcome[U_co]]:
    """Recursively replaces tuples with `JointEvaluator`s."""
    if isinstance(arg, tuple):
        return icepool.evaluator.JointEvaluator(
            *(replace_tuples_with_joint_evaluator(x) for x in arg))
    elif isinstance(arg, MultisetEvaluator):
        return arg
    else:
        raise TypeError(f'Expected evaluator, got {type(arg)}.')


@overload
def multiset_function(function: Callable[[MV], NestedTupleOrEvaluator[T,
                                                                      U_co]],
                      /) -> MultisetEvaluator[T, NestedTupleOrOutcome[U_co]]:
    ...


@overload
def multiset_function(function: Callable[[MV, MV],
                                         NestedTupleOrEvaluator[T, U_co]],
                      /) -> MultisetEvaluator[T, NestedTupleOrOutcome[U_co]]:
    ...


@overload
def multiset_function(function: Callable[[MV, MV, MV],
                                         NestedTupleOrEvaluator[T, U_co]],
                      /) -> MultisetEvaluator[T, NestedTupleOrOutcome[U_co]]:
    ...


@overload
def multiset_function(function: Callable[[MV, MV, MV, MV],
                                         NestedTupleOrEvaluator[T, U_co]],
                      /) -> MultisetEvaluator[T, NestedTupleOrOutcome[U_co]]:
    ...


def multiset_function(function: Callable[..., NestedTupleOrEvaluator[T, U_co]],
                      /) -> MultisetEvaluator[T, NestedTupleOrOutcome[U_co]]:
    """EXPERIMENTAL: A decorator that turns a function into a `MultisetEvaluator`.

    The provided function should take in arguments representing multisets,
    do a limited set of operations on them (see `MultisetExpression`), and
    finish off with an evaluation. You can return tuples to perform a joint
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
            output an evaluator or a nested tuple of evaluators. Tuples will
            result in a `JointEvaluator`.
    """
    parameters = inspect.signature(function, follow_wrapped=False).parameters
    multiset_variables = []
    for index, parameter in enumerate(parameters.values()):
        if parameter.kind not in [
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ] or parameter.default != inspect.Parameter.empty:
            raise ValueError(
                'Callable must take only a fixed number of positional arguments.'
            )
        multiset_variables.append(
            MV(is_free=True, index=index, name=parameter.name))
    tuple_or_evaluator = function(*multiset_variables)
    evaluator = replace_tuples_with_joint_evaluator(tuple_or_evaluator)
    # This is not actually a function.
    return update_wrapper(evaluator, function)  # type: ignore


class MultisetFunctionEvaluator(MultisetEvaluator[T, U_co]):
    __name__ = '(unnamed)'

    def __init__(self, *inputs: 'icepool.MultisetExpressionBase[T, Any]',
                 evaluator: MultisetEvaluator[T, U_co]) -> None:
        self._evaluator = evaluator
        bound_inputs: 'list[icepool.MultisetExpressionBase]' = []
        self._expressions = tuple(
            input._unbind(bound_inputs) for input in inputs)
        self._bound_inputs = tuple(bound_inputs)

    def next_state_ascending(self, state, outcome, *counts):
        if state is None:
            expressions = self._expressions
            evaluator_state = None
        else:
            expressions, evaluator_state = state

        evaluator_slice, bound_slice, free_slice = self._count_slices
        evaluator_counts = counts[evaluator_slice]
        bound_counts = counts[bound_slice]
        free_counts = counts[free_slice]

        expressions, expression_counts = zip(
            *(expression._apply_variables(outcome, bound_counts, free_counts)
              for expression in expressions))
        evaluator_state = self._next_state_method_ascending(
            evaluator_state, outcome, *evaluator_counts, *expression_counts)
        return expressions, evaluator_state

    def next_state_descending(self, state, outcome, *counts):
        if state is None:
            expressions = self._expressions
            evaluator_state = None
        else:
            expressions, evaluator_state = state

        evaluator_slice, bound_slice, free_slice = self._count_slices
        evaluator_counts = counts[evaluator_slice]
        bound_counts = counts[bound_slice]
        free_counts = counts[free_slice]

        expressions, expression_counts = zip(
            *(expression._apply_variables(outcome, bound_counts, free_counts)
              for expression in expressions))
        evaluator_state = self._next_state_method_descending(
            evaluator_state, outcome, *evaluator_counts, *expression_counts)
        return expressions, evaluator_state

    def final_outcome(
            self,
            final_state) -> 'U_co | icepool.Die[U_co] | icepool.RerollType':
        if final_state is None:
            return self._evaluator.final_outcome(None)
        else:
            _, evaluator_state = final_state
        return self._evaluator.final_outcome(evaluator_state)

    def order(self) -> Order:
        expression_order, expression_order_reason = merge_order_preferences(
            *(expression.order_preference()
              for expression in self._expressions),
            (self._evaluator.order(), OrderReason.Mandatory))
        return expression_order

    @cached_property
    def _next_state_method_ascending(self) -> Callable[..., Hashable]:
        return self._evaluator.next_state_method(Order.Ascending)

    @cached_property
    def _next_state_method_descending(self) -> Callable[..., Hashable]:
        return self._evaluator.next_state_method(Order.Descending)

    def extra_outcomes(self, *generators) -> Collection[T]:
        return self._evaluator.extra_outcomes(*generators)

    def bound_inputs(self) -> 'tuple[icepool.MultisetExpressionBase, ...]':
        return self._evaluator.bound_inputs() + self._bound_inputs

    @cached_property
    def _count_slices(self) -> 'tuple[slice, slice, slice]':
        evaluator_slice = slice(None, len(self._evaluator.bound_inputs()))
        bound_slice = slice(evaluator_slice.stop,
                            evaluator_slice.stop + len(self._bound_inputs))
        free_slice = slice(bound_slice.stop, None)
        return evaluator_slice, bound_slice, free_slice

    def __str__(self) -> str:
        return f'<multiset_function {self.__name__}>'
