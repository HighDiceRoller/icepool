__docformat__ = 'google'

import enum
import inspect

from typing import Any, Callable, Hashable, Iterable, Literal, Mapping, Protocol, Sequence, Sized, TypeAlias, TypeGuard, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from icepool.expression.multiset_expression import MultisetExpression

S = TypeVar('S', bound='Sequence')
"""A sequence type."""

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

Qs = TypeVar('Qs', bound=tuple[int, ...])
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
                raise ValueError(
                    f'Conflicting orders {orders}.\n' +
                    'Tip: If you are using highest(keep=k), try using lowest(drop=n-k) instead, or vice versa.'
                )
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


class ImplicitConversionError(TypeError):
    """Indicates that an implicit conversion failed."""


def count_positional_parameters(function: Callable) -> tuple[int, int | None]:
    """Counts the number of positional parameters of the callable.

    Returns:
        Two `int`s. The first is the number of required positional arguments;
        the second is total number of positional arguments, or `None` if there
        is a variadic `*args`.
    """
    required = 0
    total = 0
    parameters = inspect.signature(function, follow_wrapped=False).parameters
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


def guess_star(function, arg_count=1) -> bool:
    """Guesses whether the first argument should be unpacked before giving it to the function.

    Args:
        arg_count: The number of arguments that will be provided to the function.
    """
    try:
        required_count, _ = count_positional_parameters(function)
    except ValueError:
        raise ValueError(
            f'Could not guess whether to unpack the first argument to the function.\n'
            'You may need to specify `star` explicitly.')
    return required_count > arg_count
