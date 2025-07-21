__docformat__ = 'google'

from icepool.expression.multiset_expression import MultisetExpression
from icepool.lexi import compute_lexi_tuple
from icepool.operator.multiset_operator import MultisetOperator
from icepool.typing import T
from icepool.order import Order, UnsupportedOrder

from typing import Iterator, Literal, MutableSequence, Sequence


class MultisetVersus(MultisetOperator[T]):

    def __init__(self, left: MultisetExpression[T],
                 right: MultisetExpression[T], *,
                 lexi_tuple: tuple[int, int, int], order: Order):
        """Constructor.
        
        Args:
            lexi_tuple: Whether left elements are kept if they appear before, at
                the same time, and after right elements (when using preferred
                order).
            order: The preferred order in which to consider the outcomes.
        """
        self._children = (left, right)
        self._lexi_tuple = lexi_tuple
        self._order = order

    def _initial_state(
        self, order, outcomes, child_sizes: MutableSequence,
        source_sizes: Iterator, arg_sizes: Sequence
    ) -> tuple[tuple[tuple[int, int, int], int], int | None]:
        """
        State is lexi_order, countdown.
        """
        if order == self._order:
            countdown = 1
            lexi_tuple = self._lexi_tuple
        else:
            _, right_size = child_sizes
            if right_size is None:
                raise UnsupportedOrder(
                    'Reverse order not supported unless the size of the right operand is inferrable.'
                )
            countdown = right_size
            lexi_tuple = tuple(reversed(self._lexi_tuple))  # type: ignore
        return (lexi_tuple, countdown), None

    def _next_state(self, state, order, outcome, child_counts, source_counts,
                    arg_counts):
        lexi_tuple, countdown = state
        left_first, tie, right_first = lexi_tuple
        left_count, right_count = child_counts

        right_count = max(right_count, 0)

        if countdown > right_count:
            count = left_count * left_first
        elif countdown > 0:
            count = left_count * tie
        else:
            count = left_count * right_first

        countdown = max(countdown - right_count, 0)

        return (lexi_tuple, countdown), count

    @property
    def _expression_key(self):
        return MultisetVersus, self._lexi_tuple, self._order

    @property
    def _dungeonlet_key(self):
        return MultisetVersus


class MultisetCmp(MultisetOperator[T]):

    def __init__(self, left: MultisetExpression[T],
                 right: MultisetExpression[T], *, order: Order):
        """Constructor.
        
        Args:
            order: The first element seen on each side in this order will
                cancel all future elements of the other side.
        """
        self._children = (left, right)
        self._order = order

    def _initial_state(
            self, order, outcomes, child_sizes: MutableSequence,
            source_sizes: Iterator,
            arg_sizes: Sequence) -> tuple[tuple[int, int, int], int | None]:
        if order == self._order:
            forward_order = True
            left_score = 0
            right_score = 0
        else:
            left_size, right_size = child_sizes
            if left_size is None or right_size is None:
                raise UnsupportedOrder(
                    'Reverse order not supported unless the sizes of both operands are inferrable.'
                )
            forward_order = False
            left_score = left_size
            right_score = right_size
        return (forward_order, left_score, right_score), None

    def _next_state(self, state, order, outcome, child_counts, source_counts,
                    arg_counts):
        forward_order, left_score, right_score = state
        left_count, right_count = child_counts
        left_count = max(left_count, 0)
        right_count = max(right_count, 0)

        if forward_order:
            # In forward order, once we see any element from one side, all
            # elements of the other side are canceled from then on.
            left_score = left_score or (left_count > 0)
            right_score = right_score or (right_count > 0)
            if not left_score:
                count = -right_count
            elif not right_score:
                count = left_count
            else:
                count = 0
        else:
            # In backwards order, we drop elements from both sides until one
            # side runs out.
            if not left_score:
                count = -right_count
            elif not right_score:
                count = left_count
            else:
                count = 0
            left_score -= left_count
            right_score -= right_count

        return (forward_order, left_score, right_score), count

    @property
    def _expression_key(self):
        return MultisetCmp, self._order

    @property
    def _dungeonlet_key(self):
        return MultisetCmp
