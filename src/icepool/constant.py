__docformat__ = 'google'

import enum
import math


class RerollType(enum.Enum):
    Reroll = 'Reroll'
    """Indicates an outcome should be rerolled (with unlimited depth)."""
