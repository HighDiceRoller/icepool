__docformat__ = 'google'

import icepool
import icepool.math
import icepool.generator.pool_cost
import icepool.creation_args
from icepool.counts import Counts
from icepool.generator.outcome_count_generator import NextOutcomeCountGenerator, OutcomeCountGenerator
from icepool.typing import Outcome

import itertools
import math
from collections import defaultdict
from functools import cache, cached_property

from typing import Any, Collection, Hashable, Iterator, Mapping, MutableMapping, Sequence, TypeVar, overload

T_co = TypeVar('T_co', bound=Outcome, covariant=True)
"""Type variable representing the outcome type."""


@cache
def new_pool_cached(cls, dice: tuple[tuple['icepool.Die', int]],
                    sorted_roll_counts: tuple[int, ...], /) -> 'Pool':
    """Creates a new `Pool`. This function is cached.

    Args:
        cls: The `Pool` class.
        dice: A sorted sequence of (die, rolls) pairs.
        sorted_roll_counts: A tuple of length equal to the number of dice.
    """
    self = super(Pool, cls).__new__(cls)
    self._dice = dice
    self._sorted_roll_counts = sorted_roll_counts
    return self


def clear_pool_cache():
    """Clears the global pool cache."""
    new_pool_cached.cache_clear()


