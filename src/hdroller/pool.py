import hdroller
import numpy
from collections import defaultdict

"""
Possible todo:
* Make the Die part of the class?
* Decide whether to provide automatic multidimensional state, or make the subclass take care of it.
* Caching.
* Specialist algorithms for add, max, keep-highest.
* Auto state shape, min/max score?
* Early termination?
* Cacheable next_state?
* Use cache module?

Possible restrictions:
* Max score is achieved by rolling max on all dice?
:* Add likely other candidates? Min on all dice?
* Score must be non-negative?
* State should be the same shape for all?

Systems:
* CthulhuTech: sets and straights
* Cortex: mixed, keep-highest
* Vampire 5e: Pairing successes
* Ability scores: keep-highest, roll-and-group
* Neon City Overdrive: multiple pools
"""

def _tuplelize(x):
    if not isinstance(x, tuple):
        x = (x,)
    return x

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
        
    def _evaluate_internal(self, die, outcome, max_outcomes, initial_state):
        """
        Arguments:
            outcome: The current outcome under consideration. Decreases by 1 each recursion.
            max_outcomes: A tuple of the maximum outcome of each die in the pool in descending order.
                These are capped at outcome for caching.
            
        Returns:
            A dictionary { state : weight } describing the probability distribution over states.
        """
        cache_key = (die, outcome, max_outcomes, initial_state)
        if cache_key in self._cache: return self._cache[cache_key]
        
        result = defaultdict(float)
        num_dice = len(max_outcomes)
        index = outcome - die.min_outcome()
        single_weight = die.weights()[index]
        if index == 0:
            # All dice roll the only possible value.
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
                    tail = self._evaluate_internal(die, outcome - 1, tail_max_outcomes[count:], initial_state)
                    for state, tail_weight in tail.items():
                        next_state = self._next_state_tuple(outcome, count, *state)
                        result[next_state] += tail_weight * binomial_weight
            else:
                # If this outcome has zero weight, zero dice can roll this outcome.
                tail = self._evaluate_internal(die, outcome - 1, tail_max_outcomes, initial_state)
                for state, tail_weight in tail.items():
                    next_state = self._next_state_tuple(outcome, 0, *state)
                    result[next_state] += tail_weight * binomial_weight

        self._cache[cache_key] = result
        return result
    
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
        
        dist = self._evaluate_internal(die, die.max_outcome(), max_outcomes, initial_state)
        
        score_dist = defaultdict(float)
        for state, weight in dist.items():
            score = self.score(die, max_outcomes, *state)
            score_dist[score] += weight
        
        return hdroller.Die(score_dist)
