__docformat__ = 'google'

import icepool
import icepool.math

import bisect
from collections import defaultdict
from functools import cached_property
import math


def canonicalize_pool_args(die, num_dice, count_dice, truncate_min,
                           truncate_max):
    """Converts arguments to `Pool()` into a standard form.

    Returns:
        die:
        count_dice: In tuple form.
        truncate_min: In tuple form, or `None` if there is no truncation on this side.
        truncate_max: In tuple form, or `None` if there is no truncation on this side.
        convert_to_die: Iff `True`, `Pool()` should return a `Die` rather than
            a `Pool`.
    """
    if truncate_min is not None and truncate_max is not None:
        raise ValueError(
            'A pool cannot have both truncate_min and truncate_max.')

    # Compute num_dice and count_dice.

    for seq in (truncate_min, truncate_max):
        if hasattr(seq, '__len__'):
            if num_dice is not None and num_dice != len(seq):
                raise ValueError(
                    'Conflicting values for the number of dice: ' +
                    f'num_dice={num_dice}, truncate_min={truncate_min}, truncate_max={truncate_max}'
                )
            else:
                num_dice = len(seq)

    convert_to_die = isinstance(count_dice, int)

    if num_dice is None:
        # Default to zero dice, unless count_dice has something to say.
        count_dice = count_dice_tuple(0, count_dice)
        num_dice = len(count_dice)
    else:
        # Must match num_dice.
        count_dice = count_dice_tuple(num_dice, count_dice)
        if len(count_dice) != num_dice:
            raise ValueError(
                f'The length of count_dice={count_dice} conflicts with num_dice={num_dice}.'
            )

    # Put truncation into standard form.
    # This is either a sorted tuple, or `None` if there is no (effective) limit
    # to the die size on that side.
    # Values will also be clipped to the range of the fundamental die.

    if num_dice == 0:
        truncate_min = None
        truncate_max = None
    else:
        if truncate_min is not None:
            if max(truncate_min) > die.min_outcome():
                if min(truncate_min) < die.min_outcome():
                    raise ValueError(
                        'truncate_min cannot be < the min_outcome of the die.')
                # We can't truncate the die to truncate_min since it may upset
                # the iteration order.
                truncate_min = tuple(
                    sorted(die.nearest_ge(outcome) for outcome in truncate_min))
            else:
                # In this case, the truncate_min don't actually do anything.
                truncate_min = None
        if truncate_max is not None:
            if min(truncate_max) < die.max_outcome():
                if max(truncate_max) > die.max_outcome():
                    raise ValueError(
                        'truncate_max cannot be > the max_outcome of the die.')
                # We can't truncate the die to truncate_max since it may upset
                # the iteration order.
                truncate_max = tuple(
                    sorted(die.nearest_le(outcome) for outcome in truncate_max))
            else:
                # In this case, the truncate_max don't actually do anything.
                truncate_max = None

    return die, count_dice, truncate_min, truncate_max, convert_to_die


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


def standard_pool(*die_sizes, count_dice=None):
    """Creates a pool of standard dice.

    For example, `standard_pool(8, 8, 6, 6, 6)` would be a pool of 2 d8s and 3 d6s.

    If no die sizes are given, the pool will consist of zero d1s.

    Args:
        *die_sizes: The size of each die in the pool.
        count_dice: Which dice will be counted, as `Pool()`.
            As with `Pool()`, you can also use the `[]` operator after the fact.
            For example, `standard_pool(8, 8, 6, 6, 6)[-2:]` would keep the
            highest two dice of 2 d8s and 3 d6s.
    """
    if len(die_sizes) == 0:
        return Pool(icepool.d1, num_dice=0)
    return Pool(icepool.d(max(die_sizes)),
                count_dice=count_dice,
                truncate_max=die_sizes)


