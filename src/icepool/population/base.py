__docformat__ = 'google'

from collections import defaultdict
import icepool
from icepool.collection.counts import CountsKeysView, CountsValuesView, CountsItemsView
from icepool.typing import U, Outcome, T_co, count_positional_parameters

from abc import ABC, abstractmethod
import bisect
from functools import cached_property
import itertools
import math
import numbers
import operator
import random

from typing import Any, Callable, Generic, Hashable, Mapping, MutableMapping, Sequence, Sized, TypeVar, overload

C = TypeVar('C', bound='Population')
"""Type variable representing a subclass of `Population`."""


# This typing is a compromise due to Mapping not support covariant key type.
class Population(ABC, Generic[T_co], Mapping[Any, int]):
    """A mapping from outcomes to `int` quantities.

    Outcomes with each instance must be hashable and totally orderable.

    Subclasses include `Die` and `Deck`.
    """

    # Abstract methods.

    @property
    @abstractmethod
    def _new_type(self) -> type:
        """The type to use when constructing a new instance."""

    @abstractmethod
    def keys(self) -> CountsKeysView[T_co]:
        """The outcomes within the population in sorted order."""

    @abstractmethod
    def values(self) -> CountsValuesView:
        """The quantities within the population in outcome order."""

    @abstractmethod
    def items(self) -> CountsItemsView[T_co]:
        """The (outcome, quantity)s of the population in sorted order."""

    def _unary_operator(self, op: Callable[..., U], *args, **kwargs):
        data: MutableMapping[Any, int] = defaultdict(int)
        for outcome, quantity in self.items():
            new_outcome = op(outcome, *args, **kwargs)
            data[new_outcome] += quantity
        return self._new_type(data)

    # Outcomes.

    def outcomes(self) -> CountsKeysView[T_co]:
        """The outcomes of the mapping in ascending order.

        These are also the `keys` of the mapping.
        Prefer to use the name `outcomes`.
        """
        return self.keys()

    @cached_property
    def _common_outcome_length(self) -> int | None:
        result = None
        for outcome in self.outcomes():
            if isinstance(outcome, Sized):
                if result is None:
                    result = len(outcome)
                elif len(outcome) != result:
                    return None
        return result

    def common_outcome_length(self) -> int | None:
        """The common length of all outcomes.

        If outcomes have no lengths or different lengths, the result is `None`.
        """
        return self._common_outcome_length

    def is_empty(self) -> bool:
        """`True` iff this population has no outcomes. """
        return len(self) == 0

    def min_outcome(self) -> T_co:
        """The least outcome."""
        return self.outcomes()[0]

    def max_outcome(self) -> T_co:
        """The greatest outcome."""
        return self.outcomes()[-1]

    def nearest_le(self, outcome) -> T_co | None:
        """The nearest outcome that is <= the argument.

        Returns `None` if there is no such outcome.
        """
        if outcome in self:
            return outcome
        index = bisect.bisect_right(self.outcomes(), outcome) - 1
        if index < 0:
            return None
        return self.outcomes()[index]

    def nearest_lt(self, outcome) -> T_co | None:
        """The nearest outcome that is < the argument.

        Returns `None` if there is no such outcome.
        """
        index = bisect.bisect_left(self.outcomes(), outcome) - 1
        if index < 0:
            return None
        return self.outcomes()[index]

    def nearest_ge(self, outcome) -> T_co | None:
        """The nearest outcome that is >= the argument.

        Returns `None` if there is no such outcome.
        """
        if outcome in self:
            return outcome
        index = bisect.bisect_left(self.outcomes(), outcome)
        if index >= len(self):
            return None
        return self.outcomes()[index]

    def nearest_gt(self, outcome) -> T_co | None:
        """The nearest outcome that is > the argument.

        Returns `None` if there is no such outcome.
        """
        index = bisect.bisect_right(self.outcomes(), outcome)
        if index >= len(self):
            return None
        return self.outcomes()[index]

    # Quantities.

    def quantity(self, outcome: Hashable) -> int:
        """The quantity of a single outcome, or 0 if not present."""
        return self.get(outcome, 0)

    @overload
    def quantities(self) -> CountsValuesView:
        ...

    @overload
    def quantities(self, outcomes: Sequence) -> Sequence[int]:
        ...

    def quantities(
            self,
            outcomes: Sequence | None = None
    ) -> CountsValuesView | Sequence[int]:
        """The quantities of the mapping in sorted order.

        These are also the `values` of the mapping.
        Prefer to use the name `quantities`.

        Args:
            outcomes: If provided, the quantities corresponding to these
                outcomes will be returned (or 0 if not present).
        """
        if outcomes is None:
            return self.values()
        else:
            return tuple(self.quantity(outcome) for outcome in outcomes)

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

    def scale_quantities(self: C, scale: int) -> C:
        """Scales all quantities by an integer."""
        if scale == 1:
            return self
        data = {outcome: quantity * scale for outcome, quantity in self.items()}
        return self._new_type(data)

    def has_zero_quantities(self) -> bool:
        """`True` iff `self` contains at least one outcome with zero quantity. """
        return 0 in self.values()

    def quantity_ne(self, outcome) -> int:
        """The quantity != a single outcome. """
        return self.denominator() - self.quantity(outcome)

    @cached_property
    def _cumulative_quantities(self) -> Mapping[T_co, int]:
        result = {}
        cdf = 0
        for outcome, quantity in self.items():
            cdf += quantity
            result[outcome] = cdf
        return result

    def quantity_le(self, outcome) -> int:
        """The quantity <= a single outcome."""
        outcome = self.nearest_le(outcome)
        if outcome is None:
            return 0
        else:
            return self._cumulative_quantities[outcome]

    def quantity_lt(self, outcome) -> int:
        """The quantity < a single outcome."""
        outcome = self.nearest_lt(outcome)
        if outcome is None:
            return 0
        else:
            return self._cumulative_quantities[outcome]

    def quantity_ge(self, outcome) -> int:
        """The quantity >= a single outcome."""
        return self.denominator() - self.quantity_lt(outcome)

    def quantity_gt(self, outcome) -> int:
        """The quantity > a single outcome."""
        return self.denominator() - self.quantity_le(outcome)

    @cached_property
    def _quantities_le(self) -> Sequence[int]:
        return tuple(itertools.accumulate(self.values()))

    def quantities_le(self, outcomes: Sequence | None = None) -> Sequence[int]:
        """The quantity <= each outcome in order.

        Args:
            outcomes: If provided, the quantities corresponding to these
                outcomes will be returned (or 0 if not present).
        """
        if outcomes is None:
            return self._quantities_le
        else:
            return tuple(self.quantity_le(x) for x in outcomes)

    @cached_property
    def _quantities_ge(self) -> Sequence[int]:
        return tuple(
            itertools.accumulate(self.values()[:-1],
                                 operator.sub,
                                 initial=self.denominator()))

    def quantities_ge(self, outcomes: Sequence | None = None) -> Sequence[int]:
        """The quantity >= each outcome in order.

        Args:
            outcomes: If provided, the quantities corresponding to these
                outcomes will be returned (or 0 if not present).
        """
        if outcomes is None:
            return self._quantities_ge
        else:
            return tuple(self.quantity_ge(x) for x in outcomes)

    def quantities_lt(self, outcomes: Sequence | None = None) -> Sequence[int]:
        """The quantity < each outcome in order.

        Args:
            outcomes: If provided, the quantities corresponding to these
                outcomes will be returned (or 0 if not present).
        """
        return tuple(
            self.denominator() - x for x in self.quantities_ge(outcomes))

    def quantities_gt(self, outcomes: Sequence | None = None) -> Sequence[int]:
        """The quantity > each outcome in order.

        Args:
            outcomes: If provided, the quantities corresponding to these
                outcomes will be returned (or 0 if not present).
        """
        return tuple(
            self.denominator() - x for x in self.quantities_le(outcomes))

    # Probabilities.

    def probability(self, outcome: Hashable) -> float:
        """The probability of a single outcome, or 0.0 if not present. """
        return self.quantity(outcome) / self.denominator()

    def probability_le(self, outcome: Hashable) -> float:
        """The probability <= a single outcome. """
        return self.quantity_le(outcome) / self.denominator()

    def probability_lt(self, outcome: Hashable) -> float:
        """The probability < a single outcome. """
        return self.quantity_lt(outcome) / self.denominator()

    def probability_ge(self, outcome: Hashable) -> float:
        """The probability >= a single outcome. """
        return self.quantity_ge(outcome) / self.denominator()

    def probability_gt(self, outcome: Hashable) -> float:
        """The probability > a single outcome. """
        return self.quantity_gt(outcome) / self.denominator()

    @cached_property
    def _probabilities(self) -> Sequence[float]:
        return tuple(v / self.denominator() for v in self.values())

    def probabilities(self,
                      outcomes: Sequence | None = None,
                      *,
                      percent: bool = False) -> Sequence[float]:
        """The probability of each outcome in order.

        Also known as the probability mass function (PMF).

        Args:
            outcomes: If provided, the probabilities corresponding to these
                outcomes will be returned (or 0 if not present).
            percent: If set, the results will be in percent (i.e. total of 100.0).
                Otherwise, the total will be 1.0.
        """
        if outcomes is None:
            result = self._probabilities
        else:
            result = tuple(self.probability(x) for x in outcomes)

        if percent:
            return tuple(100.0 * x for x in result)
        else:
            return result

    @cached_property
    def _probabilities_le(self) -> Sequence[float]:
        return tuple(
            quantity / self.denominator() for quantity in self.quantities_le())

    def probabilities_le(self,
                         outcomes: Sequence | None = None,
                         *,
                         percent: bool = False) -> Sequence[float]:
        """The probability of rolling <= each outcome in order.

        Also known as the cumulative distribution function (CDF),
        though this term is ambigiuous whether it is < or <=.

        Args:
            outcomes: If provided, the probabilities corresponding to these
                outcomes will be returned (or 0 if not present).
            percent: If set, the results will be in percent (i.e. total of 100.0).
                Otherwise, the total will be 1.0.
        """
        if outcomes is None:
            result = self._probabilities_le
        else:
            result = tuple(self.probability_le(x) for x in outcomes)

        if percent:
            return tuple(100.0 * x for x in result)
        else:
            return result

    @cached_property
    def _probabilities_ge(self) -> Sequence[float]:
        return tuple(
            quantity / self.denominator() for quantity in self.quantities_ge())

    def probabilities_ge(self,
                         outcomes: Sequence | None = None,
                         *,
                         percent: bool = False) -> Sequence[float]:
        """The probability of rolling >= each outcome in order.

        Also known as the survival function (SF) or
        complementary cumulative distribution function (CCDF),
        though these term are ambigiuous whether they are is > or >=.

        Args:
            outcomes: If provided, the probabilities corresponding to these
                outcomes will be returned (or 0 if not present).
            percent: If set, the results will be in percent (i.e. total of 100.0).
                Otherwise, the total will be 1.0.
        """
        if outcomes is None:
            result = self._probabilities_ge
        else:
            result = tuple(self.probability_ge(x) for x in outcomes)

        if percent:
            return tuple(100.0 * x for x in result)
        else:
            return result

    def probabilities_lt(self,
                         outcomes: Sequence | None = None,
                         *,
                         percent: bool = False) -> Sequence[float]:
        """The probability of rolling < each outcome in order.

        Args:
            outcomes: If provided, the probabilities corresponding to these
                outcomes will be returned (or 0 if not present).
            percent: If set, the results will be in percent (i.e. total of 100.0).
                Otherwise, the total will be 1.0.
        """
        if outcomes is None:
            result = tuple(1.0 - x for x in self._probabilities_ge)
        else:
            result = tuple(1.0 - self.probability_ge(x) for x in outcomes)

        if percent:
            return tuple(100.0 * x for x in result)
        else:
            return result

    def probabilities_gt(self,
                         outcomes: Sequence | None = None,
                         *,
                         percent: bool = False) -> Sequence[float]:
        """The probability of rolling > each outcome in order.

        Args:
            outcomes: If provided, the probabilities corresponding to these
                outcomes will be returned (or 0 if not present).
            percent: If set, the results will be in percent (i.e. total of 100.0).
                Otherwise, the total will be 1.0.
        """
        if outcomes is None:
            result = tuple(1.0 - x for x in self._probabilities_le)
        else:
            result = tuple(1.0 - self.probability_le(x) for x in outcomes)

        if percent:
            return tuple(100.0 * x for x in result)
        else:
            return result

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

    def kolmogorov_smirnov(self, other) -> float:
        """Kolmogorov–Smirnov statistic. The maximum absolute difference between CDFs. """
        a, b = icepool.align(self, other)
        return max(
            abs(a - b)
            for a, b in zip(a.probabilities_le(), b.probabilities_le()))

    def cramer_von_mises(self, other) -> float:
        """Cramér-von Mises statistic. The sum-of-squares difference between CDFs. """
        a, b = icepool.align(self, other)
        return sum((a - b)**2
                   for a, b in zip(a.probabilities_le(), b.probabilities_le()))

    def median(self):
        """The median, taking the mean in case of a tie.

        This will fail if the outcomes do not support division;
        in this case, use `median_low` or `median_high` instead.
        """
        return self.quantile(1, 2)

    def median_low(self) -> T_co:
        """The median, taking the lower in case of a tie."""
        return self.quantile_low(1, 2)

    def median_high(self) -> T_co:
        """The median, taking the higher in case of a tie."""
        return self.quantile_high(1, 2)

    def quantile(self, n: int, d: int = 100):
        """The outcome `n / d` of the way through the CDF, taking the mean in case of a tie.

        This will fail if the outcomes do not support addition and division;
        in this case, use `quantile_low` or `quantile_high` instead.
        """
        # Should support addition and division.
        return (self.quantile_low(n, d) +
                self.quantile_high(n, d)) / 2  # type: ignore

    def quantile_low(self, n: int, d: int = 100) -> T_co:
        """The outcome `n / d` of the way through the CDF, taking the lesser in case of a tie."""
        index = bisect.bisect_left(self.quantities_le(),
                                   (n * self.denominator() + d - 1) // d)
        if index >= len(self):
            return self.max_outcome()
        return self.outcomes()[index]

    def quantile_high(self, n: int, d: int = 100) -> T_co:
        """The outcome `n / d` of the way through the CDF, taking the greater in case of a tie."""
        index = bisect.bisect_right(self.quantities_le(),
                                    n * self.denominator() // d)
        if index >= len(self):
            return self.max_outcome()
        return self.outcomes()[index]

    def mean(self: 'Population[numbers.Real]') -> float:
        return sum(outcome * quantity
                   for outcome, quantity in self.items()) / self.denominator()

    def variance(self: 'Population[numbers.Real]') -> float:
        """This is the population variance, not the sample variance."""
        mean = self.mean()
        mean_of_squares = sum(
            quantity * outcome**2
            for outcome, quantity in self.items()) / self.denominator()
        return mean_of_squares - mean * mean

    def standard_deviation(self: 'Population[numbers.Real]') -> float:
        return math.sqrt(self.variance())

    sd = standard_deviation

    def standardized_moment(self: 'Population[numbers.Real]', k: int) -> float:
        sd = self.standard_deviation()
        mean = self.mean()
        ev = sum(p * (outcome - mean)**k
                 for outcome, p in zip(self.outcomes(), self.probabilities()))
        return ev / (sd**k)

    def skewness(self: 'Population[numbers.Real]') -> float:
        return self.standardized_moment(3)

    def excess_kurtosis(self: 'Population[numbers.Real]') -> float:
        return self.standardized_moment(4) - 3.0

    # Joint statistics.

    class _Marginals(Sequence):
        """Helper class for implementing `marginals()`."""

        def __init__(self, population, /):
            self._population = population

        def __len__(self) -> int:
            """The minimum len() of all outcomes."""
            return min(len(x) for x in self._population.outcomes())

        def __getitem__(self, dims: int | slice, /):
            """Marginalizes the given dimensions."""
            return self._population._unary_operator(operator.getitem, dims)

    @property
    def marginals(self):
        """A property that applies the `[]` operator to outcomes.

        For example, `population.marginals[:2]` will marginalize the first two
        elements of the outcomes.
        """
        return Population._Marginals(self)

    def covariance(self: 'Population[tuple[numbers.Real, ...]]', i: int,
                   j: int) -> float:
        mean_i = self.marginals[i].mean()
        mean_j = self.marginals[j].mean()
        return sum((outcome[i] - mean_i) * (outcome[j] - mean_j) * quantity
                   for outcome, quantity in self.items()) / self.denominator()

    def correlation(self: 'Population[tuple[numbers.Real, ...]]', i: int,
                    j: int) -> float:
        sd_i = self.marginals[i].standard_deviation()
        sd_j = self.marginals[j].standard_deviation()
        return self.covariance(i, j) / (sd_i * sd_j)

    def sample(self) -> T_co:
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

    def format(self, format_spec: str, /, **kwargs) -> str:
        """Formats this mapping as a string.

        `format_spec` should start with the output format,
        which can be:
        * `md` for Markdown (default)
        * `bbcode` for BBCode
        * `csv` for comma-separated values
        * `html` for HTML

        After this, you may optionally add a `:` followed by a series of
        requested columns. Allowed columns are:

        * `o`: Outcomes.
        * `*o`: Outcomes, unpacked if applicable.
        * `q==`, `q<=`, `q>=`: Quantities ==, <=, or >= each outcome.
        * `p==`, `p<=`, `p>=`: Probabilities (0-1) ==, <=, or >= each outcome.
        * `%==`, `%<=`, `%>=`: Probabilities (0%-100%) ==, <=, or >= each outcome.

        Columns may optionally be separated using `|` characters.

        The default columns are `*o|q==|%==`, which are the unpacked outcomes,
        the quantities, and the probabilities. The quantities are omitted from
        the default columns if any individual quantity is 10**30 or greater.
        """
        if not self.is_empty() and self.modal_quantity() < 10**30:
            default_column_spec = '*oq==%=='
        else:
            default_column_spec = '*o%=='
        if len(format_spec) == 0:
            format_spec = 'md:' + default_column_spec

        format_spec = format_spec.replace('|', '')

        parts = format_spec.split(':')

        if len(parts) == 1:
            output_format = parts[0]
            col_spec = default_column_spec
        elif len(parts) == 2:
            output_format = parts[0]
            col_spec = parts[1]
        else:
            raise ValueError('format_spec has too many colons.')

        if output_format == 'md':
            return icepool.population.format.markdown(self, col_spec)
        elif output_format == 'bbcode':
            return icepool.population.format.bbcode(self, col_spec)
        elif output_format == 'csv':
            return icepool.population.format.csv(self, col_spec, **kwargs)
        elif output_format == 'html':
            return icepool.population.format.html(self, col_spec)
        else:
            raise ValueError(f"Unsupported output format '{output_format}'")

    def __format__(self, format_spec: str, /) -> str:
        return self.format(format_spec)

    def __str__(self) -> str:
        return f'{self}'