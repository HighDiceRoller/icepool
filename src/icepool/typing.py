__docformat__ = 'google'

import enum
import inspect

from typing import Any, Callable, Generic, Hashable, Iterable, Literal, Mapping, Protocol, Sequence, Sized, TypeAlias, TypeGuard, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from icepool.multiset_expression import MultisetExpression

A_co = TypeVar('A_co', covariant=True)
"""Any type."""

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


# We don't use @runtime_checkable due to poor performance and the validation is
# limited anyways.
class Expandable(Protocol[A_co]):
    """Objects that can be expanded in Cartesian products."""

    @property
    def _items_for_cartesian_product(self) -> Sequence[tuple[A_co, int]]:
        """Returns a sequence of (outcome, quantity) pairs."""
        ...


class NoExpand(Expandable[A_co]):
    """Wraps an argument, instructing `map` and similar functions not to expand it.

    This is not intended for use outside of `map` (or similar) call sites.
    
    Example:
    ```python
    map(lambda x: (x, x), d6)
    # Here the d6 is expanded so that the function is evaluated six times
    # with x = 1, 2, 3, 4, 5, 6.
    # = Die([(1, 1), (2, 2), (3, 3), ...])

    map(lambda x: (x, x), NoExpand(d6))
    # Here the d6 is passed as a Die to the function, which then rolls it twice
    # independently.
    # = Die([(1, 1), (1, 2), (1, 3), ...])
    # = tupleize(d6, d6)
    ```
    """

    arg: A_co
    """The wrapped argument."""

    def __init__(self, arg: A_co, /):
        self.arg = arg

    @property
    def _items_for_cartesian_product(self) -> Sequence[tuple[A_co, int]]:
        return [(self.arg, 1)]


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


class InferStarError(ValueError):
    """Indicates that `star` could not be inferred."""


def infer_star(function, arg_count=1) -> bool:
    """Infers whether the first argument should be unpacked before giving it to the function.

    Args:
        arg_count: The number of arguments that will be provided to the function.
    """
    try:
        required_count, _ = count_positional_parameters(function)
    except ValueError:
        raise InferStarError(
            f'Could not determine the number of arguments taken by the function. You will need to specify star explicitly.'
        )
    return required_count > arg_count
