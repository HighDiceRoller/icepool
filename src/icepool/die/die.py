__docformat__ = 'google'

import icepool
import icepool.die.format
import icepool.creation_args
from icepool.counts import Counts, CountsKeysView, CountsValuesView, CountsItemsView
from icepool.elementwise import unary_elementwise, binary_elementwise

import bisect
from collections import defaultdict
from functools import cached_property
import itertools
import math
import operator
import random

from typing import Any, Callable, Iterator
from collections.abc import Container, Mapping, MutableMapping, Sequence


class Die(Mapping[Any, int]):
    """An immutable `Mapping` of outcomes to nonnegative `int` weights.

    Dice are immutable. Methods do not modify the die in-place;
    rather they return a die representing the result.

    It *is* (mostly) well-defined to have a die with zero-weight outcomes,
    even though this is not a proper probability distribution.
    These can be useful in a few cases, such as:

    * `Pool` and `EvalPool` will iterate through zero-weight outcomes
        with 0 `count`, rather than `None` or skipping that outcome.
    * `icepool.align()` and the like are convenient for making dice share the
        same set of outcomes.

    However, zero-weight outcomes have a computational cost like any other
    outcome. Unless you have a specific use case in mind, it's best to leave
    them out.

    Most operators and methods will not introduce zero-weight outcomes if their
    arguments do not have any.

    It's also possible to have "empty" dice with no outcomes at all,
    though these have little use other than being sentinel values.
    """

    _data: Counts

    def __new__(cls,
                outcomes: Mapping[Any, int] | Sequence,
                times: Sequence[int] | int = 1,
                denominator_method: str = 'lcm') -> 'Die':
        """Constructor for a die.

        Don't confuse this with `d()`:

        * `Die([6])`: A die that always rolls the `int` 6.
        * `d(6)`: A d6.

        Also, don't confuse this with `Pool()`:

        * `Die([1, 2, 3, 4, 5, 6])`: A d6.
        * `Pool([1, 2, 3, 4, 5, 6])`: A pool of six dice that always rolls one
            of each number.

        Here are some different ways of constructing a d6:

        * Just import it: `from icepool import d6`
        * Use the `d()` function: `icepool.d(6)`
        * Use a d6 that you already have: `Die(d6)` or `Die([d6])`
        * Mix a d3 and a d3+3: `Die([d3, d3+3])`
        * Use a dict: `Die({1:1, 2:1, 3:1, 4:1, 5:1, 6:1})`
        * Give the faces as args: `Die([1, 2, 3, 4, 5, 6])`

        All weights must be non-negative, though they can be zero.

        Args:
            outcomes: The faces of the die. This can be one of the following:
                * A `Mapping` from outcomes to weights.
                * A sequence of outcomes. Each element will have the same total
                    weight.

                Note that `Die` and `Deck` both count as `Mapping`s.

                Each outcome may be one of the following:
                * A `Mapping` from outcomes to weights.
                    The outcomes of the `Mapping` will be "flattened" into the
                    result. This option will be taken in preference to treating
                    the `Mapping` itself as an outcome even if the `Mapping`
                    itself is hashable and totally orderable. This means that
                    `Die` and `Deck` will never be outcomes.
                * A tuple of outcomes. Operators on dice with tuple outcomes
                    are performed element-wise. See `Die.unary_op` and
                    `Die.binary_op` for details.

                    Any tuple elements that are `Mapping`s will expand the
                    tuple according to their independent joint distribution.
                    For example, `(d6, d6)` will expand to 36 ordered tuples
                    with weight 1 each. Use this carefully since it may create a
                    large number of outcomes.
                * `icepool.Reroll`, which will drop itself
                    and the corresponding element of `times` from consideration.
                    If inside a tuple, the tuple will be dropped.
                * Anything else will be treated as a single outcome.
                    Each outcome must be hashable, and the
                    set of outcomes must be totally orderable (after expansion).
                    The same outcome can appear multiple times, in which case
                    the corresponding weights will be accumulated.
            times: Multiplies the weight of each element of `outcomes`.
                `times` can either be a sequence of the same length as
                `outcomes` or a single `int` to apply to all elements of
                `outcomes`.
            denominator_method: How to determine the denominator of the result
                if the arguments themselves contain weights. This is also used
                for `Mapping` arguments. From greatest to least:
                * 'prod': Product of the individual argument denominators, times
                    the total of `weights`. This is like rolling all of the
                    possible dice, and then selecting a result.
                * 'lcm' (default): LCM of the individual argument denominators,
                    times the total of `weights`. This is like rolling `weights`
                    first, then selecting an argument to roll.
                * 'lcm_joint': LCM of the individual (argument denominators
                    times corresponding element of `weights`). This is like
                    rolling the above, but the specific weight rolled is used
                    to help determine the result of the selected argument.
                * 'reduce': The final weights are divided by their GCD.
        Raises:
            `ValueError`: `None` is not a valid outcome for a die.
        """
        if isinstance(outcomes, Die):
            if times == 1:
                return outcomes
            else:
                outcomes = outcomes._data

        outcomes, times = icepool.creation_args.itemize(outcomes, times)

        if len(outcomes) == 1 and times[0] == 1 and isinstance(
                outcomes[0], Die):
            return outcomes[0]

        self = super(Die, cls).__new__(cls)
        self._data = icepool.creation_args.expand_args_for_die(
            outcomes, times, denominator_method=denominator_method)
        return self

    def unary_op(self, op: Callable, *args, **kwargs) -> 'Die':
        """Performs the unary operation on the outcomes.

        Operations on tuples are performed elementwise recursively. If you need
        some other specific behavior, use your own outcome class, or use `sub()`
        rather than an operator.

        This is used for the standard unary operators
        `-, +, abs, ~, round, trunc, floor, ceil`
        as well as the additional methods
        `zero, bool`.

        This is NOT used for the `[]` operator; when used directly, this is
        interpreted as a `Mapping` operation and returns the count corresponding
        to a given outcome. See `marginal()` for applying the `[]` operator to
        outcomes.

        Returns:
            A die representing the result.

        Raises:
            ValueError if tuples are of mismatched length.
        """
        data: MutableMapping[Any, int] = defaultdict(int)
        for outcome, weight in self.items():
            new_outcome = unary_elementwise(outcome, op, *args, **kwargs)
            data[new_outcome] += weight
        return icepool.Die(data)

    def unary_op_non_elementwise(self, op: Callable, *args, **kwargs) -> 'Die':
        """As `unary_op()`, but not elementwise.

        This is used for the `marginals()`.
        """
        data: MutableMapping[Any, int] = defaultdict(int)
        for outcome, weight in self.items():
            new_outcome = op(outcome, *args, **kwargs)
            data[new_outcome] += weight
        return icepool.Die(data)

    def binary_op(self, other: 'Die', op: Callable, *args, **kwargs) -> 'Die':
        """Performs the operation on pairs of outcomes.

        Operations on tuples are performed elementwise recursively. If you need
        some other specific behavior, use your own outcome class, or use `sub()`
        rather than an operator.

        By the time this is called, the other operand has already been
        converted to a die.

        This is used for the standard binary operators
        `+, -, *, /, //, %, **, <<, >>, &, |, ^`.
        Note that `*` multiplies outcomes directly;
        it is not the same as `@`, which rolls the right side multiple times,
        or `d()`, which creates a standard die.

        The comparators (`<, <=, >=, >, ==, !=, cmp`) use a linear algorithm
        using the fact that outcomes are totally ordered.

        `==` and `!=` additionally set the truth value of the die according to
        whether the dice themselves are the same or not.

        The `@` operator does NOT use this method directly.
        It rolls the left die, which must have integer outcomes,
        then rolls the right die that many times and sums the outcomes.
        Only the sum is performed element-wise.

        Returns:
            A die representing the result.

        Raises:
            `ValueError` if tuples are of mismatched length within one of the
                dice or between the dice.
        """
        data: MutableMapping[Any, int] = defaultdict(int)
        for (outcome_self, weight_self), (outcome_other,
                                          weight_other) in itertools.product(
                                              self.items(), other.items()):
            new_outcome = binary_elementwise(outcome_self, outcome_other, op,
                                             *args, **kwargs)
            data[new_outcome] += weight_self * weight_other
        return icepool.Die(data)

    # Basic access.

    def outcomes(self) -> CountsKeysView:
        """The sorted outcomes of the die.

        These are also the `keys` of the die as a `Mapping`.
        Prefer to use the name `outcomes`.
        """
        return self._data.keys()

    keys = outcomes

    def weights(self) -> CountsValuesView:
        """The weights of the die in outcome order.

        These are also the `values` of the die as a `Mapping`.
        Prefer to use the name `weights`.
        """
        return self._data.values()

    values = weights

    def items(self) -> CountsItemsView:
        """Returns the sequence of sorted outcome, weight pairs. """
        return self._data.items()

    def __getitem__(self, outcome, /) -> int:
        return self._data[outcome]

    def __iter__(self) -> Iterator:
        return iter(self.keys())

    def num_outcomes(self) -> int:
        """Returns the number of outcomes (including those with zero weight). """
        return len(self._data)

    __len__ = num_outcomes

    def is_empty(self) -> bool:
        """Returns `True` if this die has no outcomes. """
        return self.num_outcomes() == 0

    def __contains__(self, outcome) -> bool:
        return outcome in self._data

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
        """Returns the common length of the outcomes.

        If any outcome has no length, the outcomes have mixed length, or the
        die is empty, the result is `None`.
        """
        return self._outcome_len

    def has_zero_weights(self) -> bool:
        """Returns `True` iff `self` contains at least one outcome with zero weight. """
        return self._data.has_zero_values()

    # Weights.

    @cached_property
    def _denominator(self) -> int:
        return sum(self._data.values())

    def denominator(self) -> int:
        """The total weight of all outcomes. """
        return self._denominator

    total_weight = denominator

    @cached_property
    def _pmf(self):
        return tuple(weight / self.denominator() for weight in self.weights())

    def pmf(self, percent: bool = False):
        """Probability mass function. The probability of rolling each outcome in order.

        Args:
            percent: If set, the results will be in percent (i.e. total of 100.0).
                Otherwise, the total will be 1.0.
        """
        if percent:
            return tuple(100.0 * x for x in self._pmf)
        else:
            return self._pmf

    @cached_property
    def _cweights(self) -> Sequence[int]:
        return tuple(itertools.accumulate(self.weights()))

    def cweights(self) -> Sequence[int]:
        """Cumulative weights. The weight <= each outcome in order. """
        return self._cweights

    @cached_property
    def _sweights(self) -> Sequence[int]:
        return tuple(
            itertools.accumulate(self.weights()[:-1],
                                 operator.sub,
                                 initial=self.denominator()))

    def sweights(self) -> Sequence[int]:
        """Survival weights. The weight >= each outcome in order. """
        return self._sweights

    @cached_property
    def _cdf(self):
        return tuple(weight / self.denominator() for weight in self.cweights())

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
        return tuple(weight / self.denominator() for weight in self.sweights())

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

    def weight_eq(self, outcome) -> int:
        """Returns the weight of a single outcome, or 0 if not present. """
        return self._data.get(outcome, 0)

    def weight_ne(self, outcome) -> int:
        """Returns the weight != a single outcome. """
        return self.denominator() - self.weight_eq(outcome)

    def weight_le(self, outcome) -> int:
        """Returns the weight <= a single outcome. """
        index = bisect.bisect_right(self.outcomes(), outcome) - 1
        if index < 0:
            return 0
        return self.cweights()[index]

    def weight_lt(self, outcome) -> int:
        """Returns the weight < a single outcome. """
        index = bisect.bisect_left(self.outcomes(), outcome) - 1
        if index < 0:
            return 0
        return self.cweights()[index]

    def weight_ge(self, outcome) -> int:
        """Returns the weight >= a single outcome. """
        index = bisect.bisect_left(self.outcomes(), outcome)
        if index >= self.num_outcomes():
            return 0
        return self.sweights()[index]

    def weight_gt(self, outcome) -> int:
        """Returns the weight > a single outcome. """
        index = bisect.bisect_right(self.outcomes(), outcome)
        if index >= self.num_outcomes():
            return 0
        return self.sweights()[index]

    def probability(self, outcome):
        """Returns the probability of a single outcome. """
        return self.weight_eq(outcome) / self.denominator()

    # Scalar statistics.

    def mode(self) -> tuple:
        """Returns a tuple containing the most common outcome(s) of the die.

        These are sorted from lowest to highest.
        """
        return tuple(outcome for outcome, weight in self.items()
                     if weight == self.modal_weight())

    def modal_weight(self) -> int:
        """The highest weight of any single outcome. """
        return max(self.weights())

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
        index = bisect.bisect_left(self.cweights(),
                                   (n * self.denominator() + d - 1) // d)
        if index >= self.num_outcomes():
            return self.max_outcome()
        return self.outcomes()[index]

    def ppf_right(self, n: int, d: int = 100):
        """Returns a quantile, `n / d` of the way through the cdf.

        If the result lies between two outcomes, returns the higher of the two.
        """
        index = bisect.bisect_right(self.cweights(),
                                    n * self.denominator() // d)
        if index >= self.num_outcomes():
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
        return sum(
            outcome * p for outcome, p in zip(self.outcomes(), self.pmf()))

    def variance(self):
        mean = self.mean()
        mean_of_squares = sum(
            p * outcome**2 for outcome, p in zip(self.outcomes(), self.pmf()))
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
        return sum((outcome[i] - mean_i) * (outcome[j] - mean_j) * weight
                   for outcome, weight in self.items()) / self.denominator()

    def correlation(self, i: int, j: int):
        sd_i = self.marginals[i].standard_deviation()
        sd_j = self.marginals[j].standard_deviation()
        return self.covariance(i, j) / (sd_i * sd_j)

    # Weight management.

    def reduce_weights(self) -> 'Die':
        """Divides all weights by their greatest common denominator. """
        return icepool.Die(self._data.reduce())

    def scale_weights(self, scale: int) -> 'Die':
        """Multiplies all weights by a constant. """
        if scale < 0:
            raise ValueError('Weights cannot be scaled by a negative number.')
        if scale == 1:
            return self
        data = {outcome: scale * weight for outcome, weight in self.items()}
        return icepool.Die(data)

    # Rerolls and other outcome management.

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
        if index >= self.num_outcomes():
            return None
        return self.outcomes()[index]

    def reroll(self,
               outcomes: Callable[..., bool] | Container | None = None,
               *extra_args,
               max_depth: int | None = None,
               star: int = 0) -> 'Die':
        """Rerolls the given outcomes.

        Args:
            outcomes: Selects which outcomes to reroll. Options:
                * A callable that takes an outcome and returns `True` if it
                    should be rerolled.
                * A container of outcomes to reroll.
                * If not provided, the min outcome will be rerolled.
            *extra_args: These will be supplied to `outcomes` as extra
                positional arguments after the outcome argument(s).
                `extra_args` can only be supplied if `outcomes` is callable.
            max_depth: The maximum number of times to reroll.
                If omitted, rerolls an unlimited number of times.
            star: If set to `True` or 1, outcomes will be unpacked as
                `*outcome` before giving it to the `outcomes` function.
                If `outcomes` is not a callable, this has no effect.

        Returns:
            A die representing the reroll.
            If the reroll would never terminate, the result has no outcomes.

        Raises:
            `ValueError` if `extra_args` are supplied with a non-callable `outcomes`.
        """
        if extra_args and not callable(outcomes):
            raise ValueError(
                'Extra positional arguments are only valid if outcomes is callable.'
            )

        if outcomes is None:
            outcomes = {self.min_outcome()}
        elif callable(outcomes):
            if star:
                outcomes = {
                    outcome for outcome in self.outcomes()
                    if outcomes(*outcome, *extra_args)
                }
            else:
                outcomes = {
                    outcome for outcome in self.outcomes()
                    if outcomes(outcome, *extra_args)
                }

        if max_depth is None:
            data = {
                outcome: weight
                for outcome, weight in self.items()
                if outcome not in outcomes
            }
        else:
            total_reroll_weight = sum(
                weight for outcome, weight in self.items()
                if outcome in outcomes)
            rerollable_factor = total_reroll_weight**max_depth
            stop_factor = (self.denominator()**max_depth +
                           total_reroll_weight**max_depth)
            data = {
                outcome:
                (rerollable_factor *
                 weight if outcome in outcomes else stop_factor * weight)
                for outcome, weight in self.items()
            }
        return icepool.Die(data)

    def reroll_until(self,
                     outcomes: Callable[..., bool] | Container,
                     *extra_args,
                     max_depth: int | None = None,
                     star: int = 0) -> 'Die':
        """Rerolls until getting one of the given outcomes.

        Essentially the complement of `reroll()`.

        Args:
            outcomes: Selects which outcomes to reroll until. Options:
                * A callable that takes an outcome and returns `True` if it
                    should be accepted.
                * A container of outcomes to reroll until.
            *extra_args: These will be supplied to `outcomes` as extra
                positional arguments after the outcome argument(s).
                `extra_args` can only be supplied if `outcomes` is callable.
            max_depth: The maximum number of times to reroll.
                If omitted, rerolls an unlimited number of times.
            star: If set to `True` or 1, outcomes will be unpacked as
                `*outcome` before giving it to the `outcomes` function.
                If `outcomes` is not a callable, this has no effect.

        Returns:
            A die representing the reroll.
            If the reroll would never terminate, the result has no outcomes.

        Raises:
            `ValueError` if `extra_args` are supplied with a non-callable `outcomes`.
        """
        if extra_args and not callable(outcomes):
            raise ValueError(
                'Extra positional arguments are only valid if outcomes is callable.'
            )

        if callable(outcomes):
            if star:
                not_outcomes = {
                    outcome for outcome in self.outcomes()
                    if not outcomes(*outcome, *extra_args)
                }
            else:
                not_outcomes = {
                    outcome for outcome in self.outcomes()
                    if not outcomes(outcome, *extra_args)
                }
        else:
            not_outcomes = {
                not_outcome for not_outcome in self.outcomes()
                if not_outcome not in outcomes
            }
        return self.reroll(not_outcomes, max_depth=max_depth)

    def truncate(self, min_outcome=None, max_outcome=None) -> 'Die':
        """Truncates the outcomes of this die to the given range.

        The endpoints are included in the result if applicable.
        If one of the arguments is not provided, that side will not be truncated.

        This effectively rerolls outcomes outside the given range.
        If instead you want to replace those outcomes with the nearest endpoint,
        use `clip()`.

        Not to be confused with `trunc(die)`, which performs integer truncation
        on each outcome.
        """
        if min_outcome is not None:
            start = bisect.bisect_left(self.outcomes(), min_outcome)
        else:
            start = None
        if max_outcome is not None:
            stop = bisect.bisect_right(self.outcomes(), max_outcome)
        else:
            stop = None
        data = {k: v for k, v in self.items()[start:stop]}
        return icepool.Die(data)

    def clip(self, min_outcome=None, max_outcome=None) -> 'Die':
        """Clips the outcomes of this die to the given values.

        The endpoints are included in the result if applicable.
        If one of the arguments is not provided, that side will not be clipped.

        This is not the same as rerolling outcomes beyond this range;
        the outcome is simply adjusted to fit within the range.
        This will typically cause some weight to bunch up at the endpoint.
        If you want to reroll outcomes beyond this range, use `truncate()`.
        """
        data: MutableMapping[Any, int] = defaultdict(int)
        for outcome, weight in self.items():
            if min_outcome is not None and outcome <= min_outcome:
                data[min_outcome] += weight
            elif max_outcome is not None and outcome >= max_outcome:
                data[max_outcome] += weight
            else:
                data[outcome] += weight
        return icepool.Die(data)

    def set_range(self,
                  min_outcome: int | None = None,
                  max_outcome: int | None = None) -> 'Die':
        """Sets the outcomes of this die to the given `int` range (inclusive).

        Args:
            min_outcome: The min outcome of the result.
                If omitted, the min outcome of this die will be used.
            max_outcome: The max outcome of the result.
                If omitted, the max outcome of this die will be used.
        """
        if min_outcome is None:
            min_outcome = self.min_outcome()
        if max_outcome is None:
            max_outcome = self.max_outcome()

        return self.set_outcomes(range(min_outcome, max_outcome + 1))

    def set_outcomes(self, outcomes) -> 'Die':
        """Sets the set of outcomes to the argument.

        This may remove outcomes (if they are not present in the argument)
        and/or add zero-weight outcomes (if they are not present in this die).
        """
        data = {x: self.weight_eq(x) for x in outcomes}
        return icepool.Die(data)

    def trim(self) -> 'Die':
        """Removes all zero-weight outcomes. """
        data = {k: v for k, v in self.items() if v > 0}
        return icepool.Die(data)

    @cached_property
    def _popped_min(self) -> tuple['Die', int]:
        die = icepool.Die(self._data.remove_min())
        return die, self.weights()[0]

    def _pop_min(self) -> tuple['Die', int]:
        """Removes the min outcome and return the result, along with the popped outcome, and the popped weight.

        Raises:
            `IndexError` if this die has no outcome to pop.
        """
        return self._popped_min

    @cached_property
    def _popped_max(self) -> tuple['Die', int]:
        die = icepool.Die(self._data.remove_max())
        return die, self.weights()[-1]

    def _pop_max(self) -> tuple['Die', int]:
        """Removes the max outcome and return the result, along with the popped outcome, and the popped weight.

        Raises:
            `IndexError` if this die has no outcome to pop.
        """
        return self._popped_max

    # Mixtures.

    def sub(self,
            repl: Mapping | Callable[[Any], Any] | Sequence,
            /,
            *extra_args,
            max_depth: int | None = 1,
            star: int = 0,
            denominator_method: str = 'lcm') -> 'Die':
        """Changes outcomes of the die to other outcomes.

        You can think of this as `sub`stituting outcomes of this die for other
        outcomes or dice. Or, as executing a `sub`routine based on the roll of
        this die.

        Args:
            repl: One of the following:
                * A map from old outcomes to new outcomes.
                    Unmapped old outcomes stay the same.
                * A callable returning a new outcome for each old outcome.
                * A sequence specifying new outcomes in order.
                The new outcomes may be dice rather than just single outcomes.
                The special value `icepool.Reroll` will reroll that old outcome.
            *extra_args: These will be supplied to `repl` as extra positional
                arguments after the outcome argument(s). `extra_args` can only
                be supplied if `repl` is callable.
            max_depth: `sub()` will be repeated with the same argument on the
                result this many times. If set to `None`, this will repeat until
                a fixed point is reached.
            star: If set to `True` or 1, outcomes will be unpacked as
                `*outcome` before giving it to the `repl` function. If `repl`
                is not a callable, this has no effect.
            denominator_method: As `icepool.Die()`.

        Returns:
            The relabeled die.

        Raises:
            `ValueError` if `extra_args` are supplied with a non-callable `repl`.
        """
        if extra_args and not callable(repl):
            raise ValueError(
                'Extra positional arguments are only valid if repl is callable.'
            )

        if max_depth == 0:
            return self
        elif max_depth == 1:
            if isinstance(repl, Mapping):
                final_repl = [(repl[outcome] if outcome in repl else outcome)
                              for outcome in self.outcomes()]
            elif callable(repl):
                if star:
                    final_repl = [
                        repl(*outcome, *extra_args)
                        for outcome in self.outcomes()
                    ]
                else:
                    final_repl = [
                        repl(outcome, *extra_args)
                        for outcome in self.outcomes()
                    ]
            else:
                final_repl = list(repl)

            return icepool.Die(final_repl,
                               self.weights(),
                               denominator_method=denominator_method)
        elif max_depth is not None:
            next = self.sub(repl,
                            max_depth=1,
                            denominator_method=denominator_method)
            return next.sub(repl,
                            max_depth=max_depth - 1,
                            denominator_method=denominator_method)
        else:
            # Seek fixed point.
            next = self.sub(repl,
                            max_depth=1,
                            denominator_method=denominator_method)
            if self.reduce_weights().equals(next.reduce_weights()):
                return self
            else:
                return next.sub(repl,
                                max_depth=None,
                                denominator_method=denominator_method)

    def explode(self,
                outcomes: Container | Callable[..., bool] | None = None,
                *extra_args,
                max_depth: int = 9,
                star: int = 0) -> 'Die':
        """Causes outcomes to be rolled again and added to the total.

        Args:
            outcomes: Which outcomes to explode. Options:
                * An container of outcomes to explode.
                * A callable that takes an outcome and returns `True` if it
                    should be exploded.
                * If not supplied, the max outcome will explode.
            *extra_args: These will be supplied to `outcomes` as extra
                positional arguments after the outcome argument(s).
                `extra_args` can only be supplied if `outcomes` is callable.
            max_depth: The maximum number of additional dice to roll.
                If not supplied, a default value will be used.
            star: If set to `True` or 1, outcomes will be unpacked as
                `*outcome` before giving it to the `outcomes` function.
                If `outcomes` is not a callable, this has no effect.

        Raises:
            `ValueError` if `extra_args` are supplied with a non-callable `outcomes`.
        """
        if extra_args and not callable(outcomes):
            raise ValueError(
                'Extra positional arguments are only valid if outcomes is callable.'
            )

        if outcomes is None:
            outcomes = {self.max_outcome()}
        elif callable(outcomes):
            if star:
                outcomes = {
                    outcome for outcome in self.outcomes()
                    if outcomes(*outcome, *extra_args)
                }
            else:
                outcomes = {
                    outcome for outcome in self.outcomes()
                    if outcomes(outcome, *extra_args)
                }
        else:
            if not outcomes:
                return self

        if max_depth < 0:
            raise ValueError('max_depth cannot be negative.')
        elif max_depth == 0:
            return self

        tail_die = self.explode(outcomes=outcomes, max_depth=max_depth - 1)

        def sub_func(outcome):
            if outcome in outcomes:
                return outcome + tail_die
            else:
                return outcome

        return self.sub(sub_func, denominator_method='lcm')

    def if_else(self,
                outcome_if_true,
                outcome_if_false,
                /,
                *,
                denominator_method: str = 'lcm') -> 'Die':
        """Ternary conditional operator.

        This replaces truthy outcomes with the first argument and falsy outcomes
        with the second argument.
        """
        return self.bool().sub(lambda x: outcome_if_true
                               if x else outcome_if_false,
                               denominator_method=denominator_method)

    # Pools and sums.

    @cached_property
    def _sum_cache(self) -> MutableMapping[int, 'Die']:
        return {}

    def _sum_all(self, num_dice: int) -> 'Die':
        """Roll this die `num_dice` times and sum the results.

        If `num_dice` is negative, roll the die `abs(num_dice)` times and negate
        the result.

        If you instead want to replace tuple (or other sequence) outcomes with
        their sum, use `die.sub(sum)`.
        """
        if num_dice in self._sum_cache:
            return self._sum_cache[num_dice]

        if num_dice < 0:
            result = -self._sum_all(-num_dice)
        elif num_dice == 0:
            result = self.zero()
        elif num_dice == 1:
            result = self
        else:
            # Binary split seems to perform much worse.
            result = self + self._sum_all(num_dice - 1)

        self._sum_cache[num_dice] = result
        return result

    def __matmul__(self, other) -> 'Die':
        """Roll the left die, then roll the right die that many times and sum the outcomes."""
        other = icepool.Die([other])

        data: MutableMapping[int, Any] = defaultdict(int)

        max_abs_die_count = max(abs(self.min_outcome()),
                                abs(self.max_outcome()))
        for die_count, die_count_weight in self.items():
            factor = other.denominator()**(max_abs_die_count - abs(die_count))
            subresult = other._sum_all(die_count)
            for outcome, subresult_weight in subresult.items():
                data[outcome] += subresult_weight * die_count_weight * factor

        return icepool.Die(data)

    def __rmatmul__(self, other) -> 'Die':
        """Roll the left die, then roll the right die that many times and sum the outcomes."""
        other = icepool.Die([other])
        return other.__matmul__(self)

    def pool(self, num_dice: int = 1) -> 'icepool.Pool':
        """Creates a pool from this die.

        Args:
            num_dice: The number of copies of this die to put in the pool.
        """
        return icepool.Pool({self: num_dice})

    def keep_highest(self,
                     num_dice: int,
                     num_keep: int = 1,
                     num_drop: int = 0) -> 'Die':
        """Roll several of this die and sum the sorted results from the highest.

        Args:
            num_dice: The number of dice to roll. All dice will have the same
                outcomes as `self`.
            num_keep: The number of dice to keep.
            num_drop: If provided, this many highest dice will be dropped before
                keeping.

        Returns:
            A die representing the probability distribution of the sum.
        """
        if num_keep == 1 and num_drop == 0:
            return self._keep_highest_single(num_dice)
        start = -(num_keep + (num_drop or 0))
        stop = -num_drop if num_drop > 0 else None
        post_roll_counts = slice(start, stop)
        return self.pool(num_dice)[post_roll_counts].sum()

    def _keep_highest_single(self, num_dice: int) -> 'Die':
        """Faster algorithm for keeping just the single highest die. """
        if num_dice == 0:
            return self.zero()
        return icepool.from_cweights(self.outcomes(),
                                     [x**num_dice for x in self.cweights()])

    def keep_lowest(self,
                    num_dice: int,
                    num_keep: int = 1,
                    num_drop: int = 0) -> 'Die':
        """Roll several of this die and sum the sorted results from the lowest.

        Args:
            num_dice: The number of dice to roll. All dice will have the same
                outcomes as `self`.
            num_keep: The number of dice to keep.
            num_drop: If provided, this many lowest dice will be dropped before
                keeping.

        Returns:
            A die representing the probability distribution of the sum.
        """
        if num_keep == 1 and num_drop == 0:
            return self._keep_lowest_single(num_dice)

        start = num_drop if num_drop > 0 else None
        stop = num_keep + (num_drop or 0)
        post_roll_counts = slice(start, stop)
        return self.pool(num_dice)[post_roll_counts].sum()

    def _keep_lowest_single(self, num_dice: int) -> 'Die':
        """Faster algorithm for keeping just the single lowest die. """
        if num_dice == 0:
            return self.zero()
        return icepool.from_sweights(self.outcomes(),
                                     [x**num_dice for x in self.sweights()])

    # Unary operators.

    def __neg__(self) -> 'Die':
        return self.unary_op(operator.neg)

    def __pos__(self) -> 'Die':
        return self.unary_op(operator.pos)

    def __invert__(self) -> 'Die':
        return self.unary_op(operator.invert)

    def abs(self) -> 'Die':
        return self.unary_op(operator.abs)

    __abs__ = abs

    def round(self, ndigits: int = None) -> 'Die':
        return self.unary_op(round, ndigits)

    __round__ = round

    def trunc(self) -> 'Die':
        return self.unary_op(math.trunc)

    __trunc__ = trunc

    def floor(self) -> 'Die':
        return self.unary_op(math.floor)

    __floor__ = floor

    def ceil(self) -> 'Die':
        return self.unary_op(math.ceil)

    __ceil__ = ceil

    class Marginals():
        """Helper class for implementing marginals()."""

        _die: 'Die'

        def __init__(self, die: 'Die'):
            self._die = die

        def __getitem__(self, dims, /) -> 'Die':

            return self._die.unary_op_non_elementwise(operator.getitem, dims)

    @property
    def marginals(self):
        """A property that applies the `[]` operator to outcomes.

        This is not performed elementwise on tuples, so that this can be used
        to slice tuples. For example, `die.marginals[:2]` will marginalize the
        first two elements of tuples.
        """
        return Die.Marginals(self)

    @staticmethod
    def _zero(x):
        return type(x)()

    def zero(self) -> 'Die':
        """Zeros all outcomes of this die.

        This is done by calling the constructor for each outcome's type with no
        arguments.

        The result will have the same denominator as this die.

        Raises:
            `ValueError` if the zeros did not resolve to a single outcome.
        """
        result = self.unary_op(Die._zero)
        if result.num_outcomes() != 1:
            raise ValueError('zero() did not resolve to a single outcome.')
        return result

    def zero_outcome(self):
        """Returns a zero-outcome for this die.

        E.g. `0` for a die whose outcomes are `int`s.
        """
        return self.zero().outcomes()[0]

    # Binary operators.

    def __add__(self, other) -> 'Die':
        other = icepool.Die([other])
        return self.binary_op(other, operator.add)

    def __radd__(self, other) -> 'Die':
        other = icepool.Die([other])
        return other.binary_op(self, operator.add)

    def __sub__(self, other) -> 'Die':
        other = icepool.Die([other])
        return self.binary_op(other, operator.sub)

    def __rsub__(self, other) -> 'Die':
        other = icepool.Die([other])
        return other.binary_op(self, operator.sub)

    def __mul__(self, other) -> 'Die':
        other = icepool.Die([other])
        return self.binary_op(other, operator.mul)

    def __rmul__(self, other) -> 'Die':
        other = icepool.Die([other])
        return other.binary_op(self, operator.mul)

    def __truediv__(self, other) -> 'Die':
        other = icepool.Die([other])
        return self.binary_op(other, operator.truediv)

    def __rtruediv__(self, other) -> 'Die':
        other = icepool.Die([other])
        return other.binary_op(self, operator.truediv)

    def __floordiv__(self, other) -> 'Die':
        other = icepool.Die([other])
        return self.binary_op(other, operator.floordiv)

    def __rfloordiv__(self, other) -> 'Die':
        other = icepool.Die([other])
        return other.binary_op(self, operator.floordiv)

    def __pow__(self, other) -> 'Die':
        other = icepool.Die([other])
        return self.binary_op(other, operator.pow)

    def __rpow__(self, other) -> 'Die':
        other = icepool.Die([other])
        return other.binary_op(self, operator.pow)

    def __mod__(self, other) -> 'Die':
        other = icepool.Die([other])
        return self.binary_op(other, operator.mod)

    def __rmod__(self, other) -> 'Die':
        other = icepool.Die([other])
        return other.binary_op(self, operator.mod)

    def __lshift__(self, other) -> 'Die':
        other = icepool.Die([other])
        return self.binary_op(other, operator.lshift)

    def __rlshift__(self, other) -> 'Die':
        other = icepool.Die([other])
        return other.binary_op(self, operator.lshift)

    def __rshift__(self, other) -> 'Die':
        other = icepool.Die([other])
        return self.binary_op(other, operator.rshift)

    def __rrshift__(self, other) -> 'Die':
        other = icepool.Die([other])
        return other.binary_op(self, operator.rshift)

    def __and__(self, other) -> 'Die':
        other = icepool.Die([other])
        return self.binary_op(other, operator.and_)

    def __rand__(self, other) -> 'Die':
        other = icepool.Die([other])
        return other.binary_op(self, operator.and_)

    def __or__(self, other) -> 'Die':
        other = icepool.Die([other])
        return self.binary_op(other, operator.or_)

    def __ror__(self, other) -> 'Die':
        other = icepool.Die([other])
        return other.binary_op(self, operator.or_)

    def __xor__(self, other) -> 'Die':
        other = icepool.Die([other])
        return self.binary_op(other, operator.xor)

    def __rxor__(self, other) -> 'Die':
        other = icepool.Die([other])
        return other.binary_op(self, operator.xor)

    # Comparators.

    @staticmethod
    def _lt_le(op: Callable, lo: 'Die', hi: 'Die') -> 'Die':
        """Linear algorithm  for < and <=.

        Args:
            op: Either `operator.lt` or `operator.le`.
            lo: The die on the left of `op`.
            hi: The die on the right of `op`.
        """
        if lo.is_empty() or hi.is_empty():
            return icepool.Die([])

        n = 0
        d = lo.denominator() * hi.denominator()

        lo_cweight = 0
        lo_iter = iter(zip(lo.outcomes(), lo.cweights()))
        lo_outcome, next_lo_cweight = next(lo_iter)
        for hi_outcome, hi_weight in hi.items():
            while op(lo_outcome, hi_outcome):
                try:
                    lo_cweight = next_lo_cweight
                    lo_outcome, next_lo_cweight = next(lo_iter)
                except StopIteration:
                    break
            n += lo_cweight * hi_weight
        return icepool.bernoulli(n, d)

    def __lt__(self, other) -> 'Die':
        other = icepool.Die([other])
        return Die._lt_le(operator.lt, self, other)

    def __le__(self, other) -> 'Die':
        other = icepool.Die([other])
        return Die._lt_le(operator.le, self, other)

    def __ge__(self, other) -> 'Die':
        other = icepool.Die([other])
        return Die._lt_le(operator.le, other, self)

    def __gt__(self, other) -> 'Die':
        other = icepool.Die([other])
        return Die._lt_le(operator.lt, other, self)

    # Equality operators. These produce a `DieWithTruth`.

    @staticmethod
    def _eq(invert: bool, a: 'Die', b: 'Die') -> 'Counts':
        """Linear algorithm  for == and !=.

        Args:
            invert: If `False`, this computes ==; if `True` this computes !=.
            a, b: The dice.
        """
        if a.is_empty() or b.is_empty():
            return Counts([])

        n = 0
        d = a.denominator() * b.denominator()

        a_iter = iter(a.items())
        b_iter = iter(b.items())

        a_outcome, a_weight = next(a_iter)
        b_outcome, b_weight = next(b_iter)

        while True:
            try:
                if a_outcome == b_outcome:
                    n += a_weight * b_weight
                    a_outcome, a_weight = next(a_iter)
                    b_outcome, b_weight = next(b_iter)
                elif a_outcome < b_outcome:
                    a_outcome, a_weight = next(a_iter)
                else:
                    b_outcome, b_weight = next(b_iter)
            except StopIteration:
                if invert:
                    return Counts([(False, n), (True, d - n)])
                else:
                    return Counts([(False, d - n), (True, n)])

    def __eq__(self, other):
        other_die = icepool.Die([other])

        def data_callback():
            return Die._eq(False, self, other_die)

        def truth_value_callback():
            return self.equals(other)

        return icepool.DieWithTruth(data_callback, truth_value_callback)

    def __ne__(self, other):
        other_die = icepool.Die([other])

        def data_callback():
            return Die._eq(True, self, other_die)

        def truth_value_callback():
            return not self.equals(other)

        return icepool.DieWithTruth(data_callback, truth_value_callback)

    def cmp(self, other) -> 'Die':
        """Returns a die with possible outcomes 1, -1, and 0.

        The weights are equal to the positive outcome of `self > other`,
        `self < other`, and the remainder respectively.
        """
        other = icepool.Die([other])

        d = self.denominator() * other.denominator()
        lt = (self < other)[True]
        eq = (self == other)[True]
        return Die({-1: lt, 0: eq, 1: d - lt - eq})

    @staticmethod
    def _sign(x) -> int:
        z = Die._zero(x)
        if x > z:
            return 1
        elif x < z:
            return -1
        else:
            return 0

    def sign(self) -> 'Die':
        """Outcomes become 1 if greater than `zero()`, -1 if less than `zero()`, and 0 otherwise.

        Note that for `float`s, +0.0, -0.0, and nan all become 0.
        """
        return self.unary_op(Die._sign)

    def bool(self) -> 'Die':
        """Takes `bool()` of all outcomes.

        Note that a die as a whole is not considered to have a truth value
        unless it is the result of the `==` or `!=` operators.
        """
        return self.unary_op(bool)

    # Equality and hashing.

    def __bool__(self):
        raise ValueError(
            'A die only has a truth value if it is the result of == or !=. '
            'If this is in the conditional of an if-statement, you probably '
            'want to use die.if_else() instead.')

    @cached_property
    def _key_tuple(self) -> tuple:
        return tuple(self.items())

    def key_tuple(self) -> tuple:
        """Returns a tuple that uniquely (as `equals()`) identifies this die.

        Apart from being hashable and totally orderable, this is not guaranteed
        to be in any particular format or have any other properties.
        """
        return self._key_tuple

    @cached_property
    def _hash(self) -> int:
        return hash(self.key_tuple())

    def __hash__(self) -> int:
        return self._hash

    def equals(self, other, *, reduce=False):
        """Returns `True` iff both dice have the same outcomes and weights.

        This is `False` if `other` is not a `Die`, even if it would convert
        to an equal `Die`.

        Truth value does NOT matter.

        If one die has a zero-weight outcome and the other die does not contain
        that outcome, they are treated as unequal by this function.

        The `==` and `!=` operators have a dual purpose; they return a die
        with a truth value determined by this method.
        Only dice returned by these methods have a truth value. The data of
        these dice is lazily evaluated since the caller may only be interested
        in the `Die` value or the truth value.

        Args:
            reduce: If `True`, the dice will be reduced before comparing.
                Otherwise, e.g. a 2:2 coin is not `equals()` to a 1:1 coin.
        """
        if not isinstance(other, Die):
            return False

        if reduce:
            return self.reduce_weights().key_tuple() == other.reduce_weights(
            ).key_tuple()
        else:
            return self.key_tuple() == other.key_tuple()

    # Rolling.

    def sample(self):
        """Returns a random roll of this die.

        Do not use for security purposes.
        """
        # We don't use random.choices since that is based on floats rather than ints.
        r = random.randrange(self.denominator())
        index = bisect.bisect_right(self.cweights(), r)
        return self.outcomes()[index]

    # Strings.

    def __repr__(self) -> str:
        inner = ', '.join(
            f'{outcome}: {weight}' for outcome, weight in self.items())
        return type(self).__qualname__ + '({' + inner + '})'

    def __str__(self) -> str:
        return f'{self}'

    def format(self, format_spec: str, **kwargs) -> str:
        """Formats this die as a string.

        `format_spec` should start with the output format,
        which is either `md` (Markdown) or `csv` (comma-separated values),
        followed by a ':' character.

        After this, zero or more columns should follow. Options are:

        * `o`: Outcomes.
        * `*o`: Outcomes, unpacked if applicable.
        * `w==`, `w<=`, `w>=`: Weights ==, <=, or >= each outcome.
        * `%==`, `%<=`, `%>=`: Chance (%) ==, <=, or >= each outcome.

        Columns may optionally be separated using ` ` (space) or `|` characters.

        The default is `'md:*o|w==|%=='`, with the weight column being omitted
        if any weight exceeds 10**30.
        """
        if len(format_spec) == 0:
            format_spec = 'md:*o'
            if not self.is_empty() and self.modal_weight() < 10**30:
                format_spec += 'w=='
            format_spec += '%=='

        format_spec = format_spec.replace('|', '')

        output_format, format_spec = format_spec.split(':')
        if output_format == 'md':
            return icepool.die.format.markdown(self, format_spec)
        elif output_format == 'csv':
            return icepool.die.format.csv(self, format_spec, **kwargs)
        else:
            raise ValueError(f"Unsupported output format '{output_format}'")

    def __format__(self, format_spec: str) -> str:
        return self.format(format_spec)
