__docformat__ = 'google'

import icepool
import icepool.math
from icepool.collections import Counts

import itertools
import math
from collections import defaultdict
from functools import cache, cached_property


def Pool(*dice):
    """Creates a pool from the given dice.

    Empty dice are dropped.

    Returns:
        A `PoolInternal` object.
    """
    dice = [icepool.Die(die) for die in dice]
    num_dice = len(dice)
    dice_counts = defaultdict(int)
    for die in dice:
        if not die.is_empty():
            dice_counts[die] += 1
    count_dice = (1,) * num_dice
    return PoolInternal(dice_counts, count_dice)


def count_dice_tuple(num_dice, count_dice):
    """Expresses `count_dice` as a tuple.

    See `Pool.set_count_dice()` for details.

    Args:
        `num_dice`: An `int` specifying the number of dice.
        `count_dice`: Raw specification for how the dice are to be counted.
    Raises:
        `ValueError` if:
            * More than one `Ellipsis` is used.
            * An `Ellipsis` is used in the center with too few `num_dice`.
    """
    if count_dice is None:
        return (1,) * num_dice
    elif isinstance(count_dice, int):
        result = [0] * num_dice
        result[count_dice] = 1
        return tuple(result)
    elif isinstance(count_dice, slice):
        if count_dice.step is not None:
            # "Step" is not useful here, so we repurpose it to set the number
            # of dice.
            num_dice = count_dice.step
            count_dice = slice(count_dice.start, count_dice.stop)
        result = [0] * num_dice
        result[count_dice] = [1] * len(result[count_dice])
        return tuple(result)
    else:
        split = None
        for i, x in enumerate(count_dice):
            if x is Ellipsis:
                if split is None:
                    split = i
                else:
                    raise ValueError(
                        'Cannot use more than one Ellipsis (...) for count_dice.'
                    )

        if split is None:
            return tuple(count_dice)

        extra_dice = num_dice - len(count_dice) + 1

        if split == 0:
            # Ellipsis on left.
            count_dice = count_dice[1:]
            if extra_dice < 0:
                return tuple(count_dice[-extra_dice:])
            else:
                return (0,) * extra_dice + tuple(count_dice)
        elif split == len(count_dice) - 1:
            # Ellipsis on right.
            count_dice = count_dice[:-1]
            if extra_dice < 0:
                return tuple(count_dice[:extra_dice])
            else:
                return tuple(count_dice) + (0,) * extra_dice
        else:
            # Ellipsis in center.
            if extra_dice < 0:
                result = [0] * num_dice
                for i in range(min(split, num_dice)):
                    result[i] += count_dice[i]
                reverse_split = split - len(count_dice)
                for i in range(-1, max(reverse_split - 1, -num_dice - 1), -1):
                    result[i] += count_dice[i]
                return tuple(result)
            else:
                return tuple(count_dice[:split]) + (0,) * extra_dice + tuple(
                    count_dice[split + 1:])


def standard_pool(*die_sizes):
    return Pool(*(icepool.d(x) for x in die_sizes))


def iter_die_pop_min(die, num_dice, min_outcome):
    """
    Args:
        die: The die to pop.
        die_count: The number of this kind of die.
        min_outcome: The outcome to pop. This is <= the die's min outcome.

    Yields:
        The popped die.
        The number of remaining dice of this kind.
        The number of dice that rolled max_outcome.
        The weight of this number of dice rolling max_outcome.
    """
    if die.min_outcome() != min_outcome:
        left_count = num_dice
        rolled_count = 0
        weight = 1
        yield die, left_count, rolled_count, weight
        return

    popped_die, single_weight = die._pop_min()

    if popped_die.is_empty():
        # This is the last outcome. All dice must roll this outcome.
        left_count = 0
        rolled_count = num_dice
        weight = single_weight**num_dice
        yield popped_die, left_count, rolled_count, weight
        return

    comb_row = icepool.math.comb_row(num_dice, single_weight)
    for rolled_count, weight in enumerate(comb_row):
        left_count = num_dice - rolled_count
        yield popped_die, left_count, rolled_count, weight


def iter_die_pop_max(die, num_dice, max_outcome):
    """
    Args:
        die: The die to pop.
        die_count: The number of this kind of die.
        max_outcome: The outcome to pop. This is >= the die's max outcome.

    Yields:
        The popped die.
        The number of remaining dice of this kind.
        The number of dice that rolled max_outcome.
        The weight of this number of dice rolling max_outcome.
    """
    if die.max_outcome() != max_outcome:
        left_count = num_dice
        rolled_count = 0
        weight = 1
        yield die, left_count, rolled_count, weight
        return

    popped_die, single_weight = die._pop_max()

    if popped_die.is_empty():
        # This is the last outcome. All dice must roll this outcome.
        left_count = 0
        rolled_count = num_dice
        weight = single_weight**num_dice
        yield popped_die, left_count, rolled_count, weight
        return

    comb_row = icepool.math.comb_row(num_dice, single_weight)
    for rolled_count, weight in enumerate(comb_row):
        left_count = num_dice - rolled_count
        yield popped_die, left_count, rolled_count, weight


