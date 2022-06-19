__docformat__ = 'google'

from icepool.counts import CountsKeysView, CountsValuesView, CountsItemsView

from abc import ABC, abstractmethod
from functools import cached_property

from typing import Any
from collections.abc import Mapping


class OutcomeCountMapping(ABC, Mapping[Any, int]):

    @abstractmethod
    def outcomes(self) -> CountsKeysView:
        """The sorted outcomes of the mapping.

        These are also the `keys` of the mapping.
        Prefer to use the name `outcomes`.
        """

    def is_empty(self) -> bool:
        """Returns `True` if this mapping has no outcomes. """
        return len(self) == 0

    @cached_property
    def _outcome_len(self) -> int | None:
        result = None
        for outcome in self.outcomes():
            try:
                if result is None:
                    result = len(outcome)
                elif len(outcome) != result:
                    return None
            except TypeError:
                return None
        return result

    def outcome_len(self) -> int | None:
        return self._outcome_len

    # Values.

    @abstractmethod
    def value_name(self) -> str:
        """Returns the name for a value, e.g. "weight" or "dups"."""

    @cached_property
    def _denominator(self) -> int:
        return sum(self.values())

    def denominator(self) -> int:
        """The sum of all values (e.g weights or dups).

        For the number of unique outcomes, including those with zero numerator,
        use `len()`.
        """
        return self._denominator

    @cached_property
    def _pmf(self):
        return tuple(v / self.denominator() for v in self.values())

    def pmf(self, percent: bool = False):
        """Probability mass function. The probability of each outcome in order.

        Args:
            percent: If set, the results will be in percent (i.e. total of 100.0).
                Otherwise, the total will be 1.0.
        """
        if percent:
            return tuple(100.0 * x for x in self._pmf)
        else:
            return self._pmf
