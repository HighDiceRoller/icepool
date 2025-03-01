__docformat__ = 'google'

from icepool.evaluator.base import MultisetEvaluatorBase, MultisetDungeon
from icepool.order import Order

from icepool.typing import T, U_co
from typing import (Any, Callable, Collection, Generic, Hashable, Iterator,
                    Mapping, MutableMapping, Sequence, TypeAlias, cast,
                    TYPE_CHECKING, overload)


class MultisetEvaluator(MultisetEvaluatorBase[T, U_co]):

    def next_state(self, state: Hashable, outcome: T, /, *counts) -> Hashable:
        """State transition function.

        This should produce a state given the previous state, an outcome,
        and the count of that outcome produced by each input.

        `evaluate()` will always call this with `state, outcome, *counts` as
        positional arguments. Furthermore, there is no expectation that a 
        subclass be able to handle an arbitrary number of counts. 
        
        Thus, you are free to:
        * Rename `state` or `outcome` in a subclass.
        * Replace `*counts` with a fixed set of parameters.

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

    def next_state_ascending(self, state: Hashable, outcome: T, /,
                             *counts) -> Hashable:
        """As next_state() but handles outcomes in ascending order only.
        
        You can implement both `next_state_ascending()` and 
        `next_state_descending()` if you want to handle both outcome orders
        with a separate implementation for each.
        """
        raise NotImplementedError()

    def next_state_descending(self, state: Hashable, outcome: T, /,
                              *counts) -> Hashable:
        """As next_state() but handles outcomes in descending order only.
        
        You can implement both `next_state_ascending()` and 
        `next_state_descending()` if you want to handle both outcome orders
        with a separate implementation for each.
        """
        raise NotImplementedError()

    def _has_override(self, method_name: str) -> bool:
        """Returns True iff the method name is overridden from MultisetEvaluator."""
        try:
            method = getattr(self, method_name)
            method_func = getattr(method, '__func__', method)
        except AttributeError:
            return False
        return method_func is not getattr(MultisetEvaluator, method_name)

    def next_state_method(self, order: Order, /) -> Callable[..., Hashable]:
        """Returns the bound next_state* method for the given order.
        
        `next_state_ascending` and `next_state_descending` are prioritized over
        `next_state`.

        Raises:
            NotImplementedError if no such method is implemented.
        """
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

    def prepare(self, order: Order,
                kwargs: Mapping[str, Hashable]) -> 'MultisetDungeon':
        return MultisetDungeon(self.next_state_method(order), order, kwargs)
