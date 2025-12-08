__docformat__ = 'google'

from abc import ABC, abstractmethod
import enum
import inspect

from typing import Callable, Hashable, Protocol, Sequence, TypeVar

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


class RerollType(enum.Enum):
    """The type of the Reroll and Restart singletons."""
    Reroll = 'Reroll'
    Restart = 'Restart'


class NoCacheType(enum.Enum):
    """The type of the NoCache singleton."""
    NoCache = 'NoCache'
    """Indicates that caching should not be performed. Exact meaning depends on context."""


class Outcome(Hashable, Protocol[T_contra]):
    """Protocol to attempt to verify that outcome types are hashable and sortable.

    Far from foolproof, e.g. it cannot enforce total ordering.
    """

    def __lt__(self, other: T_contra) -> bool:
        ...


class MaybeHashKeyed(ABC):

    @property
    @abstractmethod
    def hash_key(self) -> Hashable:
        """A hash key for this object. This should include a type.
        
        If None, this will not compare equal to any other object.
        """

    def equals(self, other) -> bool:
        if self is other:
            return True
        if self.hash_key is None:
            return False
        if hasattr(other, 'hash_key') and other.hash_key is not None:
            return self.hash_key == other.hash_key
        return False

    def __eq__(self, other) -> bool:
        # This may be overwritten in cases where == has a double meaning.
        return self.equals(other)

    def __hash__(self) -> int:
        return hash(self.hash_key)


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


class InferStarError(ValueError):
    """Indicates that `star` could not be inferred."""


def infer_star(function: Callable, arg_count: int = 1) -> bool:
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
