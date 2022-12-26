from typing import Hashable, Protocol, TypeVar

T_contra = TypeVar('T_contra', contravariant=True)


class Outcome(Hashable, Protocol[T_contra]):
    """Protocol to verify that outcomes are hashable and sortable."""

    def __lt__(self, other: T_contra) -> bool:
        ...

    def __eq__(self, other):
        ...
