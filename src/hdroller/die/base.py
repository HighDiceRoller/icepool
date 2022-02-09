__docformat__ = 'google'

import hdroller
from hdroller.collections import Weights

from abc import ABC, abstractmethod
import bisect
from collections import defaultdict
from functools import cache, cached_property
import itertools
import math
import operator
import random

class BaseDie():
    """ Abstract base die class for a die.
    
    A die is a discrete probability distribution with `int` weights.
    The outcomes can be any hashable, comparable values.
    
    It *is* (mostly) well-defined to have a die with zero-weight outcomes.
    These can be useful in a few cases, such as:
    
    * `DicePool` and `EvalPool` will iterate through zero-weight outcomes with 0 count,
        rather than `None` or skipping that outcome.
    * `hdroller.align()` and the like are convenient for making pools share the same set of outcomes.
    
    Otherwise, zero-weight outcomes have a computational cost like any other outcome,
    so it's best to leave them out if not necessary.
    
    Most operations will not introduce zero-weight outcomes if their arguments do not have any.
    
    It's also possible to have dice with no outcomes at all,
    though these have little use other than being sentinel values.
    """
    
    @abstractmethod
    def ndim(self):
        """ Returns the number of dimensions if is a `VectorDie`, or `False` otherwise. """
    
    # Abstract methods.
    
    @abstractmethod
    def unary_op(self, op, *args, **kwargs):
        """ Returns a die representing the effect of performing the operation on the outcomes.
        
        This is used for the operators `-, +, abs, ~, round, trunc, floor, ceil`.
        """
    
    @abstractmethod
    def binary_op(self, other, op, *args, **kwargs):
        """ Returns a die representing the effect of performing the operation on pairs of outcomes from the two dice.
        
        The other operand is cast to a die (using `hdroller.Die`) before performing the operation.
        
        This is used for the operators `+, -, *, /, //, %, **, <<, >>, &, |, ^, <, <=, >=, >, ==, !=`.
        Note that `*` multiplies outcomes directly; it is not the same as `@` or `d()`.
        
        Special operators:
            * The `@` operator rolls the left die, then rolls the right die that many times and sums the outcomes.
                Only the left side will be cast to a die; the right side must already be a die.
            * `==` and `!=` are applied across outcomes like the other operators.
                Unfortunately this means dice are not hashable by normal means.
                Custom functions can use `key_tuple()`, `equals()` and `hash()` as workarounds.
        """
        
    # Basic access.
    
    def has_zero_weights(self):
        """ Returns `True` iff `self` contains at least one zero weight. """
        return self._data.has_zero_weights()
    
    def outcomes(self):
        """ Returns an iterable into the sorted outcomes of the die. """
        return self._data.keys()
    
    def weights(self):
        """ Returns an iterable into the weights of the die in outcome order. """
        return self._data.values()
        
    def __contains__(self, outcome):
        return outcome in self._data
    
    def weight_eq(self, outcome):
        """ Returns the weight of a single outcome, or 0 if not present. """
        return self._data[outcome]
        
    def weight_ne(self, outcome):
        """ Returns the weight != a single outcome. """
        return self.total_weight() - self.weight_eq(outcome)
    
    def weight_le(self, outcome):
        """ Returns the weight <= a single outcome. """
        index = bisect.bisect_right(self.outcomes(), outcome) - 1
        if index < 0: return 0
        return self.cweights()[index]
        
    def weight_lt(self, outcome):
        """ Returns the weight < a single outcome. """
        index = bisect.bisect_left(self.outcomes(), outcome) - 1
        if index < 0: return 0
        return self.cweights()[index]
        
    def weight_ge(self, outcome):
        """ Returns the weight >= a single outcome. """
        index = bisect.bisect_left(self.outcomes(), outcome)
        if index >= self.num_outcomes(): return 0
        return self.sweights()[index]
        
    def weight_gt(self, outcome):
        """ Returns the weight > a single outcome. """
        index = bisect.bisect_right(self.outcomes(), outcome)
        if index >= self.num_outcomes(): return 0
        return self.sweights()[index]
    
    def probability(self, outcome):
        """ Returns the probability of a single outcome. """
        return self.weight_eq(outcome) / self.total_weight()
    
    def items(self):
        """ Returns all outcome, weight pairs. """
        return self._data.items()
    
    def num_outcomes(self):
        """ Returns the number of outcomes (including those with zero weight). """
        return len(self._data)
    
    def is_empty(self):
        """ Returns `True` if this die has no outcomes. """
        return self.num_outcomes() == 0
    
    # Unary operators.
    
    def __neg__(self):
        return self.unary_op(operator.neg)
    
    def __pos__(self):
        return self.unary_op(operator.pos)
    
    def __abs__(self):
        return self.unary_op(operator.abs)
    
    abs = __abs__
    
    @staticmethod
    def _invert(x):
        return not bool(x)
    
    def __invert__(self):
        """ This negates `bool(outcome)`. """
        return self.unary_op(self._invert)
    
    def __round__(self, ndigits=None):
        return self.unary_op(round, ndigits)
    
    def __trunc__(self):
        return self.unary_op(math.trunc)
    
    def __floor__(self):
        return self.unary_op(math.floor)
    
    def __ceil__(self):
        return self.unary_op(math.ceil)
    
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
        result = self.unary_op(BaseDie._zero)
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
        return self.unary_op(bool)
    
    # Binary operators.
    
    def __add__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.add)
    
    def __radd__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return other.binary_op(self, operator.add)
    
    def __sub__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.sub)
    
    def __rsub__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return other.binary_op(self, operator.sub)
    
    def __mul__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.mul)
    
    def __rmul__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return other.binary_op(self, operator.mul)
        
    def __truediv__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.truediv)
    
    def __rtruediv__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return other.binary_op(self, operator.truediv)
    
    def __floordiv__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.floordiv)
    
    def __rfloordiv__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return other.binary_op(self, operator.floordiv)
    
    def __pow__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.pow)
    
    def __rpow__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return other.binary_op(self, operator.pow)
    
    def __mod__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.mod)
    
    def __rmod__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return other.binary_op(self, operator.mod)
    
    def __lshift__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.lshift)
    
    def __rlshift__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return other.binary_op(self, operator.lshift)
    
    def __rshift__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.rshift)
    
    def __rrshift__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return other.binary_op(self, operator.rshift)
    
    def __and__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.and_)
    
    def __rand__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return other.binary_op(self, operator.and_)
        
    def __or__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.or_)
    
    def __ror__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return other.binary_op(self, operator.or_)
    
    def __xor__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.xor)
    
    def __rxor__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return other.binary_op(self, operator.xor)
    
    # Comparators.
    
    def __lt__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.lt)
        
    def __le__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.le)
    
    def __ge__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.ge)
        
    def __gt__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.gt)
    
    def __eq__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.eq)
    
    def __ne__(self, other):
        other = hdroller.Die(other, ndim=self.ndim())
        return self.binary_op(other, operator.ne)
    
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
        return self.unary_op(BaseDie._sign)
    
    @staticmethod
    def _cmp(x, y):
        return BaseDie._sign(x - y)
    
    def cmp(self, other):
        """ Returns a die with possible outcomes 1, -1, and 0.
        
        The weights are equal to the positive outcome of `self > other`, `self < other`, and the remainder respectively.
        """
        return self.binary_op(other, BaseDie._cmp)
    
    # Special operators.
    
    def __rmatmul__(self, other):
        """ Roll the left die, then roll the right die that many times and sum the outcomes. 
        
        Unlike other operators, this does not work for built-in types on the right side.
        For example, `1 @ 6` does not work, nor does `d(6) @ 6`. But `1 @ d(6)` works.
        
        This is because all other operators convert their right side to a die using die,
        so `6` would become a constant 6, while  `d()` converts `int`s to a standard die with that many sides,
        so `6` would become a d6. Thus the right-side conversion of `@` would be ambiguous.
        """
        other = hdroller.Die(other, ndim=self.ndim())
        return other.d(self)
    
    # Mixtures.

    def sub(self, repl, /, ndim=None, total_weight_method='lcm'):
        """ Changes outcomes of the die to other outcomes.
        
        You can think of this as `sub`stituting outcomes of this die for other outcomes or dice.
        Or, as executing a `sub`routine based on the roll of this die.
        
        Args:
            repl: One of the following:
                * A map from old outcomes to new outcomes.
                    Unmapped old outcomes stay the same.
                * A function mapping old outcomes to new outcomes.
                The new outcomes may be dice rather than just single outcomes.
            ndim: Sets the `ndim` of the result. If not provided, `ndim` will be determined automatically.
            total_weight_method: As `hdroller.mix()`.
        
        Returns:
            The relabeled die.
        """
        if hasattr(repl, 'items'):
            repl = [(repl[outcome] if outcome in repl else outcome) for outcome in self.outcomes()]
        elif callable(repl):
            repl = [repl(outcome) for outcome in self.outcomes()]

        return hdroller.mix(*repl, mix_weights=self.weights(), ndim=ndim, total_weight_method=total_weight_method)
    
    def explode(self, max_depth, outcomes=None):
        """ Causes outcomes to be rolled again and added to the total.
        
        Args:
            max_depth: The maximum number of additional dice to roll.
            outcomes: Which outcomes to explode. Options:
                * An iterable containing outcomes to explode.
                * If not supplied, the top single outcome will explode.
        """
        if max_depth < 0:
            raise ValueError('max_depth cannot be negative.')
        if max_depth == 0:
            return self
        
        if outcomes is None:
            outcomes = set([self.max_outcome()])
        
        tail_die = self.explode(max_depth-1, outcomes=outcomes)
        
        def sub_func(outcome):
            if outcome in outcomes:
                return outcome + tail_die
            else:
                return outcome
        
        return self.sub(sub_func, ndim=self.ndim(), total_weight_method='lcm')
    
    def reroll(self, outcomes, max_depth=None):
        """ Rerolls the given outcomes.
        
        Args:
            outcomes: Selects which outcomes to reroll. Options:
                * A callable that takes outcomes and returns `True` if it should be rerolled.
                * A set of outcomes to reroll.
            max_depth: The maximum number of times to reroll.
                If omitted, rerolls an unlimited number of times.
        
        Returns:
            A die representing the reroll.
            If the reroll would never terminate, the result has no outcomes.
        """
        if callable(outcomes):
            outcomes = set(outcome for outcome in self.outcomes() if outcomes(outcome))
        
        if max_depth is None:
            data = { outcome : weight for outcome, weight in self.items() if outcome not in outcomes }
        else:
            total_reroll_weight = sum(weight for outcome, weight in self.items() if outcome in outcomes )
            rerollable_factor = total_reroll_weight ** max_depth
            stop_factor = self.total_weight() ** max_depth + total_reroll_weight ** max_depth
            data = { outcome : (rerollable_factor * weight if outcome in outcomes else stop_factor * weight) for outcome, weight in self.items() }
        return hdroller.Die(data, ndim=self.ndim())
    
    def reroll_until(self, outcomes, max_depth=None):
        """ Rerolls until getting one of the given outcomes.
        
        Essentially the complement of reroll().
        
        Args:
            outcomes: Selects which outcomes to reroll until. Options:
                * A callable that takes outcomes and returns `True` if it should be accepted.
                * A set of outcomes to reroll until.
            max_depth: The maximum number of times to reroll.
                If omitted, rerolls an unlimited number of times.
        
        Returns:
            A die representing the reroll.
            If the reroll would never terminate, the result has no outcomes.
        """
        if callable(outcomes):
            not_outcomes = lambda outcome: not outcomes(outcome)
        else:
            not_outcomes = lambda outcome: outcome not in outcomes
        return self.reroll(not_outcomes, max_depth)
    
    # Repeat, keep, and sum.
    
    def highest(*dice):
        """ Roll all the dice and take the highest. """
        dice = hdroller.align(*dice)
        ndim = hdroller.check_ndim(*dice)
        cweights = tuple(math.prod(t) for t in zip(*(die.cweights() for die in dice)))
        return hdroller.from_cweights(dice[0].outcomes(), cweights, ndim=ndim)
    
    max = highest
    
    def lowest(*dice):
        """ Roll all the dice and take the lowest. """
        dice = hdroller.align(*dice)
        ndim = hdroller.check_ndim(*dice)
        sweights = tuple(math.prod(t) for t in zip(*(die.sweights() for die in dice)))
        return hdroller.from_sweights(dice[0].outcomes(), sweights, ndim=ndim)
    
    min = lowest
    
    def repeat_and_sum(self, num_dice):
        """ Roll this die `num_dice` times and sum the results. 
        
        If `num_dice` is negative, roll the die `abs(num_dice)` times and negate the result.
        """
        if num_dice < 0:
            return -self.repeat_and_sum(-num_dice)
        elif num_dice == 0:
            return self.zero()
        elif num_dice == 1:
            return self
        
        half_result = self.repeat_and_sum(num_dice // 2)
        result = half_result + half_result
        if num_dice % 2: result += self
        return result
    
    def hitting_time(self, cond, max_depth):
        """ Repeats and sums this dice until `cond` is successful, and counts the number of rolls to success.
        
        Args:
            * cond: A function that takes outcomes and returns `True` if the sum is successful.
            * max_depth: The maximum number of times to repeat.
                This can be `None` for an unlimited number of times,
                but you need to make sure that success is guaranteed within a limited number of repeats in this case.
        
        Returns:
            A die representing the number of rolls until success.
        """
        num_dice = 0
        done, not_done = self.zero().split(cond)
        done_weight = done.total_weight()
        data = [done_weight]
        while True:
            if max_depth is not None and num_dice > max_depth:
                break
            data = [x * self.total_weight() for x in data]
            not_done += self
            new_done, not_done = not_done.split(cond)
            data.append(data[-1] + new_done.total_weight())
            if not_done.total_weight() == 0:
                break
            num_dice += 1
        return hdroller.from_cweights(range(len(data)), data)
    
    def pool(self, *args, **kwargs):
        """ Creates a pool from this die, as `hdroller.Pool()`. """
        return hdroller.Pool(self, *args, **kwargs)
    
    def keep(self, num_dice=None, count_dice=None, *, max_outcomes=None, min_outcomes=None):
        """ Roll this die several times, possibly capping the maximum outcomes, and sum some or all of the sorted results.
        
        Args:
            num_dice: The number of dice to roll. All dice will have the same outcomes as `self`.
            count_dice: Only dice selected by this will be counted.
                Determines which of the **sorted** dice will be counted, and how many times.
                The dice are sorted in ascending order for this purpose,
                regardless of which order the outcomes are evaluated in.
                
                This can be an `int` or a `slice`, in which case the selected dice are counted once each.
                For example, `slice(-2, None)` would count the two highest dice.
                
                Or this can be a sequence of `int`s, one for each die in order.
                Each die is counted that many times.
                For example, `[0, 0, 2, 0, 0]` would count the middle out of five dice twice.
            max_outcomes: A sequence of one outcome per die.
                That die will be limited to that maximum outcome, with all higher outcomes being removed (i.e. rerolled).
                This is not compatible with `min_outcomes`.
            min_outcomes: A sequence of one outcome per die.
                That die will be limited to that minimum outcome, with all lower outcomes being removed (i.e. rerolled).
                This is not compatible with `max_outcomes`.
                
        Returns:
            A Die representing the probability distribution of the sum.
        """
        pool = hdroller.Pool(self, num_dice, count_dice, min_outcomes=min_outcomes, max_outcomes=max_outcomes)
        return pool.sum()
    
    def keep_highest(self, num_dice=None, num_keep=1, num_drop=0, *, max_outcomes=None, min_outcomes=None):
        """ Roll this die several times, possibly capping the maximum outcomes, and sum the sorted results from the highest.
        
        Exactly one out of `num_dice`, `min_outcomes`, and `max_outcomes` should be provided.
        
        Args:
            num_dice: The number of dice to roll. All dice will have the same outcomes as `self`.
            num_keep: The number of dice to keep.
            num_drop: If provided, this many highest dice will be dropped before keeping.
            max_outcomes: A sequence of one outcome per die.
                That die will be limited to that maximum outcome, with all higher outcomes being removed (i.e. rerolled).
            min_outcomes: A sequence of one outcome per die.
                That die will be limited to that minimum outcome, with all lower outcomes being removed (i.e. rerolled).
                
        Returns:
            A die representing the probability distribution of the sum.
        """
        if num_keep == 1 and num_drop == 0 and max_outcomes is None and min_outcomes is None:
            return self.keep_highest_single(num_dice)
        start = -(num_keep + (num_drop or 0))
        stop = -num_drop if num_drop > 0 else None
        count_dice = slice(start, stop)
        return self.keep(num_dice, count_dice, max_outcomes=max_outcomes, min_outcomes=min_outcomes)
    
    def keep_highest_single(self, num_dice=None):
        """ Faster algorithm for keeping just the single highest die. """
        if num_dice is None:
            return self.zero()
        return hdroller.from_cweights(self.outcomes(), (x ** num_dice for x in self.cweights()), ndim=self.ndim())
    
    def keep_lowest(self, num_dice=None, num_keep=1, num_drop=0, *, max_outcomes=None, min_outcomes=None):
        """ Roll this die several times, possibly capping the maximum outcomes, and sum the sorted results from the lowest.
        
        Exactly one out of `num_dice`, `min_outcomes`, and `max_outcomes` should be provided.
        
        Args:
            num_dice: The number of dice to roll. All dice will have the same outcomes as `self`.
            min_outcomes: A sequence of one outcome per die.
                That die will be limited to that minimum outcome, with all lower outcomes being removed (i.e. rerolled).
            max_outcomes: A sequence of one outcome per die.
                That die will be limited to that maximum outcome, with all higher outcomes being removed (i.e. rerolled).
            num_keep: The number of dice to keep.
            num_drop: If provided, this many lowest dice will be dropped before keeping.
                
        Returns:
            A die representing the probability distribution of the sum.
        """
        if num_keep == 1 and num_drop == 0 and max_outcomes is None and min_outcomes is None:
            return self.keep_lowest_single(num_dice)
        start = num_drop if num_drop > 0 else None
        stop = num_keep + (num_drop or 0)
        count_dice = slice(start, stop)
        return self.keep(num_dice, count_dice, max_outcomes=max_outcomes, min_outcomes=min_outcomes)
    
    def keep_lowest_single(self, num_dice=None):
        """ Faster algorithm for keeping just the single lowest die. """
        if num_dice is None:
            return self.zero()
        return hdroller.from_sweights(self.outcomes(), (x ** num_dice for x in self.sweights()), ndim=self.ndim())
    
    # Modifying outcomes and/or weights.
    
    def set_outcomes(self, outcomes):
        """ Returns a die whose outcomes are set to the argument, including zero weights.
        
        This may remove outcomes or add zero-weight outcomes.
        """
        data = {x : self.weight_eq(x) for x in outcomes}
        return hdroller.Die(data, ndim=self.ndim())
    
    def trim(self):
        """ Removes all zero-weight outcomes from self. """
        data = { k : v for k, v in self.items() if v > 0 }
        return hdroller.Die(data, ndim=self.ndim())
    
    @cached_property
    def _pop_max(self):
        d = { k : v for k, v in zip(self.outcomes()[:-1], self.weights()[:-1]) }
        die = hdroller.Die(d, ndim=self.ndim())
        return die, self.outcomes()[-1], self.weights()[-1]
    
    def pop_max(self):
        """ Remove the max outcome and return the result, along with the popped outcome, and the popped weight.
        
        Raises:
            `IndexError` if this die has no outcome to pop.
        """
        return self._pop_max
    
    @cached_property
    def _pop_min(self):
        d = { k : v for k, v in zip(self.outcomes()[1:], self.weights()[1:]) }
        die = hdroller.Die(d, ndim=self.ndim())
        return die, self.outcomes()[0], self.weights()[0]
    
    def pop_min(self):
        """ Remove the min outcome and return the result, along with the popped outcome, and the popped weight.
        
        Raises:
            `IndexError` if this die has no outcome to pop.
        """
        return self._pop_min
    
    def split(self, cond):
        """ Splits this die's items into two pieces based on `cond(outcome)`.
        
        The left result is all outcome-weight pairs where `cond(outcome)` is `False`.
        The right result is all outcome-weight pairs where `cond(outcome)` is `True`.
        """
        data_true = {}
        data_false = {}
        for outcome, weight in self.items():
            if cond(outcome):
                data_true[outcome] = weight
            else:
                data_false[outcome] = weight
        return hdroller.Die(data_true, ndim=self.ndim()), hdroller.Die(data_false, ndim=self.ndim())
    
    def reduce(self):
        """ Divides all weights by their greatest common denominator. """
        gcd = math.gcd(*self.weights())
        if gcd <= 1:
            return self
        data = { outcome : weight // gcd for outcome, weight in self.items() }
        return hdroller.Die(data, ndim=self.ndim())
    
    def scale_weights(self, scale):
        """ Multiplies all weights by a constant. """
        if scale < 0:
            raise ValueError('Weights cannot be scaled by a negative number.')
        data = { outcome : scale * weight for outcome, weight in self.items() }
        return hdroller.Die(data, ndim=self.ndim())
    
    # Scalar(-ish) statistics.
    
    def min_outcome(*dice):
        """ Returns the minimum possible outcome among the dice. """
        return min(die.outcomes()[0] for die in dice)
    
    def max_outcome(*dice):
        """ Returns the maximum possible outcome among the dice. """
        return max(die.outcomes()[-1] for die in dice)
    
    @cached_property
    def _total_weight(self):
        return sum(self._data.values())
    
    def total_weight(self):
        """ The total weight of all outcomes. """
        return self._total_weight
        
    def mode(self):
        """ Returns a tuple containing the most common outcome(s) of the die.
        
        These are sorted from lowest to highest.
        """
        return tuple(outcome for outcome, weight in self.items() if weight == self.modal_weight())
    
    def modal_weight(self):
        """ The highest weight of any single outcome. """
        return max(self.weights())
    
    def ks_stat(self, other):
        """ Kolmogorov–Smirnov stat. The maximum absolute difference between CDFs. """
        a, b = hdroller.align(self, other)
        return max(abs(a - b) for a, b in zip(a.cdf(), b.cdf()))
    
    def cvm_stat(self, other):
        """ Cramér-von Mises stat. The sum-of-squares difference between CDFs. """
        a, b = hdroller.align(self, other)
        return sum((a - b) ** 2 for a, b in zip(a.cdf(), b.cdf()))
    
    # Iterable statistics.
    
    @cached_property
    def _pmf(self):
        return tuple(weight / self.total_weight() for weight in self.weights())
    
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
        return tuple(itertools.accumulate(self.weights()[:-1], operator.sub, initial=self.total_weight()))
    
    def sweights(self):
        """ Survival weights. The weight >= each outcome in order. """
        return self._sweights
        
    @cached_property
    def _cdf(self):
        return tuple(weight / self.total_weight() for weight in self.cweights())
    
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
        return tuple(weight / self.total_weight() for weight in self.sweights())
    
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
    
    # Rolling.
    
    def sample(self):
        """ Returns a random roll of this die. 
        
        Do not use for security purposes.
        """
        # We don't use random.choices since that is based on floats rather than ints.
        r = random.randrange(self.total_weight())
        index = bisect.bisect_right(self.cweights(), r)
        return self.outcomes()[index]
    
    # Invalid operations.
    
    def __bool__(self):
        """ Dice are not considered to have truth values. 
        
        The result of a comparator operation is a die,
        which if considered to have a truth value,
        would imply that dice are sortable by that operator.
        """
        raise TypeError('A die does not have a truth value.')
    
    def __reversed__(self):
        raise TypeError('A die cannot be reversed.')
    
    def __len__(self):
        raise TypeError('The length of a die is ambiguous. Use die.num_outcomes(), die.total_weight(), or die.ndim().')
    
    # Equality and hashing.
    
    @cached_property
    def _key_tuple(self):
        return tuple(self.items()), self.ndim()
        
    def key_tuple(self):
        """ Returns a tuple that uniquely (as `equals()`) identifies this die. """
        return self._key_tuple

    def hash(self):
        """ A true __hash__ doesn't work because we used the __eq__ operator 
        for determining the chance two dice will roll equal to each other.
        
        See `hdroller.functools.die_cache` for an example.
        """
        return hash(self.key_tuple())
    
    __hash__ = None
    
    def equals(self, other):
        """ Returns `True` iff both dice have the same ndim, outcomes, and weights.
        
        Note that dice are not reduced, e.g. a 2:2 coin is not `equals()` to a 1:1 coin. 
        Zero-weight outcomes are also considered for the purposes of `equals()`.
        
        For the chance of two dice rolling the same as each other, use the == operator.
        """
        try:
            other = hdroller.Die(other, ndim=self.ndim())
        except ValueError:
            return False
        return self.key_tuple() == other.key_tuple()
