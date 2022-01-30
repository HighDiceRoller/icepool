import hdroller.indexing
import hdroller.math

import bisect
from functools import cache, cached_property
import math

def pool(die, num_dice, select_dice=None, *, min_outcomes=None, max_outcomes=None):
    """
    Args:
        die: The die this pool is based on.
        num_dice: The number of dice in the pool.
        min_outcomes, max_outcomes: At most one of these must be provided.
            If neither is provided, it has the same effect as max_outcomes=True.
            This should be an iterable with length equal to num_dice. Each limits the min/max outcome of a single die.
            Alternatively, this can be set to True, which makes all dice span all outcomes of die.
            This also determines the direction of the state iteration.
            If max_outcomes is provided, PoolEval will receive outcomes in order from min to max.
            If min_outcomes is provided, PoolEval will receive outcomes in order from max to min.
        select_dice: 
            The select_dice applies to the dice sorted from lowest to highest (regardless of direction).
            For example, slice(-2, None) would only count the two highest dice.
    """

    if min_outcomes is True:
        min_outcomes = (die.min_outcome(),) * num_dice
    elif min_outcomes is not None:
        raise NotImplementedError('min_outcomes not yet implemented for pools.')
    
    if max_outcomes is True or (min_outcomes is None and max_outcomes is None):
        max_outcomes = (die.max_outcome(),) * num_dice
    else:
        max_outcomes = tuple(sorted(min(outcome, die.max_outcome()) for outcome in max_outcomes))
    
    if select_dice is None:
        select_dice = (True,) * num_dice
    else:
        select_dice = hdroller.indexing.select_bools(num_dice, select_dice)
    
    return DicePool(die, select_dice, min_outcomes, max_outcomes)

@cache
def _pool_cached_unchecked(die, select_dice, min_outcomes, max_outcomes):
    return DicePool(die, select_dice, min_outcomes, max_outcomes)

class DicePool():
    def __init__(self, die, select_dice, min_outcomes, max_outcomes):
        """Unchecked constructor."""
        self._die = die
        self._select_dice = select_dice
        self._min_outcomes = min_outcomes
        self._max_outcomes = max_outcomes
    
    def die(self):
        return self._die
        
    def select_dice(self):
        return self._select_dice
    
    def num_dice(self):
        return len(self._select_dice)
        
    def min_outcomes(self):
        return self._min_outcomes
        
    def max_outcomes(self):
        return self._max_outcomes
    
    def _iter_pops(self):
        """
        Yields from 0 to the number of dice that can roll this outcome inclusive:
            * pool: A DicePool resulting from removing that many dice from this DicePool, while also removing the max outcome.
                If there is only one outcome remaining, only one result will be yielded, corresponding to all dice rolling that outcome.
                If the outcome has zero weight, only one result will be yielded, corresponding to zero dice rolling that outcome.
                If there are no outcomes remaining, this will be None.
            * count: An int indicating the number of selected dice that rolled the removed outcome.
            * weight: An int indicating the weight of that many dice rolling the removed outcome.
        """
        remaining_selected_dice = sum(self.select_dice())

        num_possible_dice = self.num_dice() - bisect.bisect_left(self.max_outcomes(), self.die().max_outcome())
        num_unused_dice = self.num_dice() - num_possible_dice
        popped_die, outcome, single_weight = self.die().pop_max()
        
        if popped_die is None:
            # This is the last outcome. All dice must roll this outcome.
            weight = single_weight ** num_possible_dice
            yield None, remaining_selected_dice, weight
            return
        
        if remaining_selected_dice == 0:
            # No selected dice remain. All dice must roll somewhere below, so empty all dice in one go.
            # We could follow the staircase of max_outcomes more closely but this is unlikely to be relevant in most cases.
            pool = _pool_cached_unchecked(popped_die, (), None, ())
            weight = math.prod(self.die().weight_le(max_outcome) for max_outcome in self.max_outcomes())
            yield pool, 0, weight
            return
        
        popped_max_outcomes = self.max_outcomes()[:num_unused_dice] + (outcome-1,) * num_possible_dice
        popped_select_dice = self.select_dice()
        
        # Zero dice rolling this outcome.
        # If there is no weight, this is the only possibility.
        pool = _pool_cached_unchecked(popped_die, popped_select_dice, None, popped_max_outcomes)
        weight = 1
        count = 0
        yield pool, count, weight
        
        if single_weight > 0:
            # If the outcome has nonzero weight, consider how many dice could roll this outcome.
            comb_row = hdroller.math.comb_row(num_possible_dice, single_weight)
            for weight in comb_row[1:]:
                count += popped_select_dice[-1]
                popped_max_outcomes = popped_max_outcomes[:-1]
                popped_select_dice = popped_select_dice[:-1]
                pool = _pool_cached_unchecked(popped_die, popped_select_dice, None, popped_max_outcomes)
                yield pool, count, weight
    
    @cached_property
    def _pops(self):
        return tuple(self._iter_pops())
    
    def pops(self):
        return self._pops
    
    @cached_property
    def _key_tuple(self):
        return self.die(), self.min_outcomes(), self.max_outcomes(), self.select_dice()
    
    def __eq__(self, other):
        if not isinstance(other, DicePool): return False
        return self._key_tuple == other._key_tuple
    
    @cached_property
    def _hash(self):
        return hash(self._key_tuple)
        
    def __hash__(self):
        return self._hash

    def __str__(self):
        return '\n'.join([str(self.die()), str(self.min_outcomes()), str(self.max_outcomes()), str(self.select_dice())])