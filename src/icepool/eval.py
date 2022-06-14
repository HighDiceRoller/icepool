__docformat__ = 'google'

import icepool
from icepool.alignment import Alignment

from abc import ABC, abstractmethod
from collections import defaultdict
from functools import cached_property
import itertools
import math

from typing import Any, Callable, Hashable
from collections.abc import Collection, Mapping, MutableMapping, Sequence

PREFERRED_DIRECTION_COST_FACTOR = 10
"""The preferred direction will be weighted this times as much."""


class OutcomeCountEval(ABC):
    """An abstract, immutable, callable class for evaulating one or more `OutcomeCountGens`s.

    There is one abstract method to implement: `next_state()`.
    This should incrementally calculate the result given one outcome at a time
    along with how many of that outcome were produced.
    An example sequence of calls, as far as `next_state()` is concerned, is:

    1. `state = next_state(state=None, outcome=1, count=how_many_1s)`
    2. `state = next_state(state, 2, how_many_2s)`
    3. `state = next_state(state, 3, how_many_3s)`
    4. `state = next_state(state, 4, how_many_4s)`
    5. `state = next_state(state, 5, how_many_5s)`
    6. `state = next_state(state, 6, how_many_6s)`
    7. `outcome = final_outcome(state, *gens)`

    A few other methods can optionally be overridden to further customize behavior.

    It is not expected that subclasses of `OutcomeCountEval`
    be able to handle arbitrary types or numbers of gens.
    Indeed, most are expected to handle only a fixed number of gens,
    and often even only gens with a particular type of die.

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
        and the number that outcome produced by each gen.

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
                If there are multiple gens, the set of outcomes is the
                union of the outcomes of the invididual gens. All outcomes
                with nonzero  count will be visited. Outcomes with zero count
                may or may not be visited. If you need to enforce that certain
                outcomes are visited even if they have zero count, see
                `alignment()`.
            *counts: One `int` for each gen indicating how many of the current
                outcome were produced. If there are multiple
                gens, it's possible that some outcomes will not appear in
                all gens. In this case, the count for the gen(s)
                that do not have the outcome will be 0. Zero-weight outcomes
                count as having that outcome.

                Most subclasses will expect a fixed number of gens and
                can replace this variadic parameter with a fixed number of named
                parameters.

        Returns:
            A hashable object indicating the next state.
            The special value `icepool.Reroll` can be used to immediately remove
            the state from consideration, effectively performing a full reroll.
        """

    def final_outcome(self, final_state: Hashable, /,
                      *gens: icepool.OutcomeCountGen) -> Any:
        """Optional function to generate a final outcome from a final state.

        Within `eval()`, this will be called using only positional arguments.
        Thus, you may rename any of the arguments if you wish.

        By default, the final outcome is equal to the final state.
        Note that `None` is not a valid outcome for a die,
        and if there are no outcomes, the final state will be `None`.
        Subclasses that want to handle this case should explicitly define what
        happens.

        Args:
            final_state: A state after all outcomes have been processed.
            *gens: One or more `OutcomeCountGen`s being evaluated.
                Most subclasses will expect a fixed number of generators and
                can replace this variadic parameter with a fixed number of named
                parameters.

        Returns:
            A final outcome that will be used as part of constructing the result die.
            As usual for `Die()`, this could itself be a die or `icepool.Reroll`.
        """
        return final_state

    def direction(self, *gens: icepool.OutcomeCountGen) -> int:
        """Optional function to determine the direction in which `next_state()` will see outcomes.

        The default is ascending order. This works well with mixed standard dice,
        and other dice that differ only by right-truncation.

        Args:
            *gens: One or more `OutcomeCountGen`s being evaluated.
                Most subclasses will expect a fixed number of generators and
                can replace this variadic parameter with a fixed number of named
                parameters.

        Returns:
            * > 0 if `next_state()` should always see the outcomes in ascending order.
            * < 0 if `next_state()` should always see the outcomes in descending order.
            * 0 if the order may be determined automatically.
        """
        return 1

    def alignment(self, *gens: icepool.OutcomeCountGen) -> Collection:
        """Optional function to specify an iterable of outcomes that should always be given to `next_state()` even if they have zero count.

        The default implementation returns `()`; this means outcomes with zero
        count may or may not be seen by `next_state`.

        If you want the outcomes seen by `next_state` to be consecutive
        `int`s, you can set `alignment = icepool.OutcomeCountEval.range_alignment`.
        See `range_alignment()` below.

        Returns:
            An iterable of outcomes that should be given to `next_state()` even
            if they have zero count.
        """
        return ()

    def range_alignment(self,
                        *gens: icepool.OutcomeCountGen) -> Collection[int]:
        """Example implementation of `alignment()` that produces consecutive `int` outcomes.

        Set `alignment = icepool.OutcomeCountEval.range_alignment` to use this.

        Returns:
            All `int`s from the min outcome to the max outcome among the generators,
            inclusive.

        Raises:
            `TypeError` if any generator has any non-`int` outcome.
        """
        if len(gens) == 0:
            return ()

        if any(
                any(not isinstance(x, int)
                    for x in gen.outcomes())
                for gen in gens):
            raise TypeError(
                "range_alignment cannot be used with outcomes of type other than 'int'."
            )

        min_outcome = min(gen.min_outcome() for gen in gens)
        max_outcome = max(gen.max_outcome() for gen in gens)
        return range(min_outcome, max_outcome + 1)

    @cached_property
    def _cache(self) -> MutableMapping[Any, Mapping[Any, int]]:
        """A cache of (direction, gens) -> weight distribution over states. """
        return {}

    def eval(
        self, *gens: icepool.OutcomeCountGen | Mapping[Any, int] | Sequence
    ) -> 'icepool.Die':
        """Evaluates generators.

        You can call the `OutcomeCountEval` object directly for the same effect,
        e.g. `sum_gen(gen)` is an alias for `sum_gen.eval(gen)`.

        Args:
            *gens: Each element may be one of the following:
                * A `OutcomeCountGen`.
                * A mappable mapping dice to the number of those dice.
                * A sequence of arguments to create a `Pool`.
                Most evaluators will expect a fixed number of gens.
                The union of the outcomes of the gens must be totally orderable.

        Returns:
            A `Die` representing the distribution of the final score.
        """

        # Convert non-pool arguments to `Pool`.
        converted_gens = tuple(gen if isinstance(gen, icepool.OutcomeCountGen
                                                ) else icepool.Pool(gen)
                               for gen in gens)

        if not all(gen._is_resolvable() for gen in converted_gens):
            return icepool.Die([])

        algorithm, direction = self._select_algorithm(*converted_gens)

        # We use a separate class to guarantee all outcomes are visited.
        alignment = Alignment(self.alignment(*converted_gens))

        dist = algorithm(direction, alignment, tuple(converted_gens))

        final_outcomes = []
        final_weights = []
        for state, weight in dist.items():
            outcome = self.final_outcome(state, *converted_gens)
            if outcome is None:
                raise TypeError(
                    "None is not a valid final outcome. "
                    "This may have resulted from supplying an empty gen to OutcomeCountEval. "
                    "If so, refrain from using empty gens, or override OutcomeCountEval.final_outcome() to handle this case."
                )
            if outcome is not icepool.Reroll:
                final_outcomes.append(outcome)
                final_weights.append(weight)

        return icepool.Die(final_outcomes, final_weights)

    __call__ = eval

    def _select_algorithm(
            self, *gens: icepool.OutcomeCountGen) -> tuple[Callable, int]:
        """Selects an algorithm and iteration direction.

        Returns:
            * The algorithm to use (`_eval_internal*`).
            * The direction in which `next_state()` sees outcomes.
                1 for ascending and -1 for descending.

        """
        eval_direction = self.direction(*gens)

        pop_min_costs, pop_max_costs = zip(
            *(gen._estimate_direction_costs() for gen in gens))

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

    def _eval_internal(
            self, direction: int, alignment: Alignment,
            gens: tuple[icepool.OutcomeCountGen, ...]) -> Mapping[Any, int]:
        """Internal algorithm for iterating in the more-preferred direction,
        i.e. giving outcomes to `next_state()` from wide to narrow.

        All intermediate return values are cached in the instance.

        Arguments:
            direction: The direction in which to send outcomes to `next_state()`.
            alignment: As `alignment()`. Elements will be popped off this
                during recursion.
            gens: One or more `OutcomeCountGens`s to evaluate. Elements
                will be popped off this during recursion.

        Returns:
            A dict `{ state : weight }` describing the probability distribution
                over states.
        """
        cache_key = (direction, alignment, gens)
        if cache_key in self._cache:
            return self._cache[cache_key]

        result: MutableMapping[Any, int] = defaultdict(int)

        if all(not gen.outcomes() for gen in gens) and not alignment.outcomes():
            result = {None: 1}
        else:
            outcome, prev_alignment, iterators = _pop_gens(
                direction, alignment, gens)
            for p in itertools.product(*iterators):
                prev_gens, counts, weights = zip(*p)
                prod_weight = math.prod(weights)
                prev = self._eval_internal(direction, prev_alignment, prev_gens)
                for prev_state, prev_weight in prev.items():
                    state = self.next_state(prev_state, outcome, *counts)
                    if state is not icepool.Reroll:
                        result[state] += prev_weight * prod_weight

        self._cache[cache_key] = result
        return result

    def _eval_internal_iterative(
            self, direction: int, alignment: Alignment,
            gens: tuple[icepool.OutcomeCountGen, ...]) -> Mapping[Any, int]:
        """Internal algorithm for iterating in the less-preferred direction,
        i.e. giving outcomes to `next_state()` from narrow to wide.

        This algorithm does not perform persistent memoization.
        """
        if all(not gen.outcomes() for gen in gens) and not alignment.outcomes():
            return {None: 1}
        dist: MutableMapping[Any, int] = defaultdict(int)
        dist[None, alignment, gens] = 1
        final_dist: MutableMapping[Any, int] = defaultdict(int)
        while dist:
            next_dist: MutableMapping[Any, int] = defaultdict(int)
            for (prev_state, prev_alignment, prev_gens), weight in dist.items():
                # The direction flip here is the only purpose of this algorithm.
                outcome, alignment, iterators = _pop_gens(
                    -direction, prev_alignment, prev_gens)
                for p in itertools.product(*iterators):
                    gens, counts, weights = zip(*p)
                    prod_weight = math.prod(weights)
                    state = self.next_state(prev_state, outcome, *counts)
                    if state is not icepool.Reroll:
                        if all(not gen.outcomes() for gen in gens):
                            final_dist[state] += weight * prod_weight
                        else:
                            next_dist[state, alignment,
                                      gens] += weight * prod_weight
            dist = next_dist
        return final_dist


