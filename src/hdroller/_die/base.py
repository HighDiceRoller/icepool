import hdroller
from hdroller.cache import cache, cached_property
from hdroller.containers import DieDataDict

from collections import defaultdict
import itertools
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
        return self._data.get(outcome, 0)
    
    def items(self):
        return self._data.items()
    
    def __len__(self):
        return len(self._data)
    
    # Scalar statistics.
    
    def min_outcome(self):
        return self._data.peekitem(0)[0]
    
    def max_outcome(self):
        return self._data.peekitem(-1)[0]
    
    @cached_property
    def _total_weight(self):
        return sum(self._data.values())
    
    def total_weight(self):
        return self._total_weight
    
    @cached_property
    def _mean(self):
        return sum(outcome * p for outcome, p in zip(self.outcomes(), self.pmf()))
    
    def mean(self):
        return self._mean
    
    # Iterable statistics.
    
    def cweights(self):
        yield from itertools.accumulate(self.weights())
    
    def sweights(self):
        yield from itertools.accumulate(self.weights()[:-1], operator.sub, initial=self.total_weight())
    
    def pmf(self):
        yield from (weight / self.total_weight() for weight in self.weights())
    
    def cdf(self):
        yield from (weight / self.total_weight() for weight in self.cweights())
        
    def sf(self):
        yield from (weight / self.total_weight() for weight in self.sweights())
        
    # TODO: Dict statistics.
    
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
        return hdroller.die(data)
    
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