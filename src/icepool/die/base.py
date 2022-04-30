__docformat__ = 'google'

import icepool
from icepool.collections import Slicer, Counts

from abc import ABC, abstractmethod
import bisect
from collections import defaultdict
from functools import cache, cached_property
import itertools
import math
import operator
import random


class BaseDie():
    """ Abstract base class for a die.
    
    A die is a sorted mapping of outcomes to `int` weights.
    
    Dice are immutable. Methods do not modify the die in-place;
    rather they return a die representing the result.
    
    It *is* (mostly) well-defined to have a die with zero-weight outcomes,
    even though this is not a proper probability distribution.
    These can be useful in a few cases, such as:
    
    * `DicePool` and `EvalPool` will iterate through zero-weight outcomes with 0 `count`,
        rather than `None` or skipping that outcome.
    * `icepool.align()` and the like are convenient for making dice share the same set of outcomes.
    
    However, zero-weight outcomes have a computational cost like any other outcome.
    Unless you have a specific use case in mind, it's best to leave them out if not necessary.
    
    Most operators and methods will not introduce zero-weight outcomes if their arguments do not have any.
    
    It's also possible to have "empty" dice with no outcomes at all,
    though these have little use other than being sentinel values.
    """

    @abstractmethod
    def ndim(self):
        """ Returns the number of dimensions if this is a `VectorDie`.
        
        Otherwise, returns `'icepool.Scalar'` for a `ScalarDie` and `'icepool.Empty'` for an `EmptyDie`.
        """

    # Abstract methods.

    @abstractmethod
    def _unary_op(self, op, *args, **kwargs):
        """ Returns a die representing the effect of performing the operation on the outcomes.
        
        This is used for the operators `-, +, abs, ~, round, trunc, floor, ceil`.
        """

    @abstractmethod
    def _binary_op(self, other, op, *args, **kwargs):
        """ Returns a die representing the effect of performing the operation on pairs of outcomes from the two dice.
        
        The other operand is cast to a die (using `icepool.Die`) before performing the operation.
        
        This is used for the operators `+, -, *, /, //, %, **, <<, >>, &, |, ^, <, <=, >=, >, ==, !=`.
        Note that `*` multiplies outcomes directly; it is not the same as `@` or `d()`.
        
        Special operators:
            * The `@` operator rolls the left die, then rolls the right die that many times and sums the outcomes.
                Only the left side will be cast to a die; the right side must already be a die.
            * `==` and `!=` are applied across outcomes like the other operators.
                They also set the truth value of the die according to whether the die themselves are the same.
        """

    @abstractmethod
    def _wrap_unpack(self, func):
        """ Possibly wraps `func` so that outcomes are unpacked before giving it to `func`. """

    @abstractmethod
    def markdown(self, include_weights=True):
        """ Formats the die as a Markdown string. 
        
        This will have the denominator and a table of outcomes and their probabilities.
        
        Args:
            include_weights: Iff `True`, the table will have a column for weights.
        """

    # Basic access.

    def outcomes(self):
        """ Returns an iterable into the sorted outcomes of the die. """
        return self._data.keys()

    def __contains__(self, outcome):
        return outcome in self._data

    def num_outcomes(self):
        """ Returns the number of outcomes (including those with zero weight). """
        return len(self._data)

    __len__ = num_outcomes

    def is_empty(self):
        """ Returns `True` if this die has no outcomes. """
        return self.num_outcomes() == 0

    def weights(self):
        """ Returns an iterable into the weights of the die in outcome order. """
        return self._data.values()

    def has_zero_weights(self):
        """ Returns `True` iff `self` contains at least one outcome with zero weight. """
        return self._data.has_zero_weights()

    def items(self):
        """ Returns all outcome, weight pairs. """
        return self._data.items()

    # Weights.

    @cached_property
    def _denominator(self):
        return sum(self._data.values())

    def denominator(self):
        """ The total weight of all outcomes. """
        return self._denominator

    total_weight = denominator

    @cached_property
    def _pmf(self):
        return tuple(weight / self.denominator() for weight in self.weights())

    def pmf(self, percent=False):
        """ Probability mass function. The probability of rolling each outcome in order. 
        
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
        """ Cumulative weights. The weight <= each outcome in order. """
        return self._cweights

    @cached_property
    def _sweights(self):
        return tuple(
            itertools.accumulate(self.weights()[:-1],
                                 operator.sub,
                                 initial=self.denominator()))

    def sweights(self):
        """ Survival weights. The weight >= each outcome in order. """
        return self._sweights

    @cached_property
    def _cdf(self):
        return tuple(weight / self.denominator() for weight in self.cweights())

    def cdf(self, percent=False):
        """ Cumulative distribution function. The chance of rolling <= each outcome in order. 
        
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
        """ Survival function. The chance of rolling >= each outcome in order. 
        
        Args:
            percent: If set, the results will be in percent (i.e. total of 100.0).
                Otherwise, the total will be 1.0.
        """
        if percent:
            return tuple(100.0 * x for x in self._sf)
        else:
            return self._sf

    def weight_eq(self, outcome):
        """ Returns the weight of a single outcome, or 0 if not present. """
        return self._data[outcome]

    def weight_ne(self, outcome):
        """ Returns the weight != a single outcome. """
        return self.denominator() - self.weight_eq(outcome)

    def weight_le(self, outcome):
        """ Returns the weight <= a single outcome. """
        index = bisect.bisect_right(self.outcomes(), outcome) - 1
        if index < 0:
            return 0
        return self.cweights()[index]

    def weight_lt(self, outcome):
        """ Returns the weight < a single outcome. """
        index = bisect.bisect_left(self.outcomes(), outcome) - 1
        if index < 0:
            return 0
        return self.cweights()[index]

    def weight_ge(self, outcome):
        """ Returns the weight >= a single outcome. """
        index = bisect.bisect_left(self.outcomes(), outcome)
        if index >= self.num_outcomes():
            return 0
        return self.sweights()[index]

    def weight_gt(self, outcome):
        """ Returns the weight > a single outcome. """
        index = bisect.bisect_right(self.outcomes(), outcome)
        if index >= self.num_outcomes():
            return 0
        return self.sweights()[index]

    def probability(self, outcome):
        """ Returns the probability of a single outcome. """
        return self.weight_eq(outcome) / self.denominator()

    # Scalar(-ish) statistics.

    def mode(self):
        """ Returns a tuple containing the most common outcome(s) of the die.
        
        These are sorted from lowest to highest.
        """
        return tuple(outcome for outcome, weight in self.items()
                     if weight == self.modal_weight())

    def modal_weight(self):
        """ The highest weight of any single outcome. """
        return max(self.weights())

    def ks_stat(self, other):
        """ Kolmogorov–Smirnov stat. The maximum absolute difference between CDFs. """
        a, b = icepool.align(self, other)
        return max(abs(a - b) for a, b in zip(a.cdf(), b.cdf()))

    def cvm_stat(self, other):
        """ Cramér-von Mises stat. The sum-of-squares difference between CDFs. """
        a, b = icepool.align(self, other)
        return sum((a - b)**2 for a, b in zip(a.cdf(), b.cdf()))

    # Weight management.

    def reduce(self):
        """ Divides all weights by their greatest common denominator. """
        gcd = math.gcd(*self.weights())
        if gcd <= 1:
            return self
        data = {outcome: weight // gcd for outcome, weight in self.items()}
        return icepool.Die(data, ndim=self.ndim())

    def scale_weights(self, scale):
        """ Multiplies all weights by a constant. """
        if scale < 0:
            raise ValueError('Weights cannot be scaled by a negative number.')
        data = {outcome: scale * weight for outcome, weight in self.items()}
        return icepool.Die(data, ndim=self.ndim())

    # Rerolls and other outcome management.

    def min_outcome(*dice):
        """ Returns the minimum possible outcome among the dice. """
        return min(die.outcomes()[0] for die in dice)

    def max_outcome(*dice):
        """ Returns the maximum possible outcome among the dice. """
        return max(die.outcomes()[-1] for die in dice)

    def nearest_le(self, outcome):
        """ Returns the nearest outcome that is <= the argument. 
        
        Returns `None` if there is no such outcome.
        """
        index = bisect.bisect_right(self.outcomes(), outcome) - 1
        if index < 0:
            return None
        return self.outcomes()[index]

    def nearest_ge(self, outcome):
        """ Returns the nearest outcome that is >= the argument. 
        
        Returns `None` if there is no such outcome.
        """
        index = bisect.bisect_left(self.outcomes(), outcome)
        if index >= self.num_outcomes():
            return None
        return self.outcomes()[index]

    def reroll(self, outcomes=None, *, max_depth=None):
        """ Rerolls the given outcomes.
        
        Args:
            outcomes: Selects which outcomes to reroll. Options:
                * A callable that takes an outcome and returns `True` if it should be rerolled.
                    The callable will be supplied with one argument per `ndim` if this is a `VectorDie`.
                * A set of outcomes to reroll.
                * If not provided, the min outcome will be rerolled.
            max_depth: The maximum number of times to reroll.
                If omitted, rerolls an unlimited number of times.
        
        Returns:
            A die representing the reroll.
            If the reroll would never terminate, the result has no outcomes.
        """
        if outcomes is None:
            outcomes = {self.min_outcome()}
        elif callable(outcomes):
            func = self._wrap_unpack(outcomes)
            outcomes = {outcome for outcome in self.outcomes() if func(outcome)}

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
        return icepool.Die(data, ndim=self.ndim())

    def reroll_until(self, outcomes, *, max_depth=None):
        """ Rerolls until getting one of the given outcomes.
        
        Essentially the complement of `reroll()`.
        
        Args:
            outcomes: Selects which outcomes to reroll until. Options:
                * A callable that takes an outcome and returns `True` if it should be accepted.
                * A set of outcomes to reroll until.
            max_depth: The maximum number of times to reroll.
                If omitted, rerolls an unlimited number of times.
        
        Returns:
            A die representing the reroll.
            If the reroll would never terminate, the result has no outcomes.
        """
        if callable(outcomes):
            func = self._wrap_unpack(outcomes)
            not_outcomes = {
                outcome for outcome in self.outcomes() if not func(outcome)
            }
        else:
            not_outcomes = {
                not_outcome for not_outcome in self.outcomes()
                if not_outcome not in outcomes
            }
        return self.reroll(not_outcomes, max_depth=max_depth)

    def truncate(self, min_outcome=None, max_outcome=None):
        """ Truncates the outcomes of this die to the given range.
        
        The endpoints are included in the result if applicable.
        If one of the arguments is not provided, that side will not be truncated.
        
        This effectively rerolls outcomes outside the given range.
        If instead you want to replace those outcomes with the nearest endpoint, use `clip()`.
        
        Not to be confused with `trunc(die)`, which performs integer truncation on each outcome.
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
        return icepool.Die(data, ndim=self.ndim())

    def clip(self, min_outcome=None, max_outcome=None):
        """ Clips the outcomes of this die to the given values.
        
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
        return icepool.Die(data, ndim=self.ndim())

    def set_outcomes(self, outcomes):
        """ Sets the set of outcomes to the argument.
        
        This may remove outcomes (if they are not present in the argument)
        and/or add zero-weight outcomes (if they are not present in this die).
        """
        data = {x: self.weight_eq(x) for x in outcomes}
        return icepool.Die(data, ndim=self.ndim())

    def trim(self):
        """ Removes all zero-weight outcomes. """
        data = {k: v for k, v in self.items() if v > 0}
        return icepool.Die(data, ndim=self.ndim())

    @cached_property
    def _popped_min(self):
        die = icepool.Die(*self.outcomes()[1:], weights=self.weights()[1:])
        return die, self.outcomes()[0], self.weights()[0]

    def _pop_min(self):
        """ Remove the min outcome and return the result, along with the popped outcome, and the popped weight.
        
        Raises:
            `IndexError` if this die has no outcome to pop.
        """
        return self._popped_min

    @cached_property
    def _popped_max(self):
        die = icepool.Die(*self.outcomes()[:-1], weights=self.weights()[:-1])
        return die, self.outcomes()[-1], self.weights()[-1]

    def _pop_max(self):
        """ Remove the max outcome and return the result, along with the popped outcome, and the popped weight.
        
        Raises:
            `IndexError` if this die has no outcome to pop.
        """
        return self._popped_max

    # Mixtures.

    def sub(self, repl, /, *, max_depth=1, ndim=None, denominator_method='lcm'):
        """ Changes outcomes of the die to other outcomes.
        
        You can think of this as `sub`stituting outcomes of this die for other outcomes or dice.
        Or, as executing a `sub`routine based on the roll of this die.
        
        Args:
            repl: One of the following:
                * A map from old outcomes to new outcomes.
                    Unmapped old outcomes stay the same.
                * A callable mapping old outcomes to new outcomes.
                    The callable will be supplied with one argument per `ndim` if this is a `VectorDie`.
                The new outcomes may be dice rather than just single outcomes.
                The special value `icepool.Reroll` will reroll that old outcome.
            max_depth: `sub()` will be repeated with the same argument on the result this many times.
                If set to `None`, this will repeat until a fixed point is reached.
            ndim: Sets the `ndim` of the result. If not provided, `ndim` will be determined automatically.
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
                repl = self._wrap_unpack(repl)
                repl = [repl(outcome) for outcome in self.outcomes()]

            return icepool.Die(*repl,
                               weights=self.weights(),
                               ndim=ndim,
                               denominator_method=denominator_method)
        elif max_depth is not None:
            next = self.sub(repl,
                            max_depth=1,
                            ndim=ndim,
                            denominator_method=denominator_method)
            return next.sub(repl,
                            max_depth=max_depth - 1,
                            ndim=ndim,
                            denominator_method=denominator_method)
        else:
            # Seek fixed point.
            next = self.sub(repl,
                            max_depth=1,
                            ndim=ndim,
                            denominator_method=denominator_method)
            if self.reduce().equals(next.reduce()):
                return self
            else:
                return next.sub(repl,
                                max_depth=None,
                                ndim=ndim,
                                denominator_method=denominator_method)

    def explode(self, outcomes=None, *, max_depth=None):
        """ Causes outcomes to be rolled again and added to the total.
        
        Args:
            outcomes: Which outcomes to explode. Options:
                * An iterable containing outcomes to explode.
                * A callable that takes an outcome and returns `True` if it should be exploded.
                    The callable will be supplied with one argument per `ndim` if this is a `VectorDie`.
                * If not supplied, the max outcome will explode.
            max_depth: The maximum number of additional dice to roll.
                If not supplied, a default value will be used.
        """
        if outcomes is None:
            outcomes = {self.max_outcome()}
        elif callable(outcomes):
            func = self._wrap_unpack(outcomes)
            outcomes = {outcome for outcome in self.outcomes() if func(outcome)}

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

        return self.sub(sub_func, ndim=self.ndim(), denominator_method='lcm')

    # Pools.

    def lowest(*dice):
        """ Roll all the dice and take the lowest.
        
        The maximum outcome is equal to the highest maximum outcome among all input dice.
        """
        dice, ndim = icepool.dice_with_common_ndim(*dice)
        max_outcome = min(die.max_outcome() for die in dice)
        dice = [die.clip(max_outcome=max_outcome) for die in dice]
        dice = icepool.align(*dice)
        sweights = tuple(
            math.prod(t) for t in zip(*(die.sweights() for die in dice)))
        return icepool.from_sweights(dice[0].outcomes(), sweights, ndim=ndim)

    def highest(*dice):
        """ Roll all the dice and take the highest.
        
        The minimum outcome is equal to the highest minimum outcome among all input dice.
        """
        dice, ndim = icepool.dice_with_common_ndim(*dice)
        min_outcome = max(die.min_outcome() for die in dice)
        dice = [die.clip(min_outcome=min_outcome) for die in dice]
        dice = icepool.align(*dice)
        cweights = tuple(
            math.prod(t) for t in zip(*(die.cweights() for die in dice)))
        return icepool.from_cweights(dice[0].outcomes(), cweights, ndim=ndim)

    @cached_property
    def _repeat_and_sum_cache(self):
        return {}

    def repeat_and_sum(self, num_dice):
        """ Roll this die `num_dice` times and sum the results. 
        
        If `num_dice` is negative, roll the die `abs(num_dice)` times and negate the result.
        """
        if num_dice in self._repeat_and_sum_cache:
            return self._repeat_and_sum_cache[num_dice]

        if num_dice < 0:
            result = -self.repeat_and_sum(-num_dice)
        elif num_dice == 0:
            result = self.zero()
        elif num_dice == 1:
            result = self
        else:
            # Binary split seems to perform much worse.
            result = self + self.repeat_and_sum(num_dice - 1)

        self._repeat_and_sum_cache[num_dice] = result
        return result

    def pool(self, *args, **kwargs):
        """ Creates a pool from this die, as `icepool.Pool()`. """
        return icepool.Pool(self, *args, **kwargs)

    def keep(self,
             num_dice=None,
             count_dice=None,
             *,
             truncate_min=None,
             truncate_max=None):
        """ Roll this die several times, possibly truncating the maximum outcomes, and sum some or all of the sorted results.
        
        Args:
            num_dice: The number of dice to roll. All dice will have the same outcomes as `self`.
            count_dice: Only dice selected by this will be counted.
                See `DicePool.count_dice()` for details.
            truncate_min: A sequence of one outcome per die.
                That die will be truncated to that minimum outcome, with all lower outcomes being removed (i.e. rerolled).
                This is not compatible with `truncate_max`.
            truncate_max: A sequence of one outcome per die.
                That die will be truncated to that maximum outcome, with all higher outcomes being removed (i.e. rerolled).
                This is not compatible with `truncate_min`.
                
        Returns:
            A Die representing the probability distribution of the sum.
        """
        pool = icepool.Pool(self,
                            num_dice,
                            count_dice=count_dice,
                            truncate_min=truncate_min,
                            truncate_max=truncate_max)
        if isinstance(count_dice, int):
            return pool
        else:
            return pool.sum()

    def keep_highest(self,
                     num_dice=None,
                     num_keep=1,
                     num_drop=0,
                     *,
                     truncate_min=None,
                     truncate_max=None):
        """ Roll this die several times, possibly truncating the maximum outcomes, and sum the sorted results from the highest.
        
        Exactly one out of `num_dice`, `truncate_min`, and `truncate_max` should be provided.
        
        Args:
            num_dice: The number of dice to roll. All dice will have the same outcomes as `self`.
            num_keep: The number of dice to keep.
            num_drop: If provided, this many highest dice will be dropped before keeping.
            truncate_min: A sequence of one outcome per die.
                That die will be truncated to that minimum outcome, with all lower outcomes being removed (i.e. rerolled).
            truncate_max: A sequence of one outcome per die.
                That die will be truncated to that maximum outcome, with all higher outcomes being removed (i.e. rerolled).
                
        Returns:
            A die representing the probability distribution of the sum.
        """
        if num_keep == 1 and num_drop == 0 and truncate_min is None and truncate_max is None:
            return self.keep_highest_single(num_dice)
        start = -(num_keep + (num_drop or 0))
        stop = -num_drop if num_drop > 0 else None
        count_dice = slice(start, stop)
        return self.keep(num_dice,
                         count_dice,
                         truncate_min=truncate_min,
                         truncate_max=truncate_max)

    def keep_highest_single(self, num_dice=None):
        """ Faster algorithm for keeping just the single highest die. """
        if num_dice is None:
            return self.zero()
        return icepool.from_cweights(self.outcomes(),
                                     (x**num_dice for x in self.cweights()),
                                     ndim=self.ndim())

    def keep_lowest(self,
                    num_dice=None,
                    num_keep=1,
                    num_drop=0,
                    *,
                    truncate_min=None,
                    truncate_max=None):
        """ Roll this die several times, possibly capping the maximum outcomes, and sum the sorted results from the lowest.
        
        Exactly one out of `num_dice`, `truncate_min`, and `truncate_max` should be provided.
        
        Args:
            num_dice: The number of dice to roll. All dice will have the same outcomes as `self`.
            num_keep: The number of dice to keep.
            num_drop: If provided, this many lowest dice will be dropped before keeping.
            truncate_min: A sequence of one outcome per die.
                That die will be truncated to that minimum outcome, with all lower outcomes being removed (i.e. rerolled).
            truncate_max: A sequence of one outcome per die.
                That die will be truncated to that maximum outcome, with all higher outcomes being removed (i.e. rerolled).
                
        Returns:
            A die representing the probability distribution of the sum.
        """
        if num_keep == 1 and num_drop == 0 and truncate_min is None and truncate_max is None:
            return self.keep_lowest_single(num_dice)
        start = num_drop if num_drop > 0 else None
        stop = num_keep + (num_drop or 0)
        count_dice = slice(start, stop)
        return self.keep(num_dice,
                         count_dice,
                         truncate_min=truncate_min,
                         truncate_max=truncate_max)

    def keep_lowest_single(self, num_dice=None):
        """ Faster algorithm for keeping just the single lowest die. """
        if num_dice is None:
            return self.zero()
        return icepool.from_sweights(self.outcomes(),
                                     (x**num_dice for x in self.sweights()),
                                     ndim=self.ndim())

    # Unary operators.

    def __neg__(self):
        return self._unary_op(operator.neg)

    def __pos__(self):
        return self._unary_op(operator.pos)

    def __abs__(self):
        return self._unary_op(operator.abs)

    abs = __abs__

    def __invert__(self):
        return self._unary_op(operator.invert)

    def __round__(self, ndigits=None):
        return self._unary_op(round, ndigits)

    def __trunc__(self):
        return self._unary_op(math.trunc)

    def __floor__(self):
        return self._unary_op(math.floor)

    def __ceil__(self):
        return self._unary_op(math.ceil)

    @staticmethod
    def _zero(x):
        return type(x)()

    def zero(self):
        """ Zeros all outcomes of this die. 
        
        This is done by calling the constructor for each outcome's type with no arguments.
        
        The result will have a single outcome with weight 1.
        
        Raises:
            `ValueError` if the zeros did not resolve to a single outcome.
        """
        result = self._unary_op(BaseDie._zero)
        if result.num_outcomes() != 1:
            raise ValueError('zero() did not resolve to a single outcome.')
        return result.reduce()

    def zero_outcome(self):
        """ Returns a zero-outcome for this die, e.g. `0` for a die whose outcomes are `int`s. """
        return self.zero().outcomes()[0]

    def bool(self):
        """ Takes `bool()` of all outcomes.
        
        Note the die as a whole is not considered to have a truth value.
        """
        return self._unary_op(bool)

    # Binary operators.

    def __add__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return self._binary_op(other, operator.add)

    def __radd__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return other._binary_op(self, operator.add)

    def __sub__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return self._binary_op(other, operator.sub)

    def __rsub__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return other._binary_op(self, operator.sub)

    def __mul__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return self._binary_op(other, operator.mul)

    def __rmul__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return other._binary_op(self, operator.mul)

    def __truediv__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return self._binary_op(other, operator.truediv)

    def __rtruediv__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return other._binary_op(self, operator.truediv)

    def __floordiv__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return self._binary_op(other, operator.floordiv)

    def __rfloordiv__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return other._binary_op(self, operator.floordiv)

    def __pow__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return self._binary_op(other, operator.pow)

    def __rpow__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return other._binary_op(self, operator.pow)

    def __mod__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return self._binary_op(other, operator.mod)

    def __rmod__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return other._binary_op(self, operator.mod)

    def __lshift__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return self._binary_op(other, operator.lshift)

    def __rlshift__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return other._binary_op(self, operator.lshift)

    def __rshift__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return self._binary_op(other, operator.rshift)

    def __rrshift__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return other._binary_op(self, operator.rshift)

    def __and__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return self._binary_op(other, operator.and_)

    def __rand__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return other._binary_op(self, operator.and_)

    def __or__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return self._binary_op(other, operator.or_)

    def __ror__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return other._binary_op(self, operator.or_)

    def __xor__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return self._binary_op(other, operator.xor)

    def __rxor__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return other._binary_op(self, operator.xor)

    # Comparators.

    def __lt__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return self._binary_op(other, operator.lt)

    def __le__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return self._binary_op(other, operator.le)

    def __ge__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return self._binary_op(other, operator.ge)

    def __gt__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        return self._binary_op(other, operator.gt)

    # Equality operators. These additionally set the truth value of the result.

    def __eq__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        result = self._binary_op(other, operator.eq)
        result._truth_value = self.equals(other)
        return result

    def __ne__(self, other):
        other = icepool.Die(other, ndim=self.ndim())
        result = self._binary_op(other, operator.ne)
        result._truth_value = not self.equals(other)
        return result

    @staticmethod
    def _sign(x):
        z = BaseDie._zero(x)
        if x > z:
            return 1
        elif x < z:
            return -1
        else:
            return 0

    def sign(self):
        """ Outcomes become 1 if greater than `zero()`, -1 if less than `zero()`, and 0 otherwise.
        
        Note that for `float`s, +0.0, -0.0, and nan all become 0.
        """
        return self._unary_op(BaseDie._sign)

    @staticmethod
    def _cmp(x, y):
        return BaseDie._sign(x - y)

    def cmp(self, other):
        """ Returns a die with possible outcomes 1, -1, and 0.
        
        The weights are equal to the positive outcome of `self > other`, `self < other`, and the remainder respectively.
        """
        return self._binary_op(other, BaseDie._cmp)

    # Special operators.

    def __rmatmul__(self, other):
        """ Roll the left die, then roll the right die that many times and sum the outcomes. 
        
        Unlike other operators, this does not work for built-in types on the right side.
        For example, `1 @ 6` does not work, nor does `d(6) @ 6`. But `1 @ d(6)` works.
        
        This is because all other operators convert their right side to a die using die,
        so `6` would become a constant 6, while  `d()` converts `int`s to a standard die with that many sides,
        so `6` would become a d6. Thus the right-side conversion of `@` would be ambiguous.
        """
        other = icepool.Die(other, ndim=self.ndim())
        return other.d(self)

    # Rolling.

    def sample(self):
        """ Returns a random roll of this die. 
        
        Do not use for security purposes.
        """
        # We don't use random.choices since that is based on floats rather than ints.
        r = random.randrange(self.denominator())
        index = bisect.bisect_right(self.cweights(), r)
        return self.outcomes()[index]

    # Invalid operations.

    def __reversed__(self):
        raise TypeError('A die cannot be reversed.')

    # Equality and hashing.

    def __bool__(self):
        if hasattr(self, '_truth_value'):
            return self._truth_value
        else:
            raise ValueError(
                'A die only has a truth value if it is the result of == or !=. If this is in the conditional of an if-statement, you probably want to use die.if_else() instead.'
            )

    @cached_property
    def _key_tuple(self):
        return tuple(self.items()), self.ndim()

    def key_tuple(self):
        """ Returns a tuple that uniquely (as `equals()`) identifies this die. """
        return self._key_tuple

    @cached_property
    def _hash(self):
        return hash(self.key_tuple())

    def __hash__(self):
        return self._hash

    def equals(self, other, *, reduce=False):
        """ Returns `True` iff both dice have the same ndim, outcomes, and weights. Truth value does NOT matter.
        
        If one die has a zero-weight outcome and the other die does not contain that outcome,
        they are treated as unequal by this function.
        
        The `==` and `!=` operators have a dual purpose; they return a die representing the result of the operator as normal,
        but the die additionally has a truth value determined by this method.
        Only dice returned by these methods have a truth value.
        
        Args:
            reduce: If `True`, the dice will be reduced before comparing.
                Otherwise, e.g. a 2:2 coin is not `equals()` to a 1:1 coin. 
        """
        try:
            other = icepool.Die(other, ndim=self.ndim())
        except ValueError:
            return False

        if reduce:
            return self.reduce().key_tuple() == other.reduce().key_tuple()
        else:
            return self.key_tuple() == other.key_tuple()

    # Strings.

    def __str__(self):
        return self.markdown(include_weights=self.denominator() < 10**30)
