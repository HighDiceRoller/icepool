import hdroller
import numpy
from collections import defaultdict

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

class SinglePoolScorer():
    def initial_state(self, initial_pool):
        """
        Arguments:
            initial_pool: A Pool object.
        Returns:
            A hashable object indicating the initial state.
        
        If you want to use information about the pool(s) being evaluated,
        you need to save that information to the state here.
        This is done to avoid polluting cache keys with unused information.
        """
        raise NotImplementedError()
        
    def next_state(self, outcome, count, prev_state):
        """
        Arguments:
            outcome: The current outcome.
            counts: An integer indicating how many counted dice rolled the current outcome.
            prev_state: A hashable object indicating the state before rolling the current outcome.
        
        Returns:
            A hashable object indicating the next state.
        """
        raise NotImplementedError()
        
    def score(self, initial_pool, initial_state, state):
        """
        Arguments:
            initial_state
            initial_pool
            state: A final state after all dice in the pool have been consumed.
        
        Returns:
            An integer indicating the final score for that state.
        """
        raise NotImplementedError()
    
    def evaluate(self, pool):
        """
        pool: A pool to evaluate this scorer on.
        """
        if not hasattr(self, '_cache'):
            self._cache = {}
        
        initial_state = self.initial_state(pool)
        
        dist = self._evaluate_internal(initial_state, pool)
        
        score_dist = defaultdict(float)
        for state, weight in dist.items():
            score = self.score(pool, initial_state, state)
            score_dist[score] += weight
        
        return hdroller.Die(score_dist)
    
    def _evaluate_internal(self, initial_state, pool):
        """
        Arguments:
            initial_state: The initial state. This is passed without change recursively.
            pool: The pool to evaluate.
            
        Returns:
            A dictionary { state : weight } describing the probability distribution over states.
        """
        cache_key = (initial_state, pool)
        if cache_key in self._cache: return self._cache[cache_key]
        
        result = defaultdict(float)
        
        outcome = pool.max_outcome()
        single_weight = pool.max_single_weight()
        
        if len(pool.die()) == 1:
            # There's only one possible value, so all dice roll it.
            count = numpy.count_nonzero(pool.mask())
            state = self.next_state(outcome, count, initial_state)
            weight = single_weight ** count
            result[state] = weight
        else:
            for prev_pool, weight, count in pool.iter_pop():
                prev = self._evaluate_internal(initial_state, prev_pool)
                for prev_state, prev_weight in prev.items():
                    state = self.next_state(outcome, count, prev_state)
                    result[state] += prev_weight * weight

        self._cache[cache_key] = result
        return result
