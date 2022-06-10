__docformat__ = 'google'

import icepool
import icepool.math
from icepool.collections import Counts

import itertools
import math
from collections import defaultdict
from functools import cache, cached_property

from typing import Any, Callable, Generator
from collections.abc import Collection, MutableMapping, Sequence


def count_dice_tuple(
        num_dice: int,
        count_dice: int | slice | tuple[int, ...] | None) -> tuple[int, ...]:
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


def standard_pool(*die_sizes: int) -> 'Pool':
    """Returns a pool of standard dice.

    Args:
        *die_sizes: For each of these die_size X, the pool will contain one dX.
    """
    return Pool(*(icepool.d(x) for x in die_sizes))


def iter_die_pop_min(
        die: 'icepool.Die', num_dice: int, min_outcome
) -> Generator[tuple['icepool.Die', int, int, int], None, None]:
    """Helper function to iterate over the possibilities of several identical dice rolling a min outcome.

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
        num_remain = num_dice
        num_rolled = 0
        weight = 1
        yield die, num_remain, num_rolled, weight
        return

    popped_die, single_weight = die._pop_min()

    if popped_die.is_empty():
        # This is the last outcome. All dice must roll this outcome.
        num_remain = 0
        num_rolled = num_dice
        weight = single_weight**num_dice
        yield popped_die, num_remain, num_rolled, weight
        return

    comb_row = icepool.math.comb_row(num_dice, single_weight)
    for num_rolled, weight in enumerate(comb_row):
        num_remain = num_dice - num_rolled
        yield popped_die, num_remain, num_rolled, weight


def iter_die_pop_max(
        die: 'icepool.Die', num_dice: int, max_outcome
) -> Generator[tuple['icepool.Die', int, int, int], None, None]:
    """Helper function to iterate over the possibilities of several identical dice rolling a max outcome.

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
        num_remain = num_dice
        num_rolled = 0
        weight = 1
        yield die, num_remain, num_rolled, weight
        return

    popped_die, single_weight = die._pop_max()

    if popped_die.is_empty():
        # This is the last outcome. All dice must roll this outcome.
        num_remain = 0
        num_rolled = num_dice
        weight = single_weight**num_dice
        yield popped_die, num_remain, num_rolled, weight
        return

    comb_row = icepool.math.comb_row(num_dice, single_weight)
    for num_rolled, weight in enumerate(comb_row):
        num_remain = num_dice - num_rolled
        yield popped_die, num_remain, num_rolled, weight


@cache
def new_pool_cached(cls, sorted_num_dices: Sequence[tuple['icepool.Die', int]],
                    count_dice: tuple[int, ...]) -> 'Pool':
    """Creates a new pool. This function is cached.

    Args:
        cls: The pool class.
        sorted_num_dices: A sorted sequence of (die, num_dice) pairs.
        count_dice: A tuple of length equal to the number of dice.
    """
    self = super(Pool, cls).__new__(cls)
    self._dice = Counts(sorted_num_dices)
    self._count_dice = count_dice
    return self


