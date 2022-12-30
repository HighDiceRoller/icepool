__docformat__ = 'google'

import enum
import math


class Order(enum.IntEnum):
    """Can be used to define what order outcomes are seen in by OutcomeCountEvaluators."""
    Ascending = 1
    Descending = -1
    Any = 0


class RerollType(enum.Enum):
    """The type of the Reroll singleton."""
    Reroll = 'Reroll'
    """Indicates an outcome should be rerolled (with unlimited depth)."""
