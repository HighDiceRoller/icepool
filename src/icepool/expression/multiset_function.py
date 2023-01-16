import icepool.evaluator

from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.expression.variable import MultisetVariable as MV

import inspect

from typing import Callable, TypeAlias, overload

from icepool.typing import T_contra, U_co

NestedTupleOrEvaluator: TypeAlias = MultisetEvaluator[T_contra, U_co] | tuple[
    'NestedTupleOrEvaluator[T_contra, U_co]', ...]

NestedTupleOrOutcome: TypeAlias = U_co | tuple['NestedTupleOrOutcome[U_co]',
                                               ...]


def replace_tuples_with_joint_evaluator(
        tuple_or_evaluator: NestedTupleOrEvaluator[T_contra, U_co],
        /) -> MultisetEvaluator[T_contra, NestedTupleOrOutcome[U_co]]:
    """Recursively replaces tuples with `JointEvaluator`s."""
    if isinstance(tuple_or_evaluator, tuple):
        return icepool.evaluator.JointEvaluator(*(
            replace_tuples_with_joint_evaluator(x) for x in tuple_or_evaluator))
    else:
        return tuple_or_evaluator


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
    """EXPERIMENTAL: Creates an evaluator from a callable.

    For example, to create an evaluator which computes the elements each of two
    multisets has that the other doesn't:

    ```
    multiset_function(lambda a, b: ((a - b).expand(),
                                    (b - a).expand()))
    ```

    Any globals inside `func` are effectively bound at the time
    `multiset_function(func)` is called. Note that this is different than how
    ordinary Python closures behave. For example,

    ```
    target = [1, 2, 3]
    evaluator = multiset_function(lambda a: (a & target).count())
    print(evaluator.evaluate(d6.pool(3)))

    target = [1]
    print(evaluator.evaluate(d6.pool(3)))
    ```

    would produce the same thing both times.

    Args:
        func: This should take in multiset variables and output an evaluator
            or a nested tuple of evaluators. Tuples will produce a
            `JointEvaluator`.
    """
    parameters = inspect.signature(func).parameters
    for parameter in parameters.values():
        if parameter.kind not in [
                inspect.Parameter.POSITIONAL_ONLY or
                inspect.Parameter.POSITIONAL_OR_KEYWORD
        ] or parameter.default != inspect.Parameter.empty:
            raise ValueError(
                'Callable must take only a fixed number of positional arguments.'
            )
    tuple_or_evaluator = func(
        *icepool.expression.multiset_variables[:len(parameters)])
    return replace_tuples_with_joint_evaluator(tuple_or_evaluator)
