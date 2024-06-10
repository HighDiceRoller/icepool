__docformat__ = 'google'

import icepool

from functools import cache, cached_property
import operator

from typing import Any, Callable, Final, Mapping, Sequence


class AgainExpression():
    """An expression indicating that the die should be rolled again, usually with some operation applied.

    See the `Again` symbol for the full documentation.
    """

    def __init__(self,
                 function: Callable | None = None,
                 /,
                 *args,
                 truth_value: bool | None = None,
                 is_additive: bool = False):
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
            is_additive: Whether the expression is compatible with `again_count`.
        """
        self._func = function
        self._args = args
        self._truth_value = truth_value
        self.is_additive = is_additive

    @staticmethod
    def _evaluate_arg(arg, die: 'icepool.Die'):
        if isinstance(arg, AgainExpression):
            return arg._evaluate(die)
        else:
            return arg

    def _evaluate(self, die: 'icepool.Die'):
        """Recursively replaces the `Again` placeholders with the provided `Die`."""
        if self._func is None:
            return die
        else:
            return self._func(*(self._evaluate_arg(arg, die)
                                for arg in self._args))

    @staticmethod
    def _again_count_arg(arg):
        if isinstance(arg, AgainExpression):
            return arg._again_count()
        else:
            return 0

    def _again_count(self) -> int:
        """Counts the total number of Agains in the expression.
        
        Only works on additive expressions.
        """
        if self._func is None:
            return 1
        else:
            return self._func(*(self._again_count_arg(arg)
                                for arg in self._args))

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
        is_additive = self.is_additive
        if isinstance(other, AgainExpression):
            is_additive &= other.is_additive
        return AgainExpression(operator.add,
                               self,
                               other,
                               is_additive=is_additive)

    def __radd__(self, other) -> 'AgainExpression':
        is_additive = self.is_additive
        if isinstance(other, AgainExpression):
            is_additive &= other.is_additive
        return AgainExpression(operator.add,
                               other,
                               self,
                               is_additive=is_additive)

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
        is_additive = self.is_additive
        if isinstance(other, icepool.Population):
            is_additive &= (other.min_outcome() >= 0)
        elif isinstance(other, AgainExpression):
            is_additive = False
        return AgainExpression(operator.matmul,
                               other,
                               self,
                               is_additive=is_additive)

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
        truth_value = self._hash_key == other._hash_key
        return AgainExpression(operator.eq,
                               self,
                               other,
                               truth_value=truth_value)

    # This returns a value with a truth value, but not a bool.
    def __ne__(self, other) -> 'AgainExpression':  # type: ignore
        if not isinstance(other, AgainExpression):
            return AgainExpression(operator.ne, self, other, truth_value=True)
        truth_value = self._hash_key != other._hash_key
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
    def _hash_key(self) -> tuple:
        return (self._func, self._args)

    def __hash__(self) -> int:
        return hash(self._hash_key)


def contains_again(outcomes: Mapping[Any, int] | Sequence) -> bool:
    """Returns True iff the outcome (recursively) contains any instances of Again."""
    if isinstance(outcomes, icepool.Die):
        # Dice should already have flattened out any Agains.
        return False
    return any(isinstance(x, icepool.AgainExpression) for x in outcomes)


def compute_not_again_die(outcomes: Sequence,
                          times: Sequence[int]) -> 'icepool.Die':
    """Returns a Die with the Again expressions filtered out."""
    filtered = ((outcome, quantity)
                for outcome, quantity in zip(outcomes, times)
                if outcome is not icepool.Reroll
                and not isinstance(outcome, AgainExpression))
    return icepool.Die(*zip(*filtered))


def evaluate_agains_using_count(outcomes: Sequence, times: Sequence[int],
                                again_count: int) -> 'icepool.Die':
    if again_count < 0:
        raise ValueError('again_count cannot be negative.')

    not_again_die = compute_not_again_die(outcomes, times)

    zero = not_again_die.zero_outcome()

    def make_step_outcome(outcome, zero):
        """add_flat, add_terminal, add_again"""
        if isinstance(outcome, AgainExpression):
            if not outcome.is_additive:
                raise ValueError(
                    'again_count mode cannot be used with a non-additive AgainExpression.'
                )
            return icepool.tupleize(outcome._evaluate(zero), 0,
                                    outcome._again_count() - 1)
        else:
            return icepool.tupleize(zero, 1, -1)

    step_die: icepool.Die = icepool.Die(
        [make_step_outcome(outcome, zero) for outcome in outcomes], times)

    def step(flat, terminal, again, index, roll):
        if again == 0:
            return flat, terminal, again, index
        add_flat, add_terminal, add_again = roll
        flat += add_flat
        terminal += add_terminal
        again += add_again
        index += 1
        if index + again > again_count + 1:
            return icepool.Reroll
        return flat, terminal, again, index

    initial_state: icepool.Die = icepool.Die([(zero, 0, 1, 0)])

    final_state: icepool.Die = initial_state.map(step,
                                                 step_die,
                                                 star=True,
                                                 repeat=again_count + 1)

    def finalize(flat, terminal, again, index):
        return flat + terminal @ not_again_die

    return final_state.map(finalize, star=True)


def evaluate_agains_using_depth(outcomes: Sequence, times: Sequence[int],
                                again_depth: int, again_end) -> 'icepool.Die':
    if again_depth < 0:
        raise ValueError('again_depth cannot be negative.')

    if again_end is None:
        again_end = compute_not_again_die(outcomes, times).zero_outcome()

    def replace_again(outcome):
        if isinstance(outcome, AgainExpression):
            if again_end is icepool.Reroll:
                return icepool.Reroll
            else:
                return outcome._evaluate(again_end)
        else:
            # tuple or simple arg that is not Again.
            return outcome

    tail: icepool.Die = icepool.Die(
        [replace_again(outcome) for outcome in outcomes], times)

    for _ in range(again_depth):
        tail = icepool.Die(outcomes, times, again_depth=0, again_end=tail)
    return tail
