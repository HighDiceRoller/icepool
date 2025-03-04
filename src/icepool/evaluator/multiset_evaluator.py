__docformat__ = 'google'

from functools import cached_property
import icepool
from icepool.evaluator.multiset_evaluator_base import MultisetEvaluatorBase, MultisetDungeon
from icepool.expression.base import MultisetExpressionBase
from icepool.order import Order

from icepool.typing import Q, T, U_co
from typing import (Any, Callable, Collection, Generic, Hashable, Iterator,
                    Mapping, MutableMapping, Sequence, TypeAlias, cast,
                    TYPE_CHECKING, overload)


class MultisetEvaluator(MultisetEvaluatorBase[T, U_co]):

    def next_state(self, state: Hashable, outcome: T, /, *counts,
                   **kwargs: Hashable) -> Hashable:
        """State transition function.

        This should produce a state given the previous state, an outcome,
        the count of that outcome produced by each multiset input, and any
        **kwargs provided to `evaluate()`.

        `evaluate()` will always call this with `state, outcome, *counts` as
        positional arguments. Furthermore, there is no expectation that a 
        subclass be able to handle an arbitrary number of counts. 
        
        Thus, you are free to:
        * Rename `state` or `outcome` in a subclass.
        * Replace `*counts` with a fixed set of parameters.

        **kwargs are non-multiset arguments that were provided to evaluate().
        You may replace **kwargs with a fixed set of keyword parameters.

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
          implementation for each, override both `next_state_ascending()` and 
          `next_state_descending()`. If your evaluator wraps subevaluator(s),
          you can do this and use `subevaluator.next_state_method(order)` to
          retrieve the correct method for the subevaluator(s).
          See `JointEvaluator` for an example.

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

    def next_state_ascending(self, state: Hashable, outcome: T, /, *counts,
                             **kwargs: Hashable) -> Hashable:
        """As next_state() but handles outcomes in ascending order only.
        
        You can implement both `next_state_ascending()` and 
        `next_state_descending()` if you want to handle both outcome orders
        with a separate implementation for each.
        """
        raise NotImplementedError()

    def next_state_descending(self, state: Hashable, outcome: T, /, *counts,
                              **kwargs: Hashable) -> Hashable:
        """As next_state() but handles outcomes in descending order only.
        
        You can implement both `next_state_ascending()` and 
        `next_state_descending()` if you want to handle both outcome orders
        with a separate implementation for each.
        """
        raise NotImplementedError()

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

    def final_outcome(
            self, final_state: Hashable, /, **kwargs: Hashable
    ) -> 'U_co | icepool.Die[U_co] | icepool.RerollType':
        """Optional method to generate a final output outcome from a final state.

        By default, the final outcome is equal to the final state.
        Note that `None` is not a valid outcome for a `Die`,
        and if there are no outcomes, `final_outcome` will be immediately
        be callled with `final_state=None`.
        Subclasses that want to handle this case should explicitly define what
        happens.

        Args:
            final_state: A state after all outcomes have been processed.
            kwargs: Any kwargs that were passed to the evaluation.

        Returns:
            A final outcome that will be used as part of constructing the result `Die`.
            As usual for `Die()`, this could itself be a `Die` or `icepool.Reroll`.
        """
        # If not overriden, the final_state should have type U_co.
        return cast(U_co, final_state)

    def _get_next_state_method(
            self, method_name: str) -> Callable[..., Hashable] | None:
        """Returns the next_state method by name, or `None` if not implemented."""
        try:
            method = getattr(self, method_name)
            if method is None:
                return None
            method_func = getattr(method, '__func__', method)
        except AttributeError:
            return None
        if method_func is getattr(MultisetEvaluator, method_name):
            return None
        return method

    def next_state_method(self, order: Order,
                          /) -> Callable[..., Hashable] | None:
        """Returns the bound next_state* method for the given order, or `None` if that order is not supported.
        
        `next_state_ascending` and `next_state_descending` are prioritized over
        `next_state`.
        """
        if order > 0:
            return self._get_next_state_method(
                'next_state_ascending') or self._get_next_state_method(
                    'next_state')
        elif order < 0:
            return self._get_next_state_method(
                'next_state_descending') or self._get_next_state_method(
                    'next_state')
        else:
            return self._get_next_state_method(
                'next_state_ascending') or self._get_next_state_method(
                    'next_state_descending') or self._get_next_state_method(
                        'next_state')

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

    def prepare(
        self,
        inputs: 'tuple[MultisetExpressionBase[T, Q], ...]',
        kwargs: Mapping[str, Hashable],
    ):
        return MultisetEvaluatorDungeon(
            self, self.next_state_method(Order.Ascending),
            self.next_state_method(Order.Descending), self.extra_outcomes,
            self.final_outcome, kwargs), ()


class MultisetEvaluatorDungeon(MultisetDungeon[T, U_co]):

    body_inputs_len = 0

    # These are filled in by the constructor.
    next_state_ascending = None  # type: ignore
    next_state_descending = None  # type: ignore
    extra_outcomes = None  # type: ignore
    final_outcome = None  # type: ignore

    def __init__(self, preparer: MultisetEvaluator,
                 next_state_ascending: Callable[..., Hashable] | None,
                 next_state_descending: Callable[..., Hashable] | None,
                 extra_outcomes: Callable, final_outcome: Callable,
                 kwargs: Mapping[str, Hashable]):
        self.preparer = preparer
        self.next_state_ascending = next_state_ascending  # type: ignore
        self.next_state_descending = next_state_descending  # type: ignore
        self.extra_outcomes = extra_outcomes  # type: ignore
        self.final_outcome = final_outcome  # type: ignore
        self.kwargs = kwargs
        self.ascending_cache = {}
        self.descending_cache = {}

    @cached_property
    def _hash_key(self) -> Hashable:
        return (MultisetEvaluatorDungeon, self.preparer,
                tuple(sorted(self.kwargs.items())))

    @cached_property
    def _hash(self) -> int:
        return hash(self._hash_key)

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other) -> bool:
        if not isinstance(other, MultisetEvaluatorDungeon):
            return False
        return self._hash_key == other._hash_key