class Pool(OutcomeCountGenerator[T_co]):
    """Represents a set of sorted/unordered dice, only distinguished by the outcomes they roll.

    This should be used in conjunction with `OutcomeCountEvaluator` to generate a result.
    """

    _sorted_roll_counts: tuple[int, ...]
    _dice: tuple[tuple['icepool.Die[T_co]', int]]

    def __new__(
            cls,
            dice:
        'Sequence[icepool.Die[T_co] | T_co] | Mapping[icepool.Die[T_co], int] | Mapping[T_co, int] | Mapping[icepool.Die[T_co] | T_co, int]',
            times: Sequence[int] | int = 1) -> 'Pool':
        """Public constructor for a pool.

        Evaulation is most efficient when the dice are the same or same-side
        truncations of each other. For example, d4, d6, d8, d10, d12 are all
        same-side truncations of d12.

        Args:
            dice: The dice to put in the `Pool`. This can be one of the following:

                * A `Sequence` of `Die` or outcomes.
                * A `Mapping` of `Die` or outcomes to how many of that `Die` or
                    outcome to put in the `Pool`.

                All outcomes within a `Pool` must be totally orderable.
            times: Multiplies the number of times each element of `dice` will
                be put into the pool.
                `times` can either be a sequence of the same length as
                `outcomes` or a single `int` to apply to all elements of
                `outcomes`.

        Raises:
            ValueError: If a bare `Deck` or `Die` argument is provided.
                A `Pool` of a single `Die` should constructed as `Pool([die])`.
        """
        if isinstance(dice, Pool):
            if times == 1:
                return dice
            else:
                dice = dice._dice

        if isinstance(dice, (icepool.Deck, icepool.Deal)):
            raise ValueError(
                f'A Pool cannot be constructed with a {type(dice).__name__} argument.'
            )

        if isinstance(dice, icepool.Die):
            dice = [dice]

        dice, times = icepool.creation_args.itemize(dice, times)
        converted_dice = [icepool.implicit_convert_to_die(die) for die in dice]

        dice_counts: MutableMapping['icepool.Die[T_co]', int] = defaultdict(int)
        for die, qty in zip(converted_dice, times):
            dice_counts[die] += qty
        sorted_roll_counts = (1,) * sum(times)
        return cls._new_pool_from_mapping(dice_counts, sorted_roll_counts)

    @classmethod
    def _new_pool_from_mapping(
            cls, dice_counts: Mapping['icepool.Die[T_co]', int],
            sorted_roll_counts: Sequence[int]) -> 'Pool[T_co]':
        """Creates a new pool.

        Args:
            dice_counts: A map from dice to rolls.
            sorted_roll_counts: A tuple with length equal to the number of dice.
        """
        dice = tuple(
            sorted(dice_counts.items(), key=lambda kv: kv[0].key_tuple()))
        return new_pool_cached(cls, dice, sorted_roll_counts)

    @classmethod
    def _new_pool_from_tuple(
            cls, dice: tuple[tuple['icepool.Die[T_co]', int]],
            sorted_roll_counts: tuple[int, ...]) -> 'Pool[T_co]':
        """Creates a new pool.

        Args:
            dice: A sorted tuple of (dice, count).
            sorted_roll_counts: A tuple with length equal to the number of dice.
        """
        return new_pool_cached(cls, dice, sorted_roll_counts)

    @cached_property
    def _size(self) -> int:
        return sum(count for _, count in self._dice)

    def size(self) -> int:
        """The number of dice in this pool, counting multiples of the same `Die`."""
        return self._size

    def _is_resolvable(self) -> bool:
        return all(not die.is_empty() for die, _ in self._dice)

    @cached_property
    def _denominator(self) -> int:
        return math.prod(die.denominator()**count for die, count in self._dice)

    def denominator(self) -> int:
        return self._denominator

    @cached_property
    def _dice_tuple(self) -> tuple['icepool.Die[T_co]', ...]:
        return sum(((die,) * count for die, count in self._dice), start=())

    @cached_property
    def _unique_dice(self) -> Collection['icepool.Die[T_co]']:
        return set(die for die, _ in self._dice)

    def unique_dice(self) -> Collection['icepool.Die[T_co]']:
        """The collection of unique dice in this pool."""
        return self._unique_dice

    @cached_property
    def _outcomes(self) -> Sequence[T_co]:
        outcome_set = set(
            itertools.chain.from_iterable(
                die.outcomes() for die in self.unique_dice()))
        return tuple(sorted(outcome_set))

    def outcomes(self) -> Sequence[T_co]:
        """The union of outcomes among all dice in this pool."""
        return self._outcomes

    def counts_len(self) -> int:
        return 1

    def _estimate_order_costs(self) -> tuple[int, int]:
        """Estimates the cost of popping from the min and max sides.

        Returns:
            pop_min_cost
            pop_max_cost
        """
        return icepool.generator.pool_cost.estimate_costs(self)

    def sorted_roll_counts(self) -> tuple[int, ...]:
        """The tuple indicating which dice in the pool will be counted.

        The tuple has one element per `Die` in the pool, from lowest roll to
        highest roll. The `Die` in the corresponding sorted position will be
        counted that many times.
        """
        return self._sorted_roll_counts

    @overload
    def set_sorted_roll_counts(
            self, sorted_roll_counts: slice | Sequence[int]) -> 'Pool[T_co]':
        ...

    @overload
    def set_sorted_roll_counts(self,
                               sorted_roll_counts: int) -> 'icepool.Die[T_co]':
        ...

    @overload
    def set_sorted_roll_counts(
        self, sorted_roll_counts: int | slice | Sequence[int]
    ) -> 'Pool[T_co] | icepool.Die[T_co]':
        ...

    def set_sorted_roll_counts(
        self, sorted_roll_counts: int | slice | Sequence[int]
    ) -> 'Pool[T_co] | icepool.Die[T_co]':
        """A `Pool` with the selected dice counted after rolling and sorting.

        Use `pool[sorted_roll_counts]` for the same effect as this method.

        The dice are sorted in ascending order for this purpose,
        regardless of which order the outcomes are evaluated in.

        This is always an absolute selection on all `size` dice,
        not a relative selection on already-selected dice,
        which would be ambiguous in the presence of multiple or negative counts.

        For example, here are some ways of selecting the two highest dice out of 5:

        * `pool[3:5]`
        * `pool[3:]`
        * `pool[-2:]`
        * `pool[..., 1, 1]`
        * `pool[0, 0, 0, 1, 1]`

        These will count the highest as a positive and the lowest as a negative:

        * `pool[-1, 0, 0, 0, 1]`
        * `pool[-1, ..., 1]`

        The valid types of argument are:

        * An `int`. This will count only the `Die` at the specified index
            (once). In this case, the result will be a `Die`, not a `Pool`.
        * A `slice`. The selected dice are counted once each.
        * A sequence of one `int` for each `Die`.
            Each `Die` is counted that many times, which could be multiple or
            negative times.

            Up to one `...` (`Ellipsis`) may be used.
            `...` will be replaced with a number of zero
            counts depending on the size of the pool.
            This number may be "negative" if more `int`s are provided than
            the size of the `Pool`. Specifically:

            * If `sorted_roll_counts` is shorter than `size`, `...`
                acts as enough zero counts to make up the difference.
                E.g. `pool[1, ..., 1]` on five dice would act as `pool[1, 0, 0, 0, 1]`.
            * If `sorted_roll_counts` has length equal to `size`, `...` has no effect.
                E.g. `pool[1, ..., 1]` on two dice would act as `pool[1, 1]`.
            * If `sorted_roll_counts` is longer than `size` and `...` is on one side,
                elements will be dropped from `sorted_roll_counts` on the side with `...`.
                E.g. `pool[..., 1, 2, 3]` on two dice would act as `pool[2, 3]`.
            * If `sorted_roll_counts` is longer than `size` and `...`
                is in the middle, the counts will be as the sum of two
                one-sided `...`.
                E.g. `pool[-1, ..., 1]` acts like `[-1, ...]` plus `[..., 1]`.
                On a `Pool` consisting of a single `Die` this would have
                the -1 and 1 cancel each other out.

        Raises:
            ValueError: If more than one `...` is used.
        """
        convert_to_die = isinstance(sorted_roll_counts, int)
        sorted_roll_counts = sorted_roll_counts_tuple(self.size(),
                                                      sorted_roll_counts)
        if len(sorted_roll_counts) != self.size():
            if len(self._dice) != 1:
                raise ValueError(
                    'Cannot change the size of a pool unless it has exactly one type of die.'
                )
            dice = Counts([(self._dice[0][0], len(sorted_roll_counts))])
            result = Pool._new_pool_from_mapping(dice, sorted_roll_counts)
        else:
            result = Pool._new_pool_from_tuple(self._dice, sorted_roll_counts)
        if convert_to_die:
            return result.evaluate(lambda state, outcome, count: outcome
                                   if count else state)
        else:
            return result

    __getitem__ = set_sorted_roll_counts

    @cached_property
    def _min_outcome(self) -> T_co:
        return min(die.min_outcome() for die in self.unique_dice())

    def min_outcome(self) -> T_co:
        """The min outcome among all dice in this pool."""
        return self._min_outcome

    @cached_property
    def _max_outcome(self) -> T_co:
        return max(die.max_outcome() for die in self.unique_dice())

    def max_outcome(self) -> T_co:
        """The max outcome among all dice in this pool."""
        return self._max_outcome

    def _generate_min(self, min_outcome) -> NextOutcomeCountGenerator:
        """Pops the given outcome from this pool, if it is the min outcome.

        Yields:
            popped_pool: The pool after the min outcome is popped.
            net_count: The number of dice that rolled the min outcome, after
                accounting for sorted_roll_counts.
            net_weight: The weight of this incremental result.
        """
        if not self.outcomes():
            yield self, (0,), 1
            return
        generators = [
            iter_die_pop_min(die, die_count, min_outcome)
            for die, die_count in self._dice
        ]
        skip_weight = None
        for pop in itertools.product(*generators):
            total_hits = 0
            result_weight = 1
            next_dice_counts: MutableMapping[Any, int] = defaultdict(int)
            for popped_die, misses, hits, weight in pop:
                if not popped_die.is_empty():
                    next_dice_counts[popped_die] += misses
                total_hits += hits
                result_weight *= weight
            if total_hits == 0:
                result_count = 0
                popped_sorted_roll_counts = self.sorted_roll_counts()
            else:
                result_count = sum(self.sorted_roll_counts()[:total_hits])
                popped_sorted_roll_counts = self.sorted_roll_counts(
                )[total_hits:]
            popped_pool = Pool._new_pool_from_mapping(
                next_dice_counts, popped_sorted_roll_counts)
            if not any(popped_sorted_roll_counts):
                # Dump all dice in exchange for the denominator.
                skip_weight = (skip_weight or
                               0) + result_weight * popped_pool.denominator()
                continue

            yield popped_pool, (result_count,), result_weight

        if skip_weight is not None:
            yield Pool([]), (sum(self.sorted_roll_counts()),), skip_weight

    def _generate_max(self, max_outcome) -> NextOutcomeCountGenerator:
        """Pops the given outcome from this pool, if it is the max outcome.

        Yields:
            popped_pool: The pool after the max outcome is popped.
            net_count: The number of dice that rolled the max outcome, after
                accounting for sorted_roll_counts.
            net_weight: The weight of this incremental result.
        """
        if not self.outcomes():
            yield self, (0,), 1
            return
        generators = [
            iter_die_pop_max(die, die_count, max_outcome)
            for die, die_count in self._dice
        ]
        skip_weight = None
        for pop in itertools.product(*generators):
            total_hits = 0
            result_weight = 1
            next_dice_counts: MutableMapping[Any, int] = defaultdict(int)
            for popped_die, misses, hits, weight in pop:
                if not popped_die.is_empty():
                    next_dice_counts[popped_die] += misses
                total_hits += hits
                result_weight *= weight
            if total_hits == 0:
                result_count = 0
                popped_sorted_roll_counts = self.sorted_roll_counts()
            else:
                result_count = sum(self.sorted_roll_counts()[-total_hits:])
                popped_sorted_roll_counts = self.sorted_roll_counts(
                )[:-total_hits]
            popped_pool = Pool._new_pool_from_mapping(
                next_dice_counts, popped_sorted_roll_counts)
            if not any(popped_sorted_roll_counts):
                # Dump all dice in exchange for the denominator.
                skip_weight = (skip_weight or
                               0) + result_weight * popped_pool.denominator()
                continue

            yield popped_pool, (result_count,), result_weight

        if skip_weight is not None:
            yield Pool([]), (sum(self.sorted_roll_counts()),), skip_weight

    def lowest(self, keep: int = 1, drop: int = 0) -> 'icepool.Die':
        """The sum of the lowest outcomes in the pool.

        The args override any `sorted_roll_counts` of this pool.

        Args:
            keep: The number of lowest dice will be summed.
            drop: This number of lowest dice will be dropped before keeping
                dice to be summed.
        """
        if keep < 0:
            raise ValueError(f'keep={keep} cannot be negative.')
        if drop < 0:
            raise ValueError(f'drop={drop} cannot be negative.')

        start = min(drop, self.size())
        stop = min(keep + drop, self.size())
        # Should support sum.
        return self[start:stop].sum()  # type: ignore

    def highest(self, keep: int = 1, drop: int = 0) -> 'icepool.Die':
        """The sum of the highest outcomes in the pool.

        The args override any `sorted_roll_counts` of this pool.

        Args:
            keep: The number of highest dice will be summed.
            drop: This number of highest dice will be dropped before keeping
                dice to be summed.
        """
        if keep < 0:
            raise ValueError(f'keep={keep} cannot be negative.')
        if drop < 0:
            raise ValueError(f'drop={drop} cannot be negative.')

        start = self.size() - min(keep + drop, self.size())
        stop = self.size() - min(drop, self.size())
        # Should support sum.
        return self[start:stop].sum()  # type: ignore

    def __str__(self) -> str:
        return (
            f'Pool of {self.size()} dice with sorted_roll_counts={self.sorted_roll_counts()}\n'
            + ''.join(f'  {repr(die)}\n' for die in self._dice_tuple))

    @cached_property
    def _key_tuple(self) -> tuple:
        return Pool, self._dice, self._sorted_roll_counts

    def __eq__(self, other) -> bool:
        if not isinstance(other, Pool):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self) -> int:
        return hash(self._key_tuple)

    def __hash__(self) -> int:
        return self._hash


