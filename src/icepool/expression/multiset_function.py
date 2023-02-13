import icepool
import icepool.evaluator

from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.expression.variable import MultisetVariable as MV

import inspect
from functools import update_wrapper

from typing import Callable, TypeAlias, overload

from icepool.typing import T_contra, U_co

NestedTupleOrEvaluator: TypeAlias = MultisetEvaluator[T_contra, U_co] | tuple[
    'NestedTupleOrEvaluator[T_contra, U_co]', ...]

NestedTupleOrOutcome: TypeAlias = U_co | tuple['NestedTupleOrOutcome[U_co]',
                                               ...]


def replace_tuples_with_joint_evaluator(
        arg: NestedTupleOrEvaluator[T_contra, U_co],
        /) -> MultisetEvaluator[T_contra, NestedTupleOrOutcome[U_co]]:
    """Recursively replaces tuples with `JointEvaluator`s."""
    if isinstance(arg, tuple):
        return icepool.evaluator.JointEvaluator(
            *(replace_tuples_with_joint_evaluator(x) for x in arg))
    elif isinstance(arg, MultisetEvaluator):
        return arg
    else:
        raise TypeError(f'Expected evaluator, got {type(arg)}.')


@overload
def multiset_function(
        func: Callable[[MV], NestedTupleOrEvaluator[T_contra, U_co]],
        /) -> MultisetEvaluator[T_contra, NestedTupleOrOutcome[U_co]]:
    ...


@overload
def multiset_function(
        func: Callable[[MV, MV], NestedTupleOrEvaluator[T_contra, U_co]],
        /) -> MultisetEvaluator[T_contra, NestedTupleOrOutcome[U_co]]:
    ...


@overload
def multiset_function(
        func: Callable[[MV, MV, MV], NestedTupleOrEvaluator[T_contra, U_co]],
        /) -> MultisetEvaluator[T_contra, NestedTupleOrOutcome[U_co]]:
    ...


@overload
def multiset_function(
        func: Callable[[MV, MV, MV, MV], NestedTupleOrEvaluator[T_contra,
                                                                U_co]],
        /) -> MultisetEvaluator[T_contra, NestedTupleOrOutcome[U_co]]:
    ...


def multiset_function(
        func: Callable[..., NestedTupleOrEvaluator[T_contra, U_co]],
        /) -> MultisetEvaluator[T_contra, NestedTupleOrOutcome[U_co]]:
    """A decorator that turns a function into a `MultisetEvaluator`.

    The provided function should take in arguments representing multisets,
    do some operations on them (see `MultisetExpression`), and finish off with
    an evaluation. You can return tuples to perform a joint evaluation.

    For example, to create an evaluator which computes the elements each of two
    multisets has that the other doesn't:

    ```
    @multiset_function
    def two_way_difference(a, b):
        return (a - b).expand(), (b - a).expand()
    ```

    Any globals inside `func` are effectively bound at the time
    `multiset_function` is invoked. Note that this is different than how
    ordinary Python closures behave. For example,

    ```
    target = [1, 2, 3]

    @multiset_function
    def count_intersection(a):
        return (a & target).count()

    print(count_intersection(d6.pool(3)))

    target = [1]
    print(count_intersection(d6.pool(3)))
    ```

    would produce the same thing both times.

    `multiset_function` has considerable overhead, being effectively a
    mini-language within Python. For better performance, you can try
    implementing your own subclass of `MultisetEvaluator` directly.

    Args:
        func: This should take in a fixed number of multiset variables and
            output an evaluator or a nested tuple of evaluators. Tuples will
            result in a `JointEvaluator`.
    """
    parameters = inspect.signature(func, follow_wrapped=False).parameters
    for parameter in parameters.values():
        if parameter.kind not in [
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ] or parameter.default != inspect.Parameter.empty:
            raise ValueError(
                'Callable must take only a fixed number of positional arguments.'
            )
    tuple_or_evaluator = func(*(MV(i) for i in range(len(parameters))))
    evaluator = replace_tuples_with_joint_evaluator(tuple_or_evaluator)
    return update_wrapper(evaluator, func)
