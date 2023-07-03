__docformat__ = 'google'

import icepool

from functools import cached_property
import operator

from typing import Any, Callable, Final, Mapping, Sequence


class AgainExpression():
    """An expression indicating that the die should be rolled again, usually with some operation applied.

    This is designed to be used with the `Die()` constructor.
    `AgainExpression`s should not be fed to functions or methods other than
    `Die()`, but it can be used with operators. Examples:

    * `Again` + 6: Roll again and add 6.
    * `Again` + `Again`: Roll again twice and sum.

    The `again_depth` and `again_end` arguments to `Die()` affect how these
    arguments are processed.

    If you want something more complex, use e.g. `Die.map()` instead.
    """

    def __init__(self,
                 function: Callable | None = None,
                 /,
                 *args,
                 truth_value: bool | None = None):
        """Constructor.

        Any of the args may themselves be instances of `Again`. These are
        considered to be at the same level for purposes of `again_depth`.

        Args:
            function: The function to apply. If not provided, the returned object
                represents the again roll directly.
            args: The arguments that will be sent to `function`, except that any
                of type `Again` will have resolved to the `Die` resulting
                from rolling again. Only applicable if `function` is provided.
            truth_value: The truth value of the resulting object, if applicable.
                You probably don't need to use this externally.
        """
        self._func = function
        self._args = args
        self._truth_value = truth_value

    def _evaluate_arg(self, arg, die: 'icepool.Die'):
        if isinstance(arg, AgainExpression):
            return arg._evaluate(die)
        else:
            return arg

    def _evaluate(self, die: 'icepool.Die'):
        """Recursively replaces the `Again` placeholders with the provided `Die`."""
        if self._func is None:
            return die
        else:
            return self._func(
                *(self._evaluate_arg(arg, die) for arg in self._args))

    # Unary operators.

    def __neg__(self) -> 'AgainExpression':
        return AgainExpression(operator.neg, self)

    def __pos__(self) -> 'AgainExpression':
        return AgainExpression(operator.pos, self)

    def __invert__(self) -> 'AgainExpression':
        return AgainExpression(operator.invert, self)

    def __abs__(self) -> 'AgainExpression':
        return AgainExpression(operator.abs, self)

    # Binary operators.

    def __add__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.add, self, other)

    def __radd__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.add, other, self)

    def __sub__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.sub, self, other)

    def __rsub__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.sub, other, self)

    def __mul__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.mul, self, other)

    def __rmul__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.mul, other, self)

    def __truediv__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.truediv, self, other)

    def __rtruediv__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.truediv, other, self)

    def __floordiv__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.floordiv, self, other)

    def __rfloordiv__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.floordiv, other, self)

    def __pow__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.pow, self, other)

    def __rpow__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.pow, other, self)

    def __mod__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.mod, self, other)

    def __rmod__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.mod, other, self)

    def __lshift__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.lshift, self, other)

    def __rlshift__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.lshift, other, self)

    def __rshift__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.rshift, self, other)

    def __rrshift__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.rshift, other, self)

    def __and__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.and_, self, other)

    def __rand__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.and_, other, self)

    def __or__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.or_, self, other)

    def __ror__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.or_, other, self)

    def __xor__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.xor, self, other)

    def __rxor__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.xor, other, self)

    def __matmul__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.matmul, self, other)

    def __rmatmul__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.matmul, other, self)

    def __lt__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.lt, self, other)

    def __le__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.le, self, other)

    def __gt__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.gt, self, other)

    def __ge__(self, other) -> 'AgainExpression':
        return AgainExpression(operator.ge, self, other)

    # Hashing and equality.

    # This returns a value with a truth value, but not a bool.
    def __eq__(self, other) -> 'AgainExpression':  # type: ignore
        if not isinstance(other, AgainExpression):
            return AgainExpression(operator.eq, self, other, truth_value=False)
        truth_value = self._key_tuple == other._key_tuple
        return AgainExpression(operator.eq,
                               self,
                               other,
                               truth_value=truth_value)

    # This returns a value with a truth value, but not a bool.
    def __ne__(self, other) -> 'AgainExpression':  # type: ignore
        if not isinstance(other, AgainExpression):
            return AgainExpression(operator.ne, self, other, truth_value=True)
        truth_value = self._key_tuple != other._key_tuple
        return AgainExpression(operator.ne,
                               self,
                               other,
                               truth_value=truth_value)

    def __bool__(self) -> bool:
        if self._truth_value is None:
            raise ValueError(
                'An `Again` only has a truth value if it is the result of == or !=.'
            )
        return self._truth_value

    @cached_property
    def _key_tuple(self) -> tuple:
        return (self._func, self._args)

    def __hash__(self) -> int:
        return hash(self._key_tuple)


def contains_again(outcomes: Mapping[Any, int] | Sequence) -> bool:
    """Returns True iff the outcome (recursively) contains any instances of Again."""
    if isinstance(outcomes, icepool.Die):
        # Dice should already have flattened out any Agains.
        return False
    return any(isinstance(x, icepool.AgainExpression) for x in outcomes)


def replace_agains(outcomes: Mapping[Any, int] | Sequence,
                   die: 'icepool.Die') -> Mapping[Any, int] | Sequence:
    """Recursively replaces all occurences of `Again` with the given Die.

    This is not applied to tuples.
    """
    if isinstance(outcomes, icepool.Die):
        # Dice should already have flattened out any Agains.
        return outcomes
    elif isinstance(outcomes, Mapping):
        return {_replace_agains_inner(k, die): v for k, v in outcomes.items()}
    else:
        return [_replace_agains_inner(k, die) for k in outcomes]


def _replace_agains_inner(outcome, die: 'icepool.Die'):
    if isinstance(outcome, AgainExpression):
        return outcome._evaluate(die)
    else:
        # tuple or simple arg that is not Again.
        return outcome