class Pool():
    """Represents a set of unordered dice, only distinguished by the outcomes they roll.

    This should be used in conjunction with `EvalPool` to generate a result.
    """

    _count_dice: tuple[int, ...]
    _dice: Counts

    def __new__(cls, *dice) -> 'Pool':
        """Public constructor for a pool.

        Evaulation is most efficient when the dice are the same or same-side
        truncations of each other. For example, d4, d6, d8, d10, d12 are all
        same-side truncations of d12.

        Args:
            *dice: The dice to put in the pool. Empty dice are ignored. All
                outcomes within a pool must be totally orderable.
        """
        dice = tuple(icepool.Die(die) for die in dice)
        num_dice = len(dice)
        num_dices: MutableMapping['icepool.Die', int] = defaultdict(int)
        for die in dice:
            num_dices[die] += 1
        count_dice = (1,) * num_dice
        return cls._new_pool(num_dices, count_dice)

    @classmethod
    def _new_pool(cls, num_dices, count_dice) -> 'Pool':
        """Creates a new pool.

        Args:
            num_dices: At this point, this is a map from dice to num_dice, with
                no empty dice.
            count_dice: At this point, this is a tuple with length equal to the
                number of dice.
        """
        sorted_num_dices = tuple(
            sorted(num_dices.items(), key=lambda kv: kv[0].key_tuple()))
        return new_pool_cached(
            cls,  # type: ignore
            sorted_num_dices,
            count_dice)

    @cached_property
    def _num_dice(self) -> int:
        return sum(self._dice.values())

    def num_dice(self) -> int:
        """The number of dice in this pool."""
        return self._num_dice

    def has_empty_dice(self) -> bool:
        """Whether this pool contains any empty dice."""
        return any(die.is_empty() for die in self._dice.keys())

    def is_empty(self) -> bool:
        return len(self._dice) == 0

    @cached_property
    def _denominator(self) -> int:
        """The product of the total dice weights in this pool."""
        return math.prod(
            die.denominator()**count for die, count in self._dice.items())

    def denominator(self) -> int:
        return self._denominator

    @cached_property
    def _dice_tuple(self) -> tuple['icepool.Die', ...]:
        return sum(((die,) * count for die, count in self._dice.items()),
                   start=())

    def unique_dice(self) -> Collection['icepool.Die']:
        return self._dice.keys()

    @cached_property
    def _outcomes(self) -> Sequence:
        outcome_set = set(
            itertools.chain.from_iterable(
                die.outcomes() for die in self.unique_dice()))
        return tuple(sorted(outcome_set))

    def outcomes(self) -> Sequence:
        """The union of outcomes among all dice in this pool."""
        return self._outcomes

    def count_dice(self) -> tuple[int, ...]:
        """The tuple indicating which dice in the pool will be counted.

        The tuple has one element per die in the pool, from lowest roll to
        highest roll.
        """
        return self._count_dice

    def set_count_dice(self, count_dice: int | slice | tuple[int, ...] | None):
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
            A sequence of one `int` for each die.
                Each die is counted that many times, which could be multiple or
                negative times. This may resize the pool, but only if the
                pool consists of a single type of die.

                Up to one `Ellipsis` (`...`) may be used.
                If an `Ellipsis` is used, the size of the pool won't change.
                Instead, the `Ellipsis` will be replaced with a number of zero
                counts, sufficient to maintain the current size of this pool.
                This number may be "negative" if more `int`s are provided than
                the size of the pool. Specifically:

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
            result = Pool._new_pool(dice, count_dice)
        else:
            result = Pool._new_pool(self._dice, count_dice)
        if convert_to_die:
            return result.eval(lambda state, outcome, count: outcome
                               if count else state)
        else:
            return result

    __getitem__ = set_count_dice

    @cached_property
    def _min_outcome(self):
        return min(die.min_outcome() for die in self._dice.keys())

    def min_outcome(self):
        """Returns the min outcome among all dice in this pool."""
        return self._min_outcome

    @cached_property
    def _max_outcome(self):
        return max(die.max_outcome() for die in self._dice.keys())

    def max_outcome(self):
        """Returns the max outcome among all dice in this pool."""
        return self._max_outcome

    def _pop_min(self,
                 min_outcome) -> Generator[tuple['Pool', int, int], None, None]:
        """Pops the given outcome from this pool, if it is the min outcome.

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
        skip_weight = None
        for pop in itertools.product(*generators):
            net_num_rolled = 0
            result_weight = 1
            next_dice_counts: MutableMapping[Any, int] = defaultdict(int)
            for popped_die, num_remain, num_rolled, weight in pop:
                if not popped_die.is_empty():
                    next_dice_counts[popped_die] += num_remain
                net_num_rolled += num_rolled
                result_weight *= weight
            if net_num_rolled == 0:
                result_count = 0
                popped_count_dice = self.count_dice()
            else:
                result_count = sum(self.count_dice()[:net_num_rolled])
                popped_count_dice = self.count_dice()[net_num_rolled:]
            popped_pool = Pool._new_pool(next_dice_counts, popped_count_dice)
            if not any(popped_count_dice):
                # Dump all dice in exchange for the denominator.
                skip_weight = (skip_weight or
                               0) + result_weight * popped_pool.denominator()
                continue

            yield popped_pool, result_count, result_weight

        if skip_weight is not None:
            yield empty_pool, sum(self.count_dice()), skip_weight

    def _pop_max(self,
                 max_outcome) -> Generator[tuple['Pool', int, int], None, None]:
        """Pops the given outcome from this pool, if it is the max outcome.

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
        skip_weight = None
        for pop in itertools.product(*generators):
            net_num_rolled = 0
            result_weight = 1
            next_dice_counts: MutableMapping[Any, int] = defaultdict(int)
            for popped_die, num_remain, num_rolled, weight in pop:
                if not popped_die.is_empty():
                    next_dice_counts[popped_die] += num_remain
                net_num_rolled += num_rolled
                result_weight *= weight
            if net_num_rolled == 0:
                result_count = 0
                popped_count_dice = self.count_dice()
            else:
                result_count = sum(self.count_dice()[-net_num_rolled:])
                popped_count_dice = self.count_dice()[:-net_num_rolled]
            popped_pool = Pool._new_pool(next_dice_counts, popped_count_dice)
            if not any(popped_count_dice):
                # Dump all dice in exchange for the denominator.
                skip_weight = (skip_weight or
                               0) + result_weight * popped_pool.denominator()
                continue

            yield popped_pool, result_count, result_weight

        if skip_weight is not None:
            yield empty_pool, sum(self.count_dice()), skip_weight

    def eval(self, eval_or_func: 'icepool.EvalPool' | Callable,
             /) -> 'icepool.Die':
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

    def sum(self) -> 'icepool.Die':
        """Convenience method to simply sum the dice in this pool.

        This uses `icepool.sum_pool`.

        Returns:
            A die representing the sum.
        """
        return icepool.sum_pool(self)

    def lowest(self, num_keep: int = 1, num_drop: int = 0) -> 'icepool.Die':
        """The lowest outcome or sum of the lowest outcomes in the pool.

        The args override any `count_dice` of this pool.

        Args:
            num_keep: The number of lowest dice will be summed.
            num_drop: This number of lowest dice will be dropped before keeping
                dice to be summed.
        """
        if num_keep < 0:
            raise ValueError(f'num_drop={num_keep} cannot be negative.')
        if num_drop < 0:
            raise ValueError(f'num_drop={num_drop} cannot be negative.')

        start = min(num_drop, self.num_dice())
        stop = min(num_keep + num_drop, self.num_dice())
        return self[start:stop].sum()  # type: ignore

    def highest(self, num_keep: int = 1, num_drop: int = 0) -> 'icepool.Die':
        """The highest outcome or sum of the highest outcomes in the pool.

        The args override any `count_dice` of this pool.

        Args:
            num_keep: The number of highest dice will be summed.
            num_drop: This number of highest dice will be dropped before keeping
                dice to be summed.
        """
        if num_keep < 0:
            raise ValueError(f'num_drop={num_keep} cannot be negative.')
        if num_drop < 0:
            raise ValueError(f'num_drop={num_drop} cannot be negative.')

        start = self.num_dice() - min(num_keep + num_drop, self.num_dice())
        stop = self.num_dice() - min(num_drop, self.num_dice())
        return self[start:stop].sum()  # type: ignore

    def __str__(self) -> str:
        return (
            f'Pool of {self.num_dice()} dice with count_dice={self.count_dice()}\n'
            + ''.join(f'  {repr(die)}\n' for die in self._dice_tuple))

    @cached_property
    def _key_tuple(self) -> tuple:
        return tuple((die.key_tuple(), count)
                     for die, count in self._dice.items()), self._count_dice

    def __eq__(self, other) -> bool:
        if not isinstance(other, Pool):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self) -> int:
        return hash(self._key_tuple)

    def __hash__(self) -> int:
        return self._hash


empty_pool = Pool()
"""Shared empty pool instance."""
