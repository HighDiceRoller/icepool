import hdroller
import numpy
from collections import defaultdict
import itertools
import math
from functools import cached_property

"""
Possible todo:
* Specialist algorithms for add, max, keep-highest? Maybe not worth with caching.
* Early termination?
* Cacheable next_state?
* Use cache module?
* Is variadic worth it or too clever?
* Multiple pools with different die types in each pool?
* Pool as class?
* Skip zero-chance outcomes entirely?

Possible restrictions:

Systems:
* CthulhuTech: sets and straights
* Cortex: mixed, keep-highest
* Vampire 5e: Pairing successes, multiple pools
* Ability scores: keep-highest, roll-and-group
* Neon City Overdrive: Multiple pools.

V5 and NCO encourage stepping through the pools in lockstep.
"""

def _tuplelize(x):
    if not isinstance(x, tuple):
        x = (x,)
    return x
            
class Pool():
    """
    Immutable class representing a non-ordered dice pool where all the dice are the same except possibly for their maximum outcomes.
    
    This does not include scoring logic or caching.
    Those are determined by PoolScorer.
    """
    def __init__(self, die, max_outcomes, mask=None):
        """
        Arguments:
            max_outcomes: Either:
                * An iterable indicating the maximum outcome for each die in the pool.
                * An integer indicating the number of dice in the pool; all dice will have max_outcome equal to die.max_outcome().
            mask:
                The pool will be sorted from lowest to highest; only dice selected by mask will be counted.
                If omitted, all dice will be counted.
                
        For example, Pool(Die.d12, [6, 6, 8, 8, 8]) would mean 2d6 and 3d8.
        """
        self._die = die
        if numpy.isscalar(max_outcomes):
            self._max_outcomes = (die.max_outcome(),) * max_outcomes
        else:
            # Sort the max outcomes and cap them at the die's max_outcome.
            self._max_outcomes = tuple(numpy.minimum(sorted(max_outcomes), die.max_outcome()))
        
        if mask is None:
            self._mask = (True,) * len(self._max_outcomes)
        else:
            self._mask = numpy.zeros_like(self.max_outcomes, dtype=bool)
            self._mask[mask] = True
        
        if len(self._max_outcomes) != len(self._mask):
            raise IndexError('max_outcomes and mask must have the same length.')
        
        self._max_outcomes.setflags(write=False)
        self._mask.setflags(write=False)
    
    def die(self):
        return self._die
        
    def max_outcomes(self):
        """
        Maximum outcomes, sorted from lowest to highest.
        """
        return self._max_outcomes
        
    def mask(self):
        return self._mask
        
    def num_dice(self):
        return len(self.max_outcomes())
    
    @cached_property
    def _num_max_dice(self):
        return self.num_dice() - numpy.searchsorted(self.max_outcomes(), die.max_outcome())
    
    def num_max_dice(self):
        """
        The number of dice in this pool that could roll the maximum outcome.
        """
        return self._max_dice
    
    def iter_pop(self):
        """
        Yields:
            * Pools resulting from removing 0 to num_max_dice() dice from this Pool, then removing the max outcome.
                If the max outcome has zero weight, only 0 dice rolling this outcome will be yielded.
            * The removed outcome (same for all yielded tuples).
            * The weight of this many dice rolling the removed outcome.
            * The number of masked dice that rolled the removed outcome.
        """
        num_max_dice = self.num_max_dice()
        popped_die, outcome, single_weight = self.die().pop()
        popped_max_outcomes = numpy.copy(self.max_outcomes())
        popped_max_outcomes[num_max_dice:] -= 1
        
        if single_weight == 0.0:
            # Zero dice can actually roll this outcome.
            # Yield only this result.
            pool = Pool(popped_die, popped_max_outcomes, mask)
            weight = 1.0
            count = 0
            yield pool, outcome, weight, count
        else:
            for consumed_dice, weight in enumerate(hdroller.math.binomial_row(num_max_dice, single_weight)):
                index = self.num_dice() - consumed_dice
                pool = Pool(popped_die, popped_max_outcomes[:index], self.mask[:index])
                count = numpy.sum(self.mask[index:])
                yield pool, outcome, weight, count
    
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

