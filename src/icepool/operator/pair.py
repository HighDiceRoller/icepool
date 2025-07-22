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
                 comparison: Literal['==', '!=', '<=', '<', '>=',
                                     '>'], sort_order: Order,
                 extra: Literal['early', 'late', 'low', 'high', 'equal',
                                'keep', 'drop']):
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
        left_first, left_extra, tie, right_extra, right_first = compute_lexi_tuple_with_extra(
            self._comparison, self._sort_order, self._extra)

        if order == self._sort_order:
            forward_order = True
            # drop right_extra
            lexi_tuple = left_first, left_extra, tie, right_first
            left_lead = 0
            if left_first == left_extra:
                countdown = None
            else:
                left_size, right_size = child_sizes
                if right_size is None:
                    raise OrderError(
                        f'The size of the right operand must be inferrable to sort_pair({self._comparison}, extra={self._extra}).'
                    )
                # After `countdown` elements, the rest are considered to be
                # extra.
                countdown = right_size
        else:
            forward_order = False
            # reverse, then drop the resulting right_extra
            lexi_tuple = right_first, right_extra, tie, left_first
            left_size, right_size = child_sizes
            if left_size is None or right_size is None:
                raise UnsupportedOrder(
                    'Reverse order not supported unless sizes of both operands are inferrable.'
                )
            if left_first == left_extra:
                left_lead = right_size - left_size
                countdown = None
            else:
                # The first `countdown` elements will be counted as extra.
                left_lead = 0
                countdown = max(left_size - right_size, 0)
        return (lexi_tuple, forward_order, left_lead, countdown), None

    def _next_state(self, state, order, outcome, child_counts, source_counts,
                    arg_counts):
        lexi_tuple, forward_order, left_lead, countdown = state
        left_first, left_extra, tie, right_first = lexi_tuple
        left_count, right_count = child_counts
        if countdown is None:
            extra_count = 0
            left_count = max(left_count, 0)
        else:
            if forward_order:
                extra_count = max(left_count - countdown, 0)
                left_count = min(left_count, countdown)
                countdown -= left_count
            else:
                extra_count = min(left_count, countdown)
                left_count = max(left_count - countdown, 0)
                countdown -= extra_count

        right_count = max(right_count, 0)

        right_first_count = max(min(-left_lead, left_count), 0)
        if left_lead >= 0:
            tie_count = max(min(right_count - left_lead, left_count), 0)
        elif left_lead < 0:
            tie_count = max(min(left_count + left_lead, right_count), 0)

        left_lead += left_count - right_count

        left_first_count = max(min(left_lead, left_count), 0)

        count = (right_first_count * right_first + tie_count * tie +
                 left_first_count * left_first + extra_count * left_extra)

        return (lexi_tuple, forward_order, left_lead, countdown), count

    @property
    def _expression_key(self):
        return MultisetSortPair, self._comparison, self._sort_order, self._extra

    @property
    def _dungeonlet_key(self):
        return MultisetSortPair


class MultisetMaxPair(MultisetOperator[T]):

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
        return MultisetMaxPair, self._order, self._pair_equal, self._keep