class Pool(icepool.PoolBase):
    """Represents set of (mostly) indistiguishable dice.

    This should be used in conjunction with `EvalPool` to generate a result.

    A pool is defined by:

    * A fundamental die.
    * The number of dice in the pool.
    * Which of the sorted positions are counted (possibly multiple or negative
        times).
    * Possibly truncating the max or min outcomes of dice in the pool
        (but not both) relative to the fundamental die.
    """

    def __new__(cls,
                die,
                num_dice=None,
                *,
                count_dice=None,
                truncate_min=None,
                truncate_max=None):
        """Constructor for a pool.

        You can use `die.pool(num_dice=None, ...)` for the same effect as this.

        All instances are cached. The members of the actual instance may not match
        the arguments exactly; instead, they may be optimized to values that give
        the same result as far as `EvalPool` is concerned.

        Args:
            die: The fundamental die of the pool.
                If outcomes are not reachable by any die due to `truncate_min` or
                `truncate_max`, they will have 0 count. Zero-weight outcomes will
                appear with zero weight, but can still generate nonzero counts.
            num_dice: An `int` that sets the number of dice in the pool.
                If not provided, the number of dice will be inferred from the other
                arguments. If no arguments are provided at all, this defaults to 0.
            count_dice: Determines which of the **sorted** dice will be counted,
                and how many times. Prefer to use the `Pool`'s `[]` operator
                after the fact rather than providing an argument here.
                This operator is an alias for `Pool.set_count_dice()`.
                See that method's docstring for details.
            truncate_max: A sequence of one outcome per die in the pool.
                That die will be truncated to that maximum outcome, with all greater
                outcomes having 0 count. Values cannot be > the `max_outcome` of the
                fundamental die. A pool cannot have both `truncate_min` and
                `truncate_max`.This can be used to efficiently roll a set of mixed
                standard dice. For example,
                `Pool(icepool.d12, truncate_max=[6, 6, 6, 8, 8])`
                would be a pool of 3d6 and 2d8.
            truncate_min: A sequence of one outcome per die in the pool.
                That die will be truncated to that minimum outcome, with all lesser
                outcomes having 0 count. Values cannot be < the `min_outcome` of the
                fundamental die. A pool cannot have both `truncate_min` and
                `truncate_max`.

        Returns:
            A `Pool` instance. If `count_dice` is a single `int` index, the
            result will be a `Die` rather than a `Pool`.

        Raises:
            `ValueError` if arguments result in a conflicting number of dice,
            if both `truncate_min` and `truncate_max` are provided,
            or if truncation would produce an empty die.
        """
        die, count_dice, truncate_min, truncate_max, convert_to_die = canonicalize_pool_args(
            die, num_dice, count_dice, truncate_min, truncate_max)

        self = Pool._pool_cached_unchecked(die, count_dice, truncate_min,
                                           truncate_max)

        if convert_to_die:
            return self.eval(lambda state, outcome, count: outcome
                             if count else state)
        else:
            return self

    _instance_cache = {}

    @classmethod
    def _pool_cached_unchecked(cls,
                               die,
                               count_dice,
                               truncate_min=None,
                               truncate_max=None):
        key = (die.key_tuple(), count_dice, truncate_min, truncate_max)
        if key in Pool._instance_cache:
            return Pool._instance_cache[key]
        else:
            self = super(Pool, cls).__new__(cls)
            self._die = die
            self._count_dice = count_dice
            self._truncate_max = truncate_max
            self._truncate_min = truncate_min
            Pool._instance_cache[key] = self
            return self

    def _is_single_roll(self):
        return False

    def die(self):
        """The fundamental die of the pool. """
        return self._die

    def outcomes(self):
        return self.die().outcomes()

    def _min_outcome(self):
        return self.die().min_outcome()

    def _max_outcome(self):
        return self.die().max_outcome()

    def count_dice(self):
        """A tuple indicating how many times each of the dice, sorted from lowest to highest, counts. """
        return self._count_dice

    def num_dice(self):
        """The number of dice in this pool (before dropping or counting multiple times). """
        return len(self._count_dice)

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
                In this case, the result will be a die, not a pool.
            A `slice`. The selected dice are counted once each.
                If provided, the third argument resizes the pool,
                rather than being a step,
                but only if the pool does not have `truncate_max` or `truncate_min`.
            A sequence of one `int`s for each die.
                Each die is counted that many times, which could be multiple or
                negative times. This may resize the pool, but only if the pool
                does not have `truncate_max` or `truncate_min`.

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
                `truncate_max` or `truncate_min`, or if more than one `Ellipsis`
                is used.
        """
        convert_to_die = isinstance(count_dice, int)
        count_dice = count_dice_tuple(self.num_dice(), count_dice)
        if len(count_dice) != self.num_dice():
            if self.truncate_max() is not None:
                raise ValueError(
                    'Cannot change the size of a pool with truncate_max.')
            if self.truncate_min() is not None:
                raise ValueError(
                    'Cannot change the size of a pool with truncate_min.')
        result = Pool._pool_cached_unchecked(self.die(),
                                             count_dice=count_dice,
                                             truncate_max=self.truncate_max(),
                                             truncate_min=self.truncate_min())
        if convert_to_die:
            return result.eval(lambda state, outcome, count: outcome
                               if count else state)
        else:
            return result

    __getitem__ = set_count_dice

    def __iter__(self):
        raise TypeError("'Pool' object is not iterable")

    @cached_property
    def _num_drop_lowest(self):
        """How many elements of count_dice on the low side are falsy. """
        for i, count in enumerate(self.count_dice()):
            if count:
                return i
        return self.num_dice()

    def _direction_score_ascending(self):
        return self._num_drop_lowest * len(self.outcomes())

    @cached_property
    def _num_drop_highest(self):
        """How many elements of count_dice on the high side are falsy. """
        for i, count in enumerate(reversed(self.count_dice())):
            if count:
                return i
        return self.num_dice()

    def _direction_score_descending(self):
        return self._num_drop_highest * len(self.outcomes())

    def truncate_min(self, always_tuple=False):
        """A sorted tuple of thresholds below which outcomes are truncated, one for each die in the pool.

        Args:
            always_tuple: If `False`, this will return `None` if there are no
                die-specific `truncate_min`. If `True` this will return a
                `tuple` even in this case.
        """
        if self._truncate_min is None and always_tuple:
            return (self.die().min_outcome(),) * self.num_dice()
        return self._truncate_min

    def _has_truncate_min(self):
        return self._truncate_min is not None

    def truncate_max(self, always_tuple=False):
        """A sorted tuple of thresholds above which outcomes are truncated, one for each die in the pool.

        Args:
            always_tuple: If `False`, this will return `None` if there are no
                die-specific `truncate_min`. If `True` this will return a
                `tuple` even in this case.
        """
        if self._truncate_max is None and always_tuple:
            return (self.die().max_outcome(),) * self.num_dice()
        return self._truncate_max

    def _has_truncate_max(self):
        return self._truncate_max is not None

    def _iter_pop_min(self):
        """
        Yields:
            From 0 to the number of dice that can roll this outcome inclusive:
            * pool: A `Pool` resulting from removing that many dice from
                this `Pool`, while also removing the min outcome.
                If there is only one outcome with weight remaining, only one
                result will be yielded, corresponding to all dice rolling that outcome.
                If the outcome has zero weight, only one result will be yielded,
                corresponding to zero dice rolling that outcome.
                If there are no outcomes remaining, this will be `None`.
            * count: An `int` indicating the number of selected dice that rolled
                the removed outcome.
            * weight: An `int` indicating the weight of that many dice rolling
                the removed outcome.
        """

        # The near-duplication of code with pop_max is unfortunate.
        # However, the alternative of reversing the storage order of die_counts and truncate_min seems even worse.

        truncate_min = self.truncate_min(always_tuple=True)
        num_possible_dice = bisect.bisect_right(truncate_min,
                                                self.die().min_outcome())
        popped_die, outcome, single_weight = self.die()._pop_min()

        if popped_die.is_empty():
            # This is the last outcome. All dice must roll this outcome.
            pool = Pool._pool_cached_unchecked(popped_die, count_dice=())
            remaining_count = sum(self.count_dice())
            weight = single_weight**num_possible_dice
            yield pool, remaining_count, weight
            return

        # Consider various numbers of dice rolling this outcome.
        popped_truncate_min = (popped_die.min_outcome(
        ),) * num_possible_dice + truncate_min[num_possible_dice:]
        popped_count_dice = self.count_dice()
        count = 0

        comb_row = icepool.math.comb_row(num_possible_dice, single_weight)
        end_counted = self.num_dice() - self._num_drop_highest
        for weight in comb_row[:min(num_possible_dice, end_counted)]:
            pool = Pool._pool_cached_unchecked(popped_die,
                                               count_dice=popped_count_dice,
                                               truncate_min=popped_truncate_min)
            yield pool, count, weight
            count += popped_count_dice[0]
            popped_truncate_min = popped_truncate_min[1:]
            popped_count_dice = popped_count_dice[1:]

        if end_counted > num_possible_dice:
            pool = Pool._pool_cached_unchecked(popped_die,
                                               count_dice=popped_count_dice,
                                               truncate_min=popped_truncate_min)
            yield pool, count, comb_row[-1]
        else:
            # In this case, we ran out of counted dice before running out of
            # dice that could roll the outcome.
            # We empty the rest of the pool immediately since no more dice can
            # contribute counts.
            skip_weight = 0
            for weight in comb_row[end_counted:]:
                skip_weight *= popped_die.denominator()
                skip_weight += weight
            skip_weight *= math.prod(
                popped_die.weight_ge(min_outcome)
                for min_outcome in truncate_min[num_possible_dice:])
            pool = Pool._pool_cached_unchecked(popped_die, count_dice=())
            yield pool, count, skip_weight

    def _iter_pop_max(self):
        """
        Yields:
            From 0 to the number of dice that can roll this outcome inclusive:
            * pool: A `Pool` resulting from removing that many dice from
                this `Pool`, while also removing the max outcome.
                If there is only one outcome with weight remaining, only one
                result will be yielded, corresponding to all dice rolling that
                outcome.
                If the outcome has zero weight, only one result will be yielded,
                corresponding to zero dice rolling that outcome.
                If there are no outcomes remaining, this will be `None`.
            * count: An `int` indicating the number of selected dice that rolled
                the removed outcome.
            * weight: An `int` indicating the weight of that many dice rolling
                the removed outcome.
        """
        truncate_max = self.truncate_max(always_tuple=True)
        num_possible_dice = self.num_dice() - bisect.bisect_left(
            truncate_max,
            self.die().max_outcome())
        num_unused_dice = self.num_dice() - num_possible_dice
        popped_die, outcome, single_weight = self.die()._pop_max()

        if popped_die.is_empty():
            # This is the last outcome. All dice must roll this outcome.
            pool = Pool._pool_cached_unchecked(popped_die, count_dice=())
            remaining_count = sum(self.count_dice())
            weight = single_weight**num_possible_dice
            yield pool, remaining_count, weight
            return

        # Consider various numbers of dice rolling this outcome.
        popped_truncate_max = truncate_max[:num_unused_dice] + (
            popped_die.max_outcome(),) * num_possible_dice
        popped_count_dice = self.count_dice()
        count = 0

        comb_row = icepool.math.comb_row(num_possible_dice, single_weight)
        end_counted = self.num_dice() - self._num_drop_lowest
        for weight in comb_row[:min(num_possible_dice, end_counted)]:
            pool = Pool._pool_cached_unchecked(popped_die,
                                               count_dice=popped_count_dice,
                                               truncate_max=popped_truncate_max)
            yield pool, count, weight
            count += popped_count_dice[-1]
            popped_truncate_max = popped_truncate_max[:-1]
            popped_count_dice = popped_count_dice[:-1]

        if end_counted > num_possible_dice:
            pool = Pool._pool_cached_unchecked(popped_die,
                                               count_dice=popped_count_dice,
                                               truncate_max=popped_truncate_max)
            yield pool, count, comb_row[-1]
        else:
            # In this case, we ran out of counted dice before running out of
            # dice that could roll the outcome.
            # We empty the rest of the pool immediately since no more dice can
            # contribute counts.
            skip_weight = 0
            for weight in comb_row[end_counted:]:
                skip_weight *= popped_die.denominator()
                skip_weight += weight
            skip_weight *= math.prod(
                popped_die.weight_le(max_outcome)
                for max_outcome in truncate_max[:num_unused_dice])
            pool = Pool._pool_cached_unchecked(popped_die, count_dice=())
            yield pool, count, skip_weight

    @cached_property
    def _popped_min(self):
        if self.truncate_max() is not None:
            raise ValueError('pop_min is not valid with truncate_min.')
        return tuple(self._iter_pop_min())

    def _pop_min(self):
        """Returns a sequence of pool, count, weight corresponding to removing the min outcome.

        Count and weight correspond to various numbers of dice rolling that outcome.
        """
        return self._popped_min

    @cached_property
    def _popped_max(self):
        if self.truncate_min() is not None:
            raise ValueError('pop_max is not valid with truncate_min.')
        return tuple(self._iter_pop_max())

    def _pop_max(self):
        """Returns a sequence of pool, count, weight corresponding to removing the max outcome.

        Count and weight correspond to various numbers of dice rolling that outcome.
        """
        return self._popped_max

    def has_counted_dice(self):
        """Returns `True` iff any of the remaining dice are counted a nonzero number of times.

        This is used to skip to the base case when there are no more dice to consider.
        """
        return any(self.count_dice())

    def sample(self):
        """Samples a roll from this pool.

        Returns:
            A dict mapping outcomes to counts representing a single roll of this pool.
        """
        raw_rolls = []
        for min_outcome, max_outcome in zip(self.truncate_min(True),
                                            self.truncate_max(True)):
            die = self.die().truncate(min_outcome, max_outcome)
            raw_rolls.append(die.sample())
        raw_rolls = sorted(raw_rolls)
        data = defaultdict(int)
        for roll, count in zip(raw_rolls, self.count_dice()):
            data[roll] += count
        return data

    @cached_property
    def _key_tuple(self):
        return self.die().key_tuple(), self.count_dice(), self.truncate_min(
        ), self.truncate_max()

    def __eq__(self, other):
        if not isinstance(other, Pool):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self):
        return hash(self._key_tuple)

    def __hash__(self):
        return self._hash

    def __str__(self):
        return '\n'.join([
            str(self.die()),
            str(self.count_dice()),
            str(self.truncate_min()),
            str(self.truncate_max())
        ])
