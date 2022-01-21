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

class PoolScorer():
    def initial_state(self, die, max_outcomes):
        """
        Arguments:
            max_outcomes: The maximum outcome on each die, in descending order.
        Returns:
            A hashable object indicating the initial state.
        
        Note that if you want to keep track of the total number/size of dice
        or the number of dice consumed so far, you will need to insert
        that information into the state.
        This is to avoid duplicating entries in the cache when this information 
        is not used.
        """
        raise NotImplementedError()

    def next_state(self, state, outcome, count):
        """
        Arguments:
            state: A hashable object indicating the current state.
            outcome: The current outcome.
            count: How many dice rolled this outcome.
        
        Returns:
            A hashable object indicating the next state resulting from the arguments.
        """
        raise NotImplementedError()
        
    def score(self, state, die, max_outcomes):
        """
        Arguments:
            state: A final state after all dice in the pool have been consumed.
        
        Returns:
            An integer indicating the final score for that state.
        """
        raise NotImplementedError()
        
    def evaluate_state_recursive(self, die, outcome, max_outcomes, initial_state):
        """
        Arguments:
            outcome: The current outcome under consideration. Decreases by 1 each recursion.
            max_outcomes: A tuple of the maximum outcome of each die in the pool in descending order.
                These are capped at outcome for caching.
            
        Returns:
            A dictionary { state : weight } describing the probability distribution over states.
        """
        result = defaultdict(float)
        num_dice = len(max_outcomes)
        index = outcome - die.min_outcome()
        single_weight = die.weights()[index]
        if index == 0:
            # All dice roll the only possible value.
            count = len(max_outcomes)
            state = self.next_state(initial_state, outcome, count)
            weight = single_weight ** count
            result[state] = weight
        else:
            num_eligible_dice = 0
            while num_eligible_dice < len(max_outcomes) and max_outcomes[num_eligible_dice] == outcome:
                num_eligible_dice += 1
            tail_max_outcomes = (outcome - 1,) * num_eligible_dice + max_outcomes[num_eligible_dice:]
            
            binomial_weights = hdroller.math.binomial_row(num_eligible_dice, single_weight)
            for count, binomial_weight in enumerate(binomial_weights):
                tail = self.evaluate_state_recursive(die, outcome - 1, tail_max_outcomes[count:], initial_state)
                for state, tail_weight in tail.items():
                    next_state = self.next_state(state, outcome, count)
                    result[next_state] += tail_weight * binomial_weight
        return result
    
    def evaluate_recursive(self, die, pool):
        """
        pool: Either an integer indicating the size of the pool,
            or an iterable of integers, each denoting the maximum outcome on one die in the pool.
        """
        if numpy.issubdtype(type(pool), numpy.integer):
            max_outcomes = (die.max_outcome(),) * pool
        else:
            max_outcomes = tuple(reversed(sorted(pool)))
        initial_state = self.initial_state(die, max_outcomes)
        
        dist = self.evaluate_state_recursive(die, die.max_outcome(), max_outcomes, initial_state)
        
        score_dist = defaultdict(float)
        for state, weight in dist.items():
            score = self.score(state, die, max_outcomes)
            score_dist[score] += weight
        
        return hdroller.Die(score_dist)
        
    def evaluate(self, die, num_dice):
        """
        Arguments:
            die: The die to evaluate.
            num_dice: The number of dice in the pool.
                
        Returns:
            A Die representing the final score.
        """
        
        prev_dist = defaultdict(float)
        prev_dist[(0, self.initial_state(num_dice))] = 1.0
        
        for outcome, outcome_weight in reversed(list(zip(die.outcomes(), die.weights()))):
            dist = defaultdict(float)
            for (prev_consumed_dice, prev_state), prev_weight in prev_dist.items():
                remaining_dice = num_dice - prev_consumed_dice
                next_weights = prev_weight * hdroller.math.binomial_row(remaining_dice, outcome_weight)
                for count, next_weight in enumerate(next_weights):
                    next_state = self.next_state(prev_state, outcome, count)
                    next_indexes = (prev_consumed_dice + count, next_state)
                    dist[next_indexes] += next_weight
            prev_dist = dist
        
        final_scores = defaultdict(float)
        for (prev_consumed_dice, prev_state), prev_weight in prev_dist.items():
            if prev_consumed_dice == num_dice:
                score = self.score(prev_state, num_dice)
                final_scores[score] += prev_weight
        
        return hdroller.Die(final_scores)
