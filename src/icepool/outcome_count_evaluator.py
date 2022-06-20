__docformat__ = 'google'

import icepool
from icepool.alignment import Alignment

from abc import ABC, abstractmethod
from collections import defaultdict
from functools import cached_property
import itertools
import math

from typing import Any, Callable, Collection, Hashable, Mapping, MutableMapping, Sequence

PREFERRED_DIRECTION_COST_FACTOR = 10
"""The preferred direction will be favored this times as much."""


class OutcomeCountEvaluator(ABC):
    """An abstract, immutable, callable class for evaulating one or more `OutcomeCountGenerator`s.

    There is one abstract method to implement: `next_state()`.
    This should incrementally calculate the result given one outcome at a time
    along with how many of that outcome were produced.

    An example sequence of calls, as far as `next_state()` is concerned, is:

    1. `state = next_state(state=None, outcome=1, count_of_1s)`
    2. `state = next_state(state, 2, count_of_2s)`
    3. `state = next_state(state, 3, count_of_3s)`
    4. `state = next_state(state, 4, count_of_4s)`
    5. `state = next_state(state, 5, count_of_5s)`
    6. `state = next_state(state, 6, count_of_6s)`
    7. `outcome = final_outcome(state, *generators)`

    A few other methods can optionally be overridden to further customize behavior.

    It is not expected that subclasses of `OutcomeCountEvaluator`
    be able to handle arbitrary types or numbers of generators.
    Indeed, most are expected to handle only a fixed number of generators,
    and often even only generators with a particular type of `Die`.

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
        and the number that outcome produced by each generator.

        `evaluate()` will always call this using only positional arguments.
        Furthermore, there is no expectation that a subclass be able to handle
        an arbitrary number of counts. Thus, you are free to rename any of
        the parameters in a subclass, or to replace `*counts` with a fixed set
        of parameters.

        Make sure to handle the base case where `state is None`.

        States must be hashable, but unlike outcomes they do not need to be
        orderable. However, if they are not totally orderable, you must override
        `final_outcome` to create legal final outcomes.

        Args:
            state: A hashable object indicating the state before rolling the
                current outcome. If this is the first outcome being considered,
                `state` will be `None`.
            outcome: The current outcome.
                `next_state` will see all rolled outcomes in monotonic order;
                either ascending or descending depending on `direction()`.
                If there are multiple generators, the set of outcomes is the
                union of the outcomes of the invididual generators. All outcomes
                with nonzero count will be seen. Outcomes with zero count
                may or may not be seen. If you need to enforce that certain
                outcomes are seen even if they have zero count, see
                `alignment()`.
            *counts: One `int` for each generator output indicating how many of
                the current outcome were produced. All outcomes with nonzero
                count are guaranteed to be seen. To guarantee that outcomes
                are seen even if they have zero count, override `alignment()`.

        Returns:
            A hashable object indicating the next state.
            The special value `icepool.Reroll` can be used to immediately remove
            the state from consideration, effectively performing a full reroll.
        """

    def final_outcome(self, final_state: Hashable, /,
                      *generators: icepool.OutcomeCountGenerator) -> Any:
        """Optional function to generate a final outcome from a final state.

        Tthere is no expectation that a subclass be able to handle
        an arbitrary number of generators. Thus, you are free to rename any of
        the parameters in a subclass, or to replace `*generators` with a fixed
        set of parameters.

        By default, the final outcome is equal to the final state.
        Note that `None` is not a valid outcome for a `Die`,
        and if there are no outcomes, the final state will be `None`.
        Subclasses that want to handle this case should explicitly define what
        happens.

        Args:
            final_state: A state after all outcomes have been processed.
            *generators: One or more `OutcomeCountGenerator`s being evaluated.
                Most subclasses will expect a fixed number of generators and
                can replace this variadic parameter with a fixed number of named
                parameters.

        Returns:
            A final outcome that will be used as part of constructing the result `Die`.
            As usual for `Die()`, this could itself be a `Die` or `icepool.Reroll`.
        """
        return final_state

    def direction(self, *generators: icepool.OutcomeCountGenerator) -> int:
        """Optional function to determine the direction in which `next_state()` will see outcomes.

        There is no expectation that a subclass be able to handle
        an arbitrary number of generators. Thus, you are free to rename any of
        the parameters in a subclass, or to replace `*generators` with a fixed
        set of parameters.

        The default is ascending order. This works well with mixed standard dice,
        and other dice that differ only by right-truncation.

        Args:
            *generators: One or more `OutcomeCountGenerator`s being evaluated.
                Most subclasses will expect a fixed number of generators and
                can replace this variadic parameter with a fixed number of named
                parameters.

        Returns:
            * > 0 if `next_state()` should always see the outcomes in ascending order.
            * < 0 if `next_state()` should always see the outcomes in descending order.
            * 0 if the order may be determined automatically.
        """
        return 1

    def alignment(self,
                  *generators: icepool.OutcomeCountGenerator) -> Collection:
        """Optional function to specify an collection of outcomes that should always be given to `next_state()` even if they have zero count.

        There is no expectation that a subclass be able to handle
        an arbitrary number of generators. Thus, you are free to rename any of
        the parameters in a subclass, or to replace `*generators` with a fixed
        set of parameters.

        The default implementation returns `()`; this means outcomes with zero
        count may or may not be seen by `next_state`.

        If you want the outcomes seen by `next_state` to be consecutive
        `int`s, you can set `alignment = icepool.OutcomeCountEvaluator.range_alignment`.
        See `range_alignment()` below.
        """
        return ()

    def range_alignment(
            self,
            *generators: icepool.OutcomeCountGenerator) -> Collection[int]:
        """Example implementation of `alignment()` that produces consecutive `int` outcomes.

        There is no expectation that a subclass be able to handle
        an arbitrary number of generators. Thus, you are free to rename any of
        the parameters in a subclass, or to replace `*generators` with a fixed
        set of parameters.

        Set `alignment = icepool.OutcomeCountEvaluator.range_alignment` to use this.

        Returns:
            All `int`s from the min outcome to the max outcome among the generators,
            inclusive.

        Raises:
            TypeError: if any generator has any non-`int` outcome.
        """
        if len(generators) == 0:
            return ()

        if any(
                any(not isinstance(x, int)
                    for x in generator.outcomes())
                for generator in generators):
            raise TypeError(
                "range_alignment cannot be used with outcomes of type other than 'int'."
            )

        min_outcome = min(generator.min_outcome() for generator in generators)
        max_outcome = max(generator.max_outcome() for generator in generators)
        return range(min_outcome, max_outcome + 1)

    @cached_property
    def _cache(self) -> MutableMapping[Any, Mapping[Any, int]]:
        """A cache of (direction, generators) -> weight distribution over states. """
        return {}

    def evaluate(
        self, *generators: icepool.OutcomeCountGenerator | Mapping[Any, int] |
        Sequence
    ) -> 'icepool.Die':
        """Evaluates generator(s).

        You can call the `OutcomeCountEvaluator` object directly for the same effect,
        e.g. `evaluate_sum(generator)` is an alias for `evaluate_sum.evaluate(generator)`.

        Most evaluators will expect a fixed number of generators.
        The union of the outcomes of the generator(s) must be totally orderable.

        Args:
            *generators: Each element may be one of the following:
                * A `OutcomeCountGenerator`.
                * A mappable mapping dice to the number of those dice.
                * A sequence of arguments to create a `Pool`.

        Returns:
            A `Die` representing the distribution of the final score.
        """

        # Convert non-`Pool` arguments to `Pool`.
        converted_generators = tuple(
            generator if isinstance(generator, icepool.OutcomeCountGenerator
                                   ) else icepool.Pool(generator)
            for generator in generators)

        if not all(generator._is_resolvable()
                   for generator in converted_generators):
            return icepool.Die([])

        algorithm, direction = self._select_algorithm(*converted_generators)

        # We use a separate class to guarantee all outcomes are visited.
        alignment = Alignment(self.alignment(*converted_generators))

        dist = algorithm(direction, alignment, tuple(converted_generators))

        final_outcomes = []
        final_weights = []
        for state, weight in dist.items():
            outcome = self.final_outcome(state, *converted_generators)
            if outcome is None:
                raise TypeError(
                    "None is not a valid final outcome. "
                    "This may have resulted from supplying an empty generator to OutcomeCountEvaluator. "
                    "If so, refrain from using empty generators, or override OutcomeCountEvaluator.final_outcome() to handle this case."
                )
            if outcome is not icepool.Reroll:
                final_outcomes.append(outcome)
                final_weights.append(weight)

        return icepool.Die(final_outcomes, final_weights)

    __call__ = evaluate

    def _select_algorithm(
            self,
            *generators: icepool.OutcomeCountGenerator) -> tuple[Callable, int]:
        """Selects an algorithm and iteration direction.

        Returns:
            * The algorithm to use (`_eval_internal*`).
            * The direction in which `next_state()` sees outcomes.
                1 for ascending and -1 for descending.
        """
        eval_direction = self.direction(*generators)

        pop_min_costs, pop_max_costs = zip(*(
            generator._estimate_direction_costs() for generator in generators))

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
        generators: tuple[icepool.OutcomeCountGenerator,
                          ...]) -> Mapping[Any, int]:
        """Internal algorithm for iterating in the more-preferred direction,
        i.e. giving outcomes to `next_state()` from wide to narrow.

        All intermediate return values are cached in the instance.

        Arguments:
            direction: The direction in which to send outcomes to `next_state()`.
            alignment: As `alignment()`. Elements will be popped off this
                during recursion.
            generators: One or more `OutcomeCountGenerators`s to evaluate. Elements
                will be popped off this during recursion.

        Returns:
            A dict `{ state : weight }` describing the probability distribution
                over states.
        """
        cache_key = (direction, alignment, generators)
        if cache_key in self._cache:
            return self._cache[cache_key]

        result: MutableMapping[Any, int] = defaultdict(int)

        if all(not generator.outcomes()
               for generator in generators) and not alignment.outcomes():
            result = {None: 1}
        else:
            outcome, prev_alignment, iterators = OutcomeCountEvaluator._pop_generators(
                direction, alignment, generators)
            for p in itertools.product(*iterators):
                prev_generators, counts, weights = zip(*p)
                counts = tuple(itertools.chain.from_iterable(counts))
                prod_weight = math.prod(weights)
                prev = self._eval_internal(direction, prev_alignment,
                                           prev_generators)
                for prev_state, prev_weight in prev.items():
                    state = self.next_state(prev_state, outcome, *counts)
                    if state is not icepool.Reroll:
                        result[state] += prev_weight * prod_weight

        self._cache[cache_key] = result
        return result

    def _eval_internal_iterative(
        self, direction: int, alignment: Alignment,
        generators: tuple[icepool.OutcomeCountGenerator,
                          ...]) -> Mapping[Any, int]:
        """Internal algorithm for iterating in the less-preferred direction,
        i.e. giving outcomes to `next_state()` from narrow to wide.

        This algorithm does not perform persistent memoization.
        """
        if all(not generator.outcomes()
               for generator in generators) and not alignment.outcomes():
            return {None: 1}
        dist: MutableMapping[Any, int] = defaultdict(int)
        dist[None, alignment, generators] = 1
        final_dist: MutableMapping[Any, int] = defaultdict(int)
        while dist:
            next_dist: MutableMapping[Any, int] = defaultdict(int)
            for (prev_state, prev_alignment,
                 prev_generators), weight in dist.items():
                # The direction flip here is the only purpose of this algorithm.
                outcome, alignment, iterators = OutcomeCountEvaluator._pop_generators(
                    -direction, prev_alignment, prev_generators)
                for p in itertools.product(*iterators):
                    generators, counts, weights = zip(*p)
                    counts = tuple(itertools.chain.from_iterable(counts))
                    prod_weight = math.prod(weights)
                    state = self.next_state(prev_state, outcome, *counts)
                    if state is not icepool.Reroll:
                        if all(not generator.outcomes()
                               for generator in generators):
                            final_dist[state] += weight * prod_weight
                        else:
                            next_dist[state, alignment,
                                      generators] += weight * prod_weight
            dist = next_dist
        return final_dist

    @staticmethod
    def _pop_generators(
        side: int, alignment: Alignment,
        generators: tuple[icepool.OutcomeCountGenerator, ...]
    ) -> tuple[Any, Alignment, tuple['icepool.NextOutcomeCountGenerator', ...]]:
        """Pops a single outcome from the generators.

        Returns:
            * The popped outcome.
            * The remaining alignment.
            * A tuple of iterators over the resulting generators, counts, and weights.
        """
        alignment_and_generators = (alignment,) + generators
        if side >= 0:
            outcome = max(generator.max_outcome()
                          for generator in alignment_and_generators
                          if generator.outcomes())

            next_alignment, _, _ = next(alignment._generate_max(outcome))

            return outcome, next_alignment, tuple(
                generator._generate_max(outcome) for generator in generators)
        else:
            outcome = min(generator.min_outcome()
                          for generator in alignment_and_generators
                          if generator.outcomes())

            next_alignment, _, _ = next(alignment._generate_min(outcome))

            return outcome, next_alignment, tuple(
                generator._generate_min(outcome) for generator in generators)

    def sample(self, *generators: icepool.OutcomeCountGenerator |
               Mapping[Any, int] | Sequence):
        """EXPERIMENTAL: Samples one result from the generator(s) and evaluates the result."""
        # Convert non-`Pool` arguments to `Pool`.
        converted_generators = tuple(
            generator if isinstance(generator, icepool.OutcomeCountGenerator
                                   ) else icepool.Pool(generator)
            for generator in generators)

        result = self.evaluate(*itertools.chain.from_iterable(
            generator.sample() for generator in converted_generators))

        if not result.is_empty():
            return result.outcomes()[0]
        else:
            return result


