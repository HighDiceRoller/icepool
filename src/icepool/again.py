__docformat__ = 'google'

import icepool

from functools import cached_property
import operator

from typing import Any, Callable, Mapping, Sequence


class Again():
    """A placeholder value used to indicate that the die should be rolled again.

    This is designed to be used with the `Die()` constructor.
    `Again` should not be fed to functions or methods other than `Die()`, but
    it can be used with operators. Examples:

    * `Again()` + 6: Roll again and add 6.
    * `Again()` + `Again()`: Roll again twice and sum.

    The `again_depth` and `again_end` arguments to `Die()` affect how these
    arguments are processed.

    If you want something more complex, use e.g. `Die.map()` instead.
    """

    def __init__(self):
        """Creates an `Again` placeholder from the given function and args. """
        self._func = None
        self._args = ()
        self._truth_value = None

    @classmethod
    def _new_internal(cls,
                      func: Callable | None = None,
                      /,
                      *args,
                      truth_value: bool | None = None) -> 'Again':
        """Extra arguments for implementing expressions containing Again.

        Any of the args may themselves be instances of `Again`. These are
        considered to be at the same level for purposes of `again_depth`.

        Args:
            func: The function to apply. If not provided, the returned object
                represents the again roll directly.
            args: The arguments that will be sent to `func`, except that any
                of type `Again` will have resolved to the `Die` resulting
                from rolling again. Only applicable if `func` is provided.
            truth_value: The truth value of the resulting object, if applicable.
                You probably don't need to use this externally.
        """
        self = super(Again, cls).__new__(cls)
        self._func = func
        self._args = args
        self._truth_value = truth_value
        return self

    def _evaluate_arg(self, arg, die: 'icepool.Die'):
        if isinstance(arg, Again):
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

    def __neg__(self) -> 'Again':
        return Again._new_internal(operator.neg, self)

    def __pos__(self) -> 'Again':
        return Again._new_internal(operator.pos, self)

    def __invert__(self) -> 'Again':
        return Again._new_internal(operator.invert, self)

    def __abs__(self) -> 'Again':
        return Again._new_internal(operator.abs, self)

    # Binary operators.

    def __add__(self, other) -> 'Again':
        return Again._new_internal(operator.add, self, other)

    def __radd__(self, other) -> 'Again':
        return Again._new_internal(operator.add, other, self)

    def __sub__(self, other) -> 'Again':
        return Again._new_internal(operator.sub, self, other)

    def __rsub__(self, other) -> 'Again':
        return Again._new_internal(operator.sub, other, self)

    def __mul__(self, other) -> 'Again':
        return Again._new_internal(operator.mul, self, other)

    def __rmul__(self, other) -> 'Again':
        return Again._new_internal(operator.mul, other, self)

    def __truediv__(self, other) -> 'Again':
        return Again._new_internal(operator.truediv, self, other)

    def __rtruediv__(self, other) -> 'Again':
        return Again._new_internal(operator.truediv, other, self)

    def __floordiv__(self, other) -> 'Again':
        return Again._new_internal(operator.floordiv, self, other)

    def __rfloordiv__(self, other) -> 'Again':
        return Again._new_internal(operator.floordiv, other, self)

    def __pow__(self, other) -> 'Again':
        return Again._new_internal(operator.pow, self, other)

    def __rpow__(self, other) -> 'Again':
        return Again._new_internal(operator.pow, other, self)

    def __mod__(self, other) -> 'Again':
        return Again._new_internal(operator.mod, self, other)

    def __rmod__(self, other) -> 'Again':
        return Again._new_internal(operator.mod, other, self)

    def __lshift__(self, other) -> 'Again':
        return Again._new_internal(operator.lshift, self, other)

    def __rlshift__(self, other) -> 'Again':
        return Again._new_internal(operator.lshift, other, self)

    def __rshift__(self, other) -> 'Again':
        return Again._new_internal(operator.rshift, self, other)

    def __rrshift__(self, other) -> 'Again':
        return Again._new_internal(operator.rshift, other, self)

    def __and__(self, other) -> 'Again':
        return Again._new_internal(operator.and_, self, other)

    def __rand__(self, other) -> 'Again':
        return Again._new_internal(operator.and_, other, self)

    def __or__(self, other) -> 'Again':
        return Again._new_internal(operator.or_, self, other)

    def __ror__(self, other) -> 'Again':
        return Again._new_internal(operator.or_, other, self)

    def __xor__(self, other) -> 'Again':
        return Again._new_internal(operator.xor, self, other)

    def __rxor__(self, other) -> 'Again':
        return Again._new_internal(operator.xor, other, self)

    def __matmul__(self, other) -> 'Again':
        return Again._new_internal(operator.matmul, self, other)

    def __rmatmul__(self, other) -> 'Again':
        return Again._new_internal(operator.matmul, other, self)

    def __lt__(self, other) -> 'Again':
        return Again._new_internal(operator.lt, self, other)

    def __le__(self, other) -> 'Again':
        return Again._new_internal(operator.le, self, other)

    def __gt__(self, other) -> 'Again':
        return Again._new_internal(operator.gt, self, other)

    def __ge__(self, other) -> 'Again':
        return Again._new_internal(operator.ge, self, other)

    # Hashing and equality.

    # This returns a value with a truth value, but not a bool.
    def __eq__(self, other) -> 'Again':  # type: ignore
        if not isinstance(other, Again):
            return Again._new_internal(operator.eq,
                                       self,
                                       other,
                                       truth_value=False)
        truth_value = self._key_tuple == other._key_tuple
        return Again._new_internal(operator.eq,
                                   self,
                                   other,
                                   truth_value=truth_value)

    # This returns a value with a truth value, but not a bool.
    def __ne__(self, other) -> 'Again':  # type: ignore
        if not isinstance(other, Again):
            return Again._new_internal(operator.ne,
                                       self,
                                       other,
                                       truth_value=True)
        truth_value = self._key_tuple != other._key_tuple
        return Again._new_internal(operator.ne,
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
    """Returns True iff the outcome (recursively) contains any instances of Again.

    Raises:
        TypeError if Again is nested inside a tuple.
    """
    if isinstance(outcomes, icepool.Die):
        # Dice should already have flattened out any Agains.
        return False
    return any(_contains_again_inner(x) for x in outcomes)


def _contains_again_inner(outcome) -> bool:
    if isinstance(outcome, icepool.Die):
        # Dice should already have flattened out any Agains.
        return False
    elif isinstance(outcome, Mapping):
        return any(_contains_again_inner(x) for x in outcome)
    elif isinstance(outcome, icepool.Again):
        return True
    elif isinstance(outcome, tuple):
        if any(_contains_again_inner(x) for x in outcome):
            raise TypeError('tuple outcomes cannot contain Again objects.')
        return False
    else:
        return False


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
    if isinstance(outcome, icepool.Die):
        # Dice should already have flattened out any Agains.
        return outcome
    elif isinstance(outcome, Mapping):
        return {_replace_agains_inner(k, die): v for k, v in outcome.items()}
    elif isinstance(outcome, Again):
        return outcome._evaluate(die)
    else:
        # tuple or simple arg that is not Again.
        return outcome
