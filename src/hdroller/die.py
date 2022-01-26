import hdroller.math
from hdroller.pool import Pool
from hdroller.single_pool_scorer import SinglePoolScorer, pool_sum

from collections import defaultdict
from functools import cached_property, lru_cache
import numpy
import re

"""
Terminology:
outcomes: The numbers between the minimum and maximum rollable on a die (even if they have zero chance).
  These run from die.min_outcome() to die.max_outcome() inclusive.
  len(die) is the total number of outcomes.
weights: A relative probability of each outcome. This can have arbitrary positive sum, 
  but uses values equal to integers where possible, serving as a fraction that decays gracefully.
pmf: Probability mass function. The normalized version of the weights.
"""

class DieType(type):
    """
    Metaclass for Die. Used to enable shorthand for standard dice.
    """
    def __getattr__(self, key):
        if key[0] == 'd':
            die_size = int(key[1:])
            return Die.standard(die_size)
        raise AttributeError(key)

class Die(metaclass=DieType):
    """
    Immutable class representing a discrete probability distribution
    with finite support.
    """

    # Construction.
    def __new__(cls, die, *args, **kwargs):
        if isinstance(die, Die):
            # If already a Die, return the existing instance.
            if len(args) > 0:
                raise ValueError()
            if len(kwargs) > 0:
                raise ValueError()
            return die
        return super(Die, cls).__new__(cls)
    
    def __init__(self, weights, min_outcome=None):
        """
        Constructor. Arguments can be:
        * A Die, which is just itself.
        * weights (array-like) and min_outcome (integer).
        * A dict-like mapping outcomes to weights.
        * A integer outcome, which produces a Die that always rolls that outcome.
        """
        if isinstance(weights, Die):
            return # Already returned same object by __new__().
        elif numpy.issubdtype(type(weights), numpy.integer):
            # Integer casts to die that always rolls that value.
            if min_outcome is not None: raise ValueError()
            min_outcome = weights
            weights = numpy.array([1.0])
        elif hasattr(weights, 'items'):
            # A dict mapping outcomes to weights.
            raw_weights = weights
            min_outcome = min(raw_weights.keys())
            max_outcome = max(raw_weights.keys())
            weights = numpy.zeros((max_outcome - min_outcome + 1,))
            for outcome, weight in raw_weights.items():
                weights[outcome - min_outcome] = weight
        else:
            # weights is an array.
            if min_outcome is None:
                raise TypeError('When Die is constructed with a weights array, min_outcome must be provided.')
            if not numpy.issubdtype(type(min_outcome), numpy.integer):
                raise TypeError('min_outcome must be of integer type, got ' + type(min_outcome).__name__)
            if numpy.any(numpy.isinf(weights)):
                raise ValueError('Weights must be finite.')
            weights = numpy.array(weights, dtype=float)
            if weights.ndim != 1:
                raise ValueError('Weights must have exactly one dimension.')
        
        # Trim the Die.
        nz = numpy.nonzero(weights)[0]
        min_outcome += nz[0]
        weights = numpy.array(weights[nz[0]:nz[-1]+1], dtype=float)
        
        self._weights = weights
        self._weights.setflags(write=False)
        self._min_outcome = min_outcome
        
        if len(self._weights) == 0:
            raise ValueError('Die cannot have empty weights.')
        
        if numpy.isinf(self._total_weight) or (self._total_weight <= 0.0 and numpy.any(self._weights > 0.0)):
            raise OverflowError('Total weight is not representable by a float64.')
        
        if self._total_weight <= 0.0:
            raise ZeroDivisionError('Die cannot be constructed with zero weight.')
    
    @classmethod
    def _create_untrimmed(cls, weights, min_outcome):
        self = cls.__new__(cls, None)
        self._weights = numpy.array(weights, dtype=float)
        self._weights.setflags(write=False)
        self._min_outcome = min_outcome
        return self
    
    # Cached values.
    
    @cached_property
    def _total_weight(self):
        return numpy.cumsum(self._weights)[-1]
    
    @cached_property
    def _pmf(self):
        result = self._weights / self._total_weight
        result.setflags(write=False)
        return result
    
    @cached_property
    def _is_exact(self):
        is_all_integer = numpy.all(self._weights == numpy.floor(self._weights))
        is_sum_in_range = self._total_weight < hdroller.math.MAX_INT_FLOAT
        return is_all_integer and is_sum_in_range
        
    @cached_property
    def _cweights(self):
        result = numpy.cumsum(self.weights())
        result = numpy.insert(result, 0, 0.0)
        result.setflags(write=False)
        return result
        
    @cached_property
    def _sweights(self):
        result = hdroller.math.reverse_cumsum(self.weights())
        result = numpy.append(result, 0.0)
        result.setflags(write=False)
        return result
    
    @cached_property
    def _cdf(self):
        result = self._cweights / self.total_weight()
        result.setflags(write=False)
        return result
    
    @cached_property
    def _sf(self):
        result = self._sweights / self.total_weight()
        result.setflags(write=False)
        return result
    
    # Creation.
    
    @staticmethod
    @lru_cache(maxsize=None)
    def standard(num_faces):
        if num_faces < 1: raise ValueError('Standard dice must have at least 1 face.')
        return Die(numpy.ones((num_faces,)), 1)
    
    # TODO: Apply cache to all __new__ dice created with floats?
    @staticmethod
    def bernoulli(chance=0.5, denominator=1.0):
        return Die([denominator - chance, chance], 0)

    coin = bernoulli
    
    @staticmethod
    def d(*args):
        """
        Dice chaining, with integers other than the first argument treated as standard dice (rather than integers).
        Exception: If there is only a single argument, a 1 is implicitly prepended to the argument list.
        Each argument is rolled, and that many of the outcome is rolled on whatever is behind it.
        
        Examples:
        d(6) = d6
        d(6, 6) = 6d6 = roll d6 six times and add them up
        d(1, 6, 6) = 1d6d6 = roll a d6, then roll that many d6s and add them up
        """
        if len(args) == 1:
            args = (1,) + args
        return args[0] * Die._d(*args[1:])
    
    @staticmethod
    def _d(*args):
        """
        Implementation of Die.d().
        """
        if len(args) == 0:
            return Die(1)
        
        tail_die = Die._d(*args[1:])
        
        num_dice = args[0]
        if numpy.issubdtype(type(num_dice), numpy.integer):
            num_dice = Die.standard(num_dice)
        else:
            num_dice = Die(args[0])

        return num_dice * tail_die
     
    @staticmethod
    def from_cweights(cweights, min_outcome, total_weight_if_exclusive=None):
        """
        Constructs a Die from cumulative weights.
        If cweights is exclusive, set total_weight_if_exclusive to the total weight of the die.
        """
        if not total_weight_if_exclusive:
            weights = numpy.diff(cweights, prepend=0.0)
        else:
            weights = numpy.diff(cweights, append=total_weight_if_exclusive)
        return Die(weights, min_outcome)
    
    @staticmethod
    def from_sweights(sweights, min_outcome, total_weight_if_exclusive=None):
        """
        Constructs a Die from reversed cumulative weights.
        If sweights is exclusive, set total_weight_if_exclusive to the total weight of the die.
        """
        if not total_weight_if_exclusive:
            weights = numpy.flip(numpy.diff(numpy.flip(sweights), prepend=0.0))
        else:
            weights = numpy.flip(numpy.diff(numpy.flip(sweights), append=total_weight_if_exclusive))
        return Die(weights, min_outcome)
    
    @staticmethod
    def from_cdf(cdf, min_outcome, inclusive=True):
        if inclusive is True:
            pmf = numpy.diff(cdf, prepend=0.0)
        else:
            pmf = numpy.diff(cdf, append=1.0)
        return Die(pmf, min_outcome)

    @staticmethod
    def from_sf(sf, min_outcome, inclusive=True):
        if inclusive is True:
            pmf = numpy.flip(numpy.diff(numpy.flip(sf), prepend=0.0))
        else:
            pmf = numpy.flip(numpy.diff(numpy.flip(sf), append=1.0))
        return Die(pmf, min_outcome)
    
    @staticmethod
    def from_rv(rv, min_outcome, max_outcome, **kwargs):
        """
        Constructs a die by discretizing a supplied rv object (as scipy.stats).
        Any additional arguments are provided to rv.cdf().
        
        For example,
        Die.from_rv(scipy.stats.norm, -40, 40, scale=10)
        would discretize a normal distribution with a standard deviation of 10.
        
        Values beyond min/max outcome are clipped.
        """
        x = numpy.arange(min_outcome, max_outcome)
        if hasattr(rv, 'pdf'):
            # Continuous distributions get rounded.
            x = x + 0.5
        cdf = rv.cdf(x, **kwargs)
        cdf = numpy.append(cdf, 1.0)
        return Die.from_cdf(cdf, min_outcome)
    
    # Outcome information.
    def __len__(self):
        return len(self._weights)

    def min_outcome(self):
        return self._min_outcome

    def max_outcome(self):
        return self.min_outcome() + len(self) - 1

    def outcomes(self):
        return numpy.arange(self.min_outcome(), self.max_outcome() + 1)
        
    def probability(self, outcome):
        """
        Returns the probability of a single outcome.
        """
        if outcome < self.min_outcome() or outcome > self.max_outcome():
            return 0.0
        else:
            return self.pmf()[outcome - self.min_outcome()]

    # Distributions.
        
    def is_exact(self):
        return self._is_exact
    
    def is_bernoulli(self):
        return self.min_outcome() >= 0 and self.max_outcome() <= 1
    
    is_coin = is_bernoulli
        
    def weights(self):
        return self._weights
    
    def pmf(self):
        return self._pmf
        
    def cweights(self, inclusive=True):
        """ 
        When zipped with outcomes(), this is the weight of rolling <= the corresponding outcome.
        inclusive: If False, changes the comparison to <.
        """
        if inclusive is True:
            return self._cweights[1:]
        elif inclusive is False:
            return self._cweights[:-1]
        elif inclusive == 'both':
            return self._cweights
        elif inclusive == 'neither':
            return self._cweights[1:-1]
            
    def sweights(self, inclusive=True):
        """
        When zipped with outcomes(), this is the weight of rolling >= the corresponding outcome.
        inclusive: If False, changes the comparison to >. If 'both', includes both endpoints.
        """
        if inclusive is True:
            return self._sweights[:-1]
        elif inclusive is False:
            return self._sweights[1:]
        elif inclusive == 'both':
            return self._sweights
        elif inclusive == 'neither':
            return self._sweights[1:-1]
    
    def cdf(self, inclusive=True):
        """ 
        When zipped with outcomes(), this is the probability of rolling <= the corresponding outcome.
        inclusive: If False, changes the comparison to <.
          If 'both', includes both endpoints and should be zipped with outcomes(prepend=True).
        """
        if inclusive is True:
            return self._cdf[1:]
        elif inclusive is False:
            return self._cdf[:-1]
        elif inclusive == 'both':
            return self._cdf
        elif inclusive == 'neither':
            return self._cdf[1:-1]

    def sf(self, inclusive=True):
        """
        When zipped with outcomes(), this is the probability of rolling >= the corresponding outcome.
        inclusive: If False, changes the comparison to >. If 'both', includes both endpoints.
          If 'both', includes both endpoints and should be zipped with outcomes(append=True).
        """
        if inclusive is True:
            return self._sf[:-1]
        elif inclusive is False:
            return self._sf[1:]
        elif inclusive == 'both':
            return self._sf
        elif inclusive == 'neither':
            return self._sf[1:-1]
        
    # Statistics.
    def mean(self):
        return numpy.sum(self.pmf() * self.outcomes())
        
    def median(self):
        score = numpy.minimum(self.cweights(), self.sweights())
        mask = (score == numpy.max(score))
        return numpy.mean(self.outcomes()[mask])
    
    def mode(self):
        """
        Returns an outcome with the highest single weight.
        """
        return numpy.argmax(self.weights()) + self.min_outcome()
    
    def mode_weight(self):
        return numpy.max(self.weights())
    
    def mode_mass(self):
        return numpy.max(self.pmf())
    
    def variance(self):
        mean = self.mean()
        mean_of_squares = numpy.sum(self.pmf() * self.outcomes() * self.outcomes())
        return mean_of_squares - mean * mean
    
    def standard_deviation(self):
        return numpy.sqrt(self.variance())
        
    def standardized_moment(self, k):
        sd = self.standard_deviation()
        mean = self.mean()
        ev = numpy.sum(self.pmf() * numpy.power((self.outcomes() - mean), k))
        return ev / numpy.power(sd, k)
    
    def skewness(self):
        return self.standardized_moment(3.0)
    
    def excess_kurtosis(self):
        return self.standardized_moment(4.0) - 3.0
        
    def ks_stat(self, other):
        """ Kolmogorov–Smirnov stat. The maximum absolute difference between CDFs. """
        a, b = Die._align([self, other])
        return numpy.max(numpy.abs(a.cdf() - b.cdf()))
    
    def cvm_stat(self, other):
        """ Cramér-von Mises stat. The sum-of-squares difference between CDFs. """
        a, b = Die._align([self, other])
        return numpy.linalg.norm(a.cdf() - b.cdf())
    
    def total_weight(self):
        return self._total_weight

    # Operations that don't involve other dice.
    
    def __neg__(self):
        """ Returns a Die with all outcomes negated. """
        return Die(numpy.flip(self.weights()), -self.max_outcome())
        
    def __abs__(self):
        """ Take the absolute value of all outcomes. """
        if self.min_outcome() >= 0: return self
        if self.max_outcome() <= 0: return -self
        
        # If the die doesn't fall into either of the simple cases above,
        # it crosses zero.
        max_outcome = max(-self.min_outcome(), self.max_outcome())
        weights = numpy.zeros((max_outcome + 1,))
        
        zero_index = -self.min_outcome()
        num_non_negative = len(self.outcomes()) - zero_index
        weights[:num_non_negative] += self.weights()[zero_index:]
        weights[1:zero_index+1] += numpy.flip(self.weights()[:zero_index])
        
        return Die(weights, 0)
    
    abs = __abs__
    
    @cached_property
    def _popped(self):
        if len(self) == 1 or self.cweights()[-2] == 0.0:
            return None, self.max_outcome(), self.weights()[-1]
        else:
            return Die(self.weights()[:-1], self.min_outcome()), self.max_outcome(), self.weights()[-1]
    
    def popped(self):
        """
        Retruns a Die like this with the max outcome removed.
        
        Returns:
            A Die with the max outcome removed, or None if the last outcome is removed.
            The removed outcome.
            The weight of the removed outcome.
        """
        return self._popped
    
    # Roller wins ties by default. This returns a die that effectively has the given tiebreak mode.
    def tiebreak(self, mode):
        if mode == 'win': return self
        elif mode == 'lose': return self - 1
        elif mode == 'coin': return self - Die.coin(0.5)
        elif mode == 'reroll': return self.reroll([0])
        else: raise ValueError('Invalid tiebreak mode "%s"' % mode)

    # Operations with another Die. Non-Die operands will be cast to Die.
    def _add(self, other):
        """
        Helper for adding two dice.
        other must already be a Die.
        """
        weights = numpy.convolve(self.weights(), other.weights())
        min_outcome = self.min_outcome() + other.min_outcome()
        return Die(weights, min_outcome)
    
    def __add__(self, other):
        other = Die(other)
        return self._add(other)
    
    def __radd__(self, other):
        other = Die(other)
        return other._add(self)

    def __sub__(self, other):
        other = Die(other)
        return self._add(-other)
    
    def __rsub__(self, other):
        other = Die(other)
        return other._add(-self)

    def __mul__(self, other):
        """
        This computes the result of rolling the dice on the left, and then rolling that many dice on the right and summing them.
        Note that this is NOT commutative; a * b is not in general the same as b * a.
        """
        other = Die(other)
        
        subresults = []
        subresult_weights = []
        
        max_abs_die_count = max(abs(self.min_outcome()), abs(self.max_outcome()))
        
        for die_count, die_count_weight in zip(self.outcomes(), self.weights()):
            if die_count_weight > 0.0:
                factor = numpy.power(other.total_weight(), max_abs_die_count - abs(die_count))
                subresults.append(other.repeat_and_sum(die_count))
                subresult_weights.append(die_count_weight * factor)
        
        subresults = Die._align(subresults)
        weights = sum(subresult.weights() * subresult_weight for subresult, subresult_weight in zip(subresults, subresult_weights))
        
        return Die(weights, subresults[0].min_outcome())
    
    def __rmul__(self, other):
        return Die(other) * self
    
    def clip(self, min_outcome=None, max_outcome=None):
        """
        Restricts the outcomes of this die to the range [min_outcome, max_outcome].
        A Die can be supplied instead, in which case the range is taken from that die.
        """
        if isinstance(min_outcome, Die):
            min_outcome = min_outcome.min_outcome()
            max_outcome = min_outcome.max_outcome()
        else:
            if min_outcome is None: min_outcome = self.min_outcome()
            if max_outcome is None: max_outcome = self.max_outcome()
        left = max(0, min_outcome - self.min_outcome())
        right = len(self) + min(0, max_outcome - self.max_outcome())
        weights = numpy.copy(self.weights()[left:right])
        weights[0] += numpy.sum(self.weights()[:left])
        weights[-1] += numpy.sum(self.weights()[right:])
        return Die(weights, max(self.min_outcome(), min_outcome))
    
    # Repeat, keep, and sum.
    def max(*dice):
        """
        Roll all the dice and take the highest.
        Dice (or anything castable to a Die) may be provided as a list or as a variable number of arguments.
        """
        dice = Die._listify_dice(dice)
        dice_aligned = Die._align(dice)
        cweights = 1.0
        for die in dice_aligned: cweights *= die.cweights()
        return Die.from_cweights(cweights, dice_aligned[0].min_outcome())
    
    def min(*dice):
        """
        Roll all the dice and take the lowest.
        Dice (or anything castable to a Die) may be provided as a list or as a variable number of arguments.
        """
        dice = Die._listify_dice(dice)
        dice_aligned = Die._align(dice)
        sweights = 1.0
        for die in dice_aligned: sweights *= die.sweights()
        return Die.from_sweights(sweights, dice_aligned[0].min_outcome())
    
    def repeat_and_sum(self, num_dice):
        """
        Returns a Die representing:
        Roll this Die `num_dice` times and sum the results.
        """
        if num_dice < 0:
            return (-self).repeat_and_sum(-num_dice)
        elif num_dice == 0:
            return Die(0)
        elif num_dice == 1:
            return self
        half_result = self.repeat_and_sum(num_dice // 2)
        result = half_result + half_result
        if num_dice % 2: result += self
        return result
    
    def keep(self, max_outcomes, mask=None):
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
        pool = Pool(self, max_outcomes, mask)
        return pool_sum.evaluate(pool)
        
    def keep_highest(self, max_outcomes, num_keep=1, num_drop=0):
        """
        Roll this Die several times, possibly capping the maximum outcomes, and sum the sorted results from the highest.
        
        Arguments:
            max_outcomes: Either:
                * An iterable indicating the maximum outcome for each die in the pool.
                * An integer indicating the number of dice in the pool; all dice will have max_outcome equal to die.max_outcome().
            num_keep: The number of dice to keep.
            num_drop: If provided, this many highest dice will be dropped before keeping.
                
        Returns:
            A Die representing the probability distribution of the sum.
        """
        start = -(num_keep + (num_drop or 0))
        stop = -num_drop if num_drop > 0 else None
        mask = slice(start, stop)
        return self.keep(max_outcomes, mask)
        
    def keep_lowest(self, max_outcomes, num_keep=1, num_drop=0):
        """
        Roll this Die several times, possibly capping the maximum outcomes, and sum the sorted results from the lowest.
        
        Arguments:
            max_outcomes: Either:
                * An iterable indicating the maximum outcome for each die in the pool.
                * An integer indicating the number of dice in the pool; all dice will have max_outcome equal to die.max_outcome().
            num_keep: The number of dice to keep.
            num_drop: If provided, this many lowest dice will be dropped before keeping.
                
        Returns:
            A Die representing the probability distribution of the sum.
        """
        start = num_drop if num_drop > 0 else None
        stop = num_keep + (num_drop or 0)
        mask = slice(start, stop)
        return self.keep(max_outcomes, mask)
        
    # Operations with integers only.
    
    def __mod__(self, divisor):
        weights = numpy.zeros((divisor,))
        for outcome, weight in zip(self.outcomes(), self.weights()):
            weights[outcome % divisor] += weight
        return Die(weights, 0)
    
    def __floordiv__(self, divisor):
        min_outcome = self.min_outcome() // divisor
        max_outcome = self.max_outcome() // divisor
        weights = numpy.zeros((max_outcome - min_outcome + 1,))
        for outcome, weight in zip(self.outcomes(), self.weights()):
            weights[outcome // divisor] += weight
        return Die(weights, min_outcome)

    # Comparators. These return a Die.
    
    def __lt__(self, other):
        """
        Returns the chance this Die will roll < the other Die.     
        This is in the form of a Die that rolls 1 with that chance, and 0 otherwise.
        """
        other = Die(other)
        difference = self - other
        if difference.min_outcome() < 0:
            n = numpy.sum(difference.weights()[:-difference.min_outcome()])
            d = difference.total_weight()
            return Die.bernoulli(n, d)
        else:
            return Die(0)

    def __le__(self, other):
        """
        Returns the chance this Die will roll <= the other Die.
        This is in the form of a Die that rolls 1 with that chance, and 0 otherwise.        
        """
        return self < other + 1

    def __gt__(self, other):
        """
        Returns the chance this Die will roll > the other Die.
        This is in the form of a Die that rolls 1 with that chance, and 0 otherwise.
        """
        other = Die(other)
        return other < self

    def __ge__(self, other):
        """
        Returns the chance this Die will roll >= the other Die.
        This is in the form of a Die that rolls 1 with that chance, and 0 otherwise.
        """
        other = Die(other)
        return other <= self
        
    def equal(self, other):
        """
        Returns the chance this Die will roll == the other Die.
        This is in the form of a Die that rolls 1 with that chance, and 0 otherwise.
        """
        other = Die(other)
        a, b = Die._align([self, other])
        n = numpy.dot(a.weights(), b.weights())
        d = a.total_weight() * b.total_weight()
        return Die.bernoulli(n, d)
    
    # Logical operators.
    # These are only applicable to Bernoulli distributions, i.e. Die that have no outcomes other than 0 and 1.
    # These return a Die.
    
    def __invert__(self):
        if not self.is_bernoulli():
            raise ValueError('Logical operators can only be applied to Bernoulli distributions.')
        return 1 - self
        
    def _and(self, other):
        if not self.is_bernoulli() or not other.is_bernoulli():
            raise ValueError('Logical operators can only be applied to Bernoulli distributions.')
        return (self + other).equal(2)
        
    def __and__(self, other):
        return self._and(Die(other))
    
    def __rand__(self, other):
        return self._and(Die(other))
        
    def _or(self, other):
        if not self.is_bernoulli() or not other.is_bernoulli():
            raise ValueError('Logical operators can only be applied to Bernoulli distributions.')
        return (self + other) >= 1
        
    def __or__(self, other):
        return self._or(Die(other))
    
    def __ror__(self, other):
        return self._or(Die(other))
    
    def _xor(self, other):
        if not self.is_bernoulli() or not other.is_bernoulli():
            raise ValueError('Logical operators can only be applied to Bernoulli distributions.')
        return (self + other).equal(1)
        
    def __xor__(self, other):
        return self._xor(Die(other))
    
    def __rxor__(self, other):
        return self._xor(Die(other))
    
    # Mixtures.
    
    @staticmethod
    def mix(*dice, mix_weights=None):
        """
        Constructs a Die from a mixture of the arguments,
        equivalent to rolling a die and then choosing one of the arguments
        based on the resulting face rolled.
        Dice (or anything castable to a Die) may be provided as a list or as a variable number of arguments.
        mix_weights: An array of one weight per argument.
            If not provided, all arguments are mixed uniformly.
        """
        dice = Die._listify_dice(dice)
        dice = Die._align(dice)
        
        lcm = numpy.lcm.reduce([int(die.total_weight()) for die in dice])
        
        if mix_weights is None:
            mix_weights = numpy.ones((len(dice),))

        weights = numpy.zeros_like(dice[0].weights())
        for die, mix_weight in zip(dice, mix_weights):
            weights += mix_weight * die.weights() * (lcm / die.total_weight())
        return Die(weights, dice[0].min_outcome())
    
    def relabel(self, relabeling):
        """
        relabeling can be one of the following:
        * An array-like containing relabelings, one for each face in order.
        * A dict-like mapping old outcomes to new outcomes.
            Unmapped old outcomes stay the same.
        * A function mapping old outcomes to new outcomes.
        
        A Die may be provided instead of a single new outcome.
        """
        if hasattr(relabeling, 'items'):
            relabeling = [(relabeling[outcome] if outcome in relabeling else outcome) for outcome in self.outcomes()]
        elif callable(relabeling):
            relabeling = [relabeling(outcome) for outcome in self.outcomes()]

        return Die.mix(*relabeling, mix_weights=self.weights())

    def explode(self, max_times, outcomes=None):
        """
        outcomes: This chooses which outcomes to explode. Options:
            * A single integer outcome to explode.
            * A dict whose keys are outcomes and values are chances for that outcome to explode.
            * An iterable containing outcomes to explode.
            * If not supplied, the top single outcome will explode.
        """
        if max_times < 0:
            raise ValueError('max_times cannot be negative.')
        if max_times == 0:
            return self
        
        if outcomes is None:
            outcomes = self.max_outcome()
        
        explode_weights = self._select_weights(outcomes)
        
        non_explode_weights = self.weights() - explode_weights
        
        non_explode_die = Die(non_explode_weights, self.min_outcome())
        tail_die = self.explode(max_times-1, outcomes=outcomes)
        explode_die = Die(explode_weights, self.min_outcome()) + tail_die
        
        non_explode_die, explode_die = Die._align(non_explode_die, explode_die)
        weights = non_explode_die.weights() * tail_die.total_weight() + explode_die.weights()
        
        return Die(weights, non_explode_die.min_outcome())
    
    def reroll(self, outcomes=None, max_times=None):
        """Rerolls the given outcomes.
        
        Args:
            outcomes: Selects which outcomes to reroll. Options:
                * A single integer outcome to reroll.
                * A dict whose keys are outcomes and values are chances for that outcome to reroll.
                * An iterable containing outcomes to reroll.
            max_times: The maximum number of times to reroll.
                If omitted, rerolls an unlimited number of times.
        
        Returns:
            A Die representing the reroll.
            If the reroll would never terminate, the result is None.
        """
        if outcomes is None:
            raise TypeError('outcomes to reroll must be provided.')
        reroll_weights = self._select_weights(outcomes)
        non_reroll_weights = self.weights() - reroll_weights
        
        if max_times is None:
            if numpy.sum(non_reroll_weights) <= 0.0:
                return None
            weights = non_reroll_weights
        else:
            total_reroll_weight = numpy.sum(reroll_weights)
            rerollable_factor = numpy.power(total_reroll_weight, max_times)
            stop_factor = (numpy.power(self.total_weight(), max_times+1) - numpy.power(total_reroll_weight, max_times+1)) / (self.total_weight() - total_reroll_weight)
            weights = rerollable_factor * reroll_weights + stop_factor * non_reroll_weights
        return Die(weights, self.min_outcome())
    
    def combine(*dice, func=None):
        """
        Dice (or anything castable to a Die) may be provided as a list or as a variable number of arguments.
        func should be a function that takes in one outcome for each of the dice and outputs an integer outcome.
        
        This method is very flexible but has poor performance since it enumerates all possible joint outcomes.
        Other methods should be preferred when performance is a concern.
        See also Pool, SinglePoolScorer, and MultiPoolScorer.
        """
        
        if func is None:
            raise TypeError('func must be provided')
        
        dice = Die._listify_dice(dice)
        
        pmf_dict = defaultdict(float)
        
        def inner(partial_outcomes, partial_weight, dice):
            if len(dice) == 0:
                outcome = func(*partial_outcomes)
                pmf_dict[outcome] += partial_weight
            else:
                for outcome, weight in zip(dice[0].outcomes(), dice[0].weights()):
                    inner(partial_outcomes + [outcome], partial_weight * weight, dice[1:])
        
        inner([], 1.0, dice)
        
        return Die(pmf_dict)
        
    # Alignment.
    
    def _align(*dice):
        """ 
        Pads all the dice with zeros so that all have the same min_outcome and max_outcome.
        Note that, unlike most methods, this may leave leading or trailing zero weights.
        This should therefore not be used externally for any Die that you want to do anything with afterwards.
        """
        dice = Die._listify_dice(dice)
        
        min_outcome = min(die.min_outcome() for die in dice)
        max_outcome = max(die.max_outcome() for die in dice)
        len_align = max_outcome - min_outcome + 1

        result = []
        for die in dice:
            left_dst_index = die.min_outcome() - min_outcome
            weights = numpy.zeros((len_align,))
            weights[left_dst_index:left_dst_index + len(die.weights())] = die.weights()
            result.append(Die._create_untrimmed(weights, min_outcome))
        
        return tuple(result)
    
    # Random sampling.
    def sample(self, size=None):
        """
        Returns a random sample from this Die.        
        """
        return numpy.random.choice(self.outcomes(), size=size, p=self.pmf())

    # Out conversions.
    
    def __str__(self):
        """
        Formats the Die as a Markdown table.
        """
        if self.is_exact():
            result = f'| Outcome | Weight (out of {int(self.total_weight())}) | Probability |\n'
            result += '|----:|----:|----:|\n'
            for outcome, weight, p in zip(self.outcomes(), self.weights(), self.pmf()):
                result += f'| {int(outcome)} | {int(weight)} | {p:.3%} |\n'
        else:
            result = '| Outcome | Probability |\n'
            result += '|----:|----:|\n'
            for outcome, p in zip(self.outcomes(), self.pmf()):
                result += f'| {int(outcome)} | {p:.3%} |\n'
        return result
        
    def __float__(self):
        if not self.is_bernoulli():
            raise ValueError('Only Bernoulli distributions may be cast to float.')
        return float(self.probability(1))
    
    def __bool__(self):
        return bool(self.total_weight() > 0.0)
        
    # Hashing and equality.
    
    @cached_property
    def _key_tuple(self):
        return (self.min_outcome(),) + tuple(self.weights())
        
    def __eq__(self, other):
        """
        Returns true iff this Die has the same weights as the other Die.
        Note that fractions are not reduced.
        For example a 1:1 coin flip is NOT considered == to a 2:2 coin flip.
        """
        if not isinstance(other, Die): return False
        return self._key_tuple == other._key_tuple
    
    @cached_property
    def _hash(self):
        return hash(self._key_tuple)
        
    def __hash__(self):
        return self._hash

    # Helper methods.
    
    @staticmethod
    def _listify_dice(args):
        if len(args) == 1 and hasattr(args[0], '__iter__') and not isinstance(args[0], Die):
            args = args[0]
        
        return [Die(arg) for arg in args]
    
    def _select_weights(self, outcomes):
        """
        Returns an array of weights chosen by the argument.
        """
        factors = numpy.zeros_like(self.weights())
        if numpy.issubdtype(type(outcomes), numpy.integer):
            factors[outcomes - self._min_outcome] = 1.0 
        elif hasattr(outcomes, 'items'):
            # Dict-like.
            for outcome, factor in outcomes.items():
                factors[outcome - self._min_outcome] = factor
        elif hasattr(outcomes, '__iter__'):
            for outcome in outcomes:
                factors[outcome - self._min_outcome] = 1.0
        else:
            raise TypeError('Invalid type for selecting outcomes.')
        
        return factors * self.weights()
