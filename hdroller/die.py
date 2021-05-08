import numpy
import re
import hdroller.choose
from scipy.special import comb, erf, factorial

class DieType(type):
    """
    Metaclass for Die. Used to enable shorthand for standard dice.
    """
    def __getattr__(self, key):
        if key[0] == 'd':
            die_size = int(key[1:])
            return Die.d(die_size)
        raise AttributeError(key)

class Die(metaclass=DieType):
    """
    Immutable class representing a normalized discrete probability distribution
    with finite support.

    I considered having an option for integer weights but overflow happens
    quite quickly in many cases.
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
        
        # Precompute cdf, ccdf. These include both endpoints.
        self._cdf = numpy.cumsum(self._pmf)
        self._cdf = numpy.insert(self._cdf, 0, 0.0)
        self._ccdf = numpy.flip(numpy.cumsum(numpy.flip(self._pmf)))
        self._ccdf = numpy.append(self._ccdf, 0.0)
        
        # Set immutable so we can return them safely without copying.
        self._pmf.setflags(write=False)
        self._cdf.setflags(write=False)
        self._ccdf.setflags(write=False)

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
    def standard(faces):
        if faces < 1: raise ValueError('Standard dice must have at least 1 face.')
        return Die(numpy.ones((faces,)) / faces, 1, 'd%d' % faces)
        
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
        inclusive: If False, changes the comparison to <. If 'both', includes both endpoints.
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
    def mean(self, transform=None):
        if transform is None:
            return numpy.sum(self._pmf * self.outcomes())
        else:
            return numpy.sum(self._pmf * transform(self.outcomes()))
    
    def median(self):
        """ Returns the first outcome for which the cdf exceeds 0.5."""
        # TODO: tolerance
        return numpy.nonzero(self.cdf() > 0.5)[0][0] + self._min_outcome
    
    def mode(self):
        return numpy.argmax(self._pmf) + self._min_outcome, numpy.max(self._pmf)
    
    def variance(self):
        mean = self.mean()
        mean_of_squares = numpy.sum(self._pmf * self.outcomes() * self.outcomes())
        return mean_of_squares - mean * mean
    
    def standard_deviation(self):
        return numpy.sqrt(self.variance())
    
    def mad_median(self):
        """ Mean absolute deviation around the median. """
        median = self.median()
        abs_deviations = numpy.abs(self.outcomes() - median)
        return numpy.dot(abs_deviations, self.pmf())
    
    def total_mass(self):
        """ Primarily for debugging, since externally visible dice should stay close to normalized. """
        return numpy.sum(self._pmf)
        
    def ks_stat(self, other):
        """ Kolmogorov–Smirnov stat. Computes the maximum absolute difference between CDFs. """
        a, b = Die._union_outcomes(self, other)
        return numpy.max(numpy.abs(a.cdf(inclusive='neither') - b.cdf(inclusive='neither')))
    
    def cvm_stat(self, other):
        """ Cramér-von Mises stat. Computes the sum-of-squares difference between CDFs."""
        a, b = Die._union_outcomes(self, other)
        return numpy.linalg.norm(a.cdf() - b.cdf())

    # Operations that don't involve other dice.
    
    def __neg__(self):
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
        chance: if supplied, this top fraction of the pmf will explode
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
        
        """
        if len(self) <= 1:
            raise ValueError('Only dice with more than one outcome can explode.')
        recursive = self.explode(n-1) + self.max_outcome()
        self_last = self._pmf[-1]
        self_except_last = Die(self._pmf[:-1], self._min_outcome)
        
        self_except_last_union, recursive_union = self_except_last._union_outcomes(recursive)
        pmf = self_except_last_union._pmf + self_last * recursive_union._pmf
        return Die(pmf, self_except_last_union._min_outcome)
        """
    
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

    # Operations with other dice. These accept integers as well.
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
        
    # Sum and keep/drop.
    
    def advantage(self, n=2):
        return Die.from_cdf(numpy.power(self.cdf(), n), self._min_outcome)

    def disadvantage(self, n=2):
        return Die.from_ccdf(numpy.power(self.ccdf(), n), self._min_outcome)
        
    def clip(self, min_outcome_or_die=None, max_outcome=None):
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
    
    def min(*dice):
        """
        Returns the probability distribution of the minimum of the dice.
        """
        dice = [Die(die) for die in dice]
        dice_unions = Die._union_outcomes(*dice)
        ccdf = 1.0
        for die in dice_unions: ccdf *= die.ccdf()
        return Die.from_ccdf(ccdf, dice_unions[0]._min_outcome)._trim()
    
    def max(*dice):
        """
        Returns the probability distribution of the maximum of the dice.
        """
        dice = [Die(die) for die in dice]
        dice_unions = Die._union_outcomes(*dice)
        cdf = 1.0
        for die in dice_unions: cdf *= die.cdf()
        return Die.from_cdf(cdf, dice_unions[0]._min_outcome)._trim()
    
    def repeat_and_sum(self, num_dice):
        """
        Returns the result of rolling the dice repeatedly and adding the outcomes together.
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
    
    def repeat_and_keep_and_sum(self, num_dice, **kwargs):
        """
        This allows dice to be dropped from the top and/or bottom.
        """
        drop_lowest = 0
        drop_highest = 0
        if 'drop_lowest' in kwargs:
            drop_lowest = kwargs['drop_lowest']
        if 'drop_highest' in kwargs:
            drop_highest = kwargs['drop_highest']
        if 'keep_lowest' in kwargs:
            drop_highest = num_dice - kwargs['keep_lowest']
        if 'keep_highest' in kwargs:
            drop_lowest = num_dice - kwargs['keep_highest']
        if 'keep_middle' in kwargs:
            total_drop = num_dice - kwargs['keep_middle']
            if total_drop % 2 != 0:
                raise ValueError('keep_middle (%d) must have same parity as num_dice (%d)' % (kwargs['keep_middle'], num_dice))
            drop_lowest = total_drop // 2
            drop_highest = total_drop // 2
            
        num_kept = num_dice - drop_lowest - drop_highest
        pmf_length = ((len(self) - 1) * num_kept) + 1
        pmf = numpy.zeros((pmf_length,))
        cdf = self.cdf()
        ccdf = self.ccdf()
        # How this works: We loop over all possibilities for the sorted kept dice.
        # Then we loop over how many of the dropped dice were equal to the lowest and highest kept dice,
        # versus how many were beyond that.
        # After that it's just an application of multinomial coefficients.
        for kept in hdroller.choose.iter_multichoose_sorted_outcomes(len(self), num_kept):
            for num_below in (range(drop_lowest+1) if kept[0] > 0 else [0]):
                low_dropped = (kept[0]-1,) * num_below + (kept[0],) * (drop_lowest-num_below)
                for num_above in (range(drop_highest+1) if kept[-1] < len(self)-1 else [0]):
                    high_dropped = (kept[-1],) * (drop_highest - num_above) + (kept[-1]+1,) * num_above
                    combined = low_dropped + kept + high_dropped
                    coef = hdroller.choose.multinom_outcomes(num_dice, combined)
                    mass = coef
                    for outcome in combined:
                        if outcome < kept[0]: mass *= cdf[outcome]
                        elif outcome > kept[-1]: mass *= ccdf[outcome]
                        else: mass *= self._pmf[outcome]
                    pmf[numpy.sum(kept)] += mass
        return Die(pmf, self._min_outcome * num_kept)
    
    def repeat_and_keep_and_sum2(self, num_dice, **kwargs):
        """
        This allows dice to be dropped from the top and/or bottom.
        """
        drop_lowest = 0
        drop_highest = 0
        if 'drop_lowest' in kwargs:
            drop_lowest = kwargs['drop_lowest']
        if 'drop_highest' in kwargs:
            drop_highest = kwargs['drop_highest']
        if 'keep_lowest' in kwargs:
            drop_highest = num_dice - kwargs['keep_lowest']
        if 'keep_highest' in kwargs:
            drop_lowest = num_dice - kwargs['keep_highest']
        if 'keep_middle' in kwargs:
            total_drop = num_dice - kwargs['keep_middle']
            if total_drop % 2 != 0:
                raise ValueError('keep_middle (%d) must have same parity as num_dice (%d)' % (kwargs['keep_middle'], num_dice))
            drop_lowest = total_drop // 2
            drop_highest = total_drop // 2
        if 'keep_index' in kwargs:
            keep_index = kwargs['keep_index']
            if keep_index < 0: keep_index += num_dice
            drop_lowest = keep_index
            drop_highest = num_dice - drop_lowest - 1
        
        num_kept = num_dice - drop_lowest - drop_highest
        result_pmf_length = ((len(self) - 1) * num_kept) + 1
        result_pmf = numpy.zeros((result_pmf_length,))
        # These are non-inclusive in this case.
        cdf = self.cdf(inclusive=False)
        ccdf = self.ccdf(inclusive=False)
        
        """
        How this works:
        
        We consider all possible values for the lowest and highest kept dice.
        This splits the dice into up to five groups:
        
        "Below": dice below the lowest kept dice.
        "Low": dice equal to the lowest kept dice.
        "Middle": dice between the lowest and highest kept dice.
        "High": dice equal to the highest kept dice.
        "Above": dice above the highest kept dice.
        
        "Low" and "High" may contain dropped dice as well as kept dice.
        
        We use convolution to compute the chances for the middle dice.
        """
        
        # TODO: Revisit loop nesting order.
        
        # Number of dropped dice equal to the lowest kept die.
        for num_drop_low in range(drop_lowest+1):
            # Number of dropped dice less than the lowest kept die.
            num_drop_below = drop_lowest - num_drop_low
            # Number of dropped dice equal to the highest kept die.
            for num_drop_high in range(drop_highest+1):
                # Number of dropped dice greater than the highest kept die. 
                num_drop_above = drop_highest - num_drop_high
                # Value of the lowest kept die.
                for lowest_kept in range(len(self)):
                    prob_factor_below = numpy.power(cdf[lowest_kept], num_drop_below)
                    for highest_kept in range(lowest_kept, len(self)):
                        prob_factor_above = numpy.power(ccdf[highest_kept], num_drop_above)
                        if highest_kept == lowest_kept:
                            # Three-section case where lowest kept = highest kept.
                            num_equal_kept = num_drop_low + num_drop_high + num_kept
                            probability_factor = (
                                prob_factor_below * 
                                numpy.power(self._pmf[lowest_kept], num_equal_kept) * 
                                prob_factor_above
                            )
                            comb_factor = hdroller.choose.multinom(num_dice, (num_drop_below, num_equal_kept, num_drop_above))
                            index = lowest_kept*num_kept
                            #print('All kept dice are %d. %d below, %d equal to kept, %d above. %f' % (lowest_kept + self._min_outcome, num_drop_below, num_equal_kept, num_drop_above, comb_factor * probability_factor))
                            result_pmf[index] += comb_factor * probability_factor
                        elif highest_kept == lowest_kept+1:
                            # Four-section case where lowest and highest kept are consecutive, with no middle section.
                            for num_kept_low in range(1, num_kept):
                                num_kept_high = num_kept-num_kept_low
                                num_low = num_kept_low + num_drop_low
                                num_high = num_kept_high + num_drop_high
                                probability_factor = (
                                    prob_factor_below * 
                                    numpy.power(self._pmf[lowest_kept], num_low) * 
                                    numpy.power(self._pmf[highest_kept], num_high) * 
                                    prob_factor_above
                                )
                                comb_factor = hdroller.choose.multinom(num_dice, (num_drop_below, num_low, num_high, num_drop_above))
                                index = lowest_kept*num_kept_low + highest_kept*num_kept_high
                                #print('Kept dice are %d and %d. %f' % (lowest_kept + self._min_outcome, highest_kept + self._min_outcome, comb_factor * probability_factor))
                                result_pmf[index] += comb_factor * probability_factor
                        else:
                            # Five-section case where there is a middle region (possibly of zero size).
                            conv_mid = numpy.array([1.0])
                            # Number of dice strictly between the lowest and highest kept dice.
                            for num_kept_mid in range(0, num_kept-1):
                                # Number of dice equal to the lowest and highest kept dice.
                                for num_kept_low in range(1, num_kept-num_kept_mid):
                                    num_kept_high = num_kept-num_kept_mid-num_kept_low
                                    num_low = num_kept_low + num_drop_low
                                    num_high = num_kept_high + num_drop_high
                                    probability_factor = (
                                        prob_factor_below * 
                                        numpy.power(self._pmf[lowest_kept], num_low) * 
                                        numpy.power(self._pmf[highest_kept], num_high) * 
                                        prob_factor_above
                                    ) * conv_mid
                                    comb_factor = hdroller.choose.multinom(num_dice, (num_drop_below, num_low, num_kept_mid, num_high, num_drop_above))
                                    start_index = lowest_kept*num_kept_low + (lowest_kept+1) * num_kept_mid + highest_kept*num_kept_high
                                    #print('Kept %d @ %d, %d @ mid, %d @ %d. Index = %d. %s' % (num_kept_low, lowest_kept + self._min_outcome, num_kept_mid, num_kept_high, highest_kept + self._min_outcome, start_index, comb_factor * probability_factor))
                                    result_pmf[start_index:start_index+len(conv_mid)] += comb_factor * probability_factor
                                    
                                conv_mid = numpy.convolve(conv_mid, self._pmf[lowest_kept+1:highest_kept])
        return Die(result_pmf, self._min_outcome * num_kept)
        
    def keep_and_sum(*dice, drop_lowest=0, drop_highest=0):
        num_keep = len(dice) - drop_lowest - drop_highest
        dice = Die._union_outcomes(*dice)
        
        pmf_length = (len(dice[0])-1) * num_keep + 1
        pmf = numpy.zeros((pmf_length,))
        min_outcome = dice[0].min_outcome() * num_keep
        
        pmfs = [die._pmf for die in dice]
        cdfs = [die.cdf(inclusive='both') for die in dice] # chance of rolling < the corresponding outcome
        ccdfs = [die.ccdf(inclusive='both') for die in dice] # chance of rolling >= the corresponding outcome
        
        if num_keep > 1:
            max_counts = [drop_lowest, 1, num_keep-2, 1, drop_highest]
            def keep_and_sum_inner(lo_outcome, hi_outcome, current_die=0, counts=[0,0,0,0,0], partial_min_outcome=0, partial_pmf=numpy.array([1.0])):
                if current_die < len(dice):
                    for count_index, (count, max_count) in enumerate(zip(counts, max_counts)):
                        if count >= max_count: continue
                        next_counts = counts.copy()
                        next_counts[count_index] += 1
                        
                        if count_index == 0:  # drop_lowest
                            next_partial_min_outcome = partial_min_outcome
                            if counts[1] == 0:  # the lo die is later in the list, so this die is <
                                next_partial_pmf = partial_pmf * cdfs[current_die][lo_outcome]
                            else: # the lo die was earlier in the list, so this is <=
                                next_partial_pmf = partial_pmf * cdfs[current_die][lo_outcome+1]
                        elif count_index == 4:
                            next_partial_min_outcome = partial_min_outcome
                            if counts[3] == 0:
                                next_partial_pmf = partial_pmf * ccdfs[current_die][hi_outcome]
                            else:
                                next_partial_pmf = partial_pmf * ccdfs[current_die][hi_outcome+1]
                        elif count_index == 1:
                            # if both outcomes are equal, the "higher" die must happen first to avoid double-counting
                            if lo_outcome == hi_outcome and counts[3] == 0: continue
                            next_partial_min_outcome = partial_min_outcome + lo_outcome
                            next_partial_pmf = partial_pmf * pmfs[current_die][lo_outcome]
                        elif count_index == 3:
                            next_partial_min_outcome = partial_min_outcome + hi_outcome
                            next_partial_pmf = partial_pmf * pmfs[current_die][hi_outcome]
                        else:
                            if counts[1] == 0: start_outcome = lo_outcome
                            else: start_outcome = lo_outcome+1
                            if counts[3] == 0: end_outcome = hi_outcome
                            else: end_outcome = hi_outcome+1
                            if start_outcome >= end_outcome: continue # no outcome for this ordering
                            next_partial_min_outcome = partial_min_outcome + start_outcome
                            next_partial_pmf = numpy.convolve(partial_pmf, pmfs[current_die][start_outcome:end_outcome])
                        keep_and_sum_inner(lo_outcome, hi_outcome, current_die+1, next_counts, next_partial_min_outcome, next_partial_pmf)
                else:
                    #print(lo_outcome, hi_outcome, partial_min_outcome, partial_pmf)
                    pmf[partial_min_outcome:partial_min_outcome+len(partial_pmf)] += partial_pmf
            for lo_outcome in range(len(dice[0])):
                for hi_outcome in range(lo_outcome, len(dice[0])):
                    keep_and_sum_inner(lo_outcome, hi_outcome)
        else:
            raise NotImplementedError()
        
        return Die(pmf, min_outcome)._trim()
    
    def margin_of_success(self, other, base_outcome=0, win_ties=True):
        """ 
        Returns a Die representing the margin of success versus the other die.
        TODO: base_outcome is added to any success.
        """
        return (self - other).max(0)
        """
        TODO:
        if win_ties:
            return (self - other + base_outcome).max(base_outcome-1).relabel({base_outcome-1:0})
        else:
            return (self - other + base_outcome).max(base_outcome).relabel({base_outcome:0})
        """

    # Comparators. These return scalar floats (which can be cast to Die).
    def __lt__(self, other):
        other = Die(other)
        difference = self - other
        if difference._min_outcome < 0:
            return numpy.sum(difference._pmf[:-difference._min_outcome])
        else:
            return 0.0

    def __le__(self, other):
        return self < other + 1

    def __gt__(self, other):
        other = Die(other)
        return other < self

    def __ge__(self, other):
        other = Die(other)
        return other <= self
    
    # Random sampling.
    def sample(self, size=None):
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
        Returns a version of this Die with the leading and trailing zeros trimmed.
        Shouldn't be usually necessary publically, since methods are written to stay trimmed publically.
        """
        nz = numpy.nonzero(self._pmf)[0]
        min_outcome = self._min_outcome + nz[0]
        pmf = self._pmf[nz[0]:nz[-1]+1]
        return Die(pmf, min_outcome, name = self._name)
    
    def _normalize(self):
        """
        Returns a normalized version of this Die.
        Shouldn't be usually necessary publically, since methods are written to stay normalized publically.
        """
        norm = numpy.sum(self._pmf)
        if norm <= 0.0: raise ZeroDivisionError('Attempted to normalize die with non-positive mass')
        pmf = self._pmf / norm
        return Die(pmf, self._min_outcome, name = self._name)
