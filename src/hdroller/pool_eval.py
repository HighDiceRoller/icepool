__docformat__ = 'google'

import hdroller

from abc import ABC, abstractmethod
from collections import defaultdict
from functools import cached_property
import itertools
import math

class PoolEval(ABC):
    """ An abstract class for evaulating one or more `DicePool`s.
    
    Instances cache all intermediate state distributions.
    
    You can pretend that evaluation occurs on individual rolls of the pool as follows:
    
    1. First, specify the `initial_state()`. The state is usually some sort of running total.
    2. Then, you will be given one outcome at a time,
        along with how many dice in the pool rolled that outcome.
        Update the state using `next_state()` using that information.
    3. Finally and optionally, once all outcomes have been accounted for,
        use `final_outcome()` to specify the result of that roll.
    
    Subclasses should not modify `self` after construction.
    """
    @abstractmethod
    def initial_state(self, *pools):
        """ Generates an initial state for the evaluation.
        
        This should be a pure function with no side-effects.
        
        Arguments:
            *pools: One or more `DicePool`s being evaluated.
        
        Returns:
            A hashable object indicating the initial state.
        
        If you want to use information about the pool(s) being evaluated,
        you need to save that information to the state here.
        This is to avoid polluting cache keys with unused information.
        """
    
    @abstractmethod
    def next_state(self, prev_state, outcome, *counts):
        """ State transition function.
        
        This should produce a state given the previous state, an outcome, and the number of dice in each pool rolling that outcome.
        Note that outcomes are not guaranteed to be consecutive, as outcomes not present in any pool will not be considered.
        
        This should be a pure function with no side-effects.
        
        Args:
            prev_state: A hashable object indicating the state before rolling the current outcome.
            outcome: The current outcome.
            counts: One `int`for each pool indicating how many dice in that pool rolled the current outcome.
        
        Returns:
            A hashable object indicating the next state.
            If the return value is `None`, the state will be dropped from consideration.
            This is equivalent to performing a full reroll with no maximum depth.
        """
    
    def final_outcome(self, final_state, *pools):
        """ Optional function to generate a final outcome from a final state.
        
        If not overridden, the final state is used as the final outcome.
        
        This should be a pure function with no side-effects.
        
        Args:
            final_state: A state after all outcomes have been processed.
            *pools: One or more `DicePool`s being evaluated.
            
        Returns:
            A final outcome that will be used as part of constructing a die.
            This should be hashable and comparable.
        """
        return final_state
    
    def ndim(self, *pools):
        """ Optional function to specify the number of dimensions of the output die.
        
        The priority to determine ndim is as follows.
        
        1. The `ndim` argument to `eval()`, if not `None`.
        2. This method, if not `None`.
        3. Automatically determined by `die()`.
        
        This should be a pure function with no side-effects.
        
        Args:
            *pools: One or more `DicePool`s being evaluated.
        
        Returns:
            The number of dimensions that the output die should have,
            or `None` if this should be determined automatically by `die()`.
        """
        return None
    
    @cached_property
    def _cache(self):
        return {}
    
    def eval(self, *pools, ndim=None):
        """ Evaluates pools.
        
        Args:
            *pools: One or more `DicePool`s to evaluate.
                Most evaluators will expect a fixed number of pools.
            ndim: The number of dimensions of the resulting die.
                If omitted, this will be determined automatically.
        
        Returns:
            A die representing the distribution of the final score.
        """
        initial_state = self.initial_state(*pools)
        dist = self._eval_internal(initial_state, *pools)
        
        final_dist = defaultdict(int)
        for state, weight in dist.items():
            outcome = self.final_outcome(state, *pools)
            final_dist[outcome] += weight
        
        if ndim is None:
            ndim = self.ndim(*pools)
        
        return hdroller.die(final_dist, ndim=ndim)
    
    def _eval_internal(self, initial_state, *pools):
        """
        Arguments:
            initial_state: The initial state. This is passed without change recursively.
            *pools: One or more `DicePool`s to evaluate.
                Values of `None` indicate that pool has no remaining outcomes to process.
            
        Returns:
            A dict `{ state : weight }` describing the probability distribution over states.
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
        """ Iterates over possible numbers of dice that could roll an outcome.
        
        Args:
            outcome: The outcome under consideration.
            pool: The `DicePool` under consideration.
        
        Yields:
            prev_pool: The remainder of the pool after taking out the dice that rolled the current outcome.
            count: How many dice rolled the current outcome, or `None` if the outcome is not in this pool.
            weight: The weight of that many dice rolling the current outcome.
        """
        if pool is None or outcome not in pool.die():
            yield pool, None, 1
        else:
            yield from pool.pops()

class PoolSum(PoolEval):
    """ A simple `PoolEval` that just sums the dice in a pool. """
    def initial_state(self, pool):
        return 0
        
    def next_state(self, prev_state, outcome, count):
        return prev_state + outcome * count

pool_sum = PoolSum()
""" A shared `PoolSum` object for caching results. """

class PoolMatchingSet(PoolEval):
    """ A `PoolEval` that takes the best matching set in a pool.
    
    The outcomes are `(set_size, outcome)`.
    """
    def initial_state(self, pool):
        return -1, 0
    
    def next_state(self, prev_state, outcome, count):
        return max(prev_state, (count, outcome))
