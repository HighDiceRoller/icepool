__docformat__ = 'google'

import icepool
from icepool.counts import Counts
from icepool.die.die import Die

from functools import cached_property

from typing import Callable


class DieWithTruth(Die):
    """A die with a truth value.

    Additionally, the data is evaluated lazily since the caller may only be
    interested in the truth value.
    """
    _data_callback: Callable[[], Counts]
    _truth_value_callback: Callable[[], bool]

    def __new__(cls, data_callback: Callable[[], Counts],
                truth_value_callback: Callable[[], bool]):
        """This class does not need to be constructed publically.

        Args:
            data_callback: Called with no arguments to populate _data if
                requested.
            truth_value: The truth value of this die.
        """
        # Skip Die.__new__.
        self = super(Die, cls).__new__(cls)
        self._data_callback = data_callback  # type: ignore
        self._truth_value_callback = truth_value_callback  # type: ignore
        return self

    @cached_property
    def _data(self):
        return self._data_callback()

    @cached_property
    def _truth_value(self):
        return self._truth_value_callback()

    def __bool__(self):
        return self._truth_value