class WrapFuncEvaluator(OutcomeCountEvaluator):
    """An `OutcomeCountEvaluator` created from a single provided function.

    `next_state()` simply calls that function.
    """

    def __init__(self, func: Callable, /):
        """Constructs a new instance given the function that should be called for `next_state()`.
        Args:
            func(state, outcome, *counts): This should take the same arguments
                as `next_state()`, minus `self`, and return the next state.
        """
        self._func = func

    def next_state(self, state: Hashable, outcome, *counts: int) -> Hashable:
        return self._func(state, outcome, *counts)


class JointEvaluator(OutcomeCountEvaluator):
    """EXPERIMENTAL: An `OutcomeCountEvaluator` that jointly evaluates sub-evaluators on the same roll(s) of a generator.

    It may be more efficient to write the joint evaluation directly; this is
    provided as a convenience.
    """

    def __init__(self, *sub_evaluators: 'OutcomeCountEvaluator'):
        self._sub_evaluators = sub_evaluators

    def next_state(self, state, outcome, *counts: int) -> tuple[Hashable, ...]:
        """Runs `next_state` for all subevals.

        The state is a tuple of the substates.
        """
        if state is None:
            return tuple(
                evaluator.next_state(None, outcome, *counts)
                for evaluator in self._sub_evaluators)
        else:
            return tuple(
                evaluator.next_state(substate, outcome, *counts)
                for evaluator, substate in zip(self._sub_evaluators, state))

    def final_outcome(self, final_state,
                      *generators: icepool.OutcomeCountGenerator):
        """Runs `final_state` for all subevals.

        The final outcome is a tuple of the final suboutcomes.
        """
        return tuple(
            evaluator.final_outcome(final_substate, *generators) for evaluator,
            final_substate in zip(self._sub_evaluators, final_state))

    def direction(self, *generators: icepool.OutcomeCountGenerator) -> int:
        """Determines the common direction of the subevals.

        Raises:
            ValueError: If subevals have conflicting directions, i.e. some are
                ascending and others are descending.
        """
        subdirections = tuple(
            evaluator.direction(*generators)
            for evaluator in self._sub_evaluators)
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


