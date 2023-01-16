__docformat__ = 'google'

import enum

from typing import Hashable, Literal, Mapping, Protocol, Sequence, TypeAlias, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from icepool.expression.multiset_expression import MultisetExpression

K = TypeVar('K', bound=Hashable)
"""A key type."""

T = TypeVar('T', bound='Outcome')
"""An outcome type."""

T_co = TypeVar('T_co', bound='Outcome', covariant=True)
"""An outcome type."""

T_contra = TypeVar('T_contra', bound='Outcome', contravariant=True)
"""An outcome type."""

U = TypeVar('U', bound='Outcome')
"""Another outcome type."""

U_co = TypeVar('U_co', bound='Outcome', covariant=True)
"""Another outcome type."""

Qs_co = TypeVar('Qs_co', bound=tuple[int, ...], covariant=True)
"""A tuple of count types. In this future this may be replaced with a TypeVarTuple."""

Evaluable: TypeAlias = 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
"""Type of objects that can be evaluated by a MultisetEvaluator using ExpressionEvaluator."""


class Order(enum.IntEnum):
    """Can be used to define what order outcomes are seen in by MultisetEvaluators."""
    Ascending = 1
    Descending = -1
    Any = 0

    def merge(*orders: 'Order') -> 'Order':
        """Merges the given Orders.

        Returns:
            `Any` if all arguments are `Any`.
            `Ascending` if there is at least one `Ascending` in the arguments.
            `Descending` if there is at least one `Descending` in the arguments.

        Raises:
            `ValueError` if both `Ascending` and `Descending` are in the
            arguments.
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
    """Protocol to attempt to verify that outcome types are hashable and sortable.

    Far from foolproof, e.g. it cannot enforce total ordering.
    """

    def __lt__(self, other: T_contra) -> bool:
        ...
