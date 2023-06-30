__docformat__ = 'google'

import icepool
import icepool.expression
import icepool.math
import icepool.generator.pool_cost
import icepool.creation_args
from icepool.collection.counts import Counts
from icepool.generator.multiset_generator import NextMultisetGenerator, MultisetGenerator

import itertools
import math
import operator
from collections import defaultdict
from functools import cache, cached_property, reduce

from icepool.typing import Outcome, T
from types import EllipsisType
from typing import Any, Collection, Hashable, Iterator, Literal, Mapping, MutableMapping, Sequence, cast, overload, TYPE_CHECKING

if TYPE_CHECKING:
    from icepool.expression import MultisetExpression


class Pool(MultisetGenerator[T, tuple[int]]):
    """Represents a multiset of outcomes resulting from the roll of several dice.

    This should be used in conjunction with `MultisetEvaluator` to generate a
    result.

    Note that operators are performed on the multiset of rolls, not the multiset
    of dice. For example, `d6.pool(3) - d6.pool(3)` is not an empty pool, but
    an expression meaning "roll two pools of 3d6 and get the rolls from the
    first pool, with rolls in the second pool cancelling matching rolls in the
    first pool one-for-one".
    """

    _keep_tuple: tuple[int, ...]
    _dice: tuple[tuple['icepool.Die[T]', int]]

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
        outcome type. In this case you may want to provide a die with zero
        quantity.

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

        if isinstance(dice, (icepool.Die, icepool.Deck, icepool.Deal)):
            raise ValueError(
                f'A Pool cannot be constructed with a {type(dice).__name__} argument.'
            )

        dice, times = icepool.creation_args.itemize(dice, times)
        converted_dice = [icepool.implicit_convert_to_die(die) for die in dice]

        dice_counts: MutableMapping['icepool.Die[T]', int] = defaultdict(int)
        for die, qty in zip(converted_dice, times):
            dice_counts[die] += qty
        keep_tuple = (1,) * sum(times)
        return cls._new_from_mapping(dice_counts, keep_tuple)

    @classmethod
    @cache
    def _new_raw(cls, dice: tuple[tuple['icepool.Die[T]', int]],
                 keep_tuple: tuple[int, ...]) -> 'Pool[T]':
        """All pool creation ends up here. This method is cached.

        Args:
            dice: A tuple of (die, count) pairs.
            keep_tuple: A tuple of how many times to count each die.
        """
        self = super(Pool, cls).__new__(cls)
        self._dice = dice
        self._keep_tuple = keep_tuple
        return self

    @classmethod
    def _new_empty(cls) -> 'Pool':
        return cls._new_raw((), ())

    @classmethod
    def clear_cache(cls):
        """Clears the global pool cache."""
        Pool._new_raw.cache_clear()

    @classmethod
    def _new_from_mapping(cls, dice_counts: Mapping['icepool.Die[T]', int],
                          keep_tuple: Sequence[int]) -> 'Pool[T]':
        """Creates a new pool.

        Args:
            dice_counts: A map from dice to rolls.
            keep_tuple: A tuple with length equal to the number of dice.
        """
        dice = tuple(
            sorted(dice_counts.items(), key=lambda kv: kv[0]._key_tuple))
        return Pool._new_raw(dice, keep_tuple)

    @cached_property
    def _raw_size(self) -> int:
        return sum(count for _, count in self._dice)

    def raw_size(self) -> int:
        """The number of dice in this pool before the keep_tuple is applied."""
        return self._raw_size

    @cached_property
    def _keep_size(self) -> int:
        return sum(self.keep_tuple())

    def keep_size(self) -> int:
        """The total count produced by this pool after the keep_tuple is applied."""
        return self._keep_size

    def _is_resolvable(self) -> bool:
        return all(not die.is_empty() for die, _ in self._dice)

    @cached_property
    def _denominator(self) -> int:
        return math.prod(die.denominator()**count for die, count in self._dice)

    def denominator(self) -> int:
        return self._denominator

    @cached_property
    def _dice_tuple(self) -> tuple['icepool.Die[T]', ...]:
        return sum(((die,) * count for die, count in self._dice), start=())

    @cached_property
    def _unique_dice(self) -> Collection['icepool.Die[T]']:
        return set(die for die, _ in self._dice)

    def unique_dice(self) -> Collection['icepool.Die[T]']:
        """The collection of unique dice in this pool."""
        return self._unique_dice

    @cached_property
    def _outcomes(self) -> Sequence[T]:
        outcome_set = set(
            itertools.chain.from_iterable(
                die.outcomes() for die in self.unique_dice()))
        return tuple(sorted(outcome_set))

    def outcomes(self) -> Sequence[T]:
        """The union of possible outcomes among all dice in this pool in ascending order."""
        return self._outcomes

    def output_arity(self) -> int:
        return 1

    def _estimate_order_costs(self) -> tuple[int, int]:
        """Estimates the cost of popping from the min and max sides.

        Returns:
            pop_min_cost
            pop_max_cost
        """
        return icepool.generator.pool_cost.estimate_costs(self)

    def keep_tuple(self) -> tuple[int, ...]:
        """The tuple indicating which dice in the pool will be counted.

        The tuple has one element per `Die` in the pool, from lowest roll to
        highest roll. The `Die` in the corresponding sorted position will be
        counted that many times.
        """
        return self._keep_tuple

    @cached_property
    def _min_outcome(self) -> T:
        return min(die.min_outcome() for die in self.unique_dice())

    def min_outcome(self) -> T:
        """The min outcome among all dice in this pool."""
        return self._min_outcome

    @cached_property
    def _max_outcome(self) -> T:
        return max(die.max_outcome() for die in self.unique_dice())

    def max_outcome(self) -> T:
        """The max outcome among all dice in this pool."""
        return self._max_outcome

    def _generate_min(self, min_outcome) -> NextMultisetGenerator:
        """Pops the given outcome from this pool, if it is the min outcome.

        Yields:
            popped_pool: The pool after the min outcome is popped.
            count: The number of dice that rolled the min outcome, after
                accounting for keep_tuple.
            weight: The weight of this incremental result.
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
                popped_keep_tuple = self.keep_tuple()
            else:
                result_count = sum(self.keep_tuple()[:total_hits])
                popped_keep_tuple = self.keep_tuple()[total_hits:]
            popped_pool = Pool._new_from_mapping(next_dice_counts,
                                                 popped_keep_tuple)
            if not any(popped_keep_tuple):
                # Dump all dice in exchange for the denominator.
                skip_weight = (skip_weight or
                               0) + result_weight * popped_pool.denominator()
                continue

            yield popped_pool, (result_count,), result_weight

        if skip_weight is not None:
            yield Pool._new_empty(), (sum(self.keep_tuple()),), skip_weight

    def _generate_max(self, max_outcome) -> NextMultisetGenerator:
        """Pops the given outcome from this pool, if it is the max outcome.

        Yields:
            popped_pool: The pool after the max outcome is popped.
            count: The number of dice that rolled the max outcome, after
                accounting for keep_tuple.
            weight: The weight of this incremental result.
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
                popped_keep_tuple = self.keep_tuple()
            else:
                result_count = sum(self.keep_tuple()[-total_hits:])
                popped_keep_tuple = self.keep_tuple()[:-total_hits]
            popped_pool = Pool._new_from_mapping(next_dice_counts,
                                                 popped_keep_tuple)
            if not any(popped_keep_tuple):
                # Dump all dice in exchange for the denominator.
                skip_weight = (skip_weight or
                               0) + result_weight * popped_pool.denominator()
                continue

            yield popped_pool, (result_count,), result_weight

        if skip_weight is not None:
            yield Pool._new_empty(), (sum(self.keep_tuple()),), skip_weight

    # Overrides to MultisetExpression.

    @overload
    def keep(self, index: slice | Sequence[int | EllipsisType]) -> 'Pool[T]':
        ...

    @overload
    def keep(self, index: int) -> 'icepool.Die[T]':
        ...

    def keep(
        self, index: slice | Sequence[int | EllipsisType] | int
    ) -> 'Pool[T] | icepool.Die[T]':
        """A `Pool` with the selected dice counted after rolling and sorting.

        Use `pool[index]` for the same effect as this method.

        The rolls are sorted in ascending order for this purpose,
        regardless of which order the outcomes are evaluated in.

        For example, here are some ways of selecting the two highest rolls out
        of five:

        * `pool[3:5]`
        * `pool[3:]`
        * `pool[-2:]`
        * `pool[..., 1, 1]`
        * `pool[0, 0, 0, 1, 1]`

        These will count the highest as a positive and the lowest as a negative:

        * `pool[-1, 0, 0, 0, 1]`
        * `pool[-1, ..., 1]`

        The valid types of argument are:

        * An `int`. This will count only the roll at the specified index.
            In this case, the result is a `Die` rather than a `Pool`.
        * A `slice`. The selected dice are counted once each.
        * A sequence of one `int` for each `Die`.
            Each roll is counted that many times, which could be multiple or
            negative times.

            Up to one `...` (`Ellipsis`) may be used.
            `...` will be replaced with a number of zero
            counts depending on the size of the pool.
            This number may be "negative" if more `int`s are provided than
            the size of the `Pool`. Specifically:

            * If `index` is shorter than `size`, `...`
                acts as enough zero counts to make up the difference.
                E.g. `pool[1, ..., 1]` on five dice would act as
                `pool[1, 0, 0, 0, 1]`.
            * If `index` has length equal to `size`, `...` has no effect.
                E.g. `pool[1, ..., 1]` on two dice would act as `pool[1, 1]`.
            * If `index` is longer than `size` and `...` is on one side,
                elements will be dropped from `index` on the side with `...`.
                E.g. `pool[..., 1, 2, 3]` on two dice would act as `pool[2, 3]`.
            * If `index` is longer than `size` and `...`
                is in the middle, the counts will be as the sum of two
                one-sided `...`.
                E.g. `pool[-1, ..., 1]` acts like `[-1, ...]` plus `[..., 1]`.
                On a `Pool` consisting of a single `Die` this would have
                the -1 and 1 cancel each other out.

        If this is called more than once, the selection is applied relative
        to the previous keep_tuple. For example, applying `[:2][-1]` would
        produce the second-lowest roll.

        Raises:
            IndexError: If:
                * More than one `...` is used.
                * The current keep_tuple has negative counts.
                * The provided index specifies a fixed length that is
                    different than the total of the counts in the current
                    keep_tuple.
        """
        convert_to_die = isinstance(index, int)

        if any(x < 0 for x in self.keep_tuple()):
            raise IndexError(
                'A pool with negative counts cannot be further indexed.')

        relative_keep_tuple = make_keep_tuple(self.keep_size(), index)

        # Merge keep tuples.
        keep_tuple: list[int] = []
        for x in self.keep_tuple():
            keep_tuple.append(sum(relative_keep_tuple[:x]))
            relative_keep_tuple = relative_keep_tuple[x:]

        result = Pool._new_raw(self._dice, tuple(keep_tuple))

        if convert_to_die:
            return cast(icepool.Die[T],
                        icepool.evaluator.KeepEvaluator().evaluate(result))
        else:
            return result

    @overload
    def __getitem__(self,
                    index: slice | Sequence[int | EllipsisType]) -> 'Pool[T]':
        ...

    @overload
    def __getitem__(self, index: int) -> 'icepool.Die[T]':
        ...

    def __getitem__(
        self, index: int | slice | Sequence[int | EllipsisType]
    ) -> 'Pool[T] | icepool.Die[T]':
        return self.keep(index)

    def lowest(self, keep: int = 1, drop: int = 0) -> 'Pool[T]':
        if keep < 0:
            raise ValueError(f'keep={keep} cannot be negative.')
        if drop < 0:
            raise ValueError(f'drop={drop} cannot be negative.')

        start = min(drop, self.keep_size())
        stop = min(keep + drop, self.keep_size())
        return self[start:stop]

    def highest(self, keep: int = 1, drop: int = 0) -> 'Pool[T]':
        if keep < 0:
            raise ValueError(f'keep={keep} cannot be negative.')
        if drop < 0:
            raise ValueError(f'drop={drop} cannot be negative.')

        start = self.keep_size() - min(keep + drop, self.keep_size())
        stop = self.keep_size() - min(drop, self.keep_size())
        return self[start:stop]

    def middle(self,
               keep: int = 1,
               *,
               tie: Literal['error', 'high', 'low'] = 'error') -> 'Pool[T]':
        """Keep some of the middle elements from this multiset and drop the rest.

        In contrast to the die and free function versions, this does not
        automatically sum the dice. Use `.sum()` afterwards if you want to sum.
        Alternatively, you can perform some other evaluation.

        Args:
            keep: The number of elements to keep. If this is greater than the
                current keep_size, all are kept.
            tie: What to do if `keep` is odd but the current keep_size
                is even, or vice versa.
                * 'error' (default): Raises `IndexError`.
                * 'low': The lower of the two possible elements is taken.
                * 'high': The higher of the two possible elements is taken.
        """
        if keep < 0:
            raise ValueError(f'keep={keep} cannot be negative.')

        if keep % 2 == self.keep_size() % 2:
            # The "good" case.
            start = (self.keep_size() - keep) // 2
        else:
            # Need to consult the tiebreaker.
            match tie:
                case 'error':
                    raise IndexError(
                        f'The middle {keep} of {self.keep_size()} elements is ambiguous.'
                        " Specify tie='low' or tie='high' to determine what to pick."
                    )
                case 'high':
                    start = (self.keep_size() + 1 - keep) // 2
                case 'low':
                    start = (self.keep_size() - 1 - keep) // 2
                case _:
                    raise ValueError(
                        f"Invalid value for tie {tie}. Expected 'error', 'low', or 'high'."
                    )
        stop = start + keep
        return self[start:stop]

    def __add__(
        self, other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'MultisetExpression[T]':
        try:
            return self.disjoint_union(other)
        except TypeError:
            return NotImplemented

    def __radd__(
        self, other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'MultisetExpression[T]':
        try:
            return self.disjoint_union(other)
        except TypeError:
            return NotImplemented

    def disjoint_union(
        *args: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'MultisetExpression[T]':
        """The combined elements from all the multisets.

        We have an optimization here if all arguments are pools with all sorted
        positions counted the same. In this case we can merge the pools directly
        instead of merging the rolls after the fact.
        """
        args = tuple(
            icepool.expression.implicit_convert_to_expression(arg)
            for arg in args)
        if all(isinstance(arg, Pool) for arg in args):
            pools = cast(tuple[Pool, ...], args)
            keep_tuple: tuple[int, ...] = tuple(
                reduce(operator.add, (pool.keep_tuple() for pool in pools), ()))
            if len(keep_tuple) == 0:
                # All empty.
                return Pool._new_empty()
            if all(x == keep_tuple[0] for x in keep_tuple):
                # All sorted positions count the same, so we can merge the
                # pools.
                dice: 'MutableMapping[icepool.Die, int]' = defaultdict(int)
                for pool in pools:
                    for die, die_count in pool._dice:
                        dice[die] += die_count
                return Pool._new_from_mapping(dice, keep_tuple)
        return icepool.expression.MultisetExpression.disjoint_union(*args)

    def __mul__(self, other: int) -> 'Pool[T]':
        if not isinstance(other, int):
            return NotImplemented
        return self.multiply_counts(other)

    # Commutable in this case.
    def __rmul__(self, other: int) -> 'Pool[T]':
        if not isinstance(other, int):
            return NotImplemented
        return self.multiply_counts(other)

    def multiply_counts(self, constant: int, /) -> 'Pool[T]':
        return Pool._new_raw(self._dice,
                             tuple(x * constant for x in self.keep_tuple()))

    def __str__(self) -> str:
        return (
            f'Pool of {self.raw_size()} dice with keep_tuple={self.keep_tuple()}\n'
            + ''.join(f'  {repr(die)}\n' for die in self._dice_tuple))

    @cached_property
    def _key_tuple(self) -> tuple:
        return Pool, self._dice, self._keep_tuple


def make_keep_tuple(
        pool_size: int,
        index: int | slice | Sequence[int | EllipsisType]) -> tuple[int, ...]:
    """Expresses `index` as a keep_tuple.

    See `Pool.set_keep_tuple()` for details.

    Args:
        `pool_size`: An `int` specifying the size of the pool.
        `keep_tuple`: Raw specification for how the dice are to be counted.
    Raises:
        IndexError: If:
            * More than one `Ellipsis` is used.
            * An `Ellipsis` is used in the center with too few `pool_size`.
    """
    if isinstance(index, int):
        result = [0] * pool_size
        result[index] = 1
        return tuple(result)
    elif isinstance(index, slice):
        if index.step is not None:
            raise IndexError('step is not supported for pool subscripting')
        result = [0] * pool_size
        result[index] = [1] * len(result[index])
        return tuple(result)
    else:
        split = None
        for i, x in enumerate(index):
            if x is Ellipsis:
                if split is None:
                    split = i
                else:
                    raise IndexError(
                        'Cannot use more than one Ellipsis (...) for keep_tuple.'
                    )

        # The following code is designed to replace Ellipsis with actual zeros.
        index = cast('Sequence[int]', index)

        if split is None:
            if len(index) != pool_size:
                raise IndexError(
                    f'Length of {index} does not match pool size of {pool_size}'
                )
            return tuple(index)

        extra_dice = pool_size - len(index) + 1

        if split == 0:
            # Ellipsis on left.
            index = index[1:]
            if extra_dice < 0:
                return tuple(index[-extra_dice:])
            else:
                return (0,) * extra_dice + tuple(index)
        elif split == len(index) - 1:
            # Ellipsis on right.
            index = index[:-1]
            if extra_dice < 0:
                return tuple(index[:extra_dice])
            else:
                return tuple(index) + (0,) * extra_dice
        else:
            # Ellipsis in center.
            if extra_dice < 0:
                result = [0] * pool_size
                for i in range(min(split, pool_size)):
                    result[i] += index[i]
                reverse_split = split - len(index)
                for i in range(-1, max(reverse_split - 1, -pool_size - 1), -1):
                    result[i] += index[i]
                return tuple(result)
            else:
                return tuple(index[:split]) + (0,) * extra_dice + tuple(
                    index[split + 1:])


def standard_pool(
        die_sizes: Collection[int] | Mapping[int, int]) -> 'Pool[int]':
    """A `Pool` of standard dice (e.g. d6, d8...).

    Args:
        die_sizes: A collection of die sizes, which will put one die of that
            sizes in the pool for each element.
            Or, a mapping of die sizes to how many dice of that size to put
            into the pool.
            If empty, the pool will be considered to consist of 0d1.
    """
    if not die_sizes:
        return Pool({1: 0})
    if isinstance(die_sizes, Mapping):
        die_sizes = list(
            itertools.chain.from_iterable(
                [k] * v for k, v in die_sizes.items()))
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
