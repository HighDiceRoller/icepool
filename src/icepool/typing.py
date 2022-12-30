from typing import Collection, Hashable, Protocol, Type, TypeVar, runtime_checkable

T = TypeVar('T')

T_contra = TypeVar('T_contra', contravariant=True)


class Outcome(Hashable, Protocol[T_contra]):
    """Protocol to verify that outcomes are hashable and sortable."""

    def __lt__(self, other: T_contra) -> bool:
        ...

    def __eq__(self, other):
        ...


@runtime_checkable
class MaybeNamedTuple(Collection, Protocol):
    """Protocol for detecting named tuples."""

    _fields: tuple[str, ...]

    @classmethod
    def _make(cls: Type[T], Iterable) -> T:
        ...
