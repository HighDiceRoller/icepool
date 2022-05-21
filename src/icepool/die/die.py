__docformat__ = 'google'

import icepool
import icepool.die.format
from icepool.elementwise import unary_elementwise, binary_elementwise
from icepool.die.create import expand_die_args

import bisect
from collections import defaultdict
from functools import cached_property
import itertools
import math
import operator
import random


class Die():
    """An immutable mapping of outcomes to nonnegative `int` weights.

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

    def __new__(cls, *args, weights=None, denominator_method='lcm'):
        """Constructor for a die.

        Don't confuse this with `icepool.d()`:

        * `icepool.Die(6)`: A die that always rolls the `int` 6.
        * `icepool.d(6)`: A d6.

        Here are some different ways of constructing a d6:

        * Just import it: `from icepool import d6`
        * Use the `d()` function: `icepool.d(6)`
        * Use a d6 that you already have: `Die(d6)`
        * Mix a d3 and a d3+3: `Die(d3, d3+3)`
        * Use a dict: `Die({1:1, 2:1, 3:1, 4:1, 5:1, 6:1})`
        * Give the faces as args: `Die(1, 2, 3, 4, 5, 6)`

        All weights must be non-negative, though they can be zero.

        Args:
            *args: Each of these arguments can be one of the following:
                * A die. The outcomes of the die will be "flattened" into the
                    result; a die object will never contain a die as an outcome.
                * A dict-like that maps outcomes to weights.
                    The outcomes of the dict-like will be "flattened" into the
                    result. This option will be taken in preference to treating
                    the dict-like itself as an outcome even if the dict-like
                    itself is hashable and totally orderable.
                * A tuple of outcomes. Operators on dice with tuple outcomes
                    are performed element-wise. See `Die.unary_op` and
                    `Die.binary_op` for details.

                    Any tuple elements that are dice or dicts will expand the
                    tuple according to their independent joint distribution.
                    For example, (d6, d6) will expand to 36 ordered tuples with
                    weight 1 each. Use this carefully since it may create a
                    large number of outcomes.
                * `icepool.Reroll`, which will drop itself
                    and the corresponding element of `weights` from consideration.
                    If inside a tuple, the tuple will be dropped.
                * Anything else, including non-tuple sequences, will be treated
                    as a single outcome. Each outcome must be hashable, and the
                    set of outcomes must be totally orderable (after expansion).
                    The same outcome can appear multiple times, in which case
                    the corresponding weights will be accumulated.
            weights: Controls the relative weight of the arguments.
                If an argument expands into multiple outcomes, the weight is
                shared among those outcomes. If not provided, each argument will
                end up with the same total weight. For example, `Die(d6, 7)` is
                the same as `Die(1, 2, 3, 4, 5, 6, 7, 7, 7, 7, 7, 7)`.
            denominator_method: How to determine the denominator of the result
                if the arguments themselves contain weights. This is also used
                for dict-like arguments. From greatest to least:
                * 'prod': Product of the individual argument denominators, times
                    the total of `weights`. This is like rolling all of the
                    possible dice, and then selecting a result.
                * 'lcm' (default): LCM of the individual argument denominators,
                    times the total of `weights`. This is like rolling `weights`
                    first, then selecting an argument to roll.
                * 'lcm_weighted': LCM of the individual (argument denominators
                    times corresponding element of `weights`). This is like
                    rolling the above, but the specific weight rolled is used
                    to help determine the result of the selected argument.
                * 'reduce': The final weights are divided by their GCD.
        Raises:
            `ValueError`: `None` is not a valid outcome for a die.
        """
        if weights is None and len(args) == 1 and isinstance(args[0], Die):
            return args[0]
        self = super(Die, cls).__new__(cls)
        self._data = expand_die_args(*args,
                                     weights=weights,
                                     denominator_method=denominator_method)
        return self

    def unary_op(self, op, *args, **kwargs):
        """Performs the unary operation on the outcomes.

        Operations on tuples are performed elementwise recursively. If you need
        some other specific behavior, use your own outcome class, or use `sub()`
        rather than an operator.

        This is used for the standard unary operators
        `-, +, abs, ~, round, trunc, floor, ceil`
        as well as the additional methods
        `zero, bool`.

        This is NOT used for the `[]` operator, which is NOT performed
        element-wise.

        Returns:
            A die representing the result.

        Raises:
            ValueError if tuples are of mismatched length.
        """
        data = defaultdict(int)
        for outcome, weight in self.items():
            new_outcome = unary_elementwise(outcome, op, *args, **kwargs)
            data[new_outcome] += weight
        return icepool.Die(data)

    def unary_op_non_elementwise(self, op, *args, **kwargs):
        """As unary_op, but not elementwise.

        This is used for the `[]` operator.
        """
        data = defaultdict(int)
        for outcome, weight in self.items():
            new_outcome = op(outcome, *args, **kwargs)
            data[new_outcome] += weight
        return icepool.Die(data)

    def binary_op(self, other, op, *args, **kwargs):
        """Performs the operation on pairs of outcomes.

        Operations on tuples are performed elementwise recursively. If you need
        some other specific behavior, use your own outcome class, or use `sub()`
        rather than an operator.

        By the time this is called, the other operand has already been
        converted to a die.

        This is used for the standard binary operators
        `+, -, *, /, //, %, **, <<, >>, &, |, ^, <, <=, >=, >, ==, !=`,
        as well as the additional method `cmp`.
        Note that `*` multiplies outcomes directly;
        it is not the same as `@` or `d()`.

        `==` and `!=` additionally set the truth value of the die according to
        whether the dice themselves are the same or not.

        The `@` operator does NOT use this method directly.
        It rolls the left die, which must have integer outcomes,
        then rolls the right die that many times and sums the outcomes.
        Only the sum is performed  element-wise. Only the left side will be
        converted to a die; the right side must already be a die.

        Returns:
            A die representing the result.

        Raises:
            ValueError if tuples are of mismatched length within one of the dice
            or between the dice.
        """
        data = defaultdict(int)
        for (outcome_self, weight_self), (outcome_other,
                                          weight_other) in itertools.product(
                                              self.items(), other.items()):
            new_outcome = binary_elementwise(outcome_self, outcome_other, op,
                                             *args, **kwargs)
            data[new_outcome] += weight_self * weight_other
        return icepool.Die(data)

    # Basic access.

    def outcomes(self):
        """Returns an iterable into the sorted outcomes of the die. """
        return self._data.keys()

    def __contains__(self, outcome):
        return outcome in self._data

    def num_outcomes(self):
        """Returns the number of outcomes (including those with zero weight). """
        return len(self._data)

    @cached_property
    def _outcome_len(self):
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

    def outcome_len(self):
        """Returns the common length of the outcomes.

        If any outcome has no length, the outcomes have mixed length, or the
        die is empty, the result is `None`.
        """
        return self._outcome_len

    def is_empty(self):
        """Returns `True` if this die has no outcomes. """
        return self.num_outcomes() == 0

    def weights(self):
        """Returns an iterable into the weights of the die in outcome order. """
        return self._data.values()

    def has_zero_weights(self):
        """Returns `True` iff `self` contains at least one outcome with zero weight. """
        return self._data.has_zero_weights()

    def items(self):
        """Returns all outcome, weight pairs. """
        return self._data.items()

    # Weights.

    @cached_property
    def _denominator(self):
        return sum(self._data.values())

    def denominator(self):
        """The total weight of all outcomes. """
        return self._denominator

    total_weight = denominator

    @cached_property
    def _pmf(self):
        return tuple(weight / self.denominator() for weight in self.weights())

    def pmf(self, percent=False):
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
    def _cweights(self):
        return tuple(itertools.accumulate(self.weights()))

    def cweights(self):
        """Cumulative weights. The weight <= each outcome in order. """
        return self._cweights

    @cached_property
    def _sweights(self):
        return tuple(
            itertools.accumulate(self.weights()[:-1],
                                 operator.sub,
                                 initial=self.denominator()))

    def sweights(self):
        """Survival weights. The weight >= each outcome in order. """
        return self._sweights

    @cached_property
    def _cdf(self):
        return tuple(weight / self.denominator() for weight in self.cweights())

    def cdf(self, percent=False):
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

    def sf(self, percent=False):
        """Survival function. The chance of rolling >= each outcome in order.

        Args:
            percent: If set, the results will be in percent (i.e. total of 100.0).
                Otherwise, the total will be 1.0.
        """
        if percent:
            return tuple(100.0 * x for x in self._sf)
        else:
            return self._sf

    def weight_eq(self, outcome):
        """Returns the weight of a single outcome, or 0 if not present. """
        return self._data[outcome]

    def weight_ne(self, outcome):
        """Returns the weight != a single outcome. """
        return self.denominator() - self.weight_eq(outcome)

    def weight_le(self, outcome):
        """Returns the weight <= a single outcome. """
        index = bisect.bisect_right(self.outcomes(), outcome) - 1
        if index < 0:
            return 0
        return self.cweights()[index]

    def weight_lt(self, outcome):
        """Returns the weight < a single outcome. """
        index = bisect.bisect_left(self.outcomes(), outcome) - 1
        if index < 0:
            return 0
        return self.cweights()[index]

    def weight_ge(self, outcome):
        """Returns the weight >= a single outcome. """
        index = bisect.bisect_left(self.outcomes(), outcome)
        if index >= self.num_outcomes():
            return 0
        return self.sweights()[index]

    def weight_gt(self, outcome):
        """Returns the weight > a single outcome. """
        index = bisect.bisect_right(self.outcomes(), outcome)
        if index >= self.num_outcomes():
            return 0
        return self.sweights()[index]

    def probability(self, outcome):
        """Returns the probability of a single outcome. """
        return self.weight_eq(outcome) / self.denominator()

    # Scalar statistics.

    def mode(self):
        """Returns a tuple containing the most common outcome(s) of the die.

        These are sorted from lowest to highest.
        """
        return tuple(outcome for outcome, weight in self.items()
                     if weight == self.modal_weight())

    def modal_weight(self):
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

    def ppf_left(self, n, d=100):
        """Returns a quantile, `n / d` of the way through the cdf.

        If the result lies between two outcomes, returns the lower of the two.
        """
        index = bisect.bisect_left(self.cweights(),
                                   (n * self.denominator() + d - 1) // d)
        if index >= self.num_outcomes():
            return self.max_outcome()
        return self.outcomes()[index]

    def ppf_right(self, n, d=100):
        """Returns a quantile, `n / d` of the way through the cdf.

        If the result lies between two outcomes, returns the higher of the two.
        """
        index = bisect.bisect_right(self.cweights(),
                                    n * self.denominator() // d)
        if index >= self.num_outcomes():
            return self.max_outcome()
        return self.outcomes()[index]

    def ppf(self, n, d=100):
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

    def standardized_moment(self, k):
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

    def covariance(self, i, j):
        mean_i = self[i].mean()
        mean_j = self[j].mean()
        return sum((outcome[i] - mean_i) * (outcome[j] - mean_j) * weight
                   for outcome, weight in self.items()) / self.denominator()

    def correlation(self, i, j):
        sd_i = self[i].standard_deviation()
        sd_j = self[j].standard_deviation()
        return self.covariance(i, j) / (sd_i * sd_j)

    # Weight management.

    def reduce_weights(self):
        """Divides all weights by their greatest common denominator. """
        return icepool.Die(self._data.reduce())

    def scale_weights(self, scale):
        """Multiplies all weights by a constant. """
        if scale < 0:
            raise ValueError('Weights cannot be scaled by a negative number.')
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

    def reroll(self, outcomes=None, *, max_depth=None, star=0):
        """Rerolls the given outcomes.

        Args:
            outcomes: Selects which outcomes to reroll. Options:
                * A callable that takes an outcome and returns `True` if it
                    should be rerolled.
                * A set of outcomes to reroll.
                * If not provided, the min outcome will be rerolled.
            max_depth: The maximum number of times to reroll.
                If omitted, rerolls an unlimited number of times.
            star: If set to `True` or 1, outcomes will be unpacked as
                `*outcome` before giving it to the `outcomes` function.
                If `outcomes` is not a callable, this has no effect.

        Returns:
            A die representing the reroll.
            If the reroll would never terminate, the result has no outcomes.
        """
        if outcomes is None:
            outcomes = {self.min_outcome()}
        elif callable(outcomes):
            if star:
                outcomes = {
                    outcome for outcome in self.outcomes() if outcomes(*outcome)
                }
            else:
                outcomes = {
                    outcome for outcome in self.outcomes() if outcomes(outcome)
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

    def reroll_until(self, outcomes, *, max_depth=None, star=0):
        """Rerolls until getting one of the given outcomes.

        Essentially the complement of `reroll()`.

        Args:
            outcomes: Selects which outcomes to reroll until. Options:
                * A callable that takes an outcome and returns `True` if it
                    should be accepted.
                * A set of outcomes to reroll until.
            max_depth: The maximum number of times to reroll.
                If omitted, rerolls an unlimited number of times.
            star: If set to `True` or 1, outcomes will be unpacked as
                `*outcome` before giving it to the `outcomes` function.
                If `outcomes` is not a callable, this has no effect.

        Returns:
            A die representing the reroll.
            If the reroll would never terminate, the result has no outcomes.
        """
        if callable(outcomes):
            if star:
                not_outcomes = {
                    outcome for outcome in self.outcomes()
                    if not outcomes(*outcome)
                }
            else:
                not_outcomes = {
                    outcome for outcome in self.outcomes()
                    if not outcomes(outcome)
                }
        else:
            not_outcomes = {
                not_outcome for not_outcome in self.outcomes()
                if not_outcome not in outcomes
            }
        return self.reroll(not_outcomes, max_depth=max_depth)

    def truncate(self, min_outcome=None, max_outcome=None):
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

    def clip(self, min_outcome=None, max_outcome=None):
        """Clips the outcomes of this die to the given values.

        The endpoints are included in the result if applicable.
        If one of the arguments is not provided, that side will not be clipped.

        This is not the same as rerolling outcomes beyond this range;
        the outcome is simply adjusted to fit within the range.
        This will typically cause some weight to bunch up at the endpoint.
        If you want to reroll outcomes beyond this range, use `truncate()`.
        """
        data = defaultdict(int)
        for outcome, weight in self.items():
            if min_outcome is not None and outcome <= min_outcome:
                data[min_outcome] += weight
            elif max_outcome is not None and outcome >= max_outcome:
                data[max_outcome] += weight
            else:
                data[outcome] += weight
        return icepool.Die(data)

    def set_outcomes(self, outcomes):
        """Sets the set of outcomes to the argument.

        This may remove outcomes (if they are not present in the argument)
        and/or add zero-weight outcomes (if they are not present in this die).
        """
        data = {x: self.weight_eq(x) for x in outcomes}
        return icepool.Die(data)

    def trim(self):
        """Removes all zero-weight outcomes. """
        data = {k: v for k, v in self.items() if v > 0}
        return icepool.Die(data)

    @cached_property
    def _popped_min(self):
        die = icepool.Die(*self.outcomes()[1:], weights=self.weights()[1:])
        return die, self.outcomes()[0], self.weights()[0]

    def _pop_min(self):
        """Removes the min outcome and return the result, along with the popped outcome, and the popped weight.

        Raises:
            `IndexError` if this die has no outcome to pop.
        """
        return self._popped_min

    @cached_property
    def _popped_max(self):
        die = icepool.Die(*self.outcomes()[:-1], weights=self.weights()[:-1])
        return die, self.outcomes()[-1], self.weights()[-1]

    def _pop_max(self):
        """Removes the max outcome and return the result, along with the popped outcome, and the popped weight.

        Raises:
            `IndexError` if this die has no outcome to pop.
        """
        return self._popped_max

    # Mixtures.

    def sub(self, repl, /, *, max_depth=1, star=0, denominator_method='lcm'):
        """Changes outcomes of the die to other outcomes.

        You can think of this as `sub`stituting outcomes of this die for other
        outcomes or dice. Or, as executing a `sub`routine based on the roll of
        this die.

        Args:
            repl: One of the following:
                * A map from old outcomes to new outcomes.
                    Unmapped old outcomes stay the same.
                * A callable mapping old outcomes to new outcomes.
                The new outcomes may be dice rather than just single outcomes.
                The special value `icepool.Reroll` will reroll that old outcome.
            max_depth: `sub()` will be repeated with the same argument on the
                result this many times. If set to `None`, this will repeat until
                a fixed point is reached.
            star: If set to `True` or 1, outcomes will be unpacked as
                `*outcome` before giving it to the `repl` function. If `repl`
                is not a callable, this has no effect.
            denominator_method: As `icepool.Die()`.

        Returns:
            The relabeled die.
        """
        if max_depth == 0:
            return self
        elif max_depth == 1:
            if hasattr(repl, 'items'):
                repl = [(repl[outcome] if outcome in repl else outcome)
                        for outcome in self.outcomes()]
            elif callable(repl):
                if star:
                    repl = [repl(*outcome) for outcome in self.outcomes()]
                else:
                    repl = [repl(outcome) for outcome in self.outcomes()]

            return icepool.Die(*repl,
                               weights=self.weights(),
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

    def explode(self, outcomes=None, *, max_depth=None, star=0):
        """Causes outcomes to be rolled again and added to the total.

        Args:
            outcomes: Which outcomes to explode. Options:
                * An iterable containing outcomes to explode.
                * A callable that takes an outcome and returns `True` if it
                    should be exploded.
                * If not supplied, the max outcome will explode.
            max_depth: The maximum number of additional dice to roll.
                If not supplied, a default value will be used.
            star: If set to `True` or 1, outcomes will be unpacked as
                `*outcome` before giving it to the `outcomes` function.
                If `outcomes` is not a callable, this has no effect.
        """
        if outcomes is None:
            outcomes = {self.max_outcome()}
        elif callable(outcomes):
            if star:
                outcomes = {
                    outcome for outcome in self.outcomes() if outcomes(*outcome)
                }
            else:
                outcomes = {
                    outcome for outcome in self.outcomes() if outcomes(outcome)
                }

        if len(outcomes) == 0:
            return self

        if max_depth is None:
            max_depth = 9
        elif max_depth < 0:
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
                denominator_method='lcm'):
        """Ternary conditional operator.

        This replaces truthy outcomes with the first argument and falsy outcomes
        with the second argument.
        """
        return self.bool().sub(lambda x: outcome_if_true
                               if x else outcome_if_false,
                               denominator_method=denominator_method)

    # Pools.

    @cached_property
    def _sum_cache(self):
        return {}

    def _sum_all(self, num_dice):
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

    def _sum_truncate(self, truncate_min, truncate_max):
        """Sums truncated copies of this die.

        At least one truncation should be provided.
        """
        if truncate_min is None:
            truncate_min = ()
        elif truncate_max is None:
            truncate_max = ()
        return sum(
            self.truncate(a, b)
            for a, b in itertools.zip_longest(truncate_min, truncate_max))

    def d(self, other):
        """Roll the left die, then roll the right die that many times and sum the outcomes.

        If an `int` is provided for the right side, it becomes a standard die
        with that many faces. Otherwise it is converted to a die.
        """
        if isinstance(other, int):
            other = icepool.standard(other)
        else:
            other = icepool.Die(other)

        data = defaultdict(int)

        max_abs_die_count = max(abs(self.min_outcome()),
                                abs(self.max_outcome()))
        for die_count, die_count_weight in self.items():
            factor = other.denominator()**(max_abs_die_count - abs(die_count))
            subresult = other._sum_all(die_count)
            for outcome, subresult_weight in subresult.items():
                data[outcome] += subresult_weight * die_count_weight * factor

        return icepool.Die(data)

    def pool(self, *args, **kwargs):
        """Creates a pool from this die, as `icepool.Pool()`. """
        return icepool.Pool(self, *args, **kwargs)

    def keep_highest(self,
                     num_dice=None,
                     num_keep=1,
                     num_drop=0,
                     *,
                     truncate_min=None,
                     truncate_max=None):
        """Roll several of this die and sum the sorted results from the highest.

        Exactly one out of `num_dice`, `truncate_min`, and `truncate_max` should
        be provided.

        Args:
            num_dice: The number of dice to roll. All dice will have the same
                outcomes as `self`.
            num_keep: The number of dice to keep.
            num_drop: If provided, this many highest dice will be dropped before
                keeping.
            truncate_min: A sequence of one outcome per die.
                That die will be truncated to that minimum outcome, with all
                lower outcomes being removed (i.e. rerolled).
            truncate_max: A sequence of one outcome per die.
                That die will be truncated to that maximum outcome, with all
                higher outcomes being removed (i.e. rerolled).

        Returns:
            A die representing the probability distribution of the sum.
        """
        if num_keep == 1 and num_drop == 0 and truncate_min is None and truncate_max is None:
            return self._keep_highest_single(num_dice)
        start = -(num_keep + (num_drop or 0))
        stop = -num_drop if num_drop > 0 else None
        count_dice = slice(start, stop)
        return self.pool(num_dice,
                         count_dice=count_dice,
                         truncate_min=truncate_min,
                         truncate_max=truncate_max).sum()

    def _keep_highest_single(self, num_dice=None):
        """Faster algorithm for keeping just the single highest die. """
        if num_dice is None:
            return self.zero()
        return icepool.from_cweights(self.outcomes(),
                                     (x**num_dice for x in self.cweights()))

    def keep_lowest(self,
                    num_dice=None,
                    num_keep=1,
                    num_drop=0,
                    *,
                    truncate_min=None,
                    truncate_max=None):
        """Roll several of this die and sum the sorted results from the lowest.

        Exactly one out of `num_dice`, `truncate_min`, and `truncate_max` should
        be provided.

        Args:
            num_dice: The number of dice to roll. All dice will have the same
                outcomes as `self`.
            num_keep: The number of dice to keep.
            num_drop: If provided, this many lowest dice will be dropped before
                keeping.
            truncate_min: A sequence of one outcome per die.
                That die will be truncated to that minimum outcome, with all
                lower outcomes being removed (i.e. rerolled).
            truncate_max: A sequence of one outcome per die.
                That die will be truncated to that maximum outcome, with all
                higher outcomes being removed (i.e. rerolled).

        Returns:
            A die representing the probability distribution of the sum.
        """
        if num_keep == 1 and num_drop == 0 and truncate_min is None and truncate_max is None:
            return self._keep_lowest_single(num_dice)

        start = num_drop if num_drop > 0 else None
        stop = num_keep + (num_drop or 0)
        count_dice = slice(start, stop)
        return self.pool(num_dice,
                         count_dice=count_dice,
                         truncate_min=truncate_min,
                         truncate_max=truncate_max).sum()

    def _keep_lowest_single(self, num_dice=None):
        """Faster algorithm for keeping just the single lowest die. """
        if num_dice is None:
            return self.zero()
        return icepool.from_sweights(self.outcomes(),
                                     (x**num_dice for x in self.sweights()))

    # Unary operators.

    def __neg__(self):
        return self.unary_op(operator.neg)

    def __pos__(self):
        return self.unary_op(operator.pos)

    def __abs__(self):
        return self.unary_op(operator.abs)

    abs = __abs__

    def __invert__(self):
        return self.unary_op(operator.invert)

    def __round__(self, ndigits=None):
        return self.unary_op(round, ndigits)

    def __trunc__(self):
        return self.unary_op(math.trunc)

    def __floor__(self):
        return self.unary_op(math.floor)

    def __ceil__(self):
        return self.unary_op(math.ceil)

    def marginal(self, index_or_slice, /):
        """Marginal distribution; equivalently, indexes/slices outcomes."""
        return self.unary_op_non_elementwise(operator.getitem, index_or_slice)

    __getitem__ = marginal

    @staticmethod
    def _zero(x):
        return type(x)()

    def zero(self):
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

    def bool(self):
        """Takes `bool()` of all outcomes.

        Note the die as a whole is not considered to have a truth value.
        """
        return self.unary_op(bool)

    # Binary operators.

    def __add__(self, other):
        other = icepool.Die(other)
        return self.binary_op(other, operator.add)

    def __radd__(self, other):
        other = icepool.Die(other)
        return other.binary_op(self, operator.add)

    def __sub__(self, other):
        other = icepool.Die(other)
        return self.binary_op(other, operator.sub)

    def __rsub__(self, other):
        other = icepool.Die(other)
        return other.binary_op(self, operator.sub)

    def __mul__(self, other):
        other = icepool.Die(other)
        return self.binary_op(other, operator.mul)

    def __rmul__(self, other):
        other = icepool.Die(other)
        return other.binary_op(self, operator.mul)

    def __truediv__(self, other):
        other = icepool.Die(other)
        return self.binary_op(other, operator.truediv)

    def __rtruediv__(self, other):
        other = icepool.Die(other)
        return other.binary_op(self, operator.truediv)

    def __floordiv__(self, other):
        other = icepool.Die(other)
        return self.binary_op(other, operator.floordiv)

    def __rfloordiv__(self, other):
        other = icepool.Die(other)
        return other.binary_op(self, operator.floordiv)

    def __pow__(self, other):
        other = icepool.Die(other)
        return self.binary_op(other, operator.pow)

    def __rpow__(self, other):
        other = icepool.Die(other)
        return other.binary_op(self, operator.pow)

    def __mod__(self, other):
        other = icepool.Die(other)
        return self.binary_op(other, operator.mod)

    def __rmod__(self, other):
        other = icepool.Die(other)
        return other.binary_op(self, operator.mod)

    def __lshift__(self, other):
        other = icepool.Die(other)
        return self.binary_op(other, operator.lshift)

    def __rlshift__(self, other):
        other = icepool.Die(other)
        return other.binary_op(self, operator.lshift)

    def __rshift__(self, other):
        other = icepool.Die(other)
        return self.binary_op(other, operator.rshift)

    def __rrshift__(self, other):
        other = icepool.Die(other)
        return other.binary_op(self, operator.rshift)

    def __and__(self, other):
        other = icepool.Die(other)
        return self.binary_op(other, operator.and_)

    def __rand__(self, other):
        other = icepool.Die(other)
        return other.binary_op(self, operator.and_)

    def __or__(self, other):
        other = icepool.Die(other)
        return self.binary_op(other, operator.or_)

    def __ror__(self, other):
        other = icepool.Die(other)
        return other.binary_op(self, operator.or_)

    def __xor__(self, other):
        other = icepool.Die(other)
        return self.binary_op(other, operator.xor)

    def __rxor__(self, other):
        other = icepool.Die(other)
        return other.binary_op(self, operator.xor)

    # Comparators.

    def __lt__(self, other):
        other = icepool.Die(other)
        return self.binary_op(other, operator.lt)

    def __le__(self, other):
        other = icepool.Die(other)
        return self.binary_op(other, operator.le)

    def __ge__(self, other):
        other = icepool.Die(other)
        return self.binary_op(other, operator.ge)

    def __gt__(self, other):
        other = icepool.Die(other)
        return self.binary_op(other, operator.gt)

    # Equality operators. These additionally set the truth value of the result.

    def __eq__(self, other):
        other = icepool.Die(other)
        result = self.binary_op(other, operator.eq)
        result._truth_value = self.equals(other)
        return result

    def __ne__(self, other):
        other = icepool.Die(other)
        result = self.binary_op(other, operator.ne)
        result._truth_value = not self.equals(other)
        return result

    @staticmethod
    def _sign(x):
        z = Die._zero(x)
        if x > z:
            return 1
        elif x < z:
            return -1
        else:
            return 0

    def sign(self):
        """Outcomes become 1 if greater than `zero()`, -1 if less than `zero()`, and 0 otherwise.

        Note that for `float`s, +0.0, -0.0, and nan all become 0.
        """
        return self.unary_op(Die._sign)

    @staticmethod
    def _cmp(x, y):
        return Die._sign(x - y)

    def cmp(self, other):
        """Returns a die with possible outcomes 1, -1, and 0.

        The weights are equal to the positive outcome of `self > other`,
        `self < other`, and the remainder respectively.
        """
        return self.binary_op(other, Die._cmp)

    # Special operators.

    def __matmul__(self, other):
        """Roll the left die, then roll the right die that many times and sum the outcomes.

        Unlike other operators, this does not work for built-in types on the right side.
        For example, `1 @ 6` does not work, nor does `d(6) @ 6`. But `1 @ d(6)` works.

        This is because all other operators convert their right side to a die
        using die, so `6` would become a constant 6, while  `d()` converts
        `int`s to a standard die with that many sides, so `6` would become a d6.
        Thus the right-side conversion of `@` would be ambiguous.
        """
        if not isinstance(other, icepool.Die):
            raise TypeError(
                f'The @ operator will not automatically convert the right side of type {type(other).__qualname__} to a die.'
            )
        return self.d(other)

    def __rmatmul__(self, other):
        """Roll the left die, then roll the right die that many times and sum the outcomes.

        Unlike other operators, this does not work for built-in types on the right side.
        For example, `1 @ 6` does not work, nor does `d(6) @ 6`. But `1 @ d(6)` works.

        This is because all other operators convert their right side to a die
        using `Die()`, so `6` would become a constant 6, while  `d()` converts
        `int`s to a standard die with that many sides, so `6` would become a d6.
        Thus the right-side conversion of `@` would be ambiguous.
        """
        other = icepool.Die(other)
        return other.d(self)

    # Rolling.

    def sample(self):
        """Returns a random roll of this die.

        Do not use for security purposes.
        """
        # We don't use random.choices since that is based on floats rather than ints.
        r = random.randrange(self.denominator())
        index = bisect.bisect_right(self.cweights(), r)
        return self.outcomes()[index]

    # Invalid operations.

    def __iter__(self):
        raise TypeError('A die is not iterable.')

    def __len__(self):
        raise TypeError(
            'len() of a die is ambiguous. Use die.num_outcomes() or die.outcome_len() instead.'
        )

    def __reversed__(self):
        raise TypeError('A die cannot be reversed.')

    # Equality and hashing.

    def __bool__(self):
        if hasattr(self, '_truth_value'):
            return self._truth_value
        else:
            raise ValueError(
                'A die only has a truth value if it is the result of == or !=. '
                'If this is in the conditional of an if-statement, you probably '
                'want to use die.if_else() instead.')

    @cached_property
    def _key_tuple(self):
        return tuple(self.items())

    def key_tuple(self):
        """Returns a tuple that uniquely (as `equals()`) identifies this die. """
        return self._key_tuple

    @cached_property
    def _hash(self):
        return hash(self.key_tuple())

    def __hash__(self):
        return self._hash

    def equals(self, other, *, reduce=False):
        """Returns `True` iff both dice have the same outcomes and weights.

        Truth value does NOT matter.

        If one die has a zero-weight outcome and the other die does not contain
        that outcome, they are treated as unequal by this function.

        The `==` and `!=` operators have a dual purpose; they return a die
        representing the result of the operator as normal,
        but the die additionally has a truth value determined by this method.
        Only dice returned by these methods have a truth value.

        Args:
            reduce: If `True`, the dice will be reduced before comparing.
                Otherwise, e.g. a 2:2 coin is not `equals()` to a 1:1 coin.
        """
        try:
            other = icepool.Die(other)
        except ValueError:
            return False

        if reduce:
            return self.reduce_weights().key_tuple() == other.reduce_weights(
            ).key_tuple()
        else:
            return self.key_tuple() == other.key_tuple()

    # Strings.

    def __repr__(self):
        inner = ', '.join(
            f'{outcome}: {weight}' for outcome, weight in self.items())
        return type(self).__qualname__ + '({' + inner + '})'

    def __str__(self):
        return self.format_markdown(include_weights=self.denominator() < 10**30)

    def format_markdown(self, *, include_weights=True, unpack_outcomes=True):
        """Formats the die as a Markdown table.

        Args:
            include_weights: If `True`, a column will be emitted for the weights.
                Otherwise, only probabilities will be emitted.
            unpack_outcomes: If `True` and all outcomes have a common length,
                outcomes will be unpacked, producing one column per element.
        """
        return icepool.die.format.markdown(self,
                                           include_weights=include_weights,
                                           unpack_outcomes=unpack_outcomes)

    def format_csv(self,
                   *,
                   include_weights=True,
                   unpack_outcomes=True,
                   dialect='excel',
                   **fmtparams):
        """Formats the die as a comma-separated-values string.

        Args:
            include_weights: If `True`, a column will be emitted for the
                weights. Otherwise, only probabilities will be emitted.
            unpack_outcomes: If `True` and all outcomes have a common length,
                outcomes will be unpacked, producing one column per element.
            dialect, **fmtparams: Will be sent to `csv.writer()`.
        """
        return icepool.die.format.csv(self,
                                      include_weights=include_weights,
                                      unpack_outcomes=unpack_outcomes,
                                      dialect=dialect,
                                      **fmtparams)