def sorted_roll_counts_tuple(
        pool_size: int,
        sorted_roll_counts: int | slice | Sequence[int]) -> tuple[int, ...]:
    """Expresses `sorted_roll_counts` as a tuple.

    See `Pool.set_sorted_roll_counts()` for details.

    Args:
        `pool_size`: An `int` specifying the size of the pool.
        `sorted_roll_counts`: Raw specification for how the dice are to be counted.
    Raises:
        ValueError: If:
            * More than one `Ellipsis` is used.
            * An `Ellipsis` is used in the center with too few `pool_size`.
    """
    if isinstance(sorted_roll_counts, int):
        result = [0] * pool_size
        result[sorted_roll_counts] = 1
        return tuple(result)
    elif isinstance(sorted_roll_counts, slice):
        if sorted_roll_counts.step is not None:
            raise ValueError('step is not supported for pool subscripting')
        result = [0] * pool_size
        result[sorted_roll_counts] = [1] * len(result[sorted_roll_counts])
        return tuple(result)
    else:
        split = None
        for i, x in enumerate(sorted_roll_counts):
            if x is Ellipsis:
                if split is None:
                    split = i
                else:
                    raise ValueError(
                        'Cannot use more than one Ellipsis (...) for sorted_roll_counts.'
                    )

        if split is None:
            if len(sorted_roll_counts) != pool_size:
                raise ValueError(
                    f'Length of {sorted_roll_counts} does not match pool size of {pool_size}'
                )
            return tuple(sorted_roll_counts)

        extra_dice = pool_size - len(sorted_roll_counts) + 1

        if split == 0:
            # Ellipsis on left.
            sorted_roll_counts = sorted_roll_counts[1:]
            if extra_dice < 0:
                return tuple(sorted_roll_counts[-extra_dice:])
            else:
                return (0,) * extra_dice + tuple(sorted_roll_counts)
        elif split == len(sorted_roll_counts) - 1:
            # Ellipsis on right.
            sorted_roll_counts = sorted_roll_counts[:-1]
            if extra_dice < 0:
                return tuple(sorted_roll_counts[:extra_dice])
            else:
                return tuple(sorted_roll_counts) + (0,) * extra_dice
        else:
            # Ellipsis in center.
            if extra_dice < 0:
                result = [0] * pool_size
                for i in range(min(split, pool_size)):
                    result[i] += sorted_roll_counts[i]
                reverse_split = split - len(sorted_roll_counts)
                for i in range(-1, max(reverse_split - 1, -pool_size - 1), -1):
                    result[i] += sorted_roll_counts[i]
                return tuple(result)
            else:
                return tuple(
                    sorted_roll_counts[:split]) + (0,) * extra_dice + tuple(
                        sorted_roll_counts[split + 1:])


