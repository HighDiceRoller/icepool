import hdroller
import numpy
from collections import defaultdict

class SinglePoolScorer():
    """
    An abstract class for scoring a single dice pool.
    
    Instances cache all final and intermediate state distributions.
    As such, unless memory is a concern, you should reuse instances when possible.
    
    See PoolSum below for an example concrete subclass.
    """
    def initial_state(self, initial_pool):
        """
        This should generate an initial state for the pool.
        
        Arguments:
            initial_pool: A Pool object.
        Returns:
            A hashable object indicating the initial state.
        
        If you want to use information about the pool being evaluated,
        you need to save that information to the state here.
        This is done to avoid polluting cache keys with unused information.
        """
        raise NotImplementedError()
        
    def next_state(self, outcome, count, prev_state):
        """
        This should produce a state given the previous state and `count` dice rolling `outcome`.
        This will be called for all outcomes of the pool Die,
        even if those outcomes have zero weight or all of the dice in the pool are capped below that outcome.
        
        Arguments:
            outcome: The current outcome.
            count: An integer indicating how many dice (subject to masking) rolled the current outcome.
            prev_state: A hashable object indicating the state before rolling the current outcome.
        
        Returns:
            A hashable object indicating the next state.
        """
        raise NotImplementedError()
        
    def score(self, initial_pool, initial_state, final_state):
        """
        This should compute the final score given a final state.
        
        Arguments:
            initial_pool
            initial_state
            final_state: A final state after all dice in the pool have been consumed.
        
        Returns:
            An integer indicating the final score for that final state.
        """
        raise NotImplementedError()
    
    def evaluate(self, pool):
        """
        Arguments:
            pool: A Pool to evaluate this scorer on.
        
        Returns:
            A Die representing the distribution of the final score.
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
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = defaultdict(float)
        
        outcome = pool.max_outcome()
        single_weight = pool.max_single_weight()
        
        if len(pool.die()) == 1:
            # There's only one possible outcome, so all dice roll it.
            # TODO: What if the weights start with zeros?
            count = numpy.count_nonzero(pool.mask())
            state = self.next_state(outcome, count, initial_state)
            weight = single_weight ** count
            result[state] = weight
        else:
            for prev_pool, count, weight in pool.pops():
                prev = self._evaluate_internal(initial_state, prev_pool)
                for prev_state, prev_weight in prev.items():
                    state = self.next_state(outcome, count, prev_state)
                    result[state] += prev_weight * weight

        self._cache[cache_key] = result
        return result

class PoolSum(SinglePoolScorer):
    def initial_state(self, initial_pool):
        # The state is the running total. This starts at 0.
        return 0
    
    def next_state(self, outcome, count, prev_state):
        # Add the dice that rolled the current outcome to the running total.
        return prev_state + outcome * count
    
    def score(self, initial_pool, initial_state, final_state):
        # Return the final total.
        return final_state

pool_sum = PoolSum()