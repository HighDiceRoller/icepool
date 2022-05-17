__docformat__ = 'google'

import icepool

from abc import ABC, abstractmethod
from collections import defaultdict
from functools import cached_property
import itertools
import math


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
    def next_state(self, state, outcome, *counts):
        """State transition function.

        This should produce a state given the previous state, an outcome,
        and the number of dice in each pool rolling that outcome.

        Make sure to handle the base case where `state is None`.

        Args:
            state: A hashable object indicating the state before rolling the
                current outcome. If there was no previous outcome, this will be
                `None`.
            outcome: The current outcome.
                `next_state` will see all outcomes in monotonic order,
                either ascending or descending depending on `direction()`.
                If there are multiple pools, the set of outcomes is the union of
                the outcomes of the invididual pools.
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

    def final_outcome(self, final_state, *pools):
        """Optional function to generate a final outcome from a final state.

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

    def direction(self, *pools):
        """Optional function to determine the direction in which `next_state()` will see outcomes.

        Note that an ascending (> 0) direction is not compatible with pools with
        `truncate_min`, and a descending (< 0) direction is not compatible with
        pools with `truncate_max`.

        The default is ascending order.

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

    @cached_property
    def _cache(self):
        """A cache of (direction, pools) -> weight distribution over states. """
        return {}

    def eval(self, *pools):
        """Evaluates pools.

        You can call the `EvalPool` object directly for the same effect,
        e.g. `sum_pool(pool)` is an alias for `sum_pool.eval(pool)`.

        Args:
            *pools: Each element may be one of the following:
                * A `Pool` representing possible rolls of a pool.
                * A dict-like representing a single roll of a pool.
                    The dict maps outcomes to counts.
                * A sequence of outcomes representing a single roll of a pool.
                    Outcomes are treated as having 1 count per appearance.
                Most evaluators will expect a fixed number of pools.
                The union of the outcomes of the pools must be totally orderable.
                Pools with `truncate_min` and pools with `truncate_max` are not
                compatible with each other.

        Returns:
            A die representing the distribution of the final score.
            If all pools are `PoolRoll`s, the result is a single outcome instead.
        """

        # Convert non-pool arguments to `PoolBase`.
        pools = [
            pool
            if isinstance(pool, icepool.PoolBase) else icepool.PoolRoll(pool)
            for pool in pools
        ]

        algorithm, direction = self._select_algorithm(*pools)

        dist = algorithm(direction, *pools)

        if all(pool._is_single_roll() for pool in pools):
            for state in dist.keys():
                # Return a single outcome.
                return state
        else:
            final_outcomes = []
            final_weights = []
            for state, weight in dist.items():
                outcome = self.final_outcome(state, *pools)
                if outcome is not icepool.Reroll:
                    final_outcomes.append(outcome)
                    final_weights.append(weight)

            return icepool.Die(*final_outcomes, weights=final_weights)

    __call__ = eval

    def _select_algorithm(self, *pools):
        """Selects an algorithm and iteration direction.

        Returns:
            * The algorithm to use (`_eval_internal*`).
            * The direction in which `next_state()` sees outcomes.
                1 for ascending and -1 for descending.

        """
        has_truncate_min = any(pool._has_truncate_min() for pool in pools)
        has_truncate_max = any(pool._has_truncate_max() for pool in pools)

        if has_truncate_min and has_truncate_max:
            raise ValueError(
                'A set of pools cannot be evaluated if they have both truncate_min and truncate_max.'
            )

        direction = self.direction(*pools)

        if not direction:
            if has_truncate_max:
                direction = 1
            elif has_truncate_min:
                direction = -1
            else:
                score_ascending = sum(
                    pool._direction_score_ascending() for pool in pools)
                score_descending = sum(
                    pool._direction_score_descending() for pool in pools)
                if score_ascending < score_descending:
                    direction = -1
                else:
                    direction = 1

        if direction > 0 and has_truncate_min or direction < 0 and has_truncate_max:
            # Forced onto the less-preferred algorithm.
            return self._eval_internal_iterative, direction
        else:
            # Use the preferred algorithm.
            return self._eval_internal, direction

    def _eval_internal(self, direction, *pools):
        """Internal algorithm for iterating in the more-preferred direction,
        i.e. giving outcomes to `next_state()` from wide to narrow.

        All intermediate return values are cached in the instance.

        Arguments:
            direction: The direction in which to send outcomes to `next_state()`.
            *pools: One or more `Pool`s to evaluate.
                This *does* change recursively.

        Returns:
            A dict `{ state : weight }` describing the probability distribution
                over states.
        """
        cache_key = (direction, pools)
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = defaultdict(int)

        if all(len(pool.outcomes()) == 0 for pool in pools):
            result = {None: 1}
        else:
            outcome, iterators = _pop_pools(direction, pools)
            for p in itertools.product(*iterators):
                prev_pools, counts, weights = zip(*p)
                prod_weight = math.prod(weights)
                prev = self._eval_internal(direction, *prev_pools)
                for prev_state, prev_weight in prev.items():
                    state = self.next_state(prev_state, outcome, *counts)
                    if state is not icepool.Reroll:
                        result[state] += prev_weight * prod_weight

        self._cache[cache_key] = result
        return result

    def _eval_internal_iterative(self, direction, *pools):
        """Internal algorithm for iterating in the less-preferred direction,
        i.e. giving outcomes to `next_state()` from narrow to wide.

        This algorithm does not perform persistent memoization.
        """
        dist = defaultdict(int)
        dist[None, pools] = 1
        # This is only safe because all pools are guaranteed to pop outcomes at the same rate.
        while not all(len(pool.outcomes()) == 0 for pool in pools):
            next_dist = defaultdict(int)
            for (prev_state, prev_pools), weight in dist.items():
                # The direction flip here is the only purpose of this algorithm.
                outcome, iterators = _pop_pools(-direction, prev_pools)
                for p in itertools.product(*iterators):
                    pools, counts, weights = zip(*p)
                    prod_weight = math.prod(weights)
                    state = self.next_state(prev_state, outcome, *counts)
                    if state is not icepool.Reroll:
                        next_dist[state, pools] += weight * prod_weight
            dist = next_dist
        return {state: weight for (state, _), weight in dist.items()}


def _pop_pools(side, pools):
    """Pops a single outcome from the pools.

    Returns:
        * The popped outcome.
        * A tuple of iterators over the possible resulting pools, counts, and weights.
    """
    if side >= 0:
        outcome = max(
            pool._max_outcome() for pool in pools if len(pool.outcomes()) > 0)
        iterators = tuple(_pop_pool_max(outcome, pool) for pool in pools)
    else:
        outcome = min(
            pool._min_outcome() for pool in pools if len(pool.outcomes()) > 0)
        iterators = tuple(_pop_pool_min(outcome, pool) for pool in pools)

    return outcome, iterators


def _pop_pool_max(outcome, pool):
    """Iterates over possible numbers of dice that could roll an outcome.

    Args:
        outcome: The max outcome.
        pool: The `Pool` under consideration.

    Yields:
        prev_pool: The remainder of the pool after taking out the dice that
            rolled the current outcome.
        count: How many dice rolled the current outcome, or 0 if the outcome is
            not in this pool.
        weight: The weight of that many dice rolling the current outcome.
    """
    if outcome not in pool.outcomes():
        yield pool, 0, 1
    else:
        yield from pool._pop_max()


def _pop_pool_min(outcome, pool):
    """Iterates over possible numbers of dice that could roll an outcome.

    Args:
        outcome: The min outcome.
        pool: The `Pool` under consideration.

    Yields:
        prev_pool: The remainder of the pool after taking out the dice that
            rolled the current outcome.
        count: How many dice rolled the current outcome, or 0 if the outcome is
            not in this pool.
        weight: The weight of that many dice rolling the current outcome.
    """
    if outcome not in pool.outcomes():
        yield pool, 0, 1
    else:
        yield from pool._pop_min()


class WrapFuncEval(EvalPool):
    """An `EvalPool` created from a single provided function.

    `next_state()` simply calls that function.
    """

    def __init__(self, func, /):
        """Constructs a new instance given the function that should be called for `next_state()`.
        Args:
            func(state, outcome, *counts): This should take the same arguments
                as `next_state()`, minus `self`, and return the next state.
        """
        self._func = func

    def next_state(self, state, outcome, *counts):
        return self._func(state, outcome, *counts)


class JointEval(EvalPool):
    """EXPERIMENTAL: An `EvalPool` that jointly evaluates subevals on the same roll(s) of a pool.

    It may be more efficient to write the joint evaluation directly; this is
    provided as a convenience.
    """

    def __init__(self, *subevals):
        self._subevals = subevals

    def next_state(self, state, outcome, *counts):
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

    def final_outcome(self, final_state, *pools):
        """Runs `final_state` for all subevals.

        The final outcome is a tuple of the final suboutcomes.
        """
        return tuple(
            subeval.final_outcome(final_substate, *pools)
            for subeval, final_substate in zip(self._subevals, final_state))

    def direction(self, *pools):
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
        best_run, best_run_outcome, run, prev_outcome = state or (0, outcome, 0,
                                                                  outcome - 1)
        if count >= 1:
            if outcome == prev_outcome + 1:
                run += 1
            else:
                run = 1
        else:
            run = 0
        return max((run, outcome),
                   (best_run, best_run_outcome)) + (run, outcome)

    def final_outcome(self, final_state, *pools):
        """Returns the best run. """
        return final_state[:2]

    def direction(self, *pools):
        """This only considers outcomes in ascending order. """
        return 1