def standard_pool(
        die_sizes: Collection[int] | Mapping[int, int]) -> 'Pool[int]':
    """A `Pool` of standard dice (e.g. d6, d8...).

    Args:
        die_sizes: A collection of die sizes, which will put one die of that
            sizes in the pool for each element.
            Or, a mapping of die sizes to how many dice of that size to put
            into the pool.
    """
    if isinstance(die_sizes, Mapping):
        die_sizes = list(
            itertools.chain.from_iterable(
                [k] * v for k, v in die_sizes.items()))
    return Pool(list(icepool.d(x) for x in die_sizes))


def iter_die_pop_min(
        die: 'icepool.Die[T_co]', rolls: int,
        min_outcome) -> Iterator[tuple['icepool.Die[T_co]', int, int, int]]:
    """Helper function to iterate over the possibilities of several identical dice rolling a min outcome.

    Args:
        die: The `Die` to pop.
        rolls: The number of this kind of `Die`.
        min_outcome: The outcome to pop. This is <= the `Die`'s min outcome.

    Yields:
        popped_die
        misses: The number of dice that didn't roll this outcome.
        hits: The number of dice that rolled this outcome.
        weight: The weight of this number of dice rolling max_outcome.
    """
    if die.min_outcome() != min_outcome:
        misses = rolls
        hits = 0
        weight = 1
        yield die, misses, hits, weight
        return

    popped_die, single_weight = die._pop_min()

    if popped_die.is_empty():
        # This is the last outcome. All dice must roll this outcome.
        misses = 0
        hits = rolls
        weight = single_weight**rolls
        yield popped_die, misses, hits, weight
        return

    comb_row = icepool.math.comb_row(rolls, single_weight)
    for hits, weight in enumerate(comb_row):
        misses = rolls - hits
        yield popped_die, misses, hits, weight


def iter_die_pop_max(
        die: 'icepool.Die[T_co]', rolls: int,
        max_outcome) -> Iterator[tuple['icepool.Die[T_co]', int, int, int]]:
    """Helper function to iterate over the possibilities of several identical dice rolling a max outcome.

    Args:
        die: The `Die` to pop.
        rolls: The number of this kind of `Die`.
        max_outcome: The outcome to pop. This is >= the `Die`'s max outcome.

    Yields:
        popped_die
        misses: The number of dice that didn't roll this outcome.
        hits: The number of dice that rolled this outcome.
        weight: The weight of this number of dice rolling max_outcome.
    """
    if die.max_outcome() != max_outcome:
        misses = rolls
        hits = 0
        weight = 1
        yield die, misses, hits, weight
        return

    popped_die, single_weight = die._pop_max()

    if popped_die.is_empty():
        # This is the last outcome. All dice must roll this outcome.
        misses = 0
        hits = rolls
        weight = single_weight**rolls
        yield popped_die, misses, hits, weight
        return

    comb_row = icepool.math.comb_row(rolls, single_weight)
    for hits, weight in enumerate(comb_row):
        misses = rolls - hits
        yield popped_die, misses, hits, weight
