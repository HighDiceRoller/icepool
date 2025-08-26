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
        self, order, outcomes, child_sizes: Sequence, source_sizes: Iterator,
        arg_sizes: Sequence
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

        # The number of left elements that paired with previously-seen right
        # elements.
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


class MultisetSortPairWhile(MultisetOperator[T]):

    def __init__(self,
                 left: MultisetExpression[T],
                 right: MultisetExpression[T],
                 *,
                 keep: bool = True,
                 comparison: Literal['==', '!=', '<=', '<', '>=', '>'],
                 sort_order: Order,
                 extra: Literal['early', 'late', 'low', 'high', 'equal',
                                'continue', 'break']):
        """
        
        Args:
            left, right: The two multisets to operate on.
            comparison: The comparision to keep or drop while.
            sort_order: The order to sort in.
            keep: If set (default True), elements will be kept as long as the 
                comparison holds, then the remaining elements will be dropped.
                Otherwise, elements will be dropped as long as the comparison 
                holds, then the remaining elements will be kept.
            extra: If `left` has more elements than `other`, this determines
                how the extra elements are treated relative to their missing
                partners.
        """
        if sort_order == Order.Any:
            sort_order = Order.Descending
        self._children = (left, right)
        self._keep = keep
        self._comparison = comparison
        self._sort_order = sort_order
        self._extra = extra

    def _initial_state(
        self, order, outcomes, child_sizes: Sequence, source_sizes: Iterator,
        arg_sizes: Sequence
    ) -> tuple[tuple[tuple[int, int, int, int] | None, int | None, int | None],
               int
               | None]:
        if order != self._sort_order:
            raise UnsupportedOrder(
                'MultisetSortPairWhile must be evaluated in sort order.')
        left_first, left_extra, tie, right_extra, right_first = compute_lexi_tuple_with_extra(
            self._comparison, self._sort_order, self._extra)
        # drop right_extra
        lexi_tuple = left_first, left_extra, tie, right_first
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
        left_lead = 0
        return (lexi_tuple, left_lead, countdown), None

    def _next_state(self, state, order, outcome, child_counts, source_counts,
                    arg_counts):
        lexi_tuple, left_lead, countdown = state
        left_count, right_count = child_counts
        if countdown is None:
            extra_count = 0
            left_count = max(left_count, 0)
        else:
            extra_count = max(left_count - countdown, 0)
            left_count = min(left_count, countdown)
            countdown -= left_count

        if lexi_tuple is None:
            count = 0 if self._keep else left_count
            return (None, None, countdown), count

        left_first, left_extra, tie, right_first = lexi_tuple
        right_count = max(right_count, 0)

        # The number of left elements that paired with previously-seen right
        # elements.
        right_first_count = max(min(-left_lead, left_count), 0)
        if left_lead >= 0:
            tie_count = max(min(right_count - left_lead, left_count), 0)
        elif left_lead < 0:
            tie_count = max(min(left_count + left_lead, right_count), 0)

        left_lead += left_count - right_count

        left_first_count = max(min(left_lead, left_count), 0)

        if right_first_count > 0 and not right_first:
            lexi_tuple = None
            left_lead = None
            count = 0
        elif tie_count > 0 and not tie:
            lexi_tuple = None
            left_lead = None
            count = right_first_count
        elif left_first_count > 0 and not left_first:
            lexi_tuple = None
            left_lead = None
            count = right_first_count + tie_count
        elif extra_count > 0 and not left_extra:
            lexi_tuple = None
            left_lead = None
            count = right_first_count + tie_count + left_first_count
        else:
            count = left_count + extra_count

        if not self._keep:
            count = left_count + extra_count - count

        return (lexi_tuple, left_lead, countdown), count

    @property
    def _expression_key(self):
        return MultisetSortPairWhile, self._keep, self._comparison, self._sort_order, self._extra

    @property
    def _dungeonlet_key(self):
        return MultisetSortPairWhile, self._keep


class MultisetMaxPairLate(MultisetOperator[T]):

    def __init__(self, left: MultisetExpression[T],
                 right: MultisetExpression[T], *, order: Order,
                 pair_equal: bool, keep: bool):
        self._children = (left, right)
        self._order = order
        self._pair_equal = pair_equal
        self._keep = keep

    def _initial_state(self, order, outcomes, child_sizes: Sequence,
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
            if self._order > 0:
                raise UnsupportedOrder(
                    "max_pair methods with priority='low' must be evaluated in ascending order."
                )
            else:
                raise UnsupportedOrder(
                    "max_pair methods with priority='high' must be evaluated in descending order."
                )

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
        return MultisetMaxPairLate, self._order, self._pair_equal, self._keep


class MultisetMaxPairEarly(MultisetOperator[T]):

    def __init__(self, left: MultisetExpression[T],
                 right: MultisetExpression[T], *, order: Order,
                 pair_equal: bool, keep: bool):
        self._children = (left, right)
        self._order = order
        self._pair_equal = pair_equal
        self._keep = keep

    def _initial_state(
            self, order, outcomes, child_sizes: Sequence,
            source_sizes: Iterator,
            arg_sizes: Sequence) -> tuple[tuple[int, int], int | None]:
        left_size, right_size = child_sizes
        if order == self._order:
            if right_size is None:
                raise UnsupportedOrder(
                    'The size of the right operand must be inferrable.')
            # state:
            # right_unpaired: Number of remaining right elements that haven't
            #   been paired yet.
            # right_remaining: Number of remaining right elements overall.
            return (right_size, right_size), None
        else:
            if self._order > 0:
                raise UnsupportedOrder(
                    "max_pair methods with priority='low' must be evaluated in ascending order."
                )
            else:
                raise UnsupportedOrder(
                    "max_pair methods with priority='high' must be evaluated in descending order."
                )

    def _next_state(self, state, order, outcome, child_counts, source_counts,
                    arg_counts):
        left_count, right_count = child_counts
        left_count = max(left_count, 0)
        right_count = max(right_count, 0)
        right_unpaired, right_remaining = state
        if self._pair_equal:
            count = min(right_unpaired, left_count)
            right_unpaired -= count
            right_remaining -= right_count
            right_unpaired = min(right_unpaired, right_remaining)
        else:
            right_remaining -= right_count
            right_unpaired = min(right_unpaired, right_remaining)
            count = min(right_unpaired, left_count)
            right_unpaired -= count
        if not self._keep:
            count = left_count - count
        return (right_unpaired, right_remaining), count

    @property
    def _expression_key(self):
        return MultisetMaxPairEarly, self._order, self._pair_equal, self._keep