def _pop_gens(
        side: int, alignment: Alignment,
        gens: tuple[icepool.OutcomeCountGen,
                    ...]) -> tuple[Any, Alignment, tuple]:
    """Pops a single outcome from the gens.

    Returns:
        * The popped outcome.
        * The remaining alignment.
        * A tuple of iterators over the possible resulting gens, counts, and weights.
    """
    alignment_and_gens = (alignment,) + gens
    if side >= 0:
        outcome = max(
            gen.max_outcome() for gen in alignment_and_gens if gen.outcomes())

        next_alignment, _, _ = next(alignment._pop_max(outcome))

        return outcome, next_alignment, tuple(
            gen._pop_max(outcome) for gen in gens)
    else:
        outcome = min(
            gen.min_outcome() for gen in alignment_and_gens if gen.outcomes())

        next_alignment, _, _ = next(alignment._pop_min(outcome))

        return outcome, next_alignment, tuple(
            gen._pop_min(outcome) for gen in gens)


class WrapFuncEval(OutcomeCountEval):
    """An `OutcomeCountEval` created from a single provided function.

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


class JointEval(OutcomeCountEval):
    """EXPERIMENTAL: An `OutcomeCountEval` that jointly evaluates subevals on the same roll(s) of a gen.

    It may be more efficient to write the joint evaluation directly; this is
    provided as a convenience.
    """

    def __init__(self, *subevals: 'OutcomeCountEval'):
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

    def final_outcome(self, final_state, *gens: icepool.OutcomeCountGen):
        """Runs `final_state` for all subevals.

        The final outcome is a tuple of the final suboutcomes.
        """
        return tuple(
            subeval.final_outcome(final_substate, *gens)
            for subeval, final_substate in zip(self._subevals, final_state))

    def direction(self, *gens: icepool.OutcomeCountGen):
        """Determines the common direction of the subevals.

        Raises:
            ValueError: If subevals have conflicting directions, i.e. some are
                ascending and others are descending.
        """
        subdirections = tuple(
            subeval.direction(*gens) for subeval in self._subevals)
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


class SumGen(OutcomeCountEval):
    """A simple `OutcomeCountEval` that just sums the outcomes in a gen. """

    def next_state(self, state, outcome, count):
        """Add the outcomes to the running total. """
        if state is None:
            return outcome * count
        else:
            return state + outcome * count

    def final_outcome(self, final_state, *gens):
        if final_state is None:
            return 0
        else:
            return final_state

    def direction(self, *gens):
        """This eval doesn't care about direction. """
        return 0


