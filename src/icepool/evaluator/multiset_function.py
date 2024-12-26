import itertools
import icepool
import icepool.evaluator

from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.multiset_variable import MultisetVariable as MV

import inspect
from functools import cached_property, update_wrapper

from typing import Callable, Collection, TypeAlias, overload

from icepool.order import Order
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

    Any globals inside `function` are effectively bound at the time
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

    would produce the same thing both times. Likewise, the function should not
    have any side effects.

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
    for parameter in parameters.values():
        if parameter.kind not in [
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ] or parameter.default != inspect.Parameter.empty:
            raise ValueError(
                'Callable must take only a fixed number of positional arguments.'
            )
    tuple_or_evaluator = function(*(MV(index=i)
                                    for i in range(len(parameters))))
    evaluator = replace_tuples_with_joint_evaluator(tuple_or_evaluator)
    return update_wrapper(evaluator, function)


class MultisetFunctionEvaluator(MultisetEvaluator[T, U_co]):
    """Assigns an expression to be evaluated first to each input of an evaluator."""

    def __init__(self,
                 *expressions:
                 'icepool.multiset_expression.MultisetExpression[T]',
                 evaluator: MultisetEvaluator[T, U_co],
                 truth_value: bool | None = None) -> None:
        self._evaluator = evaluator
        self._bound_generators = tuple(
            itertools.chain.from_iterable(expression._bound_generators
                                          for expression in expressions))
        self._bound_arity = len(self._bound_generators)
        self._free_arity = max(
            (expression._free_arity() for expression in expressions),
            default=0)

        unbound_expressions: 'list[icepool.expression.MultisetExpression[T]]' = []
        extra_start = 0
        for expression in expressions:
            unbound_expression, extra_start = expression._unbind(extra_start)
            unbound_expressions.append(unbound_expression)
        self._expressions = tuple(unbound_expressions)
        self._truth_value = truth_value
        raise NotImplementedError()

    def next_state(self, state, outcome, *counts):
        if state is None:
            expression_states = (None, ) * len(self._expressions)
            evaluator_state = None
        else:
            expression_states, evaluator_state = state

        extra_counts = counts[:len(self._evaluator.extra_generators())]
        counts = counts[len(self._evaluator.extra_generators()):]

        expression_states, expression_counts = zip(
            *(expression._next_state(expression_state, outcome, *counts)
              for expression, expression_state in zip(self._expressions,
                                                      expression_states)))
        evaluator_state = self._evaluator.next_state(evaluator_state, outcome,
                                                     *extra_counts,
                                                     *expression_counts)
        return expression_states, evaluator_state

    def final_outcome(
            self,
            final_state) -> 'U_co | icepool.Die[U_co] | icepool.RerollType':
        if final_state is None:
            return self._evaluator.final_outcome(None)
        else:
            _, evaluator_state = final_state
        return self._evaluator.final_outcome(evaluator_state)

    def order(self) -> Order:
        expression_order = Order.merge(*(expression.order()
                                         for expression in self._expressions))
        return Order.merge(expression_order, self._evaluator.order())

    def extra_outcomes(self, *generators) -> Collection[T]:
        return self._evaluator.extra_outcomes(*generators)

    @cached_property
    def _extra_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._bound_generators + self._evaluator.extra_generators()

    def extra_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._extra_generators

    def validate_arity(self, arity: int) -> None:
        if arity < self._free_arity:
            raise ValueError(
                f'Expected arity of {self._free_arity}, got {arity}.')

    def __bool__(self) -> bool:
        if self._truth_value is None:
            raise TypeError(
                'MultisetExpression only has a truth value if it is the result of the == or != operator.'
            )
        return self._truth_value

    def __str__(self) -> str:
        input_string = f'{self._bound_arity} bound, {self._free_arity} free'
        if len(self._expressions) == 1:
            expression_string = f'{self._expressions[0]}'
        else:
            expression_string = ', '.join(
                str(expression) for expression in self._expressions)
        output_string = str(self._evaluator)
        return f'Expression: {input_string} -> {expression_string} -> {output_string}'
