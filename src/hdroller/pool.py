import hdroller
import numpy
from functools import cached_property, lru_cache
            
class Pool():
    """
    Immutable class representing a non-ordered dice pool where all the dice are the same except possibly for their maximum outcomes.
    
    This does not include scoring logic. Those are determined by PoolScorer.
    """
    def __init__(self, die, max_outcomes, mask=None):
        """
        Arguments:
            die: The fundamental Die of the Pool.
            max_outcomes: Either:
                * An iterable indicating the maximum outcome for each die in the pool.
                * An integer indicating the number of dice in the pool; all dice will have max_outcome equal to die.max_outcome().
            mask:
                The pool will be sorted from lowest to highest; only dice selected by mask will be counted.
                This can be anything that can index a numpy array, e.g. integer, array of integers, slice.
                If omitted, all dice will be counted.
                
        For example, Pool(Die.d12, [6, 6, 8, 8, 8], slice(-2, None)) would mean 2d6 and 3d8, taking the two highest.
        """
        self._die = die
        if numpy.isscalar(max_outcomes):
            self._max_outcomes = (die.max_outcome(),) * max_outcomes
        else:
            # Sort the max outcomes and cap them at the die's max_outcome.
            self._max_outcomes = tuple(numpy.minimum(sorted(max_outcomes), die.max_outcome()))
        
        if isinstance(mask, tuple):
            self._mask = mask
        elif mask is None:
            self._mask = (True,) * len(self._max_outcomes)
        else:
            temp = numpy.zeros_like(self._max_outcomes, dtype=bool)
            temp[mask] = True
            self._mask = tuple(temp)
    
    @classmethod
    @lru_cache(maxsize=None)
    def _create_unchecked(cls, die, max_outcomes, mask):
        """
        Fast constructor for cases where the arguments are known to be already tuples, sorted, etc.
        """
        if die is None:
            return None
        self = cls.__new__(cls)
        self._die = die
        self._max_outcomes = max_outcomes
        self._mask = mask
        return self
    
    def die(self):
        return self._die
        
    def max_outcome(self):
        """
        The maximum outcome of the die.
        """
        return self.die().max_outcome()
        
    def max_single_weight(self):
        """
        The weight of the maximum outcome on a single die.
        """
        return self.die().weights()[-1]
        
    def max_outcomes(self):
        """
        Maximum outcomes of the dice in the pool, sorted from lowest to highest.
        """
        return self._max_outcomes
        
    def mask(self):
        return self._mask
        
    def num_dice(self):
        return len(self.max_outcomes())
    
    @cached_property
    def _num_max_dice(self):
        return self.num_dice() - numpy.searchsorted(self.max_outcomes(), self.max_outcome())
    
    def num_max_dice(self):
        """
        The number of dice in this pool that could roll the maximum outcome.
        """
        return self._num_max_dice
    
    def _iter_pops(self):
        """
        Yields from 0 to num_max_dice() inclusive:
            * pool: A Pool resulting from removing that many dice from this Pool, while also removing the max outcome.
                If the max outcome has all the remaining weight, only one result will be yielded, corresponding to all dice rolling that outcome.
                If the max outcome has zero weight, only one result will be yielded, corresponding to removing 0 dice from the pool.
                If there are no outcomes remaining, this will be None.
            * count: An integer indicating the number of masked dice that rolled the removed outcome.
            * weight: A float weight of that many dice rolling the removed outcome.
        """
        
        num_max_dice = self.num_max_dice()
        num_unused_dice = self.num_dice() - num_max_dice
        popped_die, outcome, single_weight = self.die().popped()
        
        if popped_die is None or (single_weight > 0.0 and popped_die.total_weight() == 0.0):
            # This is the last outcome with positive weight. All dice must roll this outcome.
            pool = Pool._create_unchecked(popped_die, (), ())
            weight = single_weight ** num_max_dice
            yield pool, numpy.count_nonzero(self.mask()), weight
            return
        
        popped_max_outcomes = self.max_outcomes()[:num_unused_dice] + (outcome-1,) * num_max_dice
        popped_mask = self.mask()
        
        # Zero dice rolling this outcome.
        # If there is no weight, this is the only possibility.
        pool = Pool._create_unchecked(popped_die, popped_max_outcomes, self.mask())
        weight = 1.0
        count = 0
        yield pool, count, weight
        
        # If there is weight remaining below, consider different numbers of dice rolling this outcome.
        if single_weight > 0.0:
            binom_row = hdroller.math.binom_row(num_max_dice, single_weight)
            for weight in binom_row[1:]:
                count += popped_mask[-1]
                popped_max_outcomes = popped_max_outcomes[:-1]
                popped_mask = popped_mask[:-1]
                pool = Pool._create_unchecked(popped_die, popped_max_outcomes, popped_mask)
                yield pool, count, weight
    
    @cached_property
    def _pops(self):
        return tuple(self._iter_pops())
    
    def pops(self):
        return self._pops
    
    @cached_property
    def _key_tuple(self):
        return self.die(), self.max_outcomes(), self.mask()
    
    def __eq__(self, other):
        if not isinstance(other, Pool): return False
        return self._key_tuple == other._key_tuple
    
    @cached_property
    def _hash(self):
        return hash(self._key_tuple)
        
    def __hash__(self):
        return self._hash

    def __str__(self):
        return '\n'.join(str(self.die()), str(self.max_outcomes()), str(self.mask()))