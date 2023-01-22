import icepool
import icepool.evaluator

from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.expression.variable import MultisetVariable as MV

import inspect

from typing import Callable, TypeAlias, overload

from icepool.typing import T_contra, U_co

NestedTupleOrEvaluatorOrDie: TypeAlias = MultisetEvaluator[
    T_contra, U_co] | 'icepool.Die[U_co]' | tuple[
        'NestedTupleOrEvaluatorOrDie[T_contra, U_co]', ...]

NestedTupleOrOutcome: TypeAlias = U_co | tuple['NestedTupleOrOutcome[U_co]',
                                               ...]


def replace_tuples_with_joint_evaluator(
        arg: NestedTupleOrEvaluatorOrDie[T_contra, U_co],
        /) -> MultisetEvaluator[T_contra, NestedTupleOrOutcome[U_co]]:
    """Recursively replaces tuples with `JointEvaluator`s."""
    if isinstance(arg, tuple):
        return icepool.evaluator.JointEvaluator(
            *(replace_tuples_with_joint_evaluator(x) for x in arg))
    elif isinstance(arg, icepool.Die):
        # Die resulting from a fully-bound expression.
        return icepool.evaluator.ConstantEvaluator(arg)
    else:
        return arg


@overload
def multiset_function(
        func: Callable[[MV], NestedTupleOrEvaluatorOrDie[T_contra, U_co]],
        /) -> MultisetEvaluator[T_contra, NestedTupleOrOutcome[U_co]]:
    ...


@overload
def multiset_function(
        func: Callable[[MV, MV], NestedTupleOrEvaluatorOrDie[T_contra, U_co]],
        /) -> MultisetEvaluator[T_contra, NestedTupleOrOutcome[U_co]]:
    ...


@overload
def multiset_function(
        func: Callable[[MV, MV, MV], NestedTupleOrEvaluatorOrDie[T_contra,
                                                                 U_co]],
        /) -> MultisetEvaluator[T_contra, NestedTupleOrOutcome[U_co]]:
    ...


@overload
def multiset_function(
        func: Callable[[MV, MV, MV, MV], NestedTupleOrEvaluatorOrDie[T_contra,
                                                                     U_co]],
        /) -> MultisetEvaluator[T_contra, NestedTupleOrOutcome[U_co]]:
    ...


def multiset_function(
        func: Callable[..., NestedTupleOrEvaluatorOrDie[T_contra, U_co]],
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
    tuple_or_evaluator = func(*(MV(i) for i in range(len(parameters))))
    return replace_tuples_with_joint_evaluator(tuple_or_evaluator)