class EvaluateSum(OutcomeCountEvaluator):
    """A simple `OutcomeCountEvaluator` that just sums the outcomes in a generator. """

    def next_state(self, state, outcome, count):
        """Add the outcomes to the running total. """
        if state is None:
            return outcome * count
        else:
            return state + outcome * count

    def final_outcome(self, final_state, *_):
        if final_state is None:
            return 0
        else:
            return final_state

    def direction(self, *_):
        """This evaluator doesn't care about direction. """
        return 0


evaluate_sum = EvaluateSum()
"""A shared `Sumgenerators` object for caching results. """


class EnumerateSorted(OutcomeCountEvaluator):
    """A `OutcomeCountEvaluator` that enumerates all (sorted) results.

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
                'EnumerateGenerator is not compatible with negative counts.')
        if state is None:
            return (outcome,) * count
        else:
            return state + (outcome,) * count

    def direction(self, *_):
        return self._direction


enumerate_sorted = EnumerateSorted()
"""A shared `EnumerateGenerator` object for caching results. """


class FindBestSet(OutcomeCountEvaluator):
    """A `OutcomeCountEvaluator` that takes the best matching set in a generator.

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

    def direction(self, *_):
        """This evaluator doesn't care about direction. """
        return 0


class FindBestRun(OutcomeCountEvaluator):
    """A `OutcomeCountEvaluator` that takes the best run (aka "straight") in a generator.

    Outcomes must be `int`s.

    This prioritizes run size, then the outcome.

    The outcomes are `(run_size, outcome)`.
    """

    def next_state(self, state, outcome, count):
        """Increments the current run if at least one `Die` rolled this outcome,
        then saves the run to the state.
        """
        best_run, best_run_outcome, run = state or (0, outcome, 0)
        if count >= 1:
            run += 1
        else:
            run = 0
        return max((run, outcome), (best_run, best_run_outcome)) + (run,)

    def final_outcome(self, final_state, *_):
        """The best run. """
        return final_state[:2]

    def direction(self, *_):
        """This only considers outcomes in ascending order. """
        return 1

    alignment = OutcomeCountEvaluator.range_alignment
