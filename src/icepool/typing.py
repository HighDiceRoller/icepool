__docformat__ = 'google'

import enum
import inspect

from typing import Any, Callable, Hashable, Literal, Mapping, Protocol, Sequence, TypeAlias, TypeGuard, TypeVar, TYPE_CHECKING

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


def count_positional_parameters(func: Callable) -> tuple[int, int | None]:
    """Counts the number of positional parameters of the callable.

    Returns:
        Two `int`s. The first is the number of required positional arguments;
        the second is total number of positional arguments, or `None` if there
        is a variadic `*args`.
    """
    required = 0
    total = 0
    parameters = inspect.signature(func, follow_wrapped=False).parameters
    for parameter in parameters.values():
        match parameter.kind:
            case inspect.Parameter.POSITIONAL_ONLY | inspect.Parameter.POSITIONAL_OR_KEYWORD:
                total += 1
                if parameter.default == inspect.Parameter.empty:
                    required += 1
            case inspect.Parameter.VAR_POSITIONAL:
                return required, None
            case _:
                break
    return required, total
