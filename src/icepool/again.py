__docformat__ = 'google'

import icepool

from functools import cached_property
from typing import Callable
import operator


class AgainType(type):
    """Metaclass for Again."""

    def __add__(self, other) -> 'Again':
        return Again(operator.add, Again, other)

    def __radd__(self, other):
        return Again(operator.add, other, Again)


class Again(metaclass=AgainType):
    """Experimental: A placeholder value used to indicate that the die should be rolled again with some modification.

    Examples:

    * `Again` + 6: Roll again and add 6.
    * `Again` + `Again`: Roll again twice and sum.
    """

    def __init__(self, func: Callable, /, *args):
        """

        The supplied function will be called with the base die in place of any
        `Again`s in the `args`. This function should not itself return `Again`.
        """
        self._func = func
        self._args = args

    def _substitute_arg(self, arg, die: icepool.Die):
        if arg is Again:
            return die
        elif isinstance(arg, Again):
            return arg.evaluate(die)
        else:
            return arg

    def evaluate(self, die: icepool.Die):
        return self._func(
            *(self._substitute_arg(arg, die) for arg in self._args))

    # Operators.

    def __add__(self, other) -> 'Again':
        return Again(operator.add, self, other)

    def __radd__(self, other):
        return Again(operator.add, other, self)

    # Hashing.

    @cached_property
    def _key_tuple(self) -> tuple:
        return (self._func, self._args)

    def key_tuple(self) -> tuple:
        return self._key_tuple

    def __hash__(self):
        return hash(self.key_tuple())