@cache
def new_pool(cls, counts_arg, count_dice):
    self = super(PoolInternal, cls).__new__(cls)
    self._dice = Counts(counts_arg)
    self._count_dice = count_dice
    return self


class PoolInternal():
    """Represents a set of unordered dice, only distinguished by the outcomes they roll.

    This should be used in conjunction with `EvalPool` to generate a result.
    """

    def __new__(cls, dice_counts, count_dice):
        """This should not be called directly. Use `Pool() or Die.pool()` to construct a pool.

        Args:
            dice_counts: At this point, this is a map from dice to counts, with
                no empty dice.
            count_dice: At this point, this is a tuple with length equal to the
                number of dice.
        """
        counts_arg = tuple(
            sorted(dice_counts.items(), key=lambda kv: kv[0].key_tuple()))
        return new_pool(cls, counts_arg, count_dice)

    @cached_property
    def _num_dice(self):
        return sum(self._dice.values())

    def num_dice(self):
        """The number of dice in this pool."""
        return self._num_dice

    def is_empty(self):
        return len(self._dice) == 0

    @cached_property
    def _denominator(self):
        """The product of the total dice weights in this pool."""
        return math.prod(
            die.denominator()**count for die, count in self._dice.items())

    def denominator(self):
        return self._denominator

    @cached_property
    def _dice_tuple(self):
        return sum((die,) * count for die, count in self._dice.items())

    def count_dice(self):
        return self._count_dice

    def set_count_dice(self, count_dice):
        """Returns a pool with the selected dice counted.

        You can use `pool[count_dice]` for the same effect as this method.

        The dice are sorted in ascending order for this purpose,
        regardless of which order the outcomes are evaluated in.

        This is always an absolute selection on all `num_dice`,
        not a relative selection on already-selected dice,
        which would be ambiguous in the presence of multiple or negative counts.

        For example, here are some ways of selecting the two highest dice out of 5:

        * `pool[3:5]`
        * `pool[3:]`
        * `pool[-2:]`
        * `pool[..., 1, 1]`

        These will also select the two highest dice out of 5, and will also
        resize the pool to 5 dice first:

        * `pool[3::5]`
        * `pool[3:5:5]`
        * `pool[-2::5]`
        * `pool[0, 0, 0, 1, 1]`

        These will count the highest as a positive and the lowest as a negative:

        * `pool[-1, 0, 0, 0, 1]`
        * `pool[-1, ..., 1]`

        Args:
            `None`: All dice will be counted once.
            An `int`. This will count only the die at the specified index (once).
                In this case, the result will be a `Die`, not a pool.
            A `slice`. The selected dice are counted once each.
                If provided, the third argument resizes the pool,
                rather than being a step; however, this is only valid if the
                pool consists of a single type of die.
            A sequence of one `int`s for each die.
                Each die is counted that many times, which could be multiple or
                negative times. This may resize the pool, but only if the
                pool consists of a single type of die.

                Up to one `Ellipsis` (`...`) may be used.
                If an `Ellipsis` is used, the size of the pool won't change. Instead:

                * If `count_dice` is shorter than `num_dice`, the `Ellipsis`
                    acts as enough zero counts to make up the difference.
                    E.g. `pool[1, ..., 1]` on five dice would act as `pool[1, 0, 0, 0, 1]`.
                * If `count_dice` has length equal to `num_dice`, the `Ellipsis` has no effect.
                    E.g. `pool[1, ..., 1]` on two dice would act as `pool[1, 1]`.
                * If `count_dice` is longer than `num_dice` and the `Ellipsis` is on one side,
                    elements will be dropped from `count_dice` on the side with the `Ellipsis`.
                    E.g. `pool[..., 1, 2, 3]` on two dice would act as `pool[2, 3]`.
                * If `count_dice` is longer than `num_dice` and the `Ellipsis`
                    is in the middle, the counts will be as the sum of two
                    one-sided `Ellipsis`.
                    E.g. `pool[-1, ..., 1]` acts like `[-1, ...]` plus `[..., 1]`.
                    On a pool consisting of a single single die this would have
                    the -1 and 1 cancel each other out.

        Raises:
            ValueError:  If `count_dice` would change the size of a pool with
                more than one type of die, or if more than one `Ellipsis`
                is used.
        """
        convert_to_die = isinstance(count_dice, int)
        count_dice = count_dice_tuple(self.num_dice(), count_dice)
        if len(count_dice) != self.num_dice():
            if len(self._dice) != 1:
                raise ValueError(
                    'Cannot change the size of a pool unless it has exactly one type of die.'
                )
            dice = Counts([(self._dice.keys()[0], len(count_dice))])
            result = PoolInternal(dice, count_dice)
        else:
            result = PoolInternal(self._dice, count_dice)
        if convert_to_die:
            return result.eval(lambda state, outcome, count: outcome
                               if count else state)
        else:
            return result

    __getitem__ = set_count_dice

    @cached_property
    def _min_outcome(self):
        return max(die.min_outcome() for die in self._dice.keys())

    def min_outcome(self):
        """Returns the max outcome among all dice in this pool."""
        return self._min_outcome

    @cached_property
    def _max_outcome(self):
        return max(die.max_outcome() for die in self._dice.keys())

    def max_outcome(self):
        """Returns the max outcome among all dice in this pool."""
        return self._max_outcome

    def _pop_min(self, min_outcome):
        """
        Yields:
            popped_pool: The pool after the min outcome is popped.
            net_count: The number of dice that rolled the min outcome, after
                accounting for count_dice.
            net_weight: The weight of this incremental result.
        """
        if self.is_empty():
            yield self, 0, 1
            return
        generators = [
            iter_die_pop_min(die, die_count, min_outcome)
            for die, die_count in self._dice.items()
        ]
        for pop in itertools.product(*generators):
            net_rolled_count = 0
            result_weight = 1
            next_dice_counts = defaultdict(int)
            for popped_die, left_count, rolled_count, weight in pop:
                if not popped_die.is_empty():
                    next_dice_counts[popped_die] += left_count
                net_rolled_count += rolled_count
                result_weight *= weight
            if net_rolled_count == 0:
                result_count = 0
                popped_count_dice = self.count_dice()
            else:
                result_count = sum(self.count_dice()[:net_rolled_count])
                popped_count_dice = self.count_dice()[net_rolled_count:]
            popped_pool = PoolInternal(next_dice_counts, popped_count_dice)
            if not any(popped_count_dice):
                # Dump all dice in exchange for the denominator.
                result_weight *= popped_pool.denominator()
                popped_pool = PoolInternal({}, ())

            yield popped_pool, result_count, result_weight

    def _pop_max(self, max_outcome):
        """
        Yields:
            popped_pool: The pool after the max outcome is popped.
            net_count: The number of dice that rolled the max outcome, after
                accounting for count_dice.
            net_weight: The weight of this incremental result.
        """
        if self.is_empty():
            yield self, 0, 1
            return
        generators = [
            iter_die_pop_max(die, die_count, max_outcome)
            for die, die_count in self._dice.items()
        ]
        for pop in itertools.product(*generators):
            net_rolled_count = 0
            result_weight = 1
            next_dice_counts = defaultdict(int)
            for popped_die, left_count, rolled_count, weight in pop:
                if not popped_die.is_empty():
                    next_dice_counts[popped_die] += left_count
                net_rolled_count += rolled_count
                result_weight *= weight
            if net_rolled_count == 0:
                result_count = 0
                popped_count_dice = self.count_dice()
            else:
                result_count = sum(self.count_dice()[-net_rolled_count:])
                popped_count_dice = self.count_dice()[:-net_rolled_count]
            popped_pool = PoolInternal(next_dice_counts, popped_count_dice)
            if not any(popped_count_dice):
                # Dump all dice in exchange for the denominator.
                result_weight *= popped_pool.denominator()
                popped_pool = PoolInternal({}, ())

            yield popped_pool, result_count, result_weight

    def eval(self, eval_or_func, /):
        """Evaluates this pool using the given `EvalPool` or function.
        Note that each `EvalPool` instance carries its own cache;
        if you plan to use an evaluation multiple times,
        you may want to explicitly create an `EvalPool` instance
        rather than passing a function to this method directly.
        Args:
            func: This can be an `EvalPool`, in which case it evaluates the pool
                directly. Or it can be a `EvalPool.next_state()`-like function,
                taking in `state, outcome, *counts` and returning the next state.
                In this case a temporary `WrapFuncEval` is constructed and used
                to evaluate this pool.
        """
        if not isinstance(eval_or_func, icepool.EvalPool):
            eval_or_func = icepool.WrapFuncEval(eval_or_func)
        return eval_or_func.eval(self)

    def sum(self):
        """Convenience method to simply sum the dice in this pool.
        This uses `icepool.sum_pool`.
        Returns:
            A die representing the sum.
        """
        return icepool.sum_pool(self)

    def __str__(self):
        return str(self._key_tuple)

    @cached_property
    def _key_tuple(self):
        return tuple((die.key_tuple(), count)
                     for die, count in self._dice.items()), self._count_dice

    def __eq__(self, other):
        if not isinstance(other, PoolInternal):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self):
        return hash(self._key_tuple)

    def __hash__(self):
        return self._hash