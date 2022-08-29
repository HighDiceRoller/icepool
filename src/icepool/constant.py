__docformat__ = 'google'

import enum
import math


class SpecialValue(enum.Enum):
    Reroll = 'Reroll'
    """Indicates an outcome should be rerolled (with unlimited depth)."""
