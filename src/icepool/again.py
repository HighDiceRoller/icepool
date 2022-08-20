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
    """

    def __init__(self, func: Callable | None = None, /, *args):
        """

        The supplied function will be called with the base die in place of any
        `Again`s in the `args`. This function should not itself return `Again`.
        """
        self._func = func
        self._args = args

    def _substitute_arg(self, arg, die: 'icepool.Die'):
        if isinstance(arg, Again):
            return arg.evaluate(die)
        else:
            return arg

    def evaluate(self, die: 'icepool.Die'):
        if self._func is None:
            return die
        else:
            return self._func(
                *(self._substitute_arg(arg, die) for arg in self._args))

    # Operators.

    def __add__(self, other) -> 'Again':
        return Again(operator.add, self, other)

    def __radd__(self, other):
        return Again(operator.add, other, self)

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


def is_mapping(arg) -> bool:
    return hasattr(arg, 'keys') and hasattr(arg, 'values') and hasattr(
        arg, 'items') and hasattr(arg, '__getitem__')


def contains_again(outcome) -> bool:
    """Returns True iff the outcome (recursively) contains any instances of Again.

    Raises:
        TypeError if Again is nested inside a tuple.
    """
    if isinstance(outcome, icepool.Again):
        return True
    elif isinstance(outcome, Sequence):
        result = any(contains_again(x) for x in outcome)
        if result and isinstance(outcome, tuple):
            raise TypeError('tuple outcomes cannot contain Again objects.')
        return result
    else:
        return False


def sub_agains(outcomes: Mapping[Any, int] | Sequence,
               die: 'icepool.Die') -> Mapping[Any, int] | Sequence:
    """Recursively substitutes all occurences of `Again` with the given Die.

    This is not applied to tuples.
    """
    if is_mapping(outcomes):
        return {
            _sub_agains_inner(k, die): v
            for k, v in outcomes.items()  # type: ignore
        }
    else:
        return [_sub_agains_inner(k, die) for k in outcomes]


def _sub_agains_inner(outcome, die: 'icepool.Die'):
    if is_mapping(outcome):
        return {_sub_agains_inner(k, die): v for k, v in outcome.items()}
    elif isinstance(outcome, Again):
        return outcome.evaluate(die)
    else:
        # tuple or Base arg that is not Again.
        return outcome
