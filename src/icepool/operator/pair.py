__docformat__ = 'google'

from icepool.expression.multiset_expression import MultisetExpression
from icepool.lexi import compute_lexi_tuple, compute_lexi_tuple_with_extra
from icepool.operator.multiset_operator import MultisetOperator
from icepool.order import Order, OrderError, UnsupportedOrder

from typing import Iterator, Literal, MutableSequence, Sequence
from icepool.typing import T


class MultisetSortPair(MultisetOperator[T]):

    def __init__(self, left: MultisetExpression[T],
                 right: MultisetExpression[T], *,
                 comparison: Literal['==', '!=', '<=', '<', '>=', '>'],
                 sort_order: Order, extra: Literal['early', 'late', 'low',
                                                   'high', 'drop']):
        if sort_order == Order.Any:
            sort_order = Order.Descending
        self._children = (left, right)
        self._comparison = comparison
        self._sort_order = sort_order
        self._extra = extra

    def _initial_state(
        self, order, outcomes, child_sizes: MutableSequence,
        source_sizes: Iterator, arg_sizes: Sequence
    ) -> tuple[tuple[tuple[int, int, int, int], bool, int, int | None], int
               | None]:
        """
        State is lexi_order, left_lead.
        """
        left_first, left_extra, tie, right_extra, right_first = compute_lexi_tuple_with_extra(
            self._comparison, order, self._extra)
        # drop right_extra
        lexi_tuple = left_first, left_extra, tie, right_first
        if order == self._sort_order:
            forward_order = True
            left_lead = 0
            if left_first == left_extra:
                countdown = None
            else:
                left_size, right_size = child_sizes
                if right_size is None:
                    raise OrderError(
                        f'The size of the right operand must be inferrable to sort_pair({self._comparison}, extra={self._extra}).'
                    )
                # After countdown elements, the remaining elements will be
                # unconditionally dropped.
                countdown = right_size
        else:
            forward_order = False
            left_size, right_size = child_sizes
            if left_size is None or right_size is None:
                raise UnsupportedOrder(
                    'Reverse order not supported unless sizes of both operands are inferrable.'
                )
            left_lead = right_size - left_size  # TODO: use both this and countdown, or just one?
            if left_first == left_extra:
                countdown = None
            else:
                # Elements will be unconditionally dropped until countdown
                # elements.
                countdown = left_lead
        return (lexi_tuple, forward_order, left_lead, countdown), None

    def _next_state(self, state, order, outcome, child_counts, source_counts,
                    arg_counts):
        lexi_tuple, forward_order, left_lead, countdown = state
        left_first, left_extra, tie, right_first = lexi_tuple
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

        if countdown is not None:
            countdown -= left_count

        return (lexi_tuple, forward_order, left_lead, countdown), count

    @property
    def _expression_key(self):
        return MultisetSortPair, self._comparison, self._sort_order

    @property
    def _dungeonlet_key(self):
        return MultisetSortPair


class MultisetMaximumPair(MultisetOperator[T]):

    def __init__(self, left: MultisetExpression[T],
                 right: MultisetExpression[T], *, order: Order,
                 pair_equal: bool, keep: bool):
        self._children = (left, right)
        self._order = order
        self._pair_equal = pair_equal
        self._keep = keep

    def _initial_state(self, order, outcomes, child_sizes: MutableSequence,
                       source_sizes: Iterator,
                       arg_sizes: Sequence) -> tuple[int, int | None]:
        """
        
        Returns:
            prev_pairable: The number of previously-seen elements that are
                eligible to be paired.
        """
        if order == self._order:
            return 0, None
        else:
            raise UnsupportedOrder()

    def _next_state(self, prev_pairable, order, outcome, child_counts,
                    source_counts, arg_counts):
        left_count, right_count = child_counts

        left_count = max(left_count, 0)
        right_count = max(right_count, 0)

        if self._pair_equal:
            new_pairs = min(prev_pairable + right_count, left_count)
        else:
            new_pairs = min(prev_pairable, left_count)
        prev_pairable += right_count - new_pairs
        if self._keep:
            count = new_pairs
        else:
            count = left_count - new_pairs
        return prev_pairable, count

    @property
    def _expression_key(self):
        return MultisetMaximumPair, self._order, self._pair_equal, self._keep
