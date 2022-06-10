__docformat__ = 'google'

import icepool
from icepool.collections import Counts
from icepool.die.die import Die

from functools import cached_property

from typing import Callable


class DieWithTruth(Die):
    """A die with a truth value.

    Additionally, the data is evaluated lazily since the caller may only be
    interested in the truth value.
    """
    _data_callback: Callable[[], Counts]
    _truth_value: bool

    def __new__(cls, data_callback: Callable[[], Counts], truth_value: bool):
        """This class does not need to be constructed publically.

        Args:
            data_callback: Called with no arguments to populate _data if
                requested.
            truth_value: The truth value of this die.
        """
        self = super(DieWithTruth, cls).__new__(cls)
        self._data_callback = data_callback  # type: ignore
        self._truth_value = truth_value  # type: ignore
        return self

    @cached_property
    def _data(self):
        return self._data_callback()

    def __bool__(self):
        return self._truth_value
