__docformat__ = 'google'

import enum
import math

from typing import Hashable, Literal, Protocol, TypeVar

T_contra = TypeVar('T_contra', contravariant=True)


class Order(enum.IntEnum):
    """Can be used to define what order outcomes are seen in by OutcomeCountEvaluators."""
    Ascending = 1
    Descending = -1
    Any = 0


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


SetComparatorStr = Literal['<', '<=', 'issubset', '>', '>=', 'issuperset', '!=',
                           '==', 'isdisjoint']

MultisetBinaryOperationStr = Literal['+', 'disjoint_sum', '-', 'difference',
                                     '|', 'union', '&', 'intersection', '^',
                                     'symmetric_difference']

MultisetBinaryIntOperationStr = Literal['*', '//']
