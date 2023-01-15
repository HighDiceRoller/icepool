__docformat__ = 'google'

import enum

from typing import Hashable, Literal, Mapping, Protocol, Sequence, TypeAlias, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from icepool.evaluable_interface import EvaluableInterface

T = TypeVar('T')

T_contra = TypeVar('T_contra', contravariant=True)

T_co = TypeVar('T_co', bound='Outcome', covariant=True)
"""Type variable representing an outcome type."""

Evaluable: TypeAlias = 'EvaluableInterface[T] | Mapping[T, int] | Sequence[T]'
"""Type of objects that can be evaluated by a MultisetEvaluator using ExpressionEvaluato."""


class Order(enum.IntEnum):
    """Can be used to define what order outcomes are seen in by MultisetEvaluators."""
    Ascending = 1
    Descending = -1
    Any = 0

    def merge(*orders: 'Order') -> 'Order':
        """Merges the given Orders.

        Raises:
            ValueError if both Ascending and Descending appear.
        """
        result = Order.Any
        for order in orders:
            if (result > 0 and order < 0) or (result < 0 and order > 0):
                raise ValueError(f'Conflicting orders {orders}.')
            if result == Order.Any:
                result = order
        return result


class RerollType(enum.Enum):
    """The type of the Reroll singleton."""
    Reroll = 'Reroll'
    """Indicates an outcome should be rerolled (with unlimited depth)."""


class Outcome(Hashable, Protocol[T_contra]):
    """Protocol to attempt to verify that outcomes are hashable and sortable.

    Far from foolproof, e.g. it cannot enforce total ordering.
    """

    def __lt__(self, other: T_contra) -> bool:
        ...

    def __eq__(self, other):
        ...
