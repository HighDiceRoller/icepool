__docformat__ = 'google'

import icepool
from icepool.generator.pop_order import PopOrderReason, merge_pop_orders

from abc import ABC, abstractmethod
from collections import defaultdict
import enum
from functools import cached_property
import itertools
import math

from icepool.typing import Order, T_contra, U_co

from typing import Any, Callable, Collection, Generic, Hashable, Mapping, MutableMapping, Sequence, cast, TYPE_CHECKING, overload

if TYPE_CHECKING:
    from icepool.generator.alignment import Alignment
    from icepool import MultisetExpression, MultisetGenerator

PREFERRED_ORDER_COST_FACTOR = 10
"""The preferred order will be favored this times as much."""


class MultisetEvaluator(ABC, Generic[T_contra, U_co]):
    """An abstract, immutable, callable class for evaulating one or more `MultisetGenerator`s.

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
    7. `outcome = final_outcome(state)`

    A few other methods can optionally be overridden to further customize behavior.

    It is not expected that subclasses of `MultisetEvaluator`
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
    def next_state(self, state: Hashable, outcome: T_contra, /, *counts:
                   int) -> Hashable:
        """State transition function.

        This should produce a state given the previous state, an outcome,
        and the number that outcome produced by each generator.

        `evaluate()` will always call this using only positional arguments.
        Furthermore, there is no expectation that a subclass be able to handle
        an arbitrary number of counts. Thus, you are free to rename any of
        the parameters in a subclass, or to replace `*counts` with a fixed set
        of parameters.

        Make sure to handle the base case where `state is None`.

        States must be hashable. At current, they do not have to be orderable.
        However, this may change in the future, and if they are not totally
        orderable, you must override `final_outcome` to create totally orderable
        final outcomes.

        The behavior of returning a `Die` from `next_state` is currently
        undefined.

        Args:
            state: A hashable object indicating the state before rolling the
                current outcome. If this is the first outcome being considered,
                `state` will be `None`.
            outcome: The current outcome.
                `next_state` will see all rolled outcomes in monotonic order;
                either ascending or descending depending on `order()`.
                If there are multiple generators, the set of outcomes is at 
                least the union of the outcomes of the invididual generators. 
                You can use `extra_outcomes()` to add extra outcomes.
            *counts: One value (usually an `int`) for each generator output
                indicating how many of the current outcome were produced.

        Returns:
            A hashable object indicating the next state.
            The special value `icepool.Reroll` can be used to immediately remove
            the state from consideration, effectively performing a full reroll.
        """

    def final_outcome(
        self, final_state: Hashable
    ) -> 'U_co | icepool.Die[U_co] | icepool.RerollType':
        """Optional function to generate a final output outcome from a final state.

        By default, the final outcome is equal to the final state.
        Note that `None` is not a valid outcome for a `Die`,
        and if there are no outcomes, `final_outcome` will be immediately
        be callled with `final_state=None`.
        Subclasses that want to handle this case should explicitly define what
        happens.

        Args:
            final_state: A state after all outcomes have been processed.

        Returns:
            A final outcome that will be used as part of constructing the result `Die`.
            As usual for `Die()`, this could itself be a `Die` or `icepool.Reroll`.
        """
        # If not overriden, the final_state should have type U_co.
        return cast(U_co, final_state)

    def order(self) -> Order:
        """Optional function to determine the order in which `next_state()` will see outcomes.

        The default is ascending order. This has better caching behavior with 
        mixed standard dice.

        Returns:
            * Order.Ascending (= 1)
                if `next_state()` should always see the outcomes in ascending order.
            * Order.Descending (= -1)
                if `next_state()` should always see the outcomes in descending order.
            * Order.Any (= 0)
                if the result of the evaluation is order-independent.
        """
        return Order.Ascending

    def extra_outcomes(self,
                       outcomes: Sequence[T_contra]) -> Collection[T_contra]:
        """Optional method to specify extra outcomes that should be seen as inputs to `next_state()`.

        These will be seen by `next_state` even if they do not appear in the
        generator(s). The default implementation returns `()`, or no additional
        outcomes.

        If you want `next_state` to see consecutive `int` outcomes, you can set
        `extra_outcomes = icepool.MultisetEvaluator.consecutive`.
        See `consecutive()` below.

        Args:
            outcomes: The outcomes that could be produced by the generators, in
            ascending order.
        """
        return ()

    def consecutive(self, outcomes: Sequence[int]) -> Collection[int]:
        """Example implementation of `extra_outcomes()` that produces consecutive `int` outcomes.

        There is no expectation that a subclass be able to handle
        an arbitrary number of generators. Thus, you are free to rename any of
        the parameters in a subclass, or to replace `*generators` with a fixed
        set of parameters.

        Set `extra_outcomes = icepool.MultisetEvaluator.consecutive` to use this.

        Returns:
            All `int`s from the min outcome to the max outcome among the generators,
            inclusive.

        Raises:
            TypeError: if any generator has any non-`int` outcome.
        """
        if not outcomes:
            return ()

        if any(not isinstance(x, int) for x in outcomes):
            raise TypeError(
                "consecutive cannot be used with outcomes of type other than 'int'."
            )

        return range(outcomes[0], outcomes[-1] + 1)

    def prefix_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        """An optional sequence of extra generators whose counts will be prepended to *counts."""
        return ()

    def validate_arity(self, arity: int) -> None:
        """An optional method to verify the total input arity.

        This is called after any implicit conversion to generators, but does
        not include any `extra_generators()`.

        Overriding `next_state` with a fixed number of counts will make this
        check redundant.

        Raises:
            `ValueError` if the total input arity is not valid.
        """

    @cached_property
    def _cache(
        self
    ) -> 'MutableMapping[tuple[Order, Alignment, tuple[MultisetGenerator, ...], Hashable], Mapping[Any, int]]':
        """Cached results.
        
        The key is `(order, extra_outcomes, generators, state)`.
        The value is another mapping `final_state: quantity` representing the
        state distribution produced by `order, extra_outcomes, generators` when
        starting at state `state`.
        """
        return {}

    @overload
    def evaluate(
        self, *args: 'Mapping[T_contra, int] | Sequence[T_contra]'
    ) -> 'icepool.Die[U_co]':
        ...

    @overload
    def evaluate(
        self, *args: 'MultisetExpression[T_contra]'
    ) -> 'MultisetEvaluator[T_contra, U_co]':
        ...

    @overload
    def evaluate(
        self, *args:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]'
    ) -> 'icepool.Die[U_co] | MultisetEvaluator[T_contra, U_co]':
        ...

    def evaluate(
        self, *args:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]'
    ) -> 'icepool.Die[U_co] | MultisetEvaluator[T_contra, U_co]':
        """Evaluates generator(s).

        You can call the `MultisetEvaluator` object directly for the same effect,
        e.g. `sum_evaluator(generator)` is an alias for `sum_evaluator.evaluate(generator)`.

        Most evaluators will expect a fixed number of input multisets.
        The union of the outcomes of the generator(s) must be totally orderable.

        Args:
            *args: Each may be one of the following:
                * A `MultisetExpression`.
                * A mappable mapping outcomes to the number of those outcomes.
                * A sequence of outcomes.

        Returns:
            A `Die` representing the distribution of the final outcome if no
            arg contains a free variable. Otherwise, returns a new evaluator.
        """
        from icepool.generator.alignment import Alignment

        # Convert arguments to expressions.
        expressions = tuple(
            icepool.implicit_convert_to_expression(arg) for arg in args)

        if any(expression._free_arity() > 0 for expression in expressions):
            from icepool.evaluator.expression import ExpressionEvaluator
            return ExpressionEvaluator(*expressions, evaluator=self)

        if not all(
                isinstance(expression, icepool.MultisetGenerator)
                for expression in expressions):
            from icepool.evaluator.expression import ExpressionEvaluator
            return ExpressionEvaluator(*expressions, evaluator=self).evaluate()

        generators = cast(tuple[icepool.MultisetGenerator, ...], expressions)

        self.validate_arity(
            sum(generator.output_arity() for generator in generators))

        generators = self.prefix_generators() + generators

        if not all(generator._is_resolvable() for generator in generators):
            return icepool.Die([])

        algorithm, order = self._select_algorithm(*generators)

        outcomes = icepool.sorted_union(*(generator.outcomes()
                                          for generator in generators))
        extra_outcomes = Alignment(self.extra_outcomes(outcomes))

        dist: MutableMapping[Any, int] = defaultdict(int)
        iterators = MultisetEvaluator._initialize_generators(generators)
        for p in itertools.product(*iterators):
            sub_generators, sub_weights = zip(*p)
            prod_weight = math.prod(sub_weights)
            sub_result = algorithm(order, extra_outcomes, sub_generators)
            for sub_state, sub_weight in sub_result.items():
                dist[sub_state] += sub_weight * prod_weight

        final_outcomes = []
        final_weights = []
        for state, weight in dist.items():
            outcome = self.final_outcome(state)
            if outcome is None:
                raise TypeError(
                    "None is not a valid final outcome.\n"
                    "This may have been a result of not supplying any generator with an outcome."
                )
            if outcome is not icepool.Reroll:
                final_outcomes.append(outcome)
                final_weights.append(weight)

        return icepool.Die(final_outcomes, final_weights)

    __call__ = evaluate

    def _select_algorithm(
        self, *generators: 'icepool.MultisetGenerator[T_contra, Any]'
    ) -> tuple[
            'Callable[[Order, Alignment[T_contra], tuple[icepool.MultisetGenerator[T_contra, Any], ...]], Mapping[Any, int]]',
            Order]:
        """Selects an algorithm and iteration order.

        Returns:
            * The algorithm to use (`_eval_internal*`).
            * The order in which `next_state()` sees outcomes.
                1 for ascending and -1 for descending.
        """
        eval_order = self.order()

        if not generators:
            # No generators.
            return self._eval_internal, eval_order

        preferred_pop_order, pop_order_reason = merge_pop_orders(
            *(generator._preferred_pop_order() for generator in generators))

        if preferred_pop_order is None:
            preferred_pop_order = Order.Any
            pop_order_reason = PopOrderReason.NoPreference

        # No mandatory evaluation order, go with preferred algorithm.
        # Note that this has order *opposite* the pop order.
        if eval_order == Order.Any:
            return self._eval_internal, Order(-preferred_pop_order
                                              or Order.Ascending)

        # Mandatory evaluation order.
        if preferred_pop_order == Order.Any:
            return self._eval_internal, eval_order
        elif eval_order != preferred_pop_order:
            return self._eval_internal, eval_order
        else:
            return self._eval_internal_forward, eval_order

    def _eval_internal(
        self, order: Order, extra_outcomes: 'Alignment[T_contra]',
        generators: 'tuple[icepool.MultisetGenerator[T_contra, Any], ...]'
    ) -> Mapping[Any, int]:
        """Internal algorithm for iterating in the more-preferred order.

        All intermediate return values are cached in the instance.

        Arguments:
            order: The order in which to send outcomes to `next_state()`.
            extra_outcomes: As `extra_outcomes()`. Elements will be popped off this
                during recursion.
            generators: One or more `MultisetGenerators`s to evaluate. Elements
                will be popped off this during recursion.

        Returns:
            A dict `{ state : weight }` describing the probability distribution
                over states.
        """
        cache_key = (order, extra_outcomes, generators, None)
        if cache_key in self._cache:
            return self._cache[cache_key]

        result: MutableMapping[Any, int] = defaultdict(int)

        if all(not generator.outcomes()
               for generator in generators) and not extra_outcomes.outcomes():
            result = {None: 1}
        else:
            outcome, prev_extra_outcomes, iterators = MultisetEvaluator._pop_generators(
                Order(-order), extra_outcomes, generators)
            for p in itertools.product(*iterators):
                prev_generators, counts, weights = zip(*p)
                counts = tuple(itertools.chain.from_iterable(counts))
                prod_weight = math.prod(weights)
                prev = self._eval_internal(order, prev_extra_outcomes,
                                           prev_generators)
                for prev_state, prev_weight in prev.items():
                    state = self.next_state(prev_state, outcome, *counts)
                    if state is not icepool.Reroll:
                        result[state] += prev_weight * prod_weight

        self._cache[cache_key] = result
        return result

    def _eval_internal_forward(
            self,
            order: Order,
            extra_outcomes: 'Alignment[T_contra]',
            generators: 'tuple[icepool.MultisetGenerator[T_contra, Any], ...]',
            state: Hashable = None) -> Mapping[Any, int]:
        """Internal algorithm for iterating in the less-preferred order.

        All intermediate return values are cached in the instance.

        Arguments:
            order: The order in which to send outcomes to `next_state()`.
            extra_outcomes: As `extra_outcomes()`. Elements will be popped off this
                during recursion.
            generators: One or more `MultisetGenerators`s to evaluate. Elements
                will be popped off this during recursion.

        Returns:
            A dict `{ state : weight }` describing the probability distribution
                over states.
        """
        cache_key = (order, extra_outcomes, generators, state)
        if cache_key in self._cache:
            return self._cache[cache_key]

        result: MutableMapping[Any, int] = defaultdict(int)

        if all(not generator.outcomes()
               for generator in generators) and not extra_outcomes.outcomes():
            result = {state: 1}
        else:
            outcome, next_extra_outcomes, iterators = MultisetEvaluator._pop_generators(
                order, extra_outcomes, generators)
            for p in itertools.product(*iterators):
                next_generators, counts, weights = zip(*p)
                counts = tuple(itertools.chain.from_iterable(counts))
                prod_weight = math.prod(weights)
                next_state = self.next_state(state, outcome, *counts)
                if next_state is not icepool.Reroll:
                    final_dist = self._eval_internal_forward(
                        order, next_extra_outcomes, next_generators,
                        next_state)
                    for final_state, weight in final_dist.items():
                        result[final_state] += weight * prod_weight

        self._cache[cache_key] = result
        return result

    @staticmethod
    def _initialize_generators(
        generators: 'tuple[icepool.MultisetGenerator[T_contra, Any], ...]'
    ) -> 'tuple[icepool.InitialMultisetGenerator, ...]':
        return tuple(generator._generate_initial() for generator in generators)

    @staticmethod
    def _pop_generators(
        order: Order, extra_outcomes: 'Alignment[T_contra]',
        generators: 'tuple[icepool.MultisetGenerator[T_contra, Any], ...]'
    ) -> 'tuple[T_contra, Alignment[T_contra], tuple[icepool.NextMultisetGenerator, ...]]':
        """Pops a single outcome from the generators.

        Args:
            order: The order in which to pop. Descending order pops from the top
            and ascending from the bottom.
            extra_outcomes: Any extra outcomes to use.
            generators: The generators to pop from.

        Returns:
            * The popped outcome.
            * The remaining extra outcomes.
            * A tuple of iterators over the resulting generators, counts, and weights.
        """
        extra_outcomes_and_generators = (extra_outcomes, ) + generators
        if order < 0:
            outcome = max(generator.max_outcome()
                          for generator in extra_outcomes_and_generators
                          if generator.outcomes())

            next_extra_outcomes, _, _ = next(
                extra_outcomes._generate_max(outcome))

            return outcome, next_extra_outcomes, tuple(
                generator._generate_max(outcome) for generator in generators)
        else:
            outcome = min(generator.min_outcome()
                          for generator in extra_outcomes_and_generators
                          if generator.outcomes())

            next_extra_outcomes, _, _ = next(
                extra_outcomes._generate_min(outcome))

            return outcome, next_extra_outcomes, tuple(
                generator._generate_min(outcome) for generator in generators)

    def sample(
        self, *generators:
        'icepool.MultisetGenerator[T_contra, Any] | Mapping[T_contra, int] | Sequence[T_contra]'
    ):
        """EXPERIMENTAL: Samples one result from the generator(s) and evaluates the result."""
        # Convert non-`Pool` arguments to `Pool`.
        converted_generators = tuple(
            generator if isinstance(generator, icepool.MultisetGenerator
                                    ) else icepool.Pool(generator)
            for generator in generators)

        result = self.evaluate(*itertools.chain.from_iterable(
            generator.sample() for generator in converted_generators))

        if not result.is_empty():
            return result.outcomes()[0]
        else:
            return result

    def __bool__(self) -> bool:
        raise TypeError('MultisetEvaluator does not have a truth value.')

    def __str__(self) -> str:
        return type(self).__name__
