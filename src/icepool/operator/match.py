__docformat__ = 'google'

from icepool.expression.multiset_expression import MultisetExpression
from icepool.operator.multiset_operator import MultisetOperator
from icepool.order import Order, UnsupportedOrder

from typing import Iterator, MutableSequence, Sequence
from icepool.typing import T


class MultisetSortMatch(MultisetOperator[T]):

    def __init__(self, left: MultisetExpression[T],
                 right: MultisetExpression[T], *, order: Order, tie: int,
                 left_first: int, right_first: int):
        if order == Order.Any:
            order = Order.Descending
        self._children = (left, right)
        self._order = order
        self._tie = tie
        self._left_first = left_first
        self._right_first = right_first

    def _initial_state(
            self, order, outcomes, child_sizes: MutableSequence,
            source_sizes: Iterator, param_sizes: Sequence
    ) -> tuple[tuple[int, int, int, int], int | None]:
        """
        State is left_lead, tie, left_first, right_first.
        """
        if order == self._order:
            return (0, self._tie, self._left_first, self._right_first), None
        else:
            left_size, right_size = child_sizes
            if left_size is None or right_size is None:
                raise UnsupportedOrder(
                    'Reverse order not supported unless sizes of both operands are inferrable.'
                )
            left_lead = right_size - left_size
            return (left_lead, self._tie, self._right_first,
                    self._left_first), None

    def _next_state(self, state, order, outcome, child_counts, source_counts,
                    param_counts):
        left_lead, tie, left_first, right_first = state
        left_count, right_count = child_counts
        left_count = max(left_count, 0)
        right_count = max(right_count, 0)

        count = 0
        if left_lead >= 0:
            count += max(min(right_count - left_lead, left_count), 0) * tie
        elif left_lead < 0:
            count += max(min(left_count + left_lead, right_count), 0) * tie
            count += min(-left_lead, left_count) * right_first

        left_lead += left_count - right_count

        if left_lead > 0:
            count += min(left_lead, left_count) * left_first

        return (left_lead, tie, left_first, right_first), count

    @property
    def _expression_key(self):
        return MultisetSortMatch, self._order


class MultisetMaximumMatch(MultisetOperator[T]):

    def __init__(self, left: MultisetExpression[T],
                 right: MultisetExpression[T], *, order: Order,
                 match_equal: bool, keep: bool):
        self._children = (left, right)
        self._order = order
        self._match_equal = match_equal
        self._keep = keep

    def _initial_state(self, order, outcomes, child_sizes: MutableSequence,
                       source_sizes: Iterator,
                       param_sizes: Sequence) -> tuple[int, int | None]:
        """
        
        Returns:
            prev_matchable: The number of previously-seen elements that are
                eligible to be matched.
        """
        if order == self._order:
            return 0, None
        else:
            raise UnsupportedOrder()

    def _next_state(self, prev_matchable, order, outcome, child_counts,
                    source_counts, param_counts):
        left_count, right_count = child_counts

        left_count = max(left_count, 0)
        right_count = max(right_count, 0)

        if self._match_equal:
            new_matches = min(prev_matchable + right_count, left_count)
        else:
            new_matches = min(prev_matchable, left_count)
        prev_matchable += right_count - new_matches
        if self._keep:
            count = new_matches
        else:
            count = left_count - new_matches
        return prev_matchable, count

    @property
    def _expression_key(self):
        return MultisetMaximumMatch, self._order, self._match_equal, self._keep
