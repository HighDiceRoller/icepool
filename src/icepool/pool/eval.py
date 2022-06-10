__docformat__ = 'google'

import icepool
from icepool.pool.alignment import EvalPoolAlignment
from icepool.pool.cost import estimate_costs

from abc import ABC, abstractmethod
from collections import defaultdict
from functools import cached_property
import itertools
import math

from typing import Any, Callable, Hashable
from collections.abc import Collection, Mapping, MutableMapping

PREFERRED_DIRECTION_COST_FACTOR = 10
"""The preferred direction will be weighted this times as much."""


class EvalPool(ABC):
    """An abstract, immutable, callable class for evaulating one or more `Pool`s.

    There is one abstract method to implement: `next_state()`.
    This should incrementally calculate the result of the roll
    given one outcome at a time along with how many dice rolled that outcome.
    An example sequence of calls, as far as `next_state()` is concerned, is:

    1. `state = next_state(state=None, outcome=1, count=how_many_dice_rolled_1)`
    2. `state = next_state(state, 2, how_many_dice_rolled_2)`
    3. `state = next_state(state, 3, how_many_dice_rolled_3)`
    4. `state = next_state(state, 4, how_many_dice_rolled_4)`
    5. `state = next_state(state, 5, how_many_dice_rolled_5)`
    6. `state = next_state(state, 6, how_many_dice_rolled_6)`
    7. `outcome = final_outcome(state, *pools)`

    A few other methods can optionally be overridden to further customize behavior.

    It is not expected that subclasses of `EvalPool`
    be able to handle arbitrary types or numbers of pools.
    Indeed, most are expected to handle only a fixed number of pools,
    and often even only pools with a particular type of die.

    Instances cache all intermediate state distributions.
    You should therefore reuse instances when possible.

    Instances should not be modified after construction
    in any way that affects the return values of these methods.
    Otherwise, values in the cache may be incorrect.
    """

    @abstractmethod
    def next_state(self, state: Hashable, outcome, /, *counts: int) -> Hashable:
        """State transition function.

        This should produce a state given the previous state, an outcome,
        and the number of dice in each pool rolling that outcome.

        Within `eval()`, this will be called using only positional arguments.
        Thus, you may rename any of the arguments if you wish.

        Make sure to handle the base case where `state is None`.

        Args:
            state: A hashable object indicating the state before rolling the
                current outcome. If there was no previous outcome, this will be
                `None`.
            outcome: The current outcome.
                `next_state` will see all rolled outcomes in monotonic order;
                either ascending or descending depending on `direction()`.
                If there are multiple pools, the set of outcomes is the union of
                the outcomes of the invididual pools. All outcomes with nonzero
                count will be visited. Outcomes with zero count may or may not
                be visited. If you need to enforce that certain outcomes are'
                visited even if they have zero count, see `alignment()`.
            *counts: One `int` for each pool indicating how many dice in that
                pool rolled the current outcome. If there are multiple pools,
                it's possible that some outcomes will not appear in all pools.
                In this case, the count for the pool(s) that do not have the
                outcome will be 0. Zero-weight outcomes count as having that outcome.

                Most subclasses will expect a fixed number of pools and
                can replace this variadic parameter with a fixed number of named
                parameters.

        Returns:
            A hashable object indicating the next state.
            The special value `icepool.Reroll` can be used to immediately remove
            the state from consideration, effectively performing a full reroll
            of the pool.
        """

    def final_outcome(self, final_state: Hashable, /,
                      *pools: icepool.Pool) -> Any:
        """Optional function to generate a final outcome from a final state.

        Within `eval()`, this will be called using only positional arguments.
        Thus, you may rename any of the arguments if you wish.

        By default, the final outcome is equal to the final state.
        Note that `None` is not a valid outcome for a die,
        and if all pools consist of empty dice, the final state will be `None`.
        Subclasses that want to handle this case should explicitly define what
        happens.

        Args:
            final_state: A state after all outcomes have been processed.
            *pools: One or more `Pool`s being evaluated.
                Most subclasses will expect a fixed number of pools and
                can replace this variadic parameter with a fixed number of named
                parameters.

        Returns:
            A final outcome that will be used as part of constructing the result die.
            As usual for `Die()`, this could itself be a die or `icepool.Reroll`.
        """
        return final_state

    def direction(self, *pools: icepool.Pool) -> int:
        """Optional function to determine the direction in which `next_state()` will see outcomes.

        The default is ascending order. This works well with mixed standard dice,
        and other dice that differ only by right-truncation.

        Args:
            *pools: One or more `Pool`s being evaluated.
                Most subclasses will expect a fixed number of pools and
                can replace this variadic parameter with a fixed number of named
                parameters.

        Returns:
            * > 0 if `next_state()` should always see the outcomes in ascending order.
            * < 0 if `next_state()` should always see the outcomes in descending order.
            * 0 if the order may be determined automatically.
        """
        return 1

    def alignment(self, *pools: icepool.Pool) -> Collection:
        """Optional function to specify an iterable of outcomes that should always be given to `next_state()` even if they have zero count.

        The default implementation returns `()`; this means outcomes with zero
        count may or may not be seen by `next_state`.

        If you want the outcomes seen by `next_state` to be consecutive
        `int`s, you can set `alignment = icepool.EvalPool.range_alignment`.
        See `range_alignment()` below.

        Returns:
            An iterable of outcomes that should be given to `next_state()` even
            if they have zero count.
        """
        return ()

    def range_alignment(self, *pools: icepool.Pool) -> Collection[int]:
        """Example implementation of `alignment()` that produces consecutive `int` outcomes.

        Set `alignment = icepool.EvalPool.range_alignment` to use this.

        Returns:
            All `int`s from the min outcome to the max outcome among the pools,
            inclusive.

        Raises:
            `TypeError` if any pool has any non-`int` outcome.
        """
        if len(pools) == 0:
            return ()

        if any(
                any(not isinstance(x, int)
                    for x in pool.outcomes())
                for pool in pools):
            raise TypeError(
                "range_alignment cannot be used with outcomes of type other than 'int'."
            )

        min_outcome = min(pool.min_outcome() for pool in pools)
        max_outcome = max(pool.max_outcome() for pool in pools)
        return range(min_outcome, max_outcome + 1)

    @cached_property
    def _cache(self) -> MutableMapping[Any, Mapping[Any, int]]:
        """A cache of (direction, pools) -> weight distribution over states. """
        return {}

    def eval(
            self, *pools: icepool.Pool | Mapping[Any, int] | Collection
    ) -> 'icepool.Die':
        """Evaluates pools.

        You can call the `EvalPool` object directly for the same effect,
        e.g. `sum_pool(pool)` is an alias for `sum_pool.eval(pool)`.

        Args:
            *pools: Each element may be one of the following:
                * A `Pool` representing possible rolls of a pool.
                * A dict-like representing a single roll of a pool.
                    The dict maps outcomes to counts.
                * A collection of outcomes representing a single roll of a pool.
                    Outcomes are treated as having 1 count per appearance.
                Most evaluators will expect a fixed number of pools.
                The union of the outcomes of the pools must be totally orderable.

        Returns:
            A die representing the distribution of the final score.
            If all pools are `PoolRoll`s, the result is a single outcome instead.
        """

        # Convert non-pool arguments to `Pool`.
        converted_pools = tuple(
            pool if isinstance(pool, icepool.Pool) else icepool.Pool(*pool)
            for pool in pools)

        if any(pool.has_empty_dice() for pool in converted_pools):
            return icepool.Die()

        algorithm, direction = self._select_algorithm(*converted_pools)

        # We can't reuse the Pool class for alignment because it is expected
        # to skip outcomes.
        alignment = EvalPoolAlignment(self.alignment(*converted_pools))

        dist = algorithm(direction, alignment, tuple(converted_pools))

        final_outcomes = []
        final_weights = []
        for state, weight in dist.items():
            outcome = self.final_outcome(state, *converted_pools)
            if outcome is None:
                raise TypeError(
                    "None is not a valid final outcome. "
                    "This may have resulted from supplying an empty pool to EvalPool. "
                    "If so, refrain from using empty pools, or override EvalPool.final_outcome() to handle this case."
                )
            if outcome is not icepool.Reroll:
                final_outcomes.append(outcome)
                final_weights.append(weight)

        return icepool.Die(*final_outcomes, weights=final_weights)

    __call__ = eval

    def _select_algorithm(self, *pools: icepool.Pool) -> tuple[Callable, int]:
        """Selects an algorithm and iteration direction.

        Returns:
            * The algorithm to use (`_eval_internal*`).
            * The direction in which `next_state()` sees outcomes.
                1 for ascending and -1 for descending.

        """
        eval_direction = self.direction(*pools)

        pop_min_costs, pop_max_costs = zip(
            *(estimate_costs(pool) for pool in pools))

        pop_min_cost = math.prod(pop_min_costs)
        pop_max_cost = math.prod(pop_max_costs)

        # No preferred direction case: go directly with cost.
        if eval_direction == 0:
            if pop_max_cost <= pop_min_cost:
                return self._eval_internal, 1
            else:
                return self._eval_internal, -1

        # Preferred direction case.
        # Go with the preferred direction unless there is a "significant"
        # cost factor.

        if PREFERRED_DIRECTION_COST_FACTOR * pop_max_cost < pop_min_cost:
            cost_direction = 1
        elif PREFERRED_DIRECTION_COST_FACTOR * pop_min_cost < pop_max_cost:
            cost_direction = -1
        else:
            cost_direction = 0

        if cost_direction == 0 or eval_direction == cost_direction:
            # Use the preferred algorithm.
            return self._eval_internal, eval_direction
        else:
            # Use the less-preferred algorithm.
            return self._eval_internal_iterative, eval_direction

    def _eval_internal(self, direction: int, alignment: EvalPoolAlignment,
                       pools: tuple[icepool.Pool, ...]) -> Mapping[Any, int]:
        """Internal algorithm for iterating in the more-preferred direction,
        i.e. giving outcomes to `next_state()` from wide to narrow.

        All intermediate return values are cached in the instance.

        Arguments:
            direction: The direction in which to send outcomes to `next_state()`.
            alignment: As `alignment()`. Elements will be popped off this
                during recursion.
            pools: One or more `Pool`s to evaluate. Elements will be popped off
                this during recursion.

        Returns:
            A dict `{ state : weight }` describing the probability distribution
                over states.
        """
        cache_key = (direction, alignment, pools)
        if cache_key in self._cache:
            return self._cache[cache_key]

        result: MutableMapping[Any, int] = defaultdict(int)

        if all(pool.is_empty() for pool in pools) and alignment.is_empty():
            result = {None: 1}
        else:
            outcome, prev_alignment, iterators = _pop_pools(
                direction, alignment, pools)
            for p in itertools.product(*iterators):
                prev_pools, counts, weights = zip(*p)
                prod_weight = math.prod(weights)
                prev = self._eval_internal(direction, prev_alignment,
                                           prev_pools)
                for prev_state, prev_weight in prev.items():
                    state = self.next_state(prev_state, outcome, *counts)
                    if state is not icepool.Reroll:
                        result[state] += prev_weight * prod_weight

        self._cache[cache_key] = result
        return result

    def _eval_internal_iterative(
            self, direction: int, alignment: EvalPoolAlignment,
            pools: tuple[icepool.Pool, ...]) -> Mapping[Any, int]:
        """Internal algorithm for iterating in the less-preferred direction,
        i.e. giving outcomes to `next_state()` from narrow to wide.

        This algorithm does not perform persistent memoization.
        """
        if all(pool.is_empty() for pool in pools) and alignment.is_empty():
            return {None: 1}
        dist: MutableMapping[Any, int] = defaultdict(int)
        dist[None, alignment, pools] = 1
        final_dist: MutableMapping[Any, int] = defaultdict(int)
        while dist:
            next_dist: MutableMapping[Any, int] = defaultdict(int)
            for (prev_state, prev_alignment,
                 prev_pools), weight in dist.items():
                # The direction flip here is the only purpose of this algorithm.
                outcome, alignment, iterators = _pop_pools(
                    -direction, prev_alignment, prev_pools)
                for p in itertools.product(*iterators):
                    pools, counts, weights = zip(*p)
                    prod_weight = math.prod(weights)
                    state = self.next_state(prev_state, outcome, *counts)
                    if state is not icepool.Reroll:
                        if all(pool.is_empty() for pool in pools):
                            final_dist[state] += weight * prod_weight
                        else:
                            next_dist[state, alignment,
                                      pools] += weight * prod_weight
            dist = next_dist
        return final_dist


