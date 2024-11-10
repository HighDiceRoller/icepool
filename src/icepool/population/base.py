__docformat__ = 'google'

import icepool
from icepool.collection.counts import CountsKeysView, CountsValuesView, CountsItemsView
from icepool.collection.vector import Vector
from icepool.math import try_fraction
from icepool.typing import U, Outcome, T_co, count_positional_parameters

from abc import ABC, abstractmethod
import bisect
from collections import defaultdict
from fractions import Fraction
from functools import cached_property
import itertools
import math
import numbers
import operator
import random

from typing import Any, Callable, Generic, Hashable, Iterator, Literal, Mapping, MutableMapping, Sequence, Sized, TypeVar, cast, overload

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

    @property
    def _items_for_cartesian_product(self) -> Sequence[tuple[T_co, int]]:
        return self.items()

    def _unary_operator(self, op: Callable, *args, **kwargs):
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
            if isinstance(outcome, Mapping):
                return None
            elif isinstance(outcome, Sized):
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

    def nearest(self, comparison: Literal['<=', '<', '>=', '>'], outcome,
                /) -> T_co | None:
        """The nearest outcome in this population fitting the comparison.

        Args:
            comparison: The comparison which the result must fit. For example,
                '<=' would find the greatest outcome that is not greater than
                the argument.
            outcome: The outcome to compare against.
        
        Returns:
            The nearest outcome fitting the comparison, or `None` if there is
            no such outcome.
        """
        match comparison:
            case '<=':
                if outcome in self:
                    return outcome
                index = bisect.bisect_right(self.outcomes(), outcome) - 1
                if index < 0:
                    return None
                return self.outcomes()[index]
            case '<':
                index = bisect.bisect_left(self.outcomes(), outcome) - 1
                if index < 0:
                    return None
                return self.outcomes()[index]
            case '>=':
                if outcome in self:
                    return outcome
                index = bisect.bisect_left(self.outcomes(), outcome)
                if index >= len(self):
                    return None
                return self.outcomes()[index]
            case '>':
                index = bisect.bisect_right(self.outcomes(), outcome)
                if index >= len(self):
                    return None
                return self.outcomes()[index]
            case _:
                raise ValueError(f'Invalid comparison {comparison}')

    @staticmethod
    def _zero(x):
        return x * 0

    def zero(self: C) -> C:
        """Zeros all outcomes of this population.

        This is done by multiplying all outcomes by `0`.

        The result will have the same denominator.

        Raises:
            ValueError: If the zeros did not resolve to a single outcome.
        """
        result = self._unary_operator(Population._zero)
        if len(result) != 1:
            raise ValueError('zero() did not resolve to a single outcome.')
        return result

    def zero_outcome(self) -> T_co:
        """A zero-outcome for this population.

        E.g. `0` for a `Population` whose outcomes are `int`s.
        """
        return self.zero().outcomes()[0]

    # Quantities.

    @overload
    def quantity(self, outcome: Hashable, /) -> int:
        """The quantity of a single outcome."""

    @overload
    def quantity(self, comparison: Literal['==', '!=', '<=', '<', '>=', '>'],
                 outcome: Hashable, /) -> int:
        """The total quantity fitting a comparison to a single outcome."""

    def quantity(self,
                 comparison: Literal['==', '!=', '<=', '<', '>=', '>']
                 | Hashable,
                 outcome: Hashable | None = None,
                 /) -> int:
        """The quantity of a single outcome.

        A comparison can be provided, in which case this returns the total
        quantity fitting the comparison.
        
        Args:
            comparison: The comparison to use. This can be omitted, in which
                case it is treated as '=='.
            outcome: The outcome to query.
        """
        if outcome is None:
            outcome = comparison
            comparison = '=='
        else:
            comparison = cast(Literal['==', '!=', '<=', '<', '>=', '>'],
                              comparison)

        match comparison:
            case '==':
                return self.get(outcome, 0)
            case '!=':
                return self.denominator() - self.get(outcome, 0)
            case '<=' | '<':
                threshold = self.nearest(comparison, outcome)
                if threshold is None:
                    return 0
                else:
                    return self._cumulative_quantities[threshold]
            case '>=':
                return self.denominator() - self.quantity('<', outcome)
            case '>':
                return self.denominator() - self.quantity('<=', outcome)
            case _:
                raise ValueError(f'Invalid comparison {comparison}')

    @overload
    def quantities(self, /) -> CountsValuesView:
        """All quantities in sorted order."""

    @overload
    def quantities(self, comparison: Literal['==', '!=', '<=', '<', '>=', '>'],
                   /) -> Sequence[int]:
        """The total quantities fitting the comparison for each outcome in sorted order.
        
        For example, '<=' gives the CDF.
        """

    def quantities(self,
                   comparison: Literal['==', '!=', '<=', '<', '>=', '>']
                   | None = None,
                   /) -> CountsValuesView | Sequence[int]:
        """The quantities of the mapping in sorted order.

        For example, '<=' gives the CDF.

        Args:
            comparison: Optional. If omitted, this defaults to '=='.
        """
        if comparison is None:
            comparison = '=='

        match comparison:
            case '==':
                return self.values()
            case '<=':
                return tuple(itertools.accumulate(self.values()))
            case '>=':
                return tuple(
                    itertools.accumulate(self.values()[:-1],
                                         operator.sub,
                                         initial=self.denominator()))
            case '!=':
                return tuple(self.denominator() - q for q in self.values())
            case '<':
                return tuple(self.denominator() - q
                             for q in self.quantities('>='))
            case '>':
                return tuple(self.denominator() - q
                             for q in self.quantities('<='))
            case _:
                raise ValueError(f'Invalid comparison {comparison}')

    @cached_property
    def _cumulative_quantities(self) -> Mapping[T_co, int]:
        result = {}
        cdf = 0
        for outcome, quantity in self.items():
            cdf += quantity
            result[outcome] = cdf
        return result

    @cached_property
    def _denominator(self) -> int:
        return sum(self.values())

    def denominator(self) -> int:
        """The sum of all quantities (e.g. weights or duplicates).

        For the number of unique outcomes, use `len()`.
        """
        return self._denominator

    def multiply_quantities(self: C, scale: int, /) -> C:
        """Multiplies all quantities by an integer."""
        if scale == 1:
            return self
        data = {
            outcome: quantity * scale
            for outcome, quantity in self.items()
        }
        return self._new_type(data)

    def divide_quantities(self: C, divisor: int, /) -> C:
        """Divides all quantities by an integer, rounding down.
        
        Resulting zero quantities are dropped.
        """
        if divisor == 0:
            return self
        data = {
            outcome: quantity // divisor
            for outcome, quantity in self.items() if quantity >= divisor
        }
        return self._new_type(data)

    def modulo_quantities(self: C, divisor: int, /) -> C:
        """Modulus of all quantities with an integer."""
        data = {
            outcome: quantity % divisor
            for outcome, quantity in self.items()
        }
        return self._new_type(data)

    def pad_to_denominator(self: C, target: int, /, outcome: Hashable) -> C:
        """Changes the denominator to a target number by changing the quantity of a specified outcome.
        
        Args:
            `target`: The denominator of the result.
            `outcome`: The outcome whose quantity will be adjusted.

        Returns:
            A `Population` like `self` but with the quantity of `outcome`
            adjusted so that the overall denominator is equal to  `target`.
            If the denominator is reduced to zero, it will be removed.

        Raises:
            `ValueError` if this would require the quantity of the specified
            outcome to be negative.
        """
        adjustment = target - self.denominator()
        data = {outcome: quantity for outcome, quantity in self.items()}
        new_quantity = data.get(outcome, 0) + adjustment
        if new_quantity > 0:
            data[outcome] = new_quantity
        elif new_quantity == 0:
            del data[outcome]
        else:
            raise ValueError(
                f'Padding to denominator of {target} would require a negative quantity of {new_quantity} for {outcome}'
            )
        return self._new_type(data)

    # Probabilities.

    @overload
    def probability(self, outcome: Hashable, /, *,
                    percent: Literal[False]) -> Fraction:
        """The probability of a single outcome, or 0.0 if not present."""

    @overload
    def probability(self, outcome: Hashable, /, *,
                    percent: Literal[True]) -> float:
        """The probability of a single outcome, or 0.0 if not present."""

    @overload
    def probability(self, outcome: Hashable, /) -> Fraction:
        """The probability of a single outcome, or 0.0 if not present."""

    @overload
    def probability(self, comparison: Literal['==', '!=', '<=', '<', '>=',
                                              '>'], outcome: Hashable, /, *,
                    percent: Literal[False]) -> Fraction:
        """The total probability of outcomes fitting a comparison."""

    @overload
    def probability(self, comparison: Literal['==', '!=', '<=', '<', '>=',
                                              '>'], outcome: Hashable, /, *,
                    percent: Literal[True]) -> float:
        """The total probability of outcomes fitting a comparison."""

    @overload
    def probability(self, comparison: Literal['==', '!=', '<=', '<', '>=',
                                              '>'], outcome: Hashable,
                    /) -> Fraction:
        """The total probability of outcomes fitting a comparison."""

    def probability(self,
                    comparison: Literal['==', '!=', '<=', '<', '>=', '>']
                    | Hashable,
                    outcome: Hashable | None = None,
                    /,
                    *,
                    percent: bool = False) -> Fraction | float:
        """The total probability of outcomes fitting a comparison."""
        if outcome is None:
            outcome = comparison
            comparison = '=='
        else:
            comparison = cast(Literal['==', '!=', '<=', '<', '>=', '>'],
                              comparison)
        result = Fraction(self.quantity(comparison, outcome),
                          self.denominator())
        return result * 100.0 if percent else result

    @overload
    def probabilities(self, /, *,
                      percent: Literal[False]) -> Sequence[Fraction]:
        """All probabilities in sorted order."""

    @overload
    def probabilities(self, /, *, percent: Literal[True]) -> Sequence[float]:
        """All probabilities in sorted order."""

    @overload
    def probabilities(self, /) -> Sequence[Fraction]:
        """All probabilities in sorted order."""

    @overload
    def probabilities(self, comparison: Literal['==', '!=', '<=', '<', '>=',
                                                '>'], /, *,
                      percent: Literal[False]) -> Sequence[Fraction]:
        """The total probabilities fitting the comparison for each outcome in sorted order.
        
        For example, '<=' gives the CDF.
        """

    @overload
    def probabilities(self, comparison: Literal['==', '!=', '<=', '<', '>=',
                                                '>'], /, *,
                      percent: Literal[True]) -> Sequence[float]:
        """The total probabilities fitting the comparison for each outcome in sorted order.
        
        For example, '<=' gives the CDF.
        """

    @overload
    def probabilities(self, comparison: Literal['==', '!=', '<=', '<', '>=',
                                                '>'], /) -> Sequence[Fraction]:
        """The total probabilities fitting the comparison for each outcome in sorted order.
        
        For example, '<=' gives the CDF.
        """

    def probabilities(
            self,
            comparison: Literal['==', '!=', '<=', '<', '>=', '>']
        | None = None,
            /,
            *,
            percent: bool = False) -> Sequence[Fraction] | Sequence[float]:
        """The total probabilities fitting the comparison for each outcome in sorted order.
        
        For example, '<=' gives the CDF.

        Args:
            comparison: Optional. If omitted, this defaults to '=='.
        """
        if comparison is None:
            comparison = '=='

        result = tuple(
            Fraction(q, self.denominator())
            for q in self.quantities(comparison))

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

    def kolmogorov_smirnov(self, other: 'Population') -> Fraction:
        """Kolmogorov–Smirnov statistic. The maximum absolute difference between CDFs. """
        outcomes = icepool.sorted_union(self, other)
        return max(
            abs(
                self.probability('<=', outcome) -
                other.probability('<=', outcome)) for outcome in outcomes)

    def cramer_von_mises(self, other: 'Population') -> Fraction:
        """Cramér-von Mises statistic. The sum-of-squares difference between CDFs. """
        outcomes = icepool.sorted_union(self, other)
        return sum(((self.probability('<=', outcome) -
                     other.probability('<=', outcome))**2
                    for outcome in outcomes),
                   start=Fraction(0, 1))

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
        index = bisect.bisect_left(self.quantities('<='),
                                   (n * self.denominator() + d - 1) // d)
        if index >= len(self):
            return self.max_outcome()
        return self.outcomes()[index]

    def quantile_high(self, n: int, d: int = 100) -> T_co:
        """The outcome `n / d` of the way through the CDF, taking the greater in case of a tie."""
        index = bisect.bisect_right(self.quantities('<='),
                                    n * self.denominator() // d)
        if index >= len(self):
            return self.max_outcome()
        return self.outcomes()[index]

    @overload
    def mean(self: 'Population[numbers.Rational]') -> Fraction:
        ...

    @overload
    def mean(self: 'Population[float]') -> float:
        ...

    def mean(
        self: 'Population[numbers.Rational] | Population[float]'
    ) -> Fraction | float:
        return try_fraction(
            sum(outcome * quantity for outcome, quantity in self.items()),
            self.denominator())

    @overload
    def variance(self: 'Population[numbers.Rational]') -> Fraction:
        ...

    @overload
    def variance(self: 'Population[float]') -> float:
        ...

    def variance(
        self: 'Population[numbers.Rational] | Population[float]'
    ) -> Fraction | float:
        """This is the population variance, not the sample variance."""
        mean = self.mean()
        mean_of_squares = try_fraction(
            sum(quantity * outcome**2 for outcome, quantity in self.items()),
            self.denominator())
        return mean_of_squares - mean * mean

    def standard_deviation(
            self: 'Population[numbers.Rational] | Population[float]') -> float:
        return math.sqrt(self.variance())

    sd = standard_deviation

    def standardized_moment(
            self: 'Population[numbers.Rational] | Population[float]',
            k: int) -> float:
        sd = self.standard_deviation()
        mean = self.mean()
        ev = sum(p * (outcome - mean)**k  # type: ignore 
                 for outcome, p in zip(self.outcomes(), self.probabilities()))
        return ev / (sd**k)

    def skewness(
            self: 'Population[numbers.Rational] | Population[float]') -> float:
        return self.standardized_moment(3)

    def excess_kurtosis(
            self: 'Population[numbers.Rational] | Population[float]') -> float:
        return self.standardized_moment(4) - 3.0

    def entropy(self, base: float = 2.0) -> float:
        """The entropy of a random sample from this population.
        
        Args:
            base: The logarithm base to use. Default is 2.0, which gives the 
                entropy in bits.
        """
        return -sum(p * math.log(p, base)
                    for p in self.probabilities() if p > 0.0)

    # Joint statistics.

    class _Marginals(Generic[C]):
        """Helper class for implementing `marginals()`."""

        _population: C

        def __init__(self, population, /):
            self._population = population

        def __len__(self) -> int:
            """The minimum len() of all outcomes."""
            return min(len(x) for x in self._population.outcomes())

        def __getitem__(self, dims: int | slice, /):
            """Marginalizes the given dimensions."""
            return self._population._unary_operator(operator.getitem, dims)

        def __iter__(self) -> Iterator:
            for i in range(len(self)):
                yield self[i]

        def __getattr__(self, key: str):
            if key[0] == '_':
                raise AttributeError(key)
            return self._population._unary_operator(operator.attrgetter(key))

    @property
    def marginals(self: C) -> _Marginals[C]:
        """A property that applies the `[]` operator to outcomes.

        For example, `population.marginals[:2]` will marginalize the first two
        elements of sequence outcomes.

        Attributes that do not start with an underscore will also be forwarded.
        For example, `population.marginals.x` will marginalize the `x` attribute
        from e.g. `namedtuple` outcomes.
        """
        return Population._Marginals(self)

    @overload
    def covariance(self: 'Population[tuple[numbers.Rational, ...]]', i: int,
                   j: int) -> Fraction:
        ...

    @overload
    def covariance(self: 'Population[tuple[float, ...]]', i: int,
                   j: int) -> float:
        ...

    def covariance(
            self:
        'Population[tuple[numbers.Rational, ...]] | Population[tuple[float, ...]]',
            i: int, j: int) -> Fraction | float:
        mean_i = self.marginals[i].mean()
        mean_j = self.marginals[j].mean()
        return try_fraction(
            sum((outcome[i] - mean_i) * (outcome[j] - mean_j) * quantity
                for outcome, quantity in self.items()), self.denominator())

    def correlation(
            self:
        'Population[tuple[numbers.Rational, ...]] | Population[tuple[float, ...]]',
            i: int, j: int) -> float:
        sd_i = self.marginals[i].standard_deviation()
        sd_j = self.marginals[j].standard_deviation()
        return self.covariance(i, j) / (sd_i * sd_j)

    # Transformations.

    def to_one_hot(self: C, outcomes: Sequence[T_co] | None = None) -> C:
        """Converts the outcomes of this population to a one-hot representation.

        Args:
            outcomes: If provided, each outcome will be mapped to a `Vector`
                where the element at `outcomes.index(outcome)` is set to `True`
                and the rest to `False`, or all `False` if the outcome is not
                in `outcomes`.
                If not provided, `self.outcomes()` is used.
        """
        if outcomes is None:
            outcomes = self.outcomes()

        data: MutableMapping[Vector[bool], int] = defaultdict(int)
        for outcome, quantity in zip(self.outcomes(), self.quantities()):
            value = [False] * len(outcomes)
            if outcome in outcomes:
                value[outcomes.index(outcome)] = True
            data[Vector(value)] += quantity
        return self._new_type(data)

    def sample(self) -> T_co:
        """A single random sample from this population.

        Note that this is always "with replacement" even for `Deck` since
        instances are immutable.

        This uses the standard `random` package and is not cryptographically
        secure.
        """
        # We don't use random.choices since that is based on floats rather than ints.
        r = random.randrange(self.denominator())
        index = bisect.bisect_right(self.quantities('<='), r)
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

        The default setting is equal to `f'{die:md:*o|q==|%==}'`. Here the 
        columns are the outcomes (unpacked if applicable) the quantities, and 
        the probabilities. The quantities are omitted from the default columns 
        if any individual quantity is 10**30 or greater.
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

        match output_format:
            case 'md':
                return icepool.population.format.markdown(self, col_spec)
            case 'bbcode':
                return icepool.population.format.bbcode(self, col_spec)
            case 'csv':
                return icepool.population.format.csv(self, col_spec, **kwargs)
            case 'html':
                return icepool.population.format.html(self, col_spec)
            case _:
                raise ValueError(
                    f"Unsupported output format '{output_format}'")

    def __format__(self, format_spec: str, /) -> str:
        return self.format(format_spec)

    def __str__(self) -> str:
        return f'{self}'
