__docformat__ = 'google'

import icepool

from functools import cached_property
import operator

from typing import Any, Callable, Mapping, Sequence


class Again():
    """EXPERIMENTAL: A placeholder value used to indicate that the die should be rolled again with some modification.

    Examples:

    * `Again()` + 6: Roll again and add 6.
    * `Again(lambda x: x + 6)`: Another way of doing the same thing.
    * `Again()` + `Again()`: Roll again twice and sum.

    This can also be used as part of a return value with functions such as
    `Die.sub()`, though I don't recommend getting too fancy---it can get
    confusing very quickly.
    """

    def __init__(self, func: Callable | None = None, /, *args):
        """Creates an `Again` placeholder from the given function and args.

        Any of the args may themselves be instances of `Again`. These are
        considered to be at the same level for purposes of `again_depth`.

        The supplied function will be called with the given args, except any
        arguments of type `Again` will have resolved to the `Die` resulting
        from rolling again.
        """
        self._func = func
        self._args = args

    def _evaluate_arg(self, arg, die: 'icepool.Die'):
        if isinstance(arg, Again):
            return arg._evaluate(die)
        else:
            return arg

    def _evaluate(self, die: 'icepool.Die'):
        """Recursively substitutes the provided `Die` for the `Again` placeholders."""
        if self._func is None:
            return die
        else:
            return self._func(
                *(self._evaluate_arg(arg, die) for arg in self._args))

    # Unary operators.

    def __neg__(self) -> 'Again':
        return Again(operator.neg, self)

    def __pos__(self) -> 'Again':
        return Again(operator.pos, self)

    def __invert__(self) -> 'Again':
        return Again(operator.invert, self)

    def __abs__(self) -> 'Again':
        return Again(operator.abs, self)

    # Binary operators.

    def __add__(self, other) -> 'Again':
        return Again(operator.add, self, other)

    def __radd__(self, other) -> 'Again':
        return Again(operator.add, other, self)

    def __sub__(self, other) -> 'Again':
        return Again(operator.sub, self, other)

    def __rsub__(self, other) -> 'Again':
        return Again(operator.sub, other, self)

    def __mul__(self, other) -> 'Again':
        return Again(operator.mul, self, other)

    def __rmul__(self, other) -> 'Again':
        return Again(operator.mul, other, self)

    def __truediv__(self, other) -> 'Again':
        return Again(operator.truediv, self, other)

    def __rtruediv__(self, other) -> 'Again':
        return Again(operator.truediv, other, self)

    def __floordiv__(self, other) -> 'Again':
        return Again(operator.floordiv, self, other)

    def __rfloordiv__(self, other) -> 'Again':
        return Again(operator.floordiv, other, self)

    def __pow__(self, other) -> 'Again':
        return Again(operator.pow, self, other)

    def __rpow__(self, other) -> 'Again':
        return Again(operator.pow, other, self)

    def __mod__(self, other) -> 'Again':
        return Again(operator.mod, self, other)

    def __rmod__(self, other) -> 'Again':
        return Again(operator.mod, other, self)

    def __lshift__(self, other) -> 'Again':
        return Again(operator.lshift, self, other)

    def __rlshift__(self, other) -> 'Again':
        return Again(operator.lshift, other, self)

    def __rshift__(self, other) -> 'Again':
        return Again(operator.rshift, self, other)

    def __rrshift__(self, other) -> 'Again':
        return Again(operator.rshift, other, self)

    def __and__(self, other) -> 'Again':
        return Again(operator.and_, self, other)

    def __rand__(self, other) -> 'Again':
        return Again(operator.and_, other, self)

    def __or__(self, other) -> 'Again':
        return Again(operator.or_, self, other)

    def __ror__(self, other) -> 'Again':
        return Again(operator.or_, other, self)

    def __xor__(self, other) -> 'Again':
        return Again(operator.xor, self, other)

    def __rxor__(self, other) -> 'Again':
        return Again(operator.xor, other, self)

    def __matmul__(self, other) -> 'Again':
        return Again(operator.matmul, self, other)

    def __rmatmul__(self, other) -> 'Again':
        return Again(operator.matmul, other, self)

    # Hashing and equality.

    def __eq__(self, other):
        if not isinstance(other, Again):
            return False
        return self is other or self.key_tuple() == other.key_tuple()

    @cached_property
    def _key_tuple(self) -> tuple:
        return (self._func, self._args)

    def key_tuple(self) -> tuple:
        return self._key_tuple

    def __hash__(self):
        return hash(self.key_tuple())


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


def sub_agains(outcomes: Mapping[Any, int] | Sequence,
               die: 'icepool.Die') -> Mapping[Any, int] | Sequence:
    """Recursively substitutes all occurences of `Again` with the given Die.

    This is not applied to tuples.
    """
    if isinstance(outcomes, icepool.Die):
        # Dice should already have flattened out any Agains.
        return outcomes
    elif isinstance(outcomes, Mapping):
        return {
            _sub_agains_inner(k, die): v
            for k, v in outcomes.items()  # type: ignore
        }
    else:
        return [_sub_agains_inner(k, die) for k in outcomes]


def _sub_agains_inner(outcome, die: 'icepool.Die'):
    if isinstance(outcome, icepool.Die):
        # Dice should already have flattened out any Agains.
        return outcome
    elif isinstance(outcome, Mapping):
        return {_sub_agains_inner(k, die): v for k, v in outcome.items()}
    elif isinstance(outcome, Again):
        return outcome._evaluate(die)
    else:
        # tuple or simple arg that is not Again.
        return outcome
