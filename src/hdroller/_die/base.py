import hdroller
from hdroller._die.data import DieData

import bisect
from collections import defaultdict
from functools import cache, cached_property
import itertools
import math
import operator

class BaseDie():
    # Abstract methods.
    
    @property
    def is_single(self):
        """True iff this die is univariate.
        
        This is opposed to multivariate dice, where operators apply elementwise.
        """
        raise NotImplementedError()
    
    def unary_op(self, op, *args, **kwargs):
        """Returns a die representing the effect of performing the operation on the outcomes."""
        raise NotImplementedError()
    
    def binary_op(self, other, op, *args, **kwargs):
        """Returns a die representing the effect of performing the operation on pairs of outcomes from the two dice."""
        raise NotImplementedError()
        
    # Construction.

    def __init__(self, data):
        """Users should usually not construct dice directly;
        instead they should use one of the methods defined in
        hdroller._die.create (which are imported into the 
        top-level hdroller module).
        
        Args:
            data: A hdroller.WeightDict mapping outcomes to weights.
        """
        self._data = data
        
    # Basic access.
    
    def outcomes(self):
        """Returns an iterable into the sorted outcomes of the die."""
        return self._data.keys()
    
    def weights(self):
        """Returns an iterable into the weights of the die in outcome order."""
        return self._data.values()
        
    def __contains__(self, outcome):
        return outcome in self._data
    
    def weight(self, outcome):
        """Returns the weight of a single outcome, or 0 if not present."""
        return self._data[outcome]
    
    def weight_le(self, outcome):
        index = bisect.bisect_right(self.outcomes(), outcome)
        if index >= len(self): return self.total_weight()
        return self.cweights()[index]
        
    def weight_lt(self, outcome):
        index = bisect.bisect_left(self.outcomes(), outcome)
        if index >= len(self): return self.total_weight()
        return self.cweights()[index]
        
    def weight_ge(self, outcome):
        index = bisect.bisect_left(self.outcomes(), outcome)
        if index >= len(self): return self.total_weight()
        return self.sweights()[index]
        
    def weight_gt(self, outcome):
        index = bisect.bisect_right(self.outcomes(), outcome)
        if index >= len(self): return self.total_weight()
        return self.sweights()[index]
    
    def probability(self, outcome):
        return self.weight(outcome) / self.total_weight()
    
    def items(self):
        return self._data.items()
    
    def __len__(self):
        return len(self._data)
    
    # Unary operators.
    
    def __neg__(self):
        return self.unary_op(operator.neg)
    
    def __abs__(self):
        return self.unary_op(operator.abs)
    
    abs = __abs__
    
    @staticmethod
    def _invert(x):
        return not bool(x)
    
    def __invert__(self):
        """ This negates bool(outcome). """
        return self.unary_op(self._invert)
    
    def __round__(self, ndigits=None):
        return self.unary_op(round, ndigits)
    
    def __trunc__(self):
        return self.unary_op(trunc)
    
    def __floor__(self):
        return self.unary_op(floor)
    
    def __ceil__(self):
        return self.unary_op(ceil)
    
    @staticmethod
    def _zero(x):
        """Creates a default instance of x's type."""
        return type(x)()
    
    def zero(self):
        # TODO: Do we actually want to have mixed zeros?
        return self.unary_op(self._zero).reduce()
    
    # Binary operators.
    
    def __add__(self, other):
        other = hdroller.die(other)
        return self.binary_op(other, operator.add)
    
    def __radd__(self, other):
        other = hdroller.die(other)
        return other.binary_op(self, operator.add)
    
    def __sub__(self, other):
        other = hdroller.die(other)
        return self.binary_op(other, operator.sub)
    
    def __rsub__(self, other):
        other = hdroller.die(other)
        return other.binary_op(self, operator.sub)
    
    def __floordiv__(self, other):
        other = hdroller.die(other)
        return self.binary_op(other, operator.floordiv)
    
    def __pow__(self, other):
        other = hdroller.die(other)
        return self.binary_op(other, operator.pow)
    
    def __rpow__(self, other):
        other = hdroller.die(other)
        return other.binary_op(self, operator.pow)
    
    def __mod__(self, other):
        other = hdroller.die(other)
        return self.binary_op(other, operator.mod)
    
    def __lt__(self, other):
        other = hdroller.die(other)
        return self.binary_op(other, operator.lt)
        
    def __le__(self, other):
        other = hdroller.die(other)
        return self.binary_op(other, operator.le)
    
    def __ge__(self, other):
        other = hdroller.die(other)
        return self.binary_op(other, operator.ge)
        
    def __gt__(self, other):
        other = hdroller.die(other)
        return self.binary_op(other, operator.gt)
    
    # Logical operators.
    # These operate on bool(outcome).
    
    @staticmethod
    def _and(x, y):
        return bool(x) and bool(y)
    
    def __and__(self, other):
        other = hdroller.die(other)
        return self.binary_op(other, self._and)
    
    def __rand__(self, other):
        other = hdroller.die(other)
        return other.binary_op(self, self._and)
    
    @staticmethod
    def _or(x, y):
        return bool(x) or bool(y)
        
    def __or__(self, other):
        other = hdroller.die(other)
        return self.binary_op(other, self._or)
    
    def __or__(self, other):
        other = hdroller.die(other)
        return other.binary_op(self, self._or)
    
    @staticmethod
    def _xor(x, y):
        return bool(x) + bool(y) == 1
    
    def __xor__(self, other):
        other = hdroller.die(other)
        return self.binary_op(other, self._xor)
    
    def __xor__(self, other):
        other = hdroller.die(other)
        return other.binary_op(self, self._xor)
    
    # Special operators.
    
    def __mul__(self, other):
        """Roll the left die, then roll the right die that many times and sum."""
        other = hdroller.die(other)
        
        subresults = []
        subresult_weights = []
        
        max_abs_die_count = max(abs(self.min_outcome()), abs(self.max_outcome()))
        for die_count, die_count_weight in self.items():
            factor = other.total_weight() ** (max_abs_die_count - abs(die_count))
            subresults.append(other.repeat_and_sum(die_count))
            subresult_weights.append(die_count_weight * factor)
        
        subresults = _align(subresults)
        
        data = defaultdict(int)
        
        for subresult, subresult_weight in zip(subresults, subresult_weights):
            for outcome, weight in subresult.items():
                data[outcome] += weight * subresult_weight
            
        return hdroller.die(data, force_single=other.is_single)
    
    def __rmul__(self, other):
        other = hdroller.die(other)
        return other.__mul__(self)
    
    def multiply(self, other):
        """Actually multiply the outcomes of the two dice."""
        other = hdroller.die(other)
        return self.binary_op(other, operator.mul)
    
    # Mixtures.

    def relabel(self, relabeling):
        """
        relabeling can be one of the following:
        * An array-like containing relabelings, one for each outcome in order.
        * A map from old outcomes to new outcomes.
            Unmapped old outcomes stay the same.
        * A function mapping old outcomes to new outcomes.
        
        A die may be provided instead of a single new outcome.
        """
        if hasattr(relabeling, 'items'):
            relabeling = [(relabeling[outcome] if outcome in relabeling else outcome) for outcome in self.outcomes()]
        elif callable(relabeling):
            relabeling = [relabeling(outcome) for outcome in self.outcomes()]

        return hdroller.mix(*relabeling, mix_weights=self.weights())
    
    def explode(self, max_depth, outcomes=None):
        """
        outcomes: This chooses which outcomes to explode. Options:
            * An iterable containing outcomes to explode.
            * If not supplied, the top single outcome will explode with full probability.
        """
        if max_depth < 0:
            raise ValueError('max_depth cannot be negative.')
        if max_depth == 0:
            return self
        
        if outcomes is None:
            outcomes = set([self.max_outcome()])
        
        explode = {}
        non_explode = {}
        
        for outcome, weight in self.items():
            if outcome in outcomes:
                explode[outcome] = weight
            else:
                non_explode[outcome] = weight
        
        non_explode_die = hdroller._die.create._die_from_checked_dict(non_explode, force_single=self.is_single)
        tail_die = self.explode(max_depth-1, outcomes=outcomes)
        explode_die = hdroller._die.create._die_from_checked_dict(explode, force_single=self.is_single) + tail_die
        
        non_explode_die, explode_die = _align(non_explode_die, explode_die)
        data = { outcome : n_weight * tail_die.total_weight() + x_weight for (outcome, n_weight), x_weight in zip(non_explode_die.items(), explode_die.weights()) }
        
        return hdroller._die.create._die_from_checked_dict(data, force_single=self.is_single)
    
    def reroll(self, *outcomes, max_depth=None):
        """Rerolls the given outcomes.
        
        Args:
            outcomes: Selects which outcomes to reroll. Options:
                * A set of outcomes to reroll.
            max_depth: The maximum number of times to reroll.
                If omitted, rerolls an unlimited number of times.
        
        Returns:
            A Die representing the reroll.
            If the reroll would never terminate, the result is None.
        """
        if outcomes is None:
            raise TypeError('outcomes to reroll must be provided.')
        
        if max_depth is None:
            data = { outcome : weight for outcome, weight in self.items() if outcome not in outcomes }
            if len(data) == 0:
                return None
        else:
            # TODO: simplify this
            total_reroll_weight = sum(weight for outcome, weight in self.items() if outcome in outcomes )
            rerollable_factor = total_reroll_weight ** max_depth
            stop_factor = self.total_weight() ** max_depth + total_reroll_weight ** max_depth
            data = { outcome : (rerollable_factor * weight if outcome in outcomes else stop_factor * weight) for outcome, weight in self.items() }
        return hdroller._die.create._die_from_checked_dict(data, force_single=self.is_single)
    
    # Repeat, keep, and sum.
    
    def max(*dice):
        """
        Roll all the dice and take the highest.
        Dice (or anything castable to a die) may be provided as a list or as a variable number of arguments.
        """
        dice = _align(dice)
        force_single = any(die.is_single for die in dice)
        cweights = tuple(math.prod(t) for t in zip(*(die.cweights() for die in dice)))
        return hdroller.from_cweights(dice[0].outcomes(), cweights, force_single=force_single)
    
    def min(*dice):
        """
        Roll all the dice and take the lowest.
        Dice (or anything castable to a Die) may be provided as a list or as a variable number of arguments.
        """
        dice = _align(dice)
        force_single = any(die.is_single for die in dice)
        sweights = tuple(math.prod(t) for t in zip(*(die.sweights() for die in dice)))
        return hdroller.from_sweights(dice[0].outcomes(), sweights, force_single=force_single)
    
    def repeat_and_sum(self, num_dice):
        """Roll this die `num_dice` times and sum the results."""
        if num_dice < 0:
            return (-self).repeat_and_sum(-num_dice)
        elif num_dice == 0:
            return self.zero()
        elif num_dice == 1:
            return self
        
        half_result = self.repeat_and_sum(num_dice // 2)
        result = half_result + half_result
        if num_dice % 2: result += self
        return result
    
    def keep(self, num_dice, select_dice=None, *, min_outcomes=None, max_outcomes=None):
        """
        Roll this Die several times, possibly capping the maximum outcomes, and sum some or all of the sorted results.
        
        Arguments:
            max_outcomes: Either:
                * An iterable indicating the maximum outcome for each die in the pool.
                * An integer indicating the number of dice in the pool; all dice will have max_outcome equal to die.max_outcome().
            mask:
                The pool will be sorted from lowest to highest; only dice selected by mask will be counted.
                If omitted, all dice will be counted.
                
        Returns:
            A Die representing the probability distribution of the sum.
        """
        pool = hdroller.dice_pool.pool(self, num_dice, select_dice, min_outcomes=min_outcomes, max_outcomes=max_outcomes)
        return hdroller.pool_eval.pool_sum.eval(pool)
        
    def keep_highest(self, num_dice, num_keep=1, num_drop=0, *, min_outcomes=None, max_outcomes=None):
        """
        Roll this Die several times, possibly capping the maximum outcomes, and sum the sorted results from the highest.
        
        Arguments:
            num_dice: The number of dice to roll.
            num_keep: The number of dice to keep.
            num_drop: If provided, this many highest dice will be dropped before keeping.
                
        Returns:
            A Die representing the probability distribution of the sum.
        """
        start = -(num_keep + (num_drop or 0))
        stop = -num_drop if num_drop > 0 else None
        select_dice = slice(start, stop)
        return self.keep(num_dice, select_dice, min_outcomes=min_outcomes, max_outcomes=max_outcomes)
        
    def keep_lowest(self, num_dice, num_keep=1, num_drop=0, *, min_outcomes=None, max_outcomes=None):
        """
        Roll this Die several times, possibly capping the maximum outcomes, and sum the sorted results from the lowest.
        
        Arguments:
            num_dice: The number of dice to roll.
            num_keep: The number of dice to keep.
            num_drop: If provided, this many lowest dice will be dropped before keeping.
                
        Returns:
            A Die representing the probability distribution of the sum.
        """
        start = num_drop if num_drop > 0 else None
        stop = num_keep + (num_drop or 0)
        select_dice = slice(start, stop)
        return self.keep(num_dice, select_dice, min_outcomes=min_outcomes, max_outcomes=max_outcomes)
    
    # Modifying outcomes.
    
    def _set_outcomes(self, outcomes):
        """Returns a die whose outcomes are set to the argument, including zero weights.
        
        Note that public methods are intended to have no zero-weight outcomes.
        This should therefore not be used externally for any Die that you want to do anything with afterwards.
        """
        data = {x : self.weight(x) for x in outcomes}
        return hdroller._die.create._die_from_checked_dict(data, force_single=self.is_single)
    
    @cached_property
    def _pop_min(self):
        if len(self) > 1:
            d = { k : v for k, v in zip(self.outcomes()[1:], self.weights()[1:]) }
            die = hdroller._die.create._die_from_checked_dict(d, force_single=self.is_single)
            return die, self.outcomes()[0], self.weights()[0]
        else:
            return None, self.outcomes()[0], self.weights()[0]
    
    def pop_min(self):
        """Returns a copy of self with the min outcome removed, the popped outcome, and the popped weight.
        
        If the last outcome is removed, the returned die will be None.
        """
        return self._pop_min
    
    @cached_property
    def _pop_max(self):
        if len(self) > 1:
            d = { k : v for k, v in zip(self.outcomes()[:-1], self.weights()[:-1]) }
            die = hdroller._die.create._die_from_checked_dict(d, force_single=self.is_single)
            return die, self.outcomes()[-1], self.weights()[-1]
        else:
            return None, self.outcomes()[-1], self.weights()[-1]
    
    def pop_max(self):
        """Returns a copy of self with the max outcome removed, the popped outcome, and the popped weight.
        
        If the last outcome is removed, the returned die will be None.
        """
        return self._pop_max
    
    def reduce(self):
        gcd = math.gcd(*self.weights())
        if gcd <= 1:
            return self
        data = { outcome : weight // gcd for outcome, weight in self.items() }
        return hdroller._die.create._die_from_checked_dict(data, force_single=self.is_single)
    
    # Scalar(-ish) statistics.
    
    def min_outcome(self):
        return self.outcomes()[0]
    
    def max_outcome(self):
        return self.outcomes()[-1]
    
    @cached_property
    def _total_weight(self):
        return sum(self._data.values())
    
    def total_weight(self):
        return self._total_weight
    
    def mean(self):
        return sum(outcome * p for outcome, p in zip(self.outcomes(), self.pmf()))
        
    def median(self):
        left_index = bisect.bisect_left(self.cweights(), self.total_weight() / 2)
        right_index = bisect.bisect_right(self.cweights(), self.total_weight() / 2)
        return (self.outcomes()[left_index] + self.outcomes()[right_index]) / 2
        
    def modes(self):
        """Returns a tuple containing the most common outcome(s) of the die.
        
        These are sorted from least to greatest.
        """
        return tuple(outcome for outcome, weight in self.items() if weight == self.modal_weight())
    
    def modal_weight(self):
        return max(self.weights())
    
    def variance(self):
        mean = self.mean()
        mean_of_squares = sum(p * outcome ** 2 for outcome, p in zip(self.outcomes(), self.pmf()))
        return mean_of_squares - mean * mean
    
    def standard_deviation(self):
        return math.sqrt(self.variance())
    
    sd = standard_deviation
    
    def standardized_moment(self, k):
        sd = self.standard_deviation()
        mean = self.mean()
        ev = sum(p * (outcome - mean) ** k for outcome, p in zip(self.outcomes(), self.pmf()))
        return ev / (sd ** k)
    
    def skewness(self):
        return self.standardized_moment(3.0)
    
    def excess_kurtosis(self):
        return self.standardized_moment(4.0) - 3.0
    
    def ks_stat(self, other):
        """ Kolmogorov–Smirnov stat. The maximum absolute difference between CDFs. """
        a, b = _align([self, other])
        return max(abs(a - b) for a, b in zip(a.cdf(), b.cdf()))
    
    def cvm_stat(self, other):
        """ Cramér-von Mises stat. The sum-of-squares difference between CDFs. """
        a, b = _align([self, other])
        return sum((a - b) ** 2 for a, b in zip(a.cdf(), b.cdf()))
    
    # Iterable statistics.
    
    @cached_property
    def _pmf(self):
        return tuple(weight / self.total_weight() for weight in self.weights())
    
    def pmf(self):
        return self._pmf
    
    @cached_property
    def _cweights(self):
        return tuple(itertools.accumulate(self.weights()))
    
    def cweights(self):
        return self._cweights
    
    @cached_property
    def _sweights(self):
        return tuple(itertools.accumulate(self.weights()[:-1], operator.sub, initial=self.total_weight()))
    
    def sweights(self):
        return self._sweights
        
    @cached_property
    def _cdf(self):
        return tuple(weight / self.total_weight() for weight in self.cweights())
    
    def cdf(self):
        return self._cdf
        
    @cached_property
    def _sf(self):
        return tuple(weight / self.total_weight() for weight in self.sweights())
    
    def sf(self):
        return self._sf
    
    # Strings.
    
    def __str__(self):
        """
        Formats the die as a Markdown table.
        """
        result = f'| Outcome | Weight (out of {self.total_weight()}) | Probability |\n'
        result += '|----:|----:|----:|\n'
        for outcome, weight, p in zip(self.outcomes(), self.weights(), self.pmf()):
            result += f'| {outcome} | {weight} | {p:.3%} |\n'
        return result
    
    # Hashing and equality.
    
    @cached_property
    def _key_tuple(self):
        return self.is_single, tuple(self.items())
        
    def __eq__(self, other):
        """
        Returns true iff this Die has the same outcomes and weights as the other Die.
        Note that fractions are not reduced.
        For example a 1:1 coin flip is NOT considered == to a 2:2 coin flip.
        """
        if not isinstance(other, BaseDie): return False
        return self._key_tuple == other._key_tuple
    
    @cached_property
    def _hash(self):
        return hash(self._key_tuple)
        
    def __hash__(self):
        return self._hash

def _align(*dice):
    """Pads all the dice with zero weights so that all have the same set of outcomes.
    
    Note that public methods are intended to have no zero-weight outcomes.
    This should therefore not be used externally for any Die that you want to do anything with afterwards.
    
    Args:
        *dice: Multiple dice or a single iterable of dice.
    
    Returns:
        A tuple of aligned dice.
    
    Raises:
        TypeError if the dice are of mixed singleness.
    """
    dice = _listify_dice(dice)
    
    if any(die.is_single for die in dice) != all(die.is_single for die in dice):
        raise TypeError('The passed to _align() must all be single or all multi.')
    
    union_outcomes = set(itertools.chain.from_iterable(die.outcomes() for die in dice))
    
    return tuple(die._set_outcomes(union_outcomes) for die in dice)

def _listify_dice(args):
    if len(args) == 1 and hasattr(args[0], '__iter__') and not isinstance(args[0], BaseDie):
        args = args[0]
    
    return [hdroller.die(arg) for arg in args]