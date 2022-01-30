import hdroller

from collections import defaultdict
import itertools
import math

class PoolEval():
    """An abstract class for evaulating one or more dice pools.
    
    Instances cache all intermediate state distributions.
    
    
    """
    def initial_state(self, *pools):
        """
        
        This should generate an initial state for the evaluation.
        
        Arguments:
            *pools: One or more DicePools.
        Returns:
            A hashable object indicating the initial state.
        
        If you want to use information about the pool(s) being evaluated,
        you need to save that information to the state here.
        This is done to avoid polluting cache keys with unused information.
        """
        raise NotImplementedError()
        
    def next_state(self, prev_state, outcome, *counts):
        """State transition function.
        
        This should produce a state given the previous state, an outcome, and the number of dice in each pool rolling that outcome.
        Note that outcomes are not guaranteed to be consecutive, as outcomes not present in any pool will not be considered.
        
        Args:
            prev_state: A hashable object indicating the state before rolling the current outcome.
            outcome: The current outcome.
            counts: One integer for each pool indicating how many dice in that pool rolled the current outcome.
        
        Returns:
            A hashable object indicating the next state.
            If the return value is None, the state will be dropped from consideration, effectively performing a full reroll.
        """
    
    def final_outcome(self, final_state, initial_state, *pools):
        """Optional function to generate a final outcome from a final state.
        
        If not overwritten, the final state is used as the final outcome.
        
        Args:
            final_state: A state after all outcomes have been processed.
            initial_state: The initial state of the evaluation.
            *pools: One or more DicePools.
            
        Returns:
            A final outcome that will be used as part of constructing a die.
            This should be hashable and comparable.
        """
        return final_state
    
    def eval(self, *pools, ndim=None):
        """
        Args:
            *pools: One or more DicePools to evaluate.
            Most evaluators will expect a fixed number of pools.
        
        Returns:
            A die representing the distribution of the final score.
        """
        if not hasattr(self, '_cache'):
            self._cache = {}
        
        initial_state = self.initial_state(*pools)
        dist = self._eval_internal(initial_state, *pools)
        
        final_dist = defaultdict(int)
        for state, weight in dist.items():
            outcome = self.final_outcome(state, initial_state, *pools)
            final_dist[outcome] += weight
        
        return hdroller.die(final_dist, ndim=ndim)
    
    def _eval_internal(self, initial_state, *pools):
        """
        Arguments:
            initial_state: The initial state. This is passed without change recursively.
            *pools: One or more DicePools to evaluate. Values of None indicate that pool is exhausted.
            
        Returns:
            A dictionary { state : weight } describing the probability distribution over states.
        """
        cache_key = (initial_state, pools)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = defaultdict(int)
        
        if all(pool is None for pool in pools):
            result[initial_state] = 1
        else:
            outcome = max(pool.die().max_outcome() for pool in pools if pool is not None)
            for p in itertools.product(*[self._iter_pool(outcome, pool) for pool in pools]):
                prev_pools, counts, weights = zip(*p)
                prod_weight = math.prod(weights)
                prev = self._eval_internal(initial_state, *prev_pools)
                for prev_state, prev_weight in prev.items():
                    state = self.next_state(prev_state, outcome, *counts)
                    if state is None: continue
                    result[state] += prev_weight * prod_weight

        self._cache[cache_key] = result
        return result
    
    @staticmethod
    def _iter_pool(outcome, pool):
        """
        Yields:
            prev_pool: The remainder of the pool after taking out the dice that rolled the current outcome.
            count: How many dice rolled the current outcome, or None if the outcome is not in this pool.
            weight: The weight of that many dice rolling the current outcome.
        """
        if pool is None or outcome not in pool.die():
            yield pool, None, 1
        else:
            yield from pool.pops()

class PoolSum(PoolEval):
    def initial_state(self, pool):
        return 0
        
    def next_state(self, prev_state, outcome, count):
        return prev_state + outcome * count

pool_sum = PoolSum()
