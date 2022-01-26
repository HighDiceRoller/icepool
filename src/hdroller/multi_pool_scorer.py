import hdroller
import numpy
from collections import defaultdict
import math
import itertools

class MultiPoolScorer():
    """
    An abstract class for scoring multiple dice pools.
    
    Instances cache all final and intermediate state distributions.
    As such, unless memory is a concern, you should reuse instances when possible.
    """
    def initial_state(self, initial_pools):
        """
        This should generate an initial state for the pool.
        
        Arguments:
            initial_pools: A tuple of Pool objects.
        Returns:
            A hashable object indicating the initial state.
        
        If you want to use information about the pools being evaluated,
        you need to save that information to the state here.
        This is done to avoid polluting cache keys with unused information.
        """
        raise NotImplementedError()
        
    def next_state(self, outcome, counts, prev_state):
        """
        This should produce a state given the previous state and `count` dice rolling `outcome`.
        This will be called from the lowest outcome in the pools to the highest outcome in the pools.
        
        If the return value is None, the state will be dropped from consideration, effectively performing a full reroll.
        
        Arguments:
            outcome: The current outcome.
            counts: A tuple indicating how many dice in each pool (subject to masking) rolled the current outcome.
                If the outcome is out of range of the pool's Die, the corresponding entry will be None.
            prev_state: A hashable object indicating the state before rolling the current outcome.
        
        Returns:
            A hashable object indicating the next state.
        """
        raise NotImplementedError()
        
    def score(self, initial_pools, initial_state, final_state):
        """
        This should compute the final score given a final state.
        
        Arguments:
            initial_pools
            initial_state
            final_state: A final state after all dice in the pool have been consumed.
        
        Returns:
            An integer indicating the final score for that final state.
        """
        raise NotImplementedError()
    
    def evaluate(self, pool):
        score_dist = self.evaluate_dict(pool)
        return hdroller.Die(score_dist)
    
    def evaluate_dict(self, pools):
        """
        Arguments:
            pools: An iterable of Pools to evaluate this scorer on.
        
        Returns:
            A Die representing the distribution of the final score.
        """
        if not hasattr(self, '_cache'):
            self._cache = {}
            
        pools = tuple(pools)
        
        initial_state = self.initial_state(pools)
        
        dist = self._evaluate_internal(initial_state, pools)
        
        score_dist = defaultdict(float)
        for state, weight in dist.items():
            score = self.score(pools, initial_state, state)
            score_dist[score] += weight
        
        return score_dist
    
    def _evaluate_internal(self, initial_state, pools):
        """
        Arguments:
            initial_state: The initial state. This is passed without change recursively.
            pools: A tuple of Pools to evaluate, or None if that pool is exhausted.
            
        Returns:
            A dictionary { state : weight } describing the probability distribution over states.
        """
        cache_key = (initial_state, pools)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = defaultdict(float)
        
        if all(pool is None for pool in pools):
            result[initial_state] = 1.0
        else:
            outcome = max(pool.max_outcome() for pool in pools if pool is not None)
            for p in itertools.product(*[self._iter_pool(outcome, pool) for pool in pools]):
                prev_pools, counts, weights = zip(*p)
                prod_weight = math.prod(weights)
                prev = self._evaluate_internal(initial_state, prev_pools)
                for prev_state, prev_weight in prev.items():
                    state = self.next_state(outcome, counts, prev_state)
                    if state is None: continue
                    result[state] += prev_weight * prod_weight

        self._cache[cache_key] = result
        return result
    
    @staticmethod
    def _iter_pool(outcome, pool):
        """
        Yields:
            prev_pool
            count
            weight
        """
        if pool is None or outcome > pool.max_outcome():
            yield pool, None, 1.0
        else:
            yield from pool.pops()
