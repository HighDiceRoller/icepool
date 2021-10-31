import hdroller.countdown
import hdroller.math

from collections import defaultdict
from functools import cached_property, lru_cache
import numpy
import re

"""
Terminology:
outcomes: The numbers between the minimum and maximum rollable on a die (even if they have zero chance).
  These run from die.min_outcome() to die.max_outcome() inclusive.
  len(die) is the total number of outcomes.
faces: Equal to outcomes - die.min_outcome, so they always run from 0 to len(die) - 1.
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
    Immutable class representing a normalized discrete probability distribution
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
        * weights (array-like) and min_outcome (integer).
        * int: A die which always rolls that outcome.
        * float in [0, 1]: A die which has that chance of rolling 1, and rolls 0 otherwise.
        """
        # TODO: Decide whether to check for exactness and reduce fractions here.
        if isinstance(weights, Die):
            return # Already returned same object by __new__().
        elif numpy.issubdtype(type(weights), numpy.integer):
            # Integer casts to die that always rolls that value.
            if min_outcome is not None: raise ValueError()
            self._weights = numpy.array([1.0])
            self._min_outcome = weights
        elif hasattr(weights, 'items'):
            # A dict mapping outcomes to weights.
            self._min_outcome = min(weights.keys())
            max_outcome = max(weights.keys())
            self._weights = numpy.zeros((max_outcome - self._min_outcome + 1,))
            for outcome, weight in weights.items():
                self._weights[outcome - self._min_outcome] = weight
        else:
            if min_outcome is None:
                raise TypeError('When Die is constructed with a weights array, min_outcome must be provided.')
            # weights is an array.
            if not numpy.issubdtype(type(min_outcome), numpy.integer):
                raise ValueError('min_outcome must be of integer type')
            if numpy.any(numpy.isinf(weights)):
                raise ValueError('Weights must be finite.')
            self._weights = numpy.array(weights, dtype=float)
            if self._weights.ndim != 1:
                raise ValueError('Weights must have exactly one dimension.')
            self._min_outcome = min_outcome
        
        total_weight = self._total_weight_no_cache()
        if total_weight >= hdroller.math.MAX_INT_FLOAT:
            self._weights /= total_weight
        
        self._weights.setflags(write=False)
    
    # Cached values.
    def _total_weight_no_cache(self):
        # This is used instead of numpy.sum to ensure consistency with cweights/ccweights.
        return numpy.cumsum(self._weights)[-1]
    
    @cached_property
    def _total_weight(self):
        return self._total_weight_no_cache()
    
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
    def _ccweights(self):
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
    def _ccdf(self):
        result = self._ccweights / self.total_weight()
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
    def from_ccweights(ccweights, min_outcome, total_weight_if_exclusive=None):
        """
        Constructs a Die from reversed cumulative weights.
        If ccweights is exclusive, set total_weight_if_exclusive to the total weight of the die.
        """
        if not total_weight_if_exclusive:
            weights = numpy.flip(numpy.diff(numpy.flip(ccweights), prepend=0.0))
        else:
            weights = numpy.flip(numpy.diff(numpy.flip(ccweights), append=total_weight_if_exclusive))
        return Die(weights, min_outcome)
    
    @staticmethod
    def from_cdf(cdf, min_outcome, inclusive=True):
        if inclusive is True:
            pmf = numpy.diff(cdf, prepend=0.0)
        else:
            pmf = numpy.diff(cdf, append=1.0)
        return Die(pmf, min_outcome)

    @staticmethod
    def from_ccdf(ccdf, min_outcome, inclusive=True):
        if inclusive is True:
            pmf = numpy.flip(numpy.diff(numpy.flip(ccdf), prepend=0.0))
        else:
            pmf = numpy.flip(numpy.diff(numpy.flip(ccdf), append=1.0))
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

    def outcomes(self, prepend=False, append=False):
        return numpy.array(range(self.min_outcome(), self.min_outcome() + len(self) + (append is not False))) + (prepend is not False)
        
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
          If 'both', includes both endpoints and should be zipped with outcomes(prepend=True).
        """
        if inclusive is True:
            return self._cweights[1:]
        elif inclusive is False:
            return self._cweights[:-1]
        elif inclusive == 'both':
            return self._cweights
        elif inclusive == 'neither':
            return self._cweights[1:-1]
            
    def ccweights(self, inclusive=True):
        """
        When zipped with outcomes(), this is the weight of rolling >= the corresponding outcome.
        inclusive: If False, changes the comparison to >. If 'both', includes both endpoints.
          If 'both', includes both endpoints and should be zipped with outcomes(append=True).
        """
        if inclusive is True:
            return self._ccweights[:-1]
        elif inclusive is False:
            return self._ccweights[1:]
        elif inclusive == 'both':
            return self._ccweights
        elif inclusive == 'neither':
            return self._ccweights[1:-1]
    
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

    def ccdf(self, inclusive=True):
        """
        When zipped with outcomes(), this is the probability of rolling >= the corresponding outcome.
        inclusive: If False, changes the comparison to >. If 'both', includes both endpoints.
          If 'both', includes both endpoints and should be zipped with outcomes(append=True).
        """
        if inclusive is True:
            return self._ccdf[:-1]
        elif inclusive is False:
            return self._ccdf[1:]
        elif inclusive == 'both':
            return self._ccdf
        elif inclusive == 'neither':
            return self._ccdf[1:-1]
        
    # Statistics.
    def mean(self):
        return numpy.sum(self.pmf() * self.outcomes())
        
    def median(self):
        score = numpy.minimum(self.cweights(), self.ccweights())
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
        a, b = Die.align([self, other])
        return numpy.max(numpy.abs(a.cdf() - b.cdf()))
    
    def cvm_stat(self, other):
        """ Cramér-von Mises stat. The sum-of-squares difference between CDFs. """
        a, b = Die.align([self, other])
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
        die_count_weights = []
        for die_count, die_count_weight in zip(self.outcomes(), self.weights()):
            if die_count_weight <= 0.0: continue
            subresults.append(other.repeat_and_sum(die_count))
            die_count_weights.append(die_count_weight)
        
        subresults = Die.align(subresults)
        weights = sum(subresult.weights() * die_count_weight for subresult, die_count_weight in zip(subresults, die_count_weights))
        
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
        dice_aligned = Die.align(dice)
        cweights = 1.0
        for die in dice_aligned: cweights *= die.cweights()
        return Die.from_cweights(cweights, dice_aligned[0].min_outcome()).trim()
    
    def min(*dice):
        """
        Roll all the dice and take the lowest.
        Dice (or anything castable to a Die) may be provided as a list or as a variable number of arguments.
        """
        dice = Die._listify_dice(dice)
        dice_aligned = Die.align(dice)
        ccweights = 1.0
        for die in dice_aligned: ccweights *= die.ccweights()
        return Die.from_ccweights(ccweights, dice_aligned[0].min_outcome()).trim()
    
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
    
    def keep(self, num_dice, keep_indexes, max_outcomes=None):
        """
        Returns a Die representing:
        Roll this Die `num_dice` times, sort them (in ascending order) and sum the dice in `keep_indexes`.
        max_outcomes: If provided, this limits the maximum outcomes of individual dice.
        """
        return hdroller.countdown.keep(num_dice, keep_indexes, die=self, max_outcomes=max_outcomes)
        
    def keep_highest(self, num_dice, num_keep=1, num_drop=0, max_outcomes=None):
        """
        Returns a Die representing:
        Roll this Die `num_dice` times and sum the `num_keep` highest.
        num_drop: If provided, this many highest dice will be dropped before keeping.
        max_outcomes: If provided, this limits the maximum outcomes of individual dice.
        """
        if num_dice <= num_drop or num_keep == 0:
            return Die(0)
        elif num_keep == 1 and num_drop == 0 and max_outcomes is None:
            return Die.from_cweights(numpy.power(self.cweights(), num_dice), self.min_outcome())
        
        start = -(num_keep + (num_drop or 0))
        stop = -num_drop if num_drop > 0 else None
        keep = slice(start, stop)
        return hdroller.countdown.keep(num_dice, keep, die=self, max_outcomes=max_outcomes)
        
    def keep_lowest(self, num_dice, num_keep=1, num_drop=0, max_outcomes=None):
        """
        Returns a Die representing:
        Roll this Die `num_dice` times and sum the `num_keep` lowest.
        num_drop: If provided, this many lowest dice will be dropped before keeping.
        max_outcomes: If provided, this limits the maximum outcomes of individual dice.
        """
        if num_dice <= num_drop or num_keep == 0:
            return Die(0)
        elif num_keep == 1 and num_drop == 0 and max_outcomes is None:
            return Die.from_ccweights(numpy.power(self.ccweights(), num_dice), self.min_outcome())
        
        start = num_drop if num_drop > 0 else None
        stop = num_keep + (num_drop or 0)
        keep = slice(start, stop)
        return hdroller.countdown.keep(num_dice, keep, die=self, max_outcomes=max_outcomes)
        
    def best_set(self, num_dice, score_func=None):
        """
        num_dice: The number of dice to roll.
        score_func: A function set_size, set_outcome -> score.
          If not provided, a default function will be used that prioritizes set size, then outcome.
        """
        return hdroller.countdown.best_set(self, num_dice, score_func)

    # Comparators. These return a Die.
    
    def __eq__(self, other):
        """
        Returns the chance this die will roll exactly equal to the other Die.
        This is in the form of a Die that rolls 1 with that chance, and 0 otherwise.
        """
        other = Die(other)
        a, b = Die.align([self, other])
        n = numpy.dot(a.weights(), b.weights())
        d = a.total_weight() * b.total_weight()
        return Die.bernoulli(n, d)
    
    def __ne__(self, other):
        return 1.0 - (self == other)
    
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
    
    # Logical operators.
    # These are only applicable to Bernoulli distributions, i.e. Die that have no outcomes other than 0 and 1.
    # These return a Die.
    
    def __invert__(self):
        if not self.is_bernoulli():
            raise ValueError('Logical operators can only be applied to Bernoulli distributions.')
        return 1 - self
        
    def _and(self, other):
        if not self.is_bernoulli() or not other.bernoulli():
            raise ValueError('Logical operators can only be applied to Bernoulli distributions.')
        return (self + other) == 2
        
    def __and__(self, other):
        return self._and(Die(other))
    
    def __rand__(self, other):
        return self._and(Die(other))
        
    def _or(self, other):
        if not self.is_bernoulli() or not other.bernoulli():
            raise ValueError('Logical operators can only be applied to Bernoulli distributions.')
        return (self + other) >= 1
        
    def __or__(self, other):
        return self._or(Die(other))
    
    def __ror__(self, other):
        return self._or(Die(other))
    
    def _xor(self, other):
        if not self.is_bernoulli() or not other.bernoulli():
            raise ValueError('Logical operators can only be applied to Bernoulli distributions.')
        return (self + other) == 1
        
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
        dice = Die.align(dice)
        
        if mix_weights is None:
            mix_weights = numpy.ones((len(dice),))

        weights = numpy.zeros_like(dice[0].weights())
        for die, mix_weight in zip(dice, mix_weights):
            weights += mix_weight * die.weights()
        return Die(weights, dice[0].min_outcome())
    
    def relabel(self, relabeling):
        """
        relabeling can be one of the following:
        * An array-like containing relabelings, one for each face in order.
        * A dict-like mapping old outcomes to new outcomes.
            Unmapped old outcomes stay the same.
        * A function mapping old outcomes to new outcomes.
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
        
        non_explode_die = Die(non_explode_weights, self.min_outcome()).trim()
        explode_die = Die(explode_weights, self.min_outcome()).trim()
        explode_die += self.explode(max_times-1, outcomes=outcomes)
        
        mix_weights = [numpy.sum(non_explode_weights), numpy.sum(explode_weights)]
        
        return Die.mix(non_explode_die, explode_die, mix_weights=mix_weights)
    
    def reroll(self, outcomes=None, max_times=None):
        """
        Rerolls the given outcomes.
        outcomes: Selects which outcomes to reroll. Options:
            * A single integer outcome to reroll.
            * A dict whose keys are outcomes and values are chances for that outcome to reroll.
            * An iterable containing outcomes to reroll.
        """
        if outcomes is None:
            raise TypeError('outcomes to reroll must be provided.')
        reroll_weights = self._select_weights(outcomes)
        non_reroll_weights = self.weights() - reroll_weights
        
        if max_times is None:
            if numpy.sum(non_reroll_weights) <= 0.0:
                raise ZeroDivisionError('This reroll would never terminate.')
            weights = non_reroll_weights
        else:
            total_reroll_weight = numpy.sum(reroll_weights)
            reroll_chance_single = total_reroll_weight / self.total_weight()
            rerollable_factor = numpy.power(reroll_chance_single, max_times)
            stop_factor = (1.0 - numpy.power(reroll_chance_single, max_times+1)) / (1.0 - reroll_chance_single)
            weights = rerollable_factor * reroll_weights + stop_factor * non_reroll_weights
        return Die(weights, self.min_outcome()).trim()
    
    def combine(*dice, func=None):
        """
        Dice (or anything castable to a Die) may be provided as a list or as a variable number of arguments.
        func should be a function that takes in one outcome for each of the dice and outputs an integer outcome.
        
        This method is very flexible but has poor performance since it enumerates all possible joint outcomes.
        Other methods should be preferred when performance is a concern.
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
    
    def align(*dice):
        """ 
        Pads all the dice with zeros so that all have the same min_outcome, max_outcome, and total weight.
        Note that, unlike most methods, this may leave leading or trailing zero weights.
        """
        dice = Die._listify_dice(dice)
        
        min_outcome = min(die.min_outcome() for die in dice)
        max_outcome = max(die.max_outcome() for die in dice)
        len_align = max_outcome - min_outcome + 1
        
        result_total_weight = 1.0
        if all(die.is_exact() for die in dice):
            lcd = numpy.lcm.reduce([int(die.total_weight()) for die in dice])
            if lcd <= hdroller.math.MAX_INT_FLOAT:
                result_total_weight = lcd
        
        result = []
        for die in dice:
            weight_factor = result_total_weight / die.total_weight()
            left_dst_index = die.min_outcome() - min_outcome
            weights = numpy.zeros((len_align,))
            weights[left_dst_index:left_dst_index + len(die.weights())] = die.weights() * weight_factor
            result.append(Die(weights, min_outcome))
        
        return tuple(result)
    
    def trim(self):
        """
        Returns a copy of this Die with the leading and trailing zeros trimmed.
        Most methods already return a trimmed result by default.
        """
        nz = numpy.nonzero(self.weights())[0]
        min_outcome = self.min_outcome() + nz[0]
        weights = self.weights()[nz[0]:nz[-1]+1]
        return Die(weights, min_outcome)
        
    
    # Random sampling.
    def sample(self, size=None):
        """
        Returns a random sample from this Die.        
        """
        return numpy.random.choice(self.outcomes(), size=size, p=self.pmf())

    # Out conversions.
    
    def __str__(self):
        result = ''
        for outcome, weight, p in zip(self.outcomes(), self.weights(), self.pmf()):
            if self.is_exact():
                result += '%d, %d/%d, %f\n' % (outcome, weight, self.total_weight(), p)
            else:
                result += '%d, %f\n' % (outcome, p)
        return result
        
    def __float__(self):
        if not self.is_bernoulli():
            raise ValueError('Only Bernoulli distributions may be cast to float.')
        return float(self.probability(1))

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