class PoolScorer():
    def initial_state(self, die, max_outcomes):
        """
        Arguments:
            max_outcomes: The maximum outcome on each die, in descending order.
        Returns:
            A hashable indicating the initial state.
        
        Note that if you want to keep track of the total number/size of dice
        or the number of dice consumed so far, you will need to insert
        that information into the state.
        This is to avoid duplicating entries in the cache when this information 
        is not used.
        """
        raise NotImplementedError()

    def next_state(self, outcome, count, *state):
        """
        Arguments:
            outcome: The current outcome.
            count: How many dice rolled this outcome.
            *state: A hashable indicating the current state.
                Subclasses may implement this as one or more ordered arguments
                rather than as a variadic argument.
        
        Returns:
            A hashable object indicating the next state resulting from the arguments.
        """
        raise NotImplementedError()
        
    def score(self, die, max_outcomes, *state):
        """
        Arguments:
            *state: A final state after all dice in the pool have been consumed.
                Subclasses may implement this as one or more ordered arguments
                rather than as a variadic argument.
        
        Returns:
            An integer indicating the final score for that state.
        """
        raise NotImplementedError()
   
    def _initial_state_tuple(self, die, max_outcomes):
        return _tuplelize(self.initial_state(die, max_outcomes))
        
    def _next_state_tuple(self, outcome, count, *state):
        return _tuplelize(self.next_state(outcome, count, *state))
    
    def evaluate(self, die, pool):
        """
        pool: Either an integer indicating the size of the pool,
            or an iterable of integers, each denoting the maximum outcome on one die in the pool.
        """
        if not hasattr(self, '_cache'):
            self._cache = {}
        
        if numpy.issubdtype(type(pool), numpy.integer):
            max_outcomes = (die.max_outcome(),) * pool
        else:
            max_outcomes = tuple(reversed(sorted(pool)))
        initial_state = self._initial_state_tuple(die, max_outcomes)
        
        dist = self._evaluate_internal(die, initial_state, die.max_outcome(), max_outcomes)
        
        score_dist = defaultdict(float)
        for state, weight in dist.items():
            score = self.score(die, max_outcomes, *state)
            score_dist[score] += weight
        
        return hdroller.Die(score_dist)
        
    def _evaluate_internal(self, die, initial_state, outcome, max_outcomes):
        """
        Arguments:
            outcome: The current outcome under consideration. Decreases by 1 each recursion.
            max_outcomes: A tuple of the maximum outcome of each die in the pool in descending order.
                These are capped at outcome for caching.
            
        Returns:
            A dictionary { state : weight } describing the probability distribution over states.
        """
        cache_key = (die, initial_state, outcome, max_outcomes)
        if cache_key in self._cache: return self._cache[cache_key]
        
        result = defaultdict(float)
        num_dice = len(max_outcomes)
        index = outcome - die.min_outcome()
        single_weight = die.weights()[index]
        if index == 0:
            # There's only one possible value, so all dice roll it.
            count = len(max_outcomes)
            state = self._next_state_tuple(outcome, count, *initial_state)
            weight = single_weight ** count
            result[state] = weight
        else:
            num_eligible_dice = 0
            while num_eligible_dice < len(max_outcomes) and max_outcomes[num_eligible_dice] == outcome:
                num_eligible_dice += 1
            tail_max_outcomes = (outcome - 1,) * num_eligible_dice + max_outcomes[num_eligible_dice:]
            
            if single_weight > 0.0:
                binomial_weights = hdroller.math.binomial_row(num_eligible_dice, single_weight)
                for count, binomial_weight in enumerate(binomial_weights):
                    tail = self._evaluate_internal(die, initial_state, outcome - 1, tail_max_outcomes[count:])
                    for state, tail_weight in tail.items():
                        next_state = self._next_state_tuple(outcome, count, *state)
                        result[next_state] += tail_weight * binomial_weight
            else:
                # If this outcome has zero weight, zero dice can roll this outcome.
                tail = self._evaluate_internal(die, initial_state, outcome - 1, tail_max_outcomes)
                for state, tail_weight in tail.items():
                    next_state = self._next_state_tuple(outcome, 0, *state)
                    result[next_state] += tail_weight * binomial_weight

        self._cache[cache_key] = result
        return result
        
    