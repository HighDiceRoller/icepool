import hdroller.math
import hdroller.die_repeater

from functools import cached_property
import numpy
import re
from scipy.special import erf, factorial

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
    
    def __init__(self, pmf, min_outcome=None, name=None):
        if name is None: name = '?'
        if isinstance(pmf, Die):
            return # Already returned same object by __new__().
        elif numpy.issubdtype(type(pmf), numpy.integer):
            # Integer casts to die that always rolls that value.
            if min_outcome is not None: raise ValueError()
            self._pmf = numpy.array([1.0])
            self._min_outcome = pmf
            self._name = '%d' % pmf
        elif numpy.issubdtype(type(pmf), numpy.floating):
            if min_outcome is not None: raise ValueError()
            if not (pmf >= 0.0 and pmf <= 1.0):
                raise ValueError('Only floats between 0.0 and 1.0 can be cast to Die.')
            self._pmf = numpy.array([1.0 - pmf, pmf])
            self._min_outcome = 0
            self._name = name
        else:
            if not numpy.issubdtype(type(min_outcome), numpy.integer):
                raise ValueError('min_outcome must be of integer type')
            self._pmf = numpy.array(pmf)
            self._min_outcome = min_outcome
            self._name = name
        
        self._pmf.setflags(write=False)
    
    # Internal caches.
    @cached_property
    def _cdf(self):
        result = numpy.cumsum(self._pmf)
        result = numpy.insert(result, 0, 0.0)
        result.setflags(write=False)
        return result
    
    @cached_property
    def _ccdf(self):
        result = hdroller.math.reverse_cumsum(self._pmf)
        result = numpy.append(result, 0.0)
        result.setflags(write=False)
        return result
    
    @cached_property
    def _repeater(self):
        return hdroller.die_repeater.DieRepeater(self)
    
    # Creation.

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
    def from_faces(faces):
        """
        Constructs a die from a list of faces, with each facing having equal probability.
        """
        min_outcome = numpy.min(faces)
        max_outcome = numpy.max(faces)
        pmf = numpy.zeros((max_outcome - min_outcome + 1,))
        for face in faces:
            pmf[face-min_outcome] += 1
        pmf /= len(faces)
        return Die(pmf, min_outcome)

    @staticmethod
    def d(*args):
        """
        Standard dice and dice chaining.
        Last argument becomes a standard die if it is an integer.
        Otherwise it is cast to a die.
        Other arguments also become standard dice if they are integers, unless they are the first argument.
        They then roll what's behind them a number of times equal to their own roll, and sum the results together.
        Examples:
        d(6) = d6
        d(6, 6) = 6d6 = roll d6 six times and add them up
        d(1, 6, 6) = 1d6d6 = roll a d6, and then roll that many d6s and add them up
        """
        return Die._d(*args, treat_leading_integer_as_standard_die=False)
    
    @staticmethod
    def _d(*args, treat_leading_integer_as_standard_die=False):
        """
        Implementation of Die.d().
        """
        if len(args) == 1:
            single_die = args[0]
            if numpy.issubdtype(type(single_die), numpy.integer):
                return Die.standard(single_die)
            else:
                single_die = Die(single_die)
            return single_die
        
        tail_die = Die._d(*args[1:], treat_leading_integer_as_standard_die=True)
        
        num_dice = args[0]
        if treat_leading_integer_as_standard_die and numpy.issubdtype(type(num_dice), numpy.integer):
            num_dice = Die.standard(num_dice)
        else:
            num_dice = Die(args[0])

        return num_dice * tail_die
    
    @staticmethod
    def standard(num_faces):
        if num_faces < 1: raise ValueError('Standard dice must have at least 1 face.')
        return Die(numpy.ones((num_faces,)) / num_faces, 1, 'd%d' % num_faces)
        
    @staticmethod
    def coin(chance=0.5):
        return Die(chance)
    
    @staticmethod
    def bernoulli(chance=0.5):
        return Die.coin(chance)

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
        geometric = Die.geometric(**kwargs)
        return geometric - geometric
    
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
        
    # Outcome information.
    def __len__(self):
        return len(self._pmf)

    def min_outcome(self):
        return self._min_outcome

    def max_outcome(self):
        return self._min_outcome + len(self) - 1

    def outcomes(self, include_one_past_end=False):
        return numpy.array(range(self._min_outcome, self._min_outcome + len(self) + include_one_past_end))

    # Distributions.
    def pmf(self):
        return self._pmf
    
    def cdf(self, inclusive=True):
        """ 
        When zipped with outcomes(), this is the probability of rolling <= the corresponding outcome.
        inclusive: If False, changes the comparison to <.
          If 'both', includes both endpoints and should be zipped with outcomes(include_one_past_end=True).
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
          If 'both', includes both endpoints and should be zipped with outcomes(include_one_past_end=True).
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
        return numpy.sum(self._pmf * self.outcomes())
    
    # TODO: median
    
    def mode(self):
        """
        Returns the outcome and mass of the highest single element of the PMF.
        """
        return numpy.argmax(self._pmf) + self._min_outcome, numpy.max(self._pmf)
    
    def variance(self):
        mean = self.mean()
        mean_of_squares = numpy.sum(self._pmf * self.outcomes() * self.outcomes())
        return mean_of_squares - mean * mean
    
    def standard_deviation(self):
        return numpy.sqrt(self.variance())
        
    def ks_stat(self, other):
        """ Kolmogorov–Smirnov stat. The maximum absolute difference between CDFs. """
        a, b = Die._union_outcomes(self, other)
        return numpy.max(numpy.abs(a.cdf() - b.cdf()))
    
    def cvm_stat(self, other):
        """ Cramér-von Mises stat. The sum-of-squares difference between CDFs. """
        a, b = Die._union_outcomes(self, other)
        return numpy.linalg.norm(a.cdf() - b.cdf())
    
    def total_mass(self):
        """ Primarily for debugging, since externally visible dice should stay close to normalized. """
        return numpy.sum(self._pmf)

    # Operations that don't involve other dice.
    
    def __neg__(self):
        """ Returns a Die with all outcomes negated. """
        return Die(numpy.flip(self._pmf), -self.max_outcome())
    
    def relabel(self, relabeling):
        """
        relabeling can be one of the following:
        * An array-like containing relabelings by index.
        * A dict-like mapping old outcomes to new outcomes.
          Unmapped old outcomes stay the same.
        * A function mapping old outcomes to new outcomes.
        """
        if hasattr(relabeling, 'items'):
            relabeling = [(relabeling[outcome] if outcome in relabeling else outcome) for outcome in self.outcomes()]
        elif callable(relabeling):
            relabeling = [relabeling(outcome) for outcome in self.outcomes()]
        min_outcome = numpy.min(relabeling)
        max_outcome = numpy.max(relabeling)
        pmf = numpy.zeros((max_outcome - min_outcome + 1,))
        for index, (mass, new_outcome) in enumerate(zip(self._pmf, relabeling)):
            pmf[new_outcome - min_outcome] += mass
        return Die(pmf, min_outcome)

    def explode(self, n, chance=None):
        """
        n is the maximum number of times to explode.
        chance: if supplied, this top fraction of the pmf will explode.
        """
        # TODO: binary split, other ways of defining what explodes
        if n <= 0: return self
        recursive = self.explode(n-1, chance=chance)
        
        explode_pmf = numpy.zeros_like(self._pmf)
        if chance is not None:
            remaining_chance = chance
            for index, mass in reversed(list(enumerate(self._pmf))):
                if mass < chance:
                    explode_pmf[index] = mass
                    remaining_chance -= mass
                else:
                    explode_pmf[index] = chance
                    break
        else:
            explode_pmf[-1] = self._pmf[-1]
        
        min_outcome = self._min_outcome + min(recursive._min_outcome, 0)
        max_outcome = self.max_outcome() + max(recursive.max_outcome(), self.max_outcome())
        
        pmf = numpy.zeros((max_outcome - min_outcome + 1,))
        
        non_explode_pmf = self._pmf - explode_pmf
        non_explode_start_index = self._min_outcome - min_outcome
        pmf[non_explode_start_index:non_explode_start_index+len(non_explode_pmf)] = non_explode_pmf
        
        explode_recursive_pmf = numpy.convolve(explode_pmf, recursive._pmf)
        explode_recursive_min_outcome = self._min_outcome + recursive._min_outcome
        explode_recursive_start_index = explode_recursive_min_outcome - min_outcome
        pmf[explode_recursive_start_index:explode_recursive_start_index+len(explode_recursive_pmf)] += explode_recursive_pmf
        
        return Die(pmf, min_outcome, name=self._name + '!')._trim()
    
    def reroll(self, outcomes=None, below=None, above=None, max_rerolls=None):
        """Rerolls the given outcomes."""
        pmf = numpy.copy(self._pmf)
        all_outcomes = self.outcomes()
        reroll_mask = numpy.zeros_like(all_outcomes, dtype=bool)
        if outcomes is not None: reroll_mask[outcomes - self._min_outcome] = True
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
        
        return Die(pmf, self._min_outcome)._trim()
    
    # Roller wins ties by default. This returns a die that effectively has the given tiebreak mode.
    def tiebreak(self, mode):
        if mode == 'win': return self
        elif mode == 'lose': return self - 1
        elif mode == 'coin': return self - Die.coin(0.5)
        elif mode == 'reroll': return self.reroll([0])
        else: raise ValueError('Invalid tiebreak mode "%s"' % mode)

    # Operations with another Die. Non-Die operands will be cast to Die.
    def _add(self, other, name):
        """
        Helper for adding two dice.
        other must already be a Die.
        """
        pmf = numpy.convolve(self._pmf, other._pmf)
        min_outcome = self._min_outcome + other._min_outcome
        return Die(pmf, min_outcome, name=name)
    
    def __add__(self, other):
        other = Die(other)
        name = '%s+%s' % (self._name, other._name)
        return self._add(other, name)
    
    def __radd__(self, other):
        other = Die(other)
        name = '%s+%s' % (other._name, self._name)
        return other._add(self, name)

    def __sub__(self, other):
        other = Die(other)
        name = '%s-%s' % (self._name, other._name)
        return self._add(-other, name)
    
    def __rsub__(self, other):
        other = Die(other)
        name = '%s-%s' % (other._name, self._name)
        return other._add(-self, name)

    def __mul__(self, other):
        """
        This computes the result of rolling the dice on the left, and then rolling that many dice on the right and summing them.
        """
        other = Die(other)
        
        subresults = []
        die_count_chances = []
        for die_count, die_count_chance in zip(self.outcomes(), self._pmf):
            if die_count_chance <= 0.0: continue
            subresults.append(other.repeat_and_sum(die_count))
            die_count_chances.append(die_count_chance)
        
        subresults = Die._union_outcomes(*subresults)
        pmf = sum(subresult.pmf() * die_count_chance for subresult, die_count_chance in zip(subresults, die_count_chances))
        
        if re.match(r'^d\d+$', other._name):
            name = self._name + other._name
        else:
            name = '?'  # TODO
        return Die(pmf, subresults[0]._min_outcome, name=name)
    
    def __rmul__(self, other):
        return Die(other) * self
    
    def product(self, other):
        """
        This multiplies the outcome of the dice. It does not roll additional dice.
        """
        other = Die(other)
        if self.min_outcome < 0 or other.min_outcome < 0:
            raise NotImplementedError('Multiplication not implemented for non-positive outcomes.')
        min_outcome = self._min_outcome * other._min_outcome
        max_outcome = self.max_outcome() * other.max_outcome()
        pmf = numpy.zeros((result_max_outcome - result_min_outcome + 1))
        for outcome, mass in zip(other.outcomes(), other._pmf):
            start_index = outcome * self.min_outcome - result_min_outcome
            pmf[start_index:start_index+outcome*len(self.data):outcome] += self._pmf * mass
        return Die(pmf, result_min_outcome)
    
    def clip(self, min_outcome_or_die=None, max_outcome=None):
        """
        Restricts the outcomes of this die to the range [min_outcome, max_outcome].
        A Die can be supplied instead, in which case the range is taken from that die.
        """
        if isinstance(min_outcome_or_die, Die):
            min_outcome = min_outcome_or_die.min_outcome()
            max_outcome = min_outcome_or_die.max_outcome()
        else:
            if min_outcome_or_die is None: min_outcome = self.min_outcome()
            if max_outcome is None: max_outcome = self.max_outcome()
        left = max(0, min_outcome - self.min_outcome())
        right = len(self) + min(0, max_outcome - self.max_outcome())
        pmf = numpy.copy(self.pmf()[left:right])
        pmf[0] += numpy.sum(self.pmf()[:left])
        pmf[-1] += numpy.sum(self.pmf()[right:])
        return Die(pmf, max(self.min_outcome(), min_outcome))
    
    # Repeat, keep, and sum.
    def max(*dice):
        """
        Returns a Die representing:
        Roll all the dice and take the highest.
        """
        dice = [Die(die) for die in dice]
        dice_unions = Die._union_outcomes(*dice)
        cdf = 1.0
        for die in dice_unions: cdf *= die.cdf()
        return Die.from_cdf(cdf, dice_unions[0]._min_outcome)._trim()
    
    def min(*dice):
        """
        Returns a Die representing:
        Roll all the dice and take the lowest.
        """
        dice = [Die(die) for die in dice]
        dice_unions = Die._union_outcomes(*dice)
        ccdf = 1.0
        for die in dice_unions: ccdf *= die.ccdf()
        return Die.from_ccdf(ccdf, dice_unions[0]._min_outcome)._trim()
    
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
        
    def keep_highest(self, num_dice, num_keep):
        """
        Returns a Die representing:
        Roll this Die `num_dice` times and sum the `num_keep` highest.
        """
        return self._repeater.keep_highest(num_dice, num_keep)
        
    def keep_lowest(self, num_dice, num_keep):
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
    def __lt__(self, other):
        """
        Returns the chance this Die will roll < the other Die.        
        """
        other = Die(other)
        difference = self - other
        if difference._min_outcome < 0:
            return numpy.sum(difference._pmf[:-difference._min_outcome])
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
        return numpy.random.choice(self.outcomes(), size=size, p=self._pmf)

    # String methods.
    def name(self):
        return self._name
        
    def rename(self, name):
        return Die(self._pmf, self._min_outcome, name=name)
    
    def __str__(self):
        result = ''
        for outcome, mass in zip(self.outcomes(), self._pmf):
            result += '%d, %f\n' % (outcome, mass)
        return result

    # Helper methods.
    
    def _union_outcomes(*dice):
        """ 
        Pads all the dice with zeros so that all have the same min and max outcome. 
        Caller is responsible for any trimming before returning dice publically.
        """
        min_outcome = min(die._min_outcome for die in dice)
        max_outcome = max(die.max_outcome() for die in dice)
        union_len = max_outcome - min_outcome + 1
        
        result = []
        for die in dice:
            left_dst_index = die._min_outcome - min_outcome
            
            pmf = numpy.zeros((union_len,))
            pmf[left_dst_index:left_dst_index + len(die._pmf)] = die._pmf
            result.append(Die(pmf, min_outcome))
        
        return tuple(result)
    
    def _trim(self):
        """
        Returns a copy of this Die with the leading and trailing zeros trimmed.
        Shouldn't be usually necessary publically, since methods are written to stay trimmed publically.
        """
        nz = numpy.nonzero(self._pmf)[0]
        min_outcome = self._min_outcome + nz[0]
        pmf = self._pmf[nz[0]:nz[-1]+1]
        return Die(pmf, min_outcome, name = self._name)
    
    def _normalize(self):
        """
        Returns a normalized copy of this Die.
        Shouldn't be usually necessary publically, since methods are written to stay normalized publically.
        """
        norm = numpy.sum(self._pmf)
        if norm <= 0.0: raise ZeroDivisionError('Attempted to normalize die with non-positive mass')
        pmf = self._pmf / norm
        return Die(pmf, self._min_outcome, name = self._name)