def _pop_pools(
        side: int, alignment: EvalPoolAlignment,
        pools: tuple[icepool.Pool,
                     ...]) -> tuple[Any, EvalPoolAlignment, tuple]:
    """Pops a single outcome from the pools.

    Returns:
        * The popped outcome.
        * The remaining alignment.
        * A tuple of iterators over the possible resulting pools, counts, and weights.
    """
    alignment_and_pools = (alignment,) + pools
    if side >= 0:
        outcome = max(pool.max_outcome()
                      for pool in alignment_and_pools
                      if not pool.is_empty())

        return outcome, alignment._pop_max(outcome), tuple(
            pool._pop_max(outcome) for pool in pools)
    else:
        outcome = min(pool.min_outcome()
                      for pool in alignment_and_pools
                      if not pool.is_empty())
        if not alignment.is_empty():
            outcome = min(outcome, alignment.min_outcome())

        return outcome, alignment._pop_min(outcome), tuple(
            pool._pop_min(outcome) for pool in pools)


class WrapFuncEval(EvalPool):
    """An `EvalPool` created from a single provided function.

    `next_state()` simply calls that function.
    """

    def __init__(self, func: Callable, /):
        """Constructs a new instance given the function that should be called for `next_state()`.
        Args:
            func(state, outcome, *counts): This should take the same arguments
                as `next_state()`, minus `self`, and return the next state.
        """
        self._func = func

    def next_state(self, state, outcome, *counts: int):
        return self._func(state, outcome, *counts)


