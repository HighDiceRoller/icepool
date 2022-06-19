__docformat__ = 'google'

import icepool
from icepool.counts import CountsKeysView, CountsValuesView, CountsItemsView

from abc import ABC, abstractmethod
import bisect
from collections import defaultdict
from functools import cached_property
import itertools
import math
import operator

from typing import Any, Callable
from collections.abc import Mapping, MutableMapping, Sequence


class OutcomeQuantityMapping(ABC, Mapping[Any, int]):
    """Abstract base class for a mapping from outcomes to `int`s.

    Subclasses include `Die` and `Deck`.
    """

    # Abstract methods.

    @abstractmethod
    def keys(self) -> CountsKeysView:
        """The keys can be used as both a KeysView and as a Sequence."""

    @abstractmethod
    def values(self) -> CountsValuesView:
        """The values can be used as both a ValuesView and as a Sequence."""

    @abstractmethod
    def items(self) -> CountsItemsView:
        """The items can be used as both a ItemsView and as a Sequence."""

    @abstractmethod
    def value_name(self) -> str:
        """Returns the name for a value, e.g. "weight" or "dups"."""

    @property
    @abstractmethod
    def marginals(self):
        """A property that applies the `[]` operator to outcomes.

        This is not performed elementwise on tuples, so that this can be used
        to slice tuples. For example, `mapping.marginals[:2]` will marginalize
        the first two elements of tuples.
        """

    # Outcomes.

    def outcomes(self) -> CountsKeysView:
        """The sorted outcomes of the mapping.

        These are also the `keys` of the mapping.
        Prefer to use the name `outcomes`.
        """
        return self.keys()

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

    def is_empty(self) -> bool:
        """Returns `True` if this mapping has no outcomes. """
        return len(self) == 0

    def min_outcome(self):
        """Returns the minimum possible outcome of this die."""
        return self.outcomes()[0]

    def max_outcome(self):
        """Returns the maximum possible outcome of this die."""
        return self.outcomes()[-1]

    def nearest_le(self, outcome):
        """Returns the nearest outcome that is <= the argument.

        Returns `None` if there is no such outcome.
        """
        index = bisect.bisect_right(self.outcomes(), outcome) - 1
        if index < 0:
            return None
        return self.outcomes()[index]

    def nearest_ge(self, outcome):
        """Returns the nearest outcome that is >= the argument.

        Returns `None` if there is no such outcome.
        """
        index = bisect.bisect_left(self.outcomes(), outcome)
        if index >= len(self):
            return None
        return self.outcomes()[index]

    # Quantities.

    def quantities(self) -> CountsValuesView:
        """The quantities of the mapping in sorted order.

        These are also the `values` of the mapping.
        Prefer to use the name `quantities`.
        """
        return self.values()

    @cached_property
    def _denominator(self) -> int:
        return sum(self.values())

    def denominator(self) -> int:
        """The sum of all quantities (e.g weights or dups).

        For the number of unique outcomes, including those with zero numerator,
        use `len()`.
        """
        return self._denominator

    # Probabilities.

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

    # Quantities.

    def has_zero_quantities(self) -> bool:
        """`True` iff `self` contains at least one outcome with zero quantity. """
        return 0 in self.values()

    @cached_property
    def _cquantities(self) -> Sequence[int]:
        return tuple(itertools.accumulate(self.values()))

    def cquantities(self) -> Sequence[int]:
        """Cumulative quantities. The quantity <= each outcome in order. """
        return self._cquantities

    @cached_property
    def _squantities(self) -> Sequence[int]:
        return tuple(
            itertools.accumulate(self.values()[:-1],
                                 operator.sub,
                                 initial=self.denominator()))

    def squantities(self) -> Sequence[int]:
        """Survival quantities. The quantity >= each outcome in order. """
        return self._squantities

    @cached_property
    def _cdf(self):
        return tuple(
            quantity / self.denominator() for quantity in self.cquantities())

    def cdf(self, percent: bool = False):
        """Cumulative distribution function. The chance of rolling <= each outcome in order.

        Args:
            percent: If set, the results will be in percent (i.e. total of 100.0).
                Otherwise, the total will be 1.0.
        """
        if percent:
            return tuple(100.0 * x for x in self._cdf)
        else:
            return self._cdf

    @cached_property
    def _sf(self):
        return tuple(
            quantity / self.denominator() for quantity in self.squantities())

    def sf(self, percent: bool = False):
        """Survival function. The chance of rolling >= each outcome in order.

        Args:
            percent: If set, the results will be in percent (i.e. total of 100.0).
                Otherwise, the total will be 1.0.
        """
        if percent:
            return tuple(100.0 * x for x in self._sf)
        else:
            return self._sf

    def quantity(self, outcome) -> int:
        """Returns the quantity of a single outcome, or 0 if not present. """
        return self.get(outcome, 0)

    def quantity_ne(self, outcome) -> int:
        """Returns the quantity != a single outcome. """
        return self.denominator() - self.quantity(outcome)

    def quantity_le(self, outcome) -> int:
        """Returns the quantity <= a single outcome. """
        index = bisect.bisect_right(self.outcomes(), outcome) - 1
        if index < 0:
            return 0
        return self.cquantities()[index]

    def quantity_lt(self, outcome) -> int:
        """Returns the quantity < a single outcome. """
        index = bisect.bisect_left(self.outcomes(), outcome) - 1
        if index < 0:
            return 0
        return self.cquantities()[index]

    def quantity_ge(self, outcome) -> int:
        """Returns the quantity >= a single outcome. """
        index = bisect.bisect_left(self.outcomes(), outcome)
        if index >= len(self):
            return 0
        return self.squantities()[index]

    def quantity_gt(self, outcome) -> int:
        """Returns the quantity > a single outcome. """
        index = bisect.bisect_right(self.outcomes(), outcome)
        if index >= len(self):
            return 0
        return self.squantities()[index]

    def probability(self, outcome):
        """Returns the probability of a single outcome. """
        return self.quantity(outcome) / self.denominator()

    # Scalar statistics.

    def mode(self) -> tuple:
        """Returns a tuple containing the most common outcome(s) of the die.

        These are sorted from lowest to highest.
        """
        return tuple(outcome for outcome, quantity in self.items()
                     if quantity == self.modal_quantity())

    def modal_quantity(self) -> int:
        """The highest quantity of any single outcome. """
        return max(self.quantities())

    def ks_stat(self, other):
        """Kolmogorov–Smirnov stat. The maximum absolute difference between CDFs. """
        a, b = icepool.align(self, other)
        return max(abs(a - b) for a, b in zip(a.cdf(), b.cdf()))

    def cvm_stat(self, other):
        """Cramér-von Mises stat. The sum-of-squares difference between CDFs. """
        a, b = icepool.align(self, other)
        return sum((a - b)**2 for a, b in zip(a.cdf(), b.cdf()))

    def median_left(self):
        """Returns the median.

        If the median lies between two outcomes, returns the lower of the two. """
        return self.ppf_left(1, 2)

    def median_right(self):
        """Returns the median.

        If the median lies between two outcomes, returns the higher of the two. """
        return self.ppf_right(1, 2)

    def median(self):
        """Returns the median.

        If the median lies between two outcomes, returns the mean of the two.
        This will fail if the outcomes do not support division;
        in this case, use `median_left` or `median_right` instead.
        """
        return self.ppf(1, 2)

    def ppf_left(self, n: int, d: int = 100):
        """Returns a quantile, `n / d` of the way through the cdf.

        If the result lies between two outcomes, returns the lower of the two.
        """
        index = bisect.bisect_left(self.cquantities(),
                                   (n * self.denominator() + d - 1) // d)
        if index >= len(self):
            return self.max_outcome()
        return self.outcomes()[index]

    def ppf_right(self, n: int, d: int = 100):
        """Returns a quantile, `n / d` of the way through the cdf.

        If the result lies between two outcomes, returns the higher of the two.
        """
        index = bisect.bisect_right(self.cquantities(),
                                    n * self.denominator() // d)
        if index >= len(self):
            return self.max_outcome()
        return self.outcomes()[index]

    def ppf(self, n: int, d: int = 100):
        """Returns a quantile, `n / d` of the way through the cdf.

        If the result lies between two outcomes, returns the mean of the two.
        This will fail if the outcomes do not support division;
        in this case, use `ppf_left` or `ppf_right` instead.
        """
        return (self.ppf_left(n, d) + self.ppf_right(n, d)) / 2

    def mean(self):
        return sum(outcome * quantity
                   for outcome, quantity in self.items()) / self.denominator()

    def variance(self):
        mean = self.mean()
        mean_of_squares = sum(
            quantity * outcome**2
            for outcome, quantity in self.items()) / self.denominator()
        return mean_of_squares - mean * mean

    def standard_deviation(self):
        return math.sqrt(self.variance())

    sd = standard_deviation

    def standardized_moment(self, k: int):
        sd = self.standard_deviation()
        mean = self.mean()
        ev = sum(p * (outcome - mean)**k
                 for outcome, p in zip(self.outcomes(), self.pmf()))
        return ev / (sd**k)

    def skewness(self):
        return self.standardized_moment(3.0)

    def excess_kurtosis(self):
        return self.standardized_moment(4.0) - 3.0

    # Joint statistics.

    def covariance(self, i: int, j: int):
        mean_i = self.marginals[i].mean()
        mean_j = self.marginals[j].mean()
        return sum((outcome[i] - mean_i) * (outcome[j] - mean_j) * quantity
                   for outcome, quantity in self.items()) / self.denominator()

    def correlation(self, i: int, j: int):
        sd_i = self.marginals[i].standard_deviation()
        sd_j = self.marginals[j].standard_deviation()
        return self.covariance(i, j) / (sd_i * sd_j)