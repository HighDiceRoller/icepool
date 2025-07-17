__docformat__ = 'google'

from icepool.order import Order
from typing import Literal


def compute_lexi_tuple(comparison: Literal['==', '!=', '<=', '<', '>=', '>',
                                           'cmp'],
                       order: Order) -> tuple[int, int, int]:
    """A 3-tuple representing a lexicographic comparison between two multisets.

    This version does not specify what to do when one side has more elements
    than the other.

    Args:
        comparison: The comparison to use.
        order: The order in which outcomes are seen.

    Returns:
        A 3-tuple with the following elements:
        * 0: tie: The result if no elements were matched.
        * 1: left_first: The result if the left side had the first different
            element and it was matched with a later right side element.
        * -1: right_first: As right_first but vice versa.
    """
    match comparison:
        case '==':
            tie, left_first, right_first = 1, 0, 0
        case '!=':
            tie, left_first, right_first = 0, 1, 1
        case '<=':
            tie, left_first, right_first = 1, 1, 0
        case '<':
            tie, left_first, right_first = 0, 1, 0
        case '>=':
            tie, left_first, right_first = 1, 0, 1
        case '>':
            tie, left_first, right_first = 0, 0, 1
        case 'cmp':
            tie, left_first, right_first = 0, -1, 1
        case _:
            raise ValueError(f'Invalid comparison {comparison}')

    if order < 0:
        left_first, right_first = right_first, left_first

    return tie, left_first, right_first


def compute_lexi_tuple_with_extra(
    comparison: Literal['==', '!=', '<=', '<', '>=', '>', 'cmp'], order: Order,
    extra: Literal['early', 'late', 'low', 'high', 'drop']
) -> tuple[int, int, int, int, int]:
    """A 5-tuple representing a lexicographic comparison between two multisets.

    This version specifies what to do when one side has more elements than the
    other.

    Args:
        comparison: The comparison to use.
        order: The order in which outcomes are seen.
        extra: If one side has more elements than the other, how the extra
            elements are considered.
    
    Returns:
        A 5-tuple with the following elements:
        * 0: tie: The result if no elements were matched.
        * 1: left_extra: The result if the left side had the first different
            element and it was never matched with a right side element.
        * 2: left_first: The result if the left side had the first different
            element and it was matched with a later right side element.
        * -2: right_first: As right_first but vice versa.
        * -1: right_extra: As left_extra but vice versa.
    """
    tie, left_first, right_first = compute_lexi_tuple(comparison, order)

    if extra == 'low':
        extra = 'early' if order > 0 else 'late'
    elif extra == 'high':
        extra = 'early' if order < 0 else 'late'

    match extra:
        case 'early':
            left_extra, right_extra = left_first, right_first
        case 'late':
            left_extra, right_extra = right_first, left_first
        case 'drop':
            left_extra, right_extra = 0, 0
        case _:
            raise ValueError(f'Invalid extra {extra}')

    return tie, left_extra, left_first, right_first, right_extra