class JointEval(EvalPool):
    """EXPERIMENTAL: An `EvalPool` that jointly evaluates subevals on the same roll(s) of a pool.

    It may be more efficient to write the joint evaluation directly; this is
    provided as a convenience.
    """

    def __init__(self, *subevals: 'EvalPool'):
        self._subevals = subevals

    def next_state(self, state, outcome, *counts: int):
        """Runs `next_state` for all subevals.

        The state is a tuple of the substates.
        """
        if state is None:
            return tuple(
                subeval.next_state(None, outcome, *counts)
                for subeval in self._subevals)
        else:
            return tuple(
                subeval.next_state(substate, outcome, *counts)
                for subeval, substate in zip(self._subevals, state))

    def final_outcome(self, final_state, *pools: icepool.Pool):
        """Runs `final_state` for all subevals.

        The final outcome is a tuple of the final suboutcomes.
        """
        return tuple(
            subeval.final_outcome(final_substate, *pools)
            for subeval, final_substate in zip(self._subevals, final_state))

    def direction(self, *pools: icepool.Pool):
        """Determines the common direction of the subevals.

        Raises:
            ValueError: If subevals have conflicting directions, i.e. some are
                ascending and others are descending.
        """
        subdirections = tuple(
            subeval.direction(*pools) for subeval in self._subevals)
        ascending = any(x > 0 for x in subdirections)
        descending = any(x < 0 for x in subdirections)
        if ascending and descending:
            raise ValueError('Sub-evals have conflicting directions.')
        elif ascending:
            return 1
        elif descending:
            return -1
        else:
            return 0


