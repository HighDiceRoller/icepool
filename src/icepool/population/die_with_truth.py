__docformat__ = 'google'

import icepool
from icepool.collection.counts import Counts
from icepool.population.die import Die
from icepool.typing import T, Outcome

from functools import cached_property
import warnings

from typing import Callable, Hashable


class DieWithTruth(Die[T]):
    """A `Die` with a truth value.

    Additionally, the data is evaluated lazily since the caller may only be
    interested in the truth value.
    """
    _used_callback: bool
    """Whether either of the callbacks has been used."""
    _data_callback: Callable[[], Counts[T]]
    _truth_value_callback: Callable[[], bool]

    def __new__(cls, data_callback: Callable[[], Counts[T]],
                truth_value_callback: Callable[[], bool]) -> 'DieWithTruth[T]':
        """This class does not need to be constructed publically.

        Args:
            data_callback: Called with no arguments to populate _data if
                requested.
            truth_value: The truth value of this die.
        """
        # Skip Die.__new__.
        self = super(Die, cls).__new__(cls)
        self._used_callback = False
        self._data_callback = data_callback
        self._truth_value_callback = truth_value_callback
        return self

    # Overrides standard member type.
    @cached_property
    def _data(self) -> Counts[T]:  # type: ignore
        if self._used_callback:
            warnings.warn(
                'Both the Die result and the truth value of a comparator were used. This is likely to be unintentional.',
                category=RuntimeWarning,
                stacklevel=3)
        self._used_callback = True
        return self._data_callback()

    @cached_property
    def _truth_value(self) -> bool:
        if self._used_callback:
            warnings.warn(
                'Both the Die result and the truth value of a comparator were used. This is likely to be unintentional.',
                category=RuntimeWarning,
                stacklevel=4)
        self._used_callback = True
        return self._truth_value_callback()

    def __bool__(self) -> bool:
        return self._truth_value
