__docformat__ = 'google'

import icepool
from icepool.counts import CountsKeysView, CountsValuesView, CountsItemsView

from abc import ABC, abstractmethod
import bisect
from functools import cached_property
import itertools
import math
import operator
import random

from typing import Any, Mapping, Sequence


class Population(ABC, Mapping[Any, int]):
    """A mapping from outcomes to `int` quantities.

    Outcomes with each instance must be hashable and totally orderable.

    Subclasses include `Die` and `Deck`.
    """

    # Abstract methods.

    @abstractmethod
    def keys(self) -> CountsKeysView:
        """The outcomes within the population in sorted order."""

    @abstractmethod
    def values(self) -> CountsValuesView:
        """The quantities within the population in outcome order."""

    @abstractmethod
    def items(self) -> CountsItemsView:
        """The (outcome, quantity)s of the population in sorted order."""

    @property
    @abstractmethod
    def marginals(self):
        """A property that applies the `[]` operator to outcomes.

        This is not performed elementwise on tuples, so that this can be used
        to slice tuple outcomes. For example, `population.marginals[:2]` will
        marginalize the first two elements of tuples.
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
        """The common length of tuple outcomes.

        This is `None` if outcomes are not tuples,
        or if there are tuples of different lengths.
        """
        return self._outcome_len

    def is_empty(self) -> bool:
        """`True` iff this mapping has no outcomes. """
        return len(self) == 0

    def min_outcome(self):
        """The least outcome."""
        return self.outcomes()[0]

    def max_outcome(self):
        """The greatest outcome."""
        return self.outcomes()[-1]

    def nearest_le(self, outcome):
        """The nearest outcome that is <= the argument.

        Returns `None` if there is no such outcome.
        """
        index = bisect.bisect_right(self.outcomes(), outcome) - 1
        if index < 0:
            return None
        return self.outcomes()[index]

    def nearest_ge(self, outcome):
        """The nearest outcome that is >= the argument.

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
        """The sum of all quantities (e.g. weights or duplicates).

        For the number of unique outcomes, including those with zero quantity,
        use `len()`.
        """
        return self._denominator

    # Quantities.

    def has_zero_quantities(self) -> bool:
        """`True` iff `self` contains at least one outcome with zero quantity. """
        return 0 in self.values()

    @cached_property
    def _quantities_le(self) -> Sequence[int]:
        return tuple(itertools.accumulate(self.values()))

    def quantities_le(self) -> Sequence[int]:
        """The quantity <= each outcome in order. """
        return self._quantities_le

    @cached_property
    def _quantities_ge(self) -> Sequence[int]:
        return tuple(
            itertools.accumulate(self.values()[:-1],
                                 operator.sub,
                                 initial=self.denominator()))

    def quantities_ge(self) -> Sequence[int]:
        """The quantity >= each outcome in order. """
        return self._quantities_ge

    def quantity(self, outcome) -> int:
        """The quantity of a single outcome, or 0 if not present. """
        return self.get(outcome, 0)

    def quantity_ne(self, outcome) -> int:
        """The quantity != a single outcome. """
        return self.denominator() - self.quantity(outcome)

    def quantity_le(self, outcome) -> int:
        """The quantity <= a single outcome. """
        index = bisect.bisect_right(self.outcomes(), outcome) - 1
        if index < 0:
            return 0
        return self.quantities_le()[index]

    def quantity_lt(self, outcome) -> int:
        """The quantity < a single outcome. """
        index = bisect.bisect_left(self.outcomes(), outcome) - 1
        if index < 0:
            return 0
        return self.quantities_le()[index]

    def quantity_ge(self, outcome) -> int:
        """The quantity >= a single outcome. """
        index = bisect.bisect_left(self.outcomes(), outcome)
        if index >= len(self):
            return 0
        return self.quantities_ge()[index]

    def quantity_gt(self, outcome) -> int:
        """The quantity > a single outcome. """
        index = bisect.bisect_right(self.outcomes(), outcome)
        if index >= len(self):
            return 0
        return self.quantities_ge()[index]

    # Probabilities.

    @cached_property
    def _probabilities(self):
        return tuple(v / self.denominator() for v in self.values())

    def probabilities(self, percent: bool = False):
        """The probability of each outcome in order.

        Also known as the probability mass function (PMF).

        Args:
            percent: If set, the results will be in percent (i.e. total of 100.0).
                Otherwise, the total will be 1.0.
        """
        if percent:
            return tuple(100.0 * x for x in self._probabilities)
        else:
            return self._probabilities

    @cached_property
    def _probabilities_le(self):
        return tuple(
            quantity / self.denominator() for quantity in self.quantities_le())

    def probabilities_le(self, percent: bool = False):
        """The probability of rolling <= each outcome in order.

        Also known as the cumulative distribution function (CDF),
        though this term is ambigiuous whether it is < or <=.

        Args:
            percent: If set, the results will be in percent (i.e. total of 100.0).
                Otherwise, the total will be 1.0.
        """
        if percent:
            return tuple(100.0 * x for x in self._probabilities_le)
        else:
            return self._probabilities_le

    @cached_property
    def _probabilities_ge(self):
        return tuple(
            quantity / self.denominator() for quantity in self.quantities_ge())

    def probabilities_ge(self, percent: bool = False):
        """The probability of rolling >= each outcome in order.

        Also known as the survival function (SF) or
        complementary cumulative distribution function (CCDF),
        though these term are ambigiuous whether they are is > or >=.

        Args:
            percent: If set, the results will be in percent (i.e. total of 100.0).
                Otherwise, the total will be 1.0.
        """
        if percent:
            return tuple(100.0 * x for x in self._probabilities_ge)
        else:
            return self._probabilities_ge

    def probability(self, outcome):
        """The probability of a single outcome, or 0.0 if not present. """
        return self.quantity(outcome) / self.denominator()

    # Scalar statistics.

    def mode(self) -> tuple:
        """A tuple containing the most common outcome(s) of the population.

        These are sorted from lowest to highest.
        """
        return tuple(outcome for outcome, quantity in self.items()
                     if quantity == self.modal_quantity())

    def modal_quantity(self) -> int:
        """The highest quantity of any single outcome. """
        return max(self.quantities())

    def kolmogorov_smirnov(self, other):
        """Kolmogorov–Smirnov statistic. The maximum absolute difference between CDFs. """
        a, b = icepool.align(self, other)
        return max(
            abs(a - b)
            for a, b in zip(a.probabilities_le(), b.probabilities_le()))

    def cramer_von_mises(self, other):
        """Cramér-von Mises statistic. The sum-of-squares difference between CDFs. """
        a, b = icepool.align(self, other)
        return sum((a - b)**2
                   for a, b in zip(a.probabilities_le(), b.probabilities_le()))

    def median(self):
        """The median, taking the mean in case of a tie.

        This will fail if the outcomes do not support division;
        in this case, use `median_left` or `median_right` instead.
        """
        return self.quantile(1, 2)

    def median_left(self):
        """The median, taking the lesser in case of a tie."""
        return self.quantile_left(1, 2)

    def median_right(self):
        """The median, taking the greater in case of a tie."""
        return self.quantile_right(1, 2)

    def quantile(self, n: int, d: int = 100):
        """The outcome `n / d` of the way through the CDF, taking the mean in case of a tie.

        This will fail if the outcomes do not support division;
        in this case, use `quantile_left` or `quantile_right` instead.
        """
        return (self.quantile_left(n, d) + self.quantile_right(n, d)) / 2

    def quantile_left(self, n: int, d: int = 100):
        """The outcome `n / d` of the way through the CDF, taking the lesser in case of a tie."""
        index = bisect.bisect_left(self.quantities_le(),
                                   (n * self.denominator() + d - 1) // d)
        if index >= len(self):
            return self.max_outcome()
        return self.outcomes()[index]

    def quantile_right(self, n: int, d: int = 100):
        """The outcome `n / d` of the way through the CDF, taking the greater in case of a tie."""
        index = bisect.bisect_right(self.quantities_le(),
                                    n * self.denominator() // d)
        if index >= len(self):
            return self.max_outcome()
        return self.outcomes()[index]

    def mean(self):
        return sum(outcome * quantity
                   for outcome, quantity in self.items()) / self.denominator()

    def variance(self):
        """This is the population variance, not the sample variance."""
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
                 for outcome, p in zip(self.outcomes(), self.probabilities()))
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

    def sample(self):
        """A single random sample from this population.

        Note that this is always "with replacement" even for `Deck` since
        instances are immutable.

        This uses the standard `random` package and is not cryptographically
        secure.
        """
        # We don't use random.choices since that is based on floats rather than ints.
        r = random.randrange(self.denominator())
        index = bisect.bisect_right(self.quantities_le(), r)
        return self.outcomes()[index]

    def format(self, format_spec: str, **kwargs) -> str:
        """Formats this mapping as a string.

        `format_spec` should start with the output format,
        which is either `md` (Markdown) or `csv` (comma-separated values),
        followed by a ':' character.

        After this, zero or more columns should follow. Options are:

        * `o`: Outcomes.
        * `*o`: Outcomes, unpacked if applicable.
        * `q==`, `q<=`, `q>=`: Quantities ==, <=, or >= each outcome.
        * `p==`, `p<=`, `p>=`: Probabilities (0-1) ==, <=, or >= each outcome.
        * `%==`, `%<=`, `%>=`: Probabilities (0%-100%) ==, <=, or >= each outcome.

        Columns may optionally be separated using ` ` (space) or `|` characters.

        The default is `'md:*o|q==|%=='`, with the quantity column being omitted
        if any quantity exceeds 10**30.
        """
        if len(format_spec) == 0:
            format_spec = 'md:*o'
            if not self.is_empty() and self.modal_quantity() < 10**30:
                format_spec += 'q=='
            format_spec += '%=='

        format_spec = format_spec.replace('|', '')

        output_format, format_spec = format_spec.split(':')
        if output_format == 'md':
            return icepool.format.markdown(self, format_spec)
        elif output_format == 'csv':
            return icepool.format.csv(self, format_spec, **kwargs)
        else:
            raise ValueError(f"Unsupported output format '{output_format}'")

    def __format__(self, format_spec: str) -> str:
        return self.format(format_spec)

    def __str__(self) -> str:
        return f'{self}'