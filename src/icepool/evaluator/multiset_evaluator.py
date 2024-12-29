__docformat__ = 'google'

import icepool
from icepool.order import Order, OrderReason, merge_order_preferences

from abc import ABC, abstractmethod
from collections import defaultdict
from functools import cached_property
import itertools
import math

from icepool.typing import T, U_co
from typing import (Any, Callable, Collection, Generic, Hashable, Mapping,
                    MutableMapping, Sequence, cast, TYPE_CHECKING, overload)

if TYPE_CHECKING:
    from icepool.generator.alignment import Alignment
    from icepool import MultisetExpression

PREFERRED_ORDER_COST_FACTOR = 10
"""The preferred order will be favored this times as much."""


class MultisetEvaluator(ABC, Generic[T, U_co]):
    """An abstract, immutable, callable class for evaulating one or more input `MultisetExpression`s.

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
    be able to handle arbitrary types or numbers of inputs.
    Indeed, most are expected to handle only a fixed number of inputs,
    and often even only inputs with a particular outcome type.

    Instances cache all intermediate state distributions.
    You should therefore reuse instances when possible.

    Instances should not be modified after construction
    in any way that affects the return values of these methods.
    Otherwise, values in the cache may be incorrect.
    """

    def next_state(self, state: Hashable, outcome: T, /, *counts:
                   int) -> Hashable:
        """State transition function.

        This should produce a state given the previous state, an outcome,
        and the count of that outcome produced by each input.

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

        By default, this method may receive outcomes in any order:
        
        * If you want to guarantee ascending or descending order, you can 
          implement `next_state_ascending()` or `next_state_descending()` 
          instead.
        * Alternatively, implement `next_state()` and override `order()` to
          return the necessary order. This is useful if the necessary order
          depends on the instance.
        * If you want to handle either order, but have a different 
          implementation for each, override both  `next_state_ascending()` and 
          `next_state_descending()`.

        The behavior of returning a `Die` from `next_state` is currently
        undefined.

        Args:
            state: A hashable object indicating the state before rolling the
                current outcome. If this is the first outcome being considered,
                `state` will be `None`.
            outcome: The current outcome.
                `next_state` will see all rolled outcomes in monotonic order;
                either ascending or descending depending on `order()`.
                If there are multiple inputs, the set of outcomes is at 
                least the union of the outcomes of the invididual inputs. 
                You can use `extra_outcomes()` to add extra outcomes.
            *counts: One value (usually an `int`) for each input indicating how
                many of the current outcome were produced.

        Returns:
            A hashable object indicating the next state.
            The special value `icepool.Reroll` can be used to immediately remove
            the state from consideration, effectively performing a full reroll.
        """
        raise NotImplementedError()

    def next_state_ascending(self, state: Hashable, outcome: T, /, *counts:
                             int) -> Hashable:
        """As next_state() but handles outcomes in ascending order only.
        
        You can implement both `next_state_ascending()` and 
        `next_state_descending()` if you want to handle both outcome orders
        with a separate implementation for each.
        """
        raise NotImplementedError()

    def next_state_descending(self, state: Hashable, outcome: T, /, *counts:
                              int) -> Hashable:
        """As next_state() but handles outcomes in descending order only.
        
        You can implement both `next_state_ascending()` and 
        `next_state_descending()` if you want to handle both outcome orders
        with a separate implementation for each.
        """
        raise NotImplementedError()

    def final_outcome(self, final_state: Hashable,
                      /) -> 'U_co | icepool.Die[U_co] | icepool.RerollType':
        """Optional method to generate a final output outcome from a final state.

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
        """Optional method that specifies what outcome orderings this evaluator supports.

        By default, this is determined by which of `next_state()`, 
        `next_state_ascending()`, and `next_state_descending()` are
        overridden.

        This is most often overridden by subclasses whose iteration order is
        determined on a per-instance basis.

        Returns:
            * Order.Ascending (= 1)
                if outcomes are to be seen in ascending order.
                In this case either `next_state()` or `next_state_ascending()`
                are implemented.
            * Order.Descending (= -1)
                if outcomes are to be seen in descending order.
                In this case either `next_state()` or `next_state_descending()`
                are implemented.
            * Order.Any (= 0)
                if outcomes can be seen in any order.
                In this case either `next_state()` or both
                `next_state_ascending()` and `next_state_descending()`
                are implemented.
        """
        overrides_ascending = self._has_override('next_state_ascending')
        overrides_descending = self._has_override('next_state_descending')
        overrides_any = self._has_override('next_state')
        if overrides_any or (overrides_ascending and overrides_descending):
            return Order.Any
        if overrides_ascending:
            return Order.Ascending
        if overrides_descending:
            return Order.Descending
        raise NotImplementedError(
            'Subclasses of MultisetEvaluator must implement at least one of next_state, next_state_ascending, next_state_descending.'
        )

    def extra_outcomes(self, outcomes: Sequence[T]) -> Collection[T]:
        """Optional method to specify extra outcomes that should be seen as inputs to `next_state()`.

        These will be seen by `next_state` even if they do not appear in the
        input(s). The default implementation returns `()`, or no additional
        outcomes.

        If you want `next_state` to see consecutive `int` outcomes, you can set
        `extra_outcomes = icepool.MultisetEvaluator.consecutive`.
        See `consecutive()` below.

        Args:
            outcomes: The outcomes that could be produced by the inputs, in
            ascending order.
        """
        return ()

    def consecutive(self, outcomes: Sequence[int]) -> Collection[int]:
        """Example implementation of `extra_outcomes()` that produces consecutive `int` outcomes.

        Set `extra_outcomes = icepool.MultisetEvaluator.consecutive` to use this.

        Returns:
            All `int`s from the min outcome to the max outcome among the inputs,
            inclusive.

        Raises:
            TypeError: if any input has any non-`int` outcome.
        """
        if not outcomes:
            return ()

        if any(not isinstance(x, int) for x in outcomes):
            raise TypeError(
                "consecutive cannot be used with outcomes of type other than 'int'."
            )

        return range(outcomes[0], outcomes[-1] + 1)

    def bound_inputs(self) -> 'tuple[icepool.MultisetExpression, ...]':
        """An optional sequence of extra inputs whose counts will be prepended to *counts.
        
        (Prepending rather than appending is analogous to `functools.partial`.)
        """
        return ()

    @cached_property
    def _cache(
        self
    ) -> 'MutableMapping[tuple[Order, Alignment, tuple[MultisetExpression, ...], Hashable], Mapping[Any, int]]':
        """Cached results.
        
        The key is `(order, extra_outcomes, inputs, state)`.
        The value is another mapping `final_state: quantity` representing the
        state distribution produced by `order, extra_outcomes, inputs` when
        starting at state `state`.
        """
        return {}

    @overload
    def evaluate(
            self,
            *args: 'Mapping[T, int] | Sequence[T]') -> 'icepool.Die[U_co]':
        ...

    @overload
    def evaluate(
            self,
            *args: 'MultisetExpression[T]') -> 'MultisetEvaluator[T, U_co]':
        ...

    @overload
    def evaluate(
        self, *args: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'icepool.Die[U_co] | MultisetEvaluator[T, U_co]':
        ...

    def evaluate(
        self, *args: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'icepool.Die[U_co] | MultisetEvaluator[T, U_co]':
        """Evaluates input expression(s).

        You can call the `MultisetEvaluator` object directly for the same effect,
        e.g. `sum_evaluator(input)` is an alias for `sum_evaluator.evaluate(input)`.

        Most evaluators will expect a fixed number of input multisets.
        The union of the outcomes of the input(s) must be totally orderable.

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
        inputs = tuple(
            icepool.implicit_convert_to_expression(arg) for arg in args)

        if any(input.has_free_variables() for input in inputs):
            from icepool.evaluator.multiset_function import MultisetFunctionEvaluator
            return MultisetFunctionEvaluator(*inputs, evaluator=self)

        inputs = self.bound_inputs() + inputs

        # This is kept to verify inputs to operators each have arity exactly 1.
        total_arity = sum(input.output_arity() for input in inputs)

        if not all(expression._is_resolvable() for expression in inputs):
            return icepool.Die([])

        algorithm, order = self._select_algorithm(*inputs)

        next_state_function = self._select_next_state_function(order)

        outcomes = icepool.sorted_union(*(expression.outcomes()
                                          for expression in inputs))
        extra_outcomes = Alignment(self.extra_outcomes(outcomes))

        dist: MutableMapping[Any, int] = defaultdict(int)
        iterators = MultisetEvaluator._initialize_inputs(inputs)
        for p in itertools.product(*iterators):
            sub_inputs, sub_weights = zip(*p)
            prod_weight = math.prod(sub_weights)
            sub_result = algorithm(order, next_state_function, extra_outcomes,
                                   sub_inputs)
            for sub_state, sub_weight in sub_result.items():
                dist[sub_state] += sub_weight * prod_weight

        final_outcomes = []
        final_weights = []
        for state, weight in dist.items():
            outcome = self.final_outcome(state)
            if outcome is None:
                raise TypeError(
                    "None is not a valid final outcome.\n"
                    "This may have been a result of not supplying any input with an outcome."
                )
            if outcome is not icepool.Reroll:
                final_outcomes.append(outcome)
                final_weights.append(weight)

        return icepool.Die(final_outcomes, final_weights)

    __call__ = evaluate

    def _select_algorithm(
        self, *inputs: 'icepool.MultisetExpression[T]'
    ) -> tuple[
            'Callable[[Order, Callable[..., Hashable], Alignment[T], tuple[icepool.MultisetExpression[T], ...]], Mapping[Any, int]]',
            Order]:
        """Selects an algorithm and iteration order.

        Returns:
            * The algorithm to use (`_eval_internal*`).
            * The order in which `next_state()` sees outcomes.
                1 for ascending and -1 for descending.
        """
        eval_order = self.order()

        if not inputs:
            # No inputs.
            return self._eval_internal, eval_order

        input_order, input_order_reason = merge_order_preferences(
            *(input.order_preference() for input in inputs))

        if input_order is None:
            input_order = Order.Any
            input_order_reason = OrderReason.NoPreference

        # No mandatory evaluation order, go with preferred algorithm.
        # Note that this has order *opposite* the pop order.
        if eval_order == Order.Any:
            return self._eval_internal, Order(-input_order or Order.Ascending)

        # Mandatory evaluation order.
        if input_order == Order.Any:
            return self._eval_internal, eval_order
        elif eval_order != input_order:
            return self._eval_internal, eval_order
        else:
            return self._eval_internal_forward, eval_order

    def _has_override(self, method_name: str) -> bool:
        """Returns True iff the method name is overridden from MultisetEvaluator."""
        try:
            method = getattr(self, method_name)
            method_func = getattr(method, '__func__', method)
        except AttributeError:
            return False
        return method_func is not getattr(MultisetEvaluator, method_name)

    def _select_next_state_function(self,
                                    order: Order) -> Callable[..., Hashable]:
        if order == Order.Descending:
            if self._has_override('next_state_descending'):
                return self.next_state_descending
        else:
            if self._has_override('next_state_ascending'):
                return self.next_state_ascending
        if self._has_override('next_state'):
            return self.next_state
        raise NotImplementedError(
            f'Could not find next_state* implementation for order {order}.')

    def _eval_internal(
        self, order: Order, next_state_function: Callable[..., Hashable],
        extra_outcomes: 'Alignment[T]',
        inputs: 'tuple[icepool.MultisetExpression[T], ...]'
    ) -> Mapping[Any, int]:
        """Internal algorithm for iterating in the more-preferred order.

        All intermediate return values are cached in the instance.

        Arguments:
            order: The order in which to send outcomes to `next_state()`.
            extra_outcomes: As `extra_outcomes()`. Elements will be popped off this
                during recursion.
            inputs: One or more `MultisetExpression`s to evaluate. Elements
                will be popped off this during recursion.

        Returns:
            A dict `{ state : weight }` describing the probability distribution
                over states.
        """
        cache_key = (order, extra_outcomes, inputs, None)
        if cache_key in self._cache:
            return self._cache[cache_key]

        result: MutableMapping[Any, int] = defaultdict(int)

        if all(not input.outcomes()
               for input in inputs) and not extra_outcomes.outcomes():
            result = {None: 1}
        else:
            outcome, prev_extra_outcomes, iterators = MultisetEvaluator._pop_inputs(
                Order(-order), extra_outcomes, inputs)
            for p in itertools.product(*iterators):
                prev_inputs, counts, weights = zip(*p)
                counts = tuple(itertools.chain.from_iterable(counts))
                prod_weight = math.prod(weights)
                prev = self._eval_internal(order, next_state_function,
                                           prev_extra_outcomes, prev_inputs)
                for prev_state, prev_weight in prev.items():
                    state = next_state_function(prev_state, outcome, *counts)
                    if state is not icepool.Reroll:
                        result[state] += prev_weight * prod_weight

        self._cache[cache_key] = result
        return result

    def _eval_internal_forward(
            self,
            order: Order,
            next_state_function: Callable[..., Hashable],
            extra_outcomes: 'Alignment[T]',
            inputs: 'tuple[icepool.MultisetExpression[T], ...]',
            state: Hashable = None) -> Mapping[Any, int]:
        """Internal algorithm for iterating in the less-preferred order.

        All intermediate return values are cached in the instance.

        Arguments:
            order: The order in which to send outcomes to `next_state()`.
            extra_outcomes: As `extra_outcomes()`. Elements will be popped off this
                during recursion.
            inputs: One or more `MultisetExpression`s to evaluate. Elements
                will be popped off this during recursion.

        Returns:
            A dict `{ state : weight }` describing the probability distribution
                over states.
        """
        cache_key = (order, extra_outcomes, inputs, state)
        if cache_key in self._cache:
            return self._cache[cache_key]

        result: MutableMapping[Any, int] = defaultdict(int)

        if all(not input.outcomes()
               for input in inputs) and not extra_outcomes.outcomes():
            result = {state: 1}
        else:
            outcome, next_extra_outcomes, iterators = MultisetEvaluator._pop_inputs(
                order, extra_outcomes, inputs)
            for p in itertools.product(*iterators):
                next_inputs, counts, weights = zip(*p)
                counts = tuple(itertools.chain.from_iterable(counts))
                prod_weight = math.prod(weights)
                next_state = next_state_function(state, outcome, *counts)
                if next_state is not icepool.Reroll:
                    final_dist = self._eval_internal_forward(
                        order, next_state_function, next_extra_outcomes,
                        next_inputs, next_state)
                    for final_state, weight in final_dist.items():
                        result[final_state] += weight * prod_weight

        self._cache[cache_key] = result
        return result

    @staticmethod
    def _initialize_inputs(
        inputs: 'tuple[icepool.MultisetExpression[T], ...]'
    ) -> 'tuple[icepool.InitialMultisetGeneration, ...]':
        return tuple(expression._generate_initial() for expression in inputs)

    @staticmethod
    def _pop_inputs(
        order: Order, extra_outcomes: 'Alignment[T]',
        inputs: 'tuple[icepool.MultisetExpression[T], ...]'
    ) -> 'tuple[T, Alignment[T], tuple[icepool.PopMultisetGeneration, ...]]':
        """Pops a single outcome from the inputs.

        Args:
            order: The order in which to pop. Descending order pops from the top
            and ascending from the bottom.
            extra_outcomes: Any extra outcomes to use.
            inputs: The inputs to pop from.

        Returns:
            * The popped outcome.
            * The remaining extra outcomes.
            * A tuple of iterators over the resulting inputs, counts, and weights.
        """
        extra_outcomes_and_inputs = (extra_outcomes, ) + inputs
        if order < 0:
            outcome = max(input.max_outcome()
                          for input in extra_outcomes_and_inputs
                          if input.outcomes())

            next_extra_outcomes, _, _ = next(
                extra_outcomes._generate_max(outcome))

            return outcome, next_extra_outcomes, tuple(
                input._generate_max(outcome) for input in inputs)
        else:
            outcome = min(input.min_outcome()
                          for input in extra_outcomes_and_inputs
                          if input.outcomes())

            next_extra_outcomes, _, _ = next(
                extra_outcomes._generate_min(outcome))

            return outcome, next_extra_outcomes, tuple(
                input._generate_min(outcome) for input in inputs)

    def sample(
        self, *inputs:
        'icepool.MultisetExpression[T] | Mapping[T, int] | Sequence[T]'):
        """EXPERIMENTAL: Samples one result from the input(s) and evaluates the result."""
        # Convert non-`Pool` arguments to `Pool`.
        converted_inputs = tuple(
            input if isinstance(input, icepool.MultisetExpression
                                ) else icepool.Pool(input) for input in inputs)

        result = self.evaluate(*itertools.chain.from_iterable(
            input.sample() for input in converted_inputs))

        if not result.is_empty():
            return result.outcomes()[0]
        else:
            return result

    def __bool__(self) -> bool:
        raise TypeError('MultisetEvaluator does not have a truth value.')

    def __str__(self) -> str:
        return type(self).__name__