sum_gen = SumGen()
"""A shared `SumGens` object for caching results. """


class EnumerateGen(OutcomeCountEval):
    """A `OutcomeCountEval` that enumerates all possible (sorted) results.

    This is expensive and not recommended unless there are few elements being output.
    """

    def __init__(self, direction=1):
        """`direction` determines the sort order.

        Positive for ascending and negative for descending.
        """
        self._direction = direction

    def next_state(self, state, outcome, count):
        if count < 0:
            raise ValueError(
                'EnumerateGen is not compatible with negative counts.')
        if state is None:
            return (outcome,) * count
        else:
            return state + (outcome,) * count

    def direction(self, *gens):
        return self._direction


enumerate_gen = EnumerateGen()
"""A shared `EnumerateGens` object for caching results. """


class FindBestSet(OutcomeCountEval):
    """A `OutcomeCountEval` that takes the best matching set in a gen.

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

    def direction(self, *gens):
        """This eval doesn't care about direction. """
        return 0


class FindBestRun(OutcomeCountEval):
    """A `OutcomeCountEval` that takes the best run (aka "straight") in a gen.

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

    def final_outcome(self, final_state, *gens):
        """Returns the best run. """
        return final_state[:2]

    def direction(self, *gens):
        """This only considers outcomes in ascending order. """
        return 1

    alignment = OutcomeCountEval.range_alignment
