import hdroller
from hdroller.cache import cache, cached_property
from hdroller.containers import WeightDict

class DieBase():
    # Abstract methods.
    
    @property
    def is_multi(self):
        """True iff this die is multivariate, i.e. operates on outcomes elementwise."""
        raise NotImplementedError()
    
    def unary_op(self, op, *args):
        """Returns a die representing the effect of performing the operation on the outcomes."""
        raise NotImplementedError()
    
    def binary_op(self, other, op, *args):
        """Returns a die representing the effect of performing the operation on pairs of outcomes."""
        raise NotImplementedError()
        
    # Construction.

    def __init__(self, data):
        """Users should usually not construct dice directly;
        instead they should use one of the methods defined in
        hdroller.die_create (which are imported into the 
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
        return self.items()
    
    # Scalar statistics.
    
    def min_outcome(self):
        return self._data.peekitem(0)[0]
    
    def max_outcome(self):
        return self._data.peekitem(-1)[0]
    
    @cached_property
    def _total_weight(self):
        return sum(self._data.values())
    
    def total_weight(self):
        return _total_weight
    
    @cached_property
    def _mean(self):
        return sum(outcome * p for outcome, p in zip(self.outcomes(), self.pmf()))
    
    def mean(self):
        return self._mean
    
    # Iterable statistics.
    
    def cweights(self):
        yield from itertools.accumulate(self.weights())
    
    def sweights(self):
        yield from itertools.accumulate(self.weights(), operator.sub, self.total_weight())
    
    def pmf(self):
        yield from (weight / self.total_weight() for weight in self.weights())
    
    def cdf(self):
        yield from (weight / self.total_weight() for weight in self.cweights())
        
    def sf(self):
        yield from (weight / self.total_weight() for weight in self.sweights())
        
    # Dict statistics.
    
    # Unary operators.
    
    def __neg__(self):
        return self.unary_op(operator.neg)
    
    def __abs__(self):
        return self.unary_op(operator.abs)
    
    abs = __abs__
    
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
        subresults = []
        subresult_weights = []
        
        max_abs_die_count = max(abs(self.min_outcome()), abs(self.max_outcome()))
        for die_count, die_count_weight in self.items():
            factor = numpy.power(other.total_weight(), max_abs_die_count - abs(die_count))
            subresults.append(other.repeat_and_sum(die_count))
            subresult_weights.append(die_count_weight * factor)
        
        subresults = Die._align(subresults)
        data = WeightDict()
        for subresult, subresult_weight in zip(subresults, subresult_weights):
            for outcome, weight in subresult.items():
                data[outcome] += weight * subresult_weight
            
        return hdroller.die(data)
    
    def __rmul__(self, other):
        other = hdroller.die(other)
        return other.__mul__(self)
    
    # Alignment.
    
    def _align(*dice):
        