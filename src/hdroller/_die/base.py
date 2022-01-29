import hdroller
from hdroller.cache import cache, cached_property

import bisect
from collections import defaultdict
import itertools
import math
import operator

class BaseDie():
    # Abstract methods.
    
    @property
    def is_multi(self):
        """True iff this die is multivariate, i.e. operates on outcomes elementwise."""
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
    
    def weight(self, outcome):
        """Returns the weight of a single outcome, or 0 if not present."""
        return self._data[outcome]
    
    def probability(self, outcome):
        return self.weight(outcome) / self.total_weight()
    
    p = probability
    
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
        return self.unary_op(_zero)
    
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
        
        subresults = BaseDie._align(subresults)
        
        data = defaultdict(int)
        
        for subresult, subresult_weight in zip(subresults, subresult_weights):
            for outcome, weight in subresult.items():
                data[outcome] += weight * subresult_weight
            
        return hdroller.die(data)
    
    def __rmul__(self, other):
        other = hdroller.die(other)
        return other.__mul__(self)
    
    def multiply(self, other):
        """Actually multiply the outcomes of the two dice."""
        other = hdroller.die(other)
        return self.binary_op(other, operator.mul)
    
    # Repeat, keep, and sum.
    def max(*dice):
        """
        Roll all the dice and take the highest.
        Dice (or anything castable to a Die) may be provided as a list or as a variable number of arguments.
        """
        dice = BaseDie._align(dice)

        cweights = tuple(math.prod(t) for t in zip(*(die.cweights() for die in dice)))
            
        return hdroller.from_cweights(dice[0].outcomes(), cweights)
    
    def min(*dice):
        """
        Roll all the dice and take the lowest.
        Dice (or anything castable to a Die) may be provided as a list or as a variable number of arguments.
        """
        dice = BaseDie._align(dice)

        sweights = tuple(math.prod(t) for t in zip(*(die.sweights() for die in dice)))
            
        return hdroller.from_sweights(dice[0].outcomes(), sweights)
    
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
        a, b = BaseDie._align([self, other])
        return max(abs(a - b) for a, b in zip(self.cdf(), other.cdf()))
    
    def cvm_stat(self, other):
        """ Cramér-von Mises stat. The sum-of-squares difference between CDFs. """
        a, b = BaseDie._align([self, other])
        return sum((a - b) ** 2 for a, b in zip(self.cdf(), other.cdf()))
    
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
        
    # TODO: Dict statistics?
    
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
    
    # Alignment.
    
    @staticmethod
    def _listify_dice(args):
        if len(args) == 1 and hasattr(args[0], '__iter__') and not isinstance(args[0], BaseDie):
            args = args[0]
        
        return [hdroller.die(arg) for arg in args]
    
    def _set_outcomes(self, outcomes):
        """Returns a die whose outcomes are set to the argument.
        
        Note that public methods are intended to have no zero-weight outcomes.
        This should therefore not be used externally for any Die that you want to do anything with afterwards.
        """
        data = {x : self.weight(x) for x in outcomes}
        return hdroller.die(data, remove_zero_weights=False)
    
    def _align(*dice):
        """Pads all the dice with zero weights so that all have the same set of outcomes.
        
        Note that public methods are intended to have no zero-weight outcomes.
        This should therefore not be used externally for any Die that you want to do anything with afterwards.
        """
        dice = BaseDie._listify_dice(dice)
        
        union_outcomes = set(itertools.chain.from_iterable(die.outcomes() for die in dice))
        
        return tuple(die._set_outcomes(union_outcomes) for die in dice)
    
    # Hashing and equality.
    
    @cached_property
    def _key_tuple(self):
        return self.is_multi, tuple(self.items())
        
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