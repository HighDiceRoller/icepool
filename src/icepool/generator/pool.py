__docformat__ = 'google'

import icepool
import icepool.expression
import icepool.math
import icepool.creation_args
from icepool.generator.keep import KeepGenerator, pop_max_from_keep_tuple, pop_min_from_keep_tuple
from icepool.generator.multiset_generator import InitialMultisetGenerator, NextMultisetGenerator
import icepool.generator.pop_order
from icepool.generator.pop_order import PopOrderReason

import itertools
import math
import operator
from collections import defaultdict
from functools import cache, cached_property, reduce

from icepool.typing import T, Order
from typing import TYPE_CHECKING, Any, Collection, Iterator, Mapping, MutableMapping, Sequence, cast

if TYPE_CHECKING:
    from icepool.expression import MultisetExpression


class Pool(KeepGenerator[T]):
    """Represents a multiset of outcomes resulting from the roll of several dice.

    This should be used in conjunction with `MultisetEvaluator` to generate a
    result.

    Note that operators are performed on the multiset of rolls, not the multiset
    of dice. For example, `d6.pool(3) - d6.pool(3)` is not an empty pool, but
    an expression meaning "roll two pools of 3d6 and get the rolls from the
    first pool, with rolls in the second pool cancelling matching rolls in the
    first pool one-for-one".
    """

    _dice: tuple[tuple['icepool.Die[T]', int]]
    _outcomes: tuple[T, ...]

    def __new__(
            cls,
            dice:
        'Sequence[icepool.Die[T] | T] | Mapping[icepool.Die[T], int] | Mapping[T, int] | Mapping[icepool.Die[T] | T, int]',
            times: Sequence[int] | int = 1) -> 'Pool':
        """Public constructor for a pool.

        Evaulation is most efficient when the dice are the same or same-side
        truncations of each other. For example, d4, d6, d8, d10, d12 are all
        same-side truncations of d12.

        It is permissible to create a `Pool` without providing dice, but not all
        evaluators will handle this case, especially if they depend on the
        outcome type. Dice may be in the pool zero times, in which case their
        outcomes will be considered but without any count (unless another die
        has that outcome).

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
                dice = {die: quantity for die, quantity in dice._dice}

        if isinstance(dice, (icepool.Die, icepool.Deck, icepool.MultiDeal)):
            raise ValueError(
                f'A Pool cannot be constructed with a {type(dice).__name__} argument.'
            )

        dice, times = icepool.creation_args.itemize(dice, times)
        converted_dice = [icepool.implicit_convert_to_die(die) for die in dice]

        dice_counts: MutableMapping['icepool.Die[T]', int] = defaultdict(int)
        for die, qty in zip(converted_dice, times):
            if qty == 0:
                continue
            dice_counts[die] += qty
        keep_tuple = (1, ) * sum(times)

        # Includes dice with zero qty.
        outcomes = icepool.sorted_union(*converted_dice)
        return cls._new_from_mapping(dice_counts, outcomes, keep_tuple)

    @classmethod
    @cache
    def _new_raw(cls, dice: tuple[tuple['icepool.Die[T]', int]],
                 outcomes: tuple[T], keep_tuple: tuple[int, ...]) -> 'Pool[T]':
        """All pool creation ends up here. This method is cached.

        Args:
            dice: A tuple of (die, count) pairs.
            keep_tuple: A tuple of how many times to count each die.
        """
        self = super(Pool, cls).__new__(cls)
        self._dice = dice
        self._outcomes = outcomes
        self._keep_tuple = keep_tuple
        return self

    @classmethod
    def clear_cache(cls):
        """Clears the global pool cache."""
        Pool._new_raw.cache_clear()

    @classmethod
    def _new_from_mapping(cls, dice_counts: Mapping['icepool.Die[T]', int],
                          outcomes: tuple[T, ...],
                          keep_tuple: Sequence[int]) -> 'Pool[T]':
        """Creates a new pool.

        Args:
            dice_counts: A map from dice to rolls.
            keep_tuple: A tuple with length equal to the number of dice.
        """
        dice = tuple(
            sorted(dice_counts.items(), key=lambda kv: kv[0]._hash_key))
        return Pool._new_raw(dice, outcomes, keep_tuple)

    @cached_property
    def _raw_size(self) -> int:
        return sum(count for _, count in self._dice)

    def raw_size(self) -> int:
        """The number of dice in this pool before the keep_tuple is applied."""
        return self._raw_size

    def _is_resolvable(self) -> bool:
        return all(not die.is_empty() for die, _ in self._dice)

    @cached_property
    def _denominator(self) -> int:
        return math.prod(die.denominator()**count for die, count in self._dice)

    def denominator(self) -> int:
        return self._denominator

    @cached_property
    def _dice_tuple(self) -> tuple['icepool.Die[T]', ...]:
        return sum(((die, ) * count for die, count in self._dice), start=())

    @cached_property
    def _unique_dice(self) -> Collection['icepool.Die[T]']:
        return set(die for die, _ in self._dice)

    def unique_dice(self) -> Collection['icepool.Die[T]']:
        """The collection of unique dice in this pool."""
        return self._unique_dice

    def outcomes(self) -> Sequence[T]:
        """The union of possible outcomes among all dice in this pool in ascending order."""
        return self._outcomes

    def output_arity(self) -> int:
        return 1

    def _preferred_pop_order(self) -> tuple[Order | None, PopOrderReason]:
        can_truncate_min, can_truncate_max = icepool.generator.pop_order.can_truncate(
            self.unique_dice())
        if can_truncate_min and not can_truncate_max:
            return Order.Ascending, PopOrderReason.PoolComposition
        if can_truncate_max and not can_truncate_min:
            return Order.Descending, PopOrderReason.PoolComposition

        lo_skip, hi_skip = icepool.generator.pop_order.lo_hi_skip(
            self.keep_tuple())
        if lo_skip > hi_skip:
            return Order.Descending, PopOrderReason.KeepSkip
        if hi_skip > lo_skip:
            return Order.Ascending, PopOrderReason.KeepSkip

        return Order.Any, PopOrderReason.NoPreference

    def min_outcome(self) -> T:
        """The min outcome among all dice in this pool."""
        return self._outcomes[0]

    def max_outcome(self) -> T:
        """The max outcome among all dice in this pool."""
        return self._outcomes[-1]

    def _generate_initial(self) -> InitialMultisetGenerator:
        yield self, 1

    def _generate_min(self, min_outcome) -> NextMultisetGenerator:
        """Pops the given outcome from this pool, if it is the min outcome.

        Yields:
            popped_pool: The pool after the min outcome is popped.
            count: The number of dice that rolled the min outcome, after
                accounting for keep_tuple.
            weight: The weight of this incremental result.
        """
        if not self.outcomes():
            yield self, (0, ), 1
            return
        if min_outcome != self.min_outcome():
            yield self, (0, ), 1
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
                if not popped_die.is_empty() and misses > 0:
                    next_dice_counts[popped_die] += misses
                total_hits += hits
                result_weight *= weight
            popped_keep_tuple, result_count = pop_min_from_keep_tuple(
                self.keep_tuple(), total_hits)
            popped_pool = Pool._new_from_mapping(next_dice_counts,
                                                 self._outcomes[1:],
                                                 popped_keep_tuple)
            if not any(popped_keep_tuple):
                # Dump all dice in exchange for the denominator.
                skip_weight = (skip_weight or
                               0) + result_weight * popped_pool.denominator()
                continue

            yield popped_pool, (result_count, ), result_weight

        if skip_weight is not None:
            popped_pool = Pool._new_raw((), self._outcomes[1:], ())
            yield popped_pool, (sum(self.keep_tuple()), ), skip_weight

    def _generate_max(self, max_outcome) -> NextMultisetGenerator:
        """Pops the given outcome from this pool, if it is the max outcome.

        Yields:
            popped_pool: The pool after the max outcome is popped.
            count: The number of dice that rolled the max outcome, after
                accounting for keep_tuple.
            weight: The weight of this incremental result.
        """
        if not self.outcomes():
            yield self, (0, ), 1
            return
        if max_outcome != self.max_outcome():
            yield self, (0, ), 1
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
                if not popped_die.is_empty() and misses > 0:
                    next_dice_counts[popped_die] += misses
                total_hits += hits
                result_weight *= weight
            popped_keep_tuple, result_count = pop_max_from_keep_tuple(
                self.keep_tuple(), total_hits)
            popped_pool = Pool._new_from_mapping(next_dice_counts,
                                                 self._outcomes[:-1],
                                                 popped_keep_tuple)
            if not any(popped_keep_tuple):
                # Dump all dice in exchange for the denominator.
                skip_weight = (skip_weight or
                               0) + result_weight * popped_pool.denominator()
                continue

            yield popped_pool, (result_count, ), result_weight

        if skip_weight is not None:
            popped_pool = Pool._new_raw((), self._outcomes[:-1], ())
            yield popped_pool, (sum(self.keep_tuple()), ), skip_weight

    def _set_keep_tuple(self, keep_tuple: tuple[int,
                                                ...]) -> 'KeepGenerator[T]':
        return Pool._new_raw(self._dice, self._outcomes, keep_tuple)

    def additive_union(
        *args: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'MultisetExpression[T]':
        args = tuple(
            icepool.expression.implicit_convert_to_expression(arg)
            for arg in args)
        if all(isinstance(arg, Pool) for arg in args):
            pools = cast(tuple[Pool[T], ...], args)
            keep_tuple: tuple[int, ...] = tuple(
                reduce(operator.add, (pool.keep_tuple() for pool in pools),
                       ()))
            if len(keep_tuple) == 0 or all(x == keep_tuple[0]
                                           for x in keep_tuple):
                # All sorted positions count the same, so we can merge the
                # pools.
                dice: 'MutableMapping[icepool.Die, int]' = defaultdict(int)
                for pool in pools:
                    for die, die_count in pool._dice:
                        dice[die] += die_count
                outcomes = icepool.sorted_union(*(pool.outcomes()
                                                  for pool in pools))
                return Pool._new_from_mapping(dice, outcomes, keep_tuple)
        return KeepGenerator.additive_union(*args)

    def __str__(self) -> str:
        return (
            f'Pool of {self.raw_size()} dice with keep_tuple={self.keep_tuple()}\n'
            + ''.join(f'  {repr(die)} : {count},\n'
                      for die, count in self._dice))

    @cached_property
    def _hash_key(self) -> tuple:
        return Pool, self._dice, self._outcomes, self._keep_tuple


def standard_pool(
        die_sizes: Collection[int] | Mapping[int, int]) -> 'Pool[int]':
    """A `Pool` of standard dice (e.g. d6, d8...).

    Args:
        die_sizes: A collection of die sizes, which will put one die of that
            sizes in the pool for each element.
            Or, a mapping of die sizes to how many dice of that size to put
            into the pool.
            If empty, the pool will be considered to consist of zero zeros.
    """
    if not die_sizes:
        return Pool({icepool.Die([0]): 0})
    if isinstance(die_sizes, Mapping):
        die_sizes = list(
            itertools.chain.from_iterable([k] * v
                                          for k, v in die_sizes.items()))
    return Pool(list(icepool.d(x) for x in die_sizes))


def iter_die_pop_min(
        die: 'icepool.Die[T]', rolls: int,
        min_outcome) -> Iterator[tuple['icepool.Die[T]', int, int, int]]:
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
        die: 'icepool.Die[T]', rolls: int,
        max_outcome) -> Iterator[tuple['icepool.Die[T]', int, int, int]]:
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
