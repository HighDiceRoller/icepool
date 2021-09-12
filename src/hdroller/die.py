import hdroller.math
import hdroller.die_repeater

from functools import cached_property, lru_cache
import numpy
import re
from scipy.special import erf, factorial

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
        elif numpy.issubdtype(type(weights), numpy.floating):
            if min_outcome is not None: raise ValueError()
            if not (weights >= 0.0 and weights <= 1.0):
                raise ValueError('Only floats between 0.0 and 1.0 can be cast to Die.')
            self._weights = numpy.array([1.0 - weights, weights])
            self._min_outcome = 0
        else:
            # weights is an array.
            if not numpy.issubdtype(type(min_outcome), numpy.integer):
                raise ValueError('min_outcome must be of integer type')
            self._weights = numpy.array(weights)
            self._min_outcome = min_outcome
        
        self._weights.setflags(write=False)
    
    # Cached values.
    @cached_property
    def _total_weight(self):
        return numpy.sum(self._weights)
    
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
        result = numpy.cumsum(self.pmf())
        result = numpy.insert(result, 0, 0.0)
        result.setflags(write=False)
        return result
    
    @cached_property
    def _ccdf(self):
        result = hdroller.math.reverse_cumsum(self.pmf())
        result = numpy.append(result, 0.0)
        result.setflags(write=False)
        return result
    
    @cached_property
    def _repeater(self):
        return hdroller.die_repeater.DieRepeater(self)
    
    # Creation.

    @staticmethod
    def mix(*args, mix_weights=None):
        """
        Constructs a Die from a mixture of the arguments,
        equivalent to rolling a die and then choosing one of the arguments
        based on the resulting face rolled.
        The arguments can be Dice or anything castable to Dice.
        mix_weights: An array of one weight per argument.
          If not provided, all arguments are mixed uniformly.
          A Die can also be used, in which case its weights determines the mix_weights.
        """
        if len(args) == 1 and not isinstance(args[0], Die):
            args = args[0]
        
        args = [Die(die) for die in args]
        args = Die._union(*args)
        
        if mix_weights is None:
            mix_weights = numpy.ones((len(args),))
        elif isinstance(mix_weights, Die):
            mix_weights = mix_weights.weights()

        weights = numpy.zeros_like(args[0].weights())
        for die, mix_weight in zip(args, mix_weights):
            weights += mix_weight * die.weights()
        return Die(weights, args[0].min_outcome())
    
    @staticmethod
    @lru_cache(maxsize=None)
    def standard(num_faces):
        if num_faces < 1: raise ValueError('Standard dice must have at least 1 face.')
        return Die(numpy.ones((num_faces,)), 1)
    
    # TODO: Apply cache to all __new__ dice created with floats?
    @staticmethod
    def bernoulli(chance=0.5):
        return Die(chance)

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
    def geometric(max_outcome=100, **kwargs):
        """
        A truncated geometric distribution.
        Any remaining probability is placed on max_outcome.
        """
        if 'half_life' in kwargs:
            factor = 0.5 ** (1.0 / kwargs['half_life'])
        else:
            raise RuntimeError('Geometric distribution requires a scaling parameter.')
        pmf = numpy.power(factor, numpy.arange(max_outcome+1)) * (1.0 - factor)
        pmf[-1] = 1.0 - numpy.sum(pmf[:-1])
        return Die(pmf, 0)
    
    @staticmethod
    def laplace(**kwargs):
        # TODO: odd or even
        geometric = Die.geometric(**kwargs)
        return geometric - geometric
    
    @staticmethod
    def sech(max_outcome=100, half_life=None):
        # TODO: odd or even, overflow weights
        x = numpy.arange(-max_outcome, max_outcome+1)
        weights = 2.0 / (numpy.power(2.0, x / half_life) + numpy.power(2.0, -x / half_life))
        return Die(weights, -max_outcome)
    
    @staticmethod
    def logistic(mean, max_abs_deviation=100, half_life=None):
        # TODO: odd or even, overflow weights
        min_outcome = int(numpy.floor(mean - max_abs_deviation))
        max_outcome = int(numpy.ceil(mean + max_abs_deviation))
        outcomes = numpy.arange(min_outcome, max_outcome+1)
        cdf = 1.0 / (1.0 + numpy.power(2.0, -(outcomes + 0.5 - mean) / half_life))
        return Die.from_cdf(cdf, min_outcome)
    
    @staticmethod
    def poisson(mean, max_outcome=20):
        """
        A truncated Poisson distribution.
        Any remaining probability is placed on max_outcome.
        """
        pmf = numpy.power(mean, numpy.arange(0.0, max_outcome)) * numpy.exp(-mean) / factorial(numpy.arange(0, max_outcome))
        pmf = numpy.append(pmf, 1.0 - numpy.sum(pmf))
        return Die(pmf, 0)
    
    @staticmethod
    def gaussian(mean_or_die, standard_deviation=None, min_outcome=None, max_outcome=None, standard_deviations_of_outcomes=4):
        """
        A Gaussian distribution, discretized from the continuous version by rounding-to-nearest.
        The standard deviation of the result will therefore not match the specified standard deviation exactly.
        """
        if isinstance(mean_or_die, Die):
            standard_deviation = mean_or_die.standard_deviation()
            mean = mean_or_die.mean()
        else:
            mean = mean_or_die
        if min_outcome is None: min_outcome = int(numpy.floor(mean - standard_deviations_of_outcomes * standard_deviation))
        if max_outcome is None: max_outcome = int(numpy.ceil(mean + standard_deviations_of_outcomes * standard_deviation))
        outcomes = numpy.arange(min_outcome, max_outcome+1)
        cdf = 0.5 * (1.0 + erf((outcomes + 0.5 - mean) / (numpy.sqrt(2) * standard_deviation)))
        return Die.from_cdf(cdf, min_outcome)
        
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
    
    # Outcome information.
    def __len__(self):
        return len(self._weights)

    def min_outcome(self):
        return self._min_outcome

    def max_outcome(self):
        return self.min_outcome() + len(self) - 1

    def outcomes(self, prepend=False, append=False):
        return numpy.array(range(self.min_outcome(), self.min_outcome() + len(self) + (append is not False))) + (prepend is not False)

    # Distributions.
    def weights(self):
        return self._weights
        
    def is_exact(self):
        return self._is_exact
    
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
        a, b = Die._union(self, other, lcd=False)
        return numpy.max(numpy.abs(a.cdf() - b.cdf()))
    
    def cvm_stat(self, other):
        """ Cramér-von Mises stat. The sum-of-squares difference between CDFs. """
        a, b = Die._union(self, other, lcd=False)
        return numpy.linalg.norm(a.cdf() - b.cdf())
    
    def total_weight(self):
        return self._total_weight

    # Operations that don't involve other dice.
    
    def __neg__(self):
        """ Returns a Die with all outcomes negated. """
        return Die(numpy.flip(self.weights()), -self.max_outcome())
    
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

    def explode(self, max_explode, *, chance=None, faces=None, outcomes=None):
        """
        chance: If supplied, this top fraction of the pmf will explode.
        faces: If supplied, this many of the top faces will explode.
        outcomes: If suppled, these outcomes will explode.
        If neither is supplied, the top single face will explode.
        """
        if max_explode < 0:
            raise ValueError('max_explode cannot be negative.')
        if max_explode == 0:
            return self
        
        explode_weights = numpy.zeros_like(self.weights())
        if chance is not None:
            if chance == 0: return self
            remaining_explode_weight = chance * self.total_weight()
            for index, mass in reversed(list(enumerate(self.weights()))):
                if mass < remaining_explode_weight:
                    explode_weights[index] = mass
                    remaining_explode_weight -= mass
                else:
                    explode_weights[index] = remaining_explode_weight
                    break
        elif faces is not None:
            if faces == 0: return self
            explode_weights[-faces:] = self.weights()[-faces:]
        elif outcomes is not None:
            explode_faces = numpy.array(outcomes) - self.min_outcome()
            explode_weights[explode_faces] = self.weights()[explode_faces]
        else:
            explode_weights[-1] = self.weights()[-1]
        
        non_explode_weights = self.weights() - explode_weights
        
        non_explode_die = Die(non_explode_weights, self.min_outcome())._trim()
        explode_die = Die(explode_weights, self.min_outcome())._trim()
        explode_die += self.explode(max_explode-1, chance=chance, faces=faces, outcomes=outcomes)
        
        mix_weights = [numpy.sum(non_explode_weights), numpy.sum(explode_weights)]
        
        return Die.mix(non_explode_die, explode_die, mix_weights=mix_weights)
    
    def reroll(self, *, outcomes=None, below=None, above=None, max_reroll=None):
        """Rerolls the given outcomes."""
        pmf = numpy.copy(self.pmf())
        all_outcomes = self.outcomes()
        reroll_mask = numpy.zeros_like(all_outcomes, dtype=bool)
        if outcomes is not None: reroll_mask[outcomes - self.min_outcome()] = True
        if below is not None: reroll_mask[all_outcomes < below] = True
        if above is not None: reroll_mask[all_outcomes > above] = True
        
        reroll_chance_single = numpy.sum(pmf[reroll_mask])
        stop_chance_single = numpy.sum(pmf[~reroll_mask])
        
        if max_rerolls is None:
            rerollable_factor = 0.0
            stop_factor = 1.0 / stop_chance_single
        else:
            rerollable_factor = numpy.power(reroll_chance_single, max_rerolls)
            stop_factor = (1.0 - numpy.power(reroll_chance_single, max_rerolls+1)) / stop_chance_single
        
        pmf[reroll_mask] *= rerollable_factor
        pmf[~reroll_mask] *= stop_factor
        
        return Die(pmf, self.min_outcome())._trim()
    
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
        
        subresults = Die._union(*subresults)
        weights = sum(subresult.weights() * die_count_weight for subresult, die_count_weight in zip(subresults, die_count_weights))
        
        return Die(weights, subresults[0].min_outcome())
    
    def __rmul__(self, other):
        return Die(other) * self
    
    def product(self, other):
        """
        This multiplies the outcome of the dice. It does not roll additional dice.
        """
        other = Die(other)
        if self.min_outcome < 0 or other.min_outcome < 0:
            raise NotImplementedError('Multiplication not implemented for non-positive outcomes.')
        min_outcome = self.min_outcome() * other.min_outcome()
        max_outcome = self.max_outcome() * other.max_outcome()
        weights = numpy.zeros((result_max_outcome - resultmin_outcome() + 1))
        for outcome, mass in zip(other.outcomes(), other.weights()):
            start_index = outcome * self.min_outcome - resultmin_outcome()
            weights[start_index:start_index+outcome*len(self.data):outcome] += self.weights() * mass
        return Die(weights, resultmin_outcome())
    
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
        Returns a Die representing:
        Roll all the dice and take the highest.
        """
        dice = [Die(die) for die in dice]
        dice_unions = Die._union(*dice)
        cweights = 1.0
        for die in dice_unions: cweights *= die.cweights()
        return Die.from_cweights(cweights, dice_unions[0].min_outcome())._trim()
    
    def min(*dice):
        """
        Returns a Die representing:
        Roll all the dice and take the lowest.
        """
        dice = [Die(die) for die in dice]
        # TODO: use weights
        dice_unions = Die._union(*dice)
        ccweights = 1.0
        for die in dice_unions: ccweights *= die.ccweights()
        return Die.from_ccweights(ccweights, dice_unions[0].min_outcome())._trim()
    
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
        
    def keep_highest(self, num_dice, num_keep=1):
        """
        Returns a Die representing:
        Roll this Die `num_dice` times and sum the `num_keep` highest.
        """
        return self._repeater.keep_highest(num_dice, num_keep)
        
    def keep_lowest(self, num_dice, num_keep=1):
        """
        Returns a Die representing:
        Roll this Die `num_dice` times and sum the `num_keep` lowest.
        """
        return self._repeater.keep_lowest(num_dice, num_keep)
        
    def keep_index(self, num_dice, index):
        """
        Returns a Die representing:
        Roll this Die `num_dice` times and take the `index`th from the bottom.
        """
        return self._repeater.keep_index(num_dice, index)

    # Comparators. These return scalar floats (which can be cast to Die).
    # TODO: Return a fraction instead?
    
    def __eq__(self, other):
        """
        Returns the chance this die will roll exactly equal to the other Die.
        """
        other = Die(other)
        a, b = Die._union(self, other, lcd=False)
        return numpy.sum(a.pmf() * b.pmf())
    
    def __ne__(self, other):
        return 1.0 - (self == other)
    
    def __lt__(self, other):
        """
        Returns the chance this Die will roll < the other Die.        
        """
        other = Die(other)
        difference = self - other
        if difference.min_outcome() < 0:
            return numpy.sum(difference.pmf()[:-difference.min_outcome()])
        else:
            return 0.0

    def __le__(self, other):
        """
        Returns the chance this Die will roll <= the other Die.        
        """
        return self < other + 1

    def __gt__(self, other):
        """
        Returns the chance this Die will roll > the other Die.        
        """
        other = Die(other)
        return other < self

    def __ge__(self, other):
        """
        Returns the chance this Die will roll >= the other Die.        
        """
        other = Die(other)
        return other <= self
    
    # Random sampling.
    def sample(self, size=None):
        """
        Returns a random sample from this Die.        
        """
        return numpy.random.choice(self.outcomes(), size=size, p=self.pmf())

    # String methods.
    
    def __str__(self):
        result = ''
        if self.is_exact():
            format_string = '%2d, %d\n'
        else:
            format_string = '%2d, %f\n'
        for outcome, weight in zip(self.outcomes(), self.weights()):
            result += format_string % (outcome, weight)
        return result

    # Helper methods.
    
    def _union(*dice, lcd=True):
        """ 
        Pads all the dice with zeros so that all have the same min and max outcome.
        If lcd is True, all weights are also multiplied to the least common denominator if all dice are exact.
        Caller is responsible for any trimming before returning dice publically.
        """
        min_outcome = min(die.min_outcome() for die in dice)
        max_outcome = max(die.max_outcome() for die in dice)
        union_len = max_outcome - min_outcome + 1
        
        result_total_weight = 1.0
        if lcd and all(die.is_exact() for die in dice):
            lcd = numpy.lcm.reduce([int(die.total_weight()) for die in dice])
            if lcd <= hdroller.math.MAX_INT_FLOAT:
                result_total_weight = lcd
        
        result = []
        for die in dice:
            weight_factor = result_total_weight / die.total_weight()
            left_dst_index = die.min_outcome() - min_outcome
            weights = numpy.zeros((union_len,))
            weights[left_dst_index:left_dst_index + len(die.weights())] = die.weights() * weight_factor
            result.append(Die(weights, min_outcome))
        
        return tuple(result)
    
    def _trim(self):
        """
        Returns a copy of this Die with the leading and trailing zeros trimmed.
        Shouldn't be usually necessary publically, since methods are written to stay trimmed publically.
        """
        nz = numpy.nonzero(self.weights())[0]
        min_outcome = self.min_outcome() + nz[0]
        weights = self.weights()[nz[0]:nz[-1]+1]
        return Die(weights, min_outcome)