class SumPool(EvalPool):
    """A simple `EvalPool` that just sums the dice in a pool. """

    def next_state(self, state, outcome, count):
        """Add the dice to the running total. """
        if state is None:
            return outcome * count
        else:
            return state + outcome * count

    def final_outcome(self, final_state, *pools):
        if final_state is None:
            return 0
        else:
            return final_state

    def direction(self, *pools):
        """This eval doesn't care about direction. """
        return 0


sum_pool = SumPool()
"""A shared `SumPool` object for caching results. """


class EnumeratePool(EvalPool):
    """A `EvalPool` that enumerates all possible (sorted) rolls of a single pool.

    This is expensive and not recommended unless few dice are being kept.
    """

    def __init__(self, direction=1):
        """`direction` determines the sort order.

        Positive for ascending and negative for descending.
        """
        self._direction = direction

    def next_state(self, state, outcome, count):
        if state is None:
            return (outcome,) * count
        else:
            return state + (outcome,) * count

    def direction(self, pool):
        if any(x < 0 for x in pool.count_dice()):
            raise ValueError(
                'EnumeratePool is not compatible with negative counts.')
        return self._direction


enumerate_pool = EnumeratePool()
"""A shared `EnumeratePool` object for caching results. """


class FindBestSet(EvalPool):
    """A `EvalPool` that takes the best matching set in a pool.

    This prioritizes set size, then the outcome.

    The outcomes are `(set_size, outcome)`.
    """

    def next_state(self, state, outcome, count):
        """Replace the last best set if this one is better.

        Note the use of tuple comparison, which priortizes elements to the left.
        """
        if state is None:
            return count, outcome
        else:
            return max(state, (count, outcome))

    def direction(self, *pools):
        """This eval doesn't care about direction. """
        return 0


class FindBestRun(EvalPool):
    """A `EvalPool` that takes the best run (aka "straight") in a pool.

    Outcomes must be `int`s.

    This prioritizes run size, then the outcome.

    The outcomes are `(run_size, outcome)`.
    """

    def next_state(self, state, outcome, count):
        """Increments the current run if at least one die rolled this outcome,
        then saves the run to the state.
        """
        best_run, best_run_outcome, run = state or (0, outcome, 0)
        if count >= 1:
            run += 1
        else:
            run = 0
        return max((run, outcome), (best_run, best_run_outcome)) + (run,)

    def final_outcome(self, final_state, *pools):
        """Returns the best run. """
        return final_state[:2]

    def direction(self, *pools):
        """This only considers outcomes in ascending order. """
        return 1

    alignment = EvalPool.range_alignment
