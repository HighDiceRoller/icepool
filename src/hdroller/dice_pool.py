__docformat__ = 'google'

import hdroller.indexing
import hdroller.math
from hdroller.functools import die_cache

import bisect
from functools import cached_property
import math

def Pool(die, num_dice=None, select_dice=None, reverse=None, *, min_outcomes=None, max_outcomes=None):
    """ Factory function for dice pools.
    
    This is capitalized because it is the preferred way of getting a new instance,
    and so that you can use `from hdroller import Pool` while leaving the name `pool` free.
    The name of the actual class is `DicePool`.
    
    Exactly one out of `num_dice`, `min_outcomes`, and `max_outcomes` should be provided.
    This will also determine whether the outcomes are evaluated by `PoolEval.next_state()`
    in ascending order or descending order.
    
    Args:
        die: The die this pool is based on.
        num_dice: The number of dice in the pool. If set, all dice will have the same outcomes as `die`.
            The outcomes will be evaluated in ascending order unless `reverse=True`.
        min_outcomes: A sequence of one outcome per die in the pool.
            That die will be limited to that minimum outcome, with all lower outcomes being removed (i.e. rerolled).
            The outcomes will be evaluated in descending order.
        max_outcomes: A sequence of one outcome per die in the pool.
            That die will be limited to that maximum outcome, with all higher outcomes being removed (i.e. rerolled).
            The outcomes will be evaluated in ascending order.
        select_dice: Only dice selected by this will be counted.
            This applies to the dice sorted from lowest to highest (regardless of iteration direction).
            For example, `slice(-2, None)` would count only the two highest dice.
            You can also use the [] operator to select dice from an existing pool.
            For example, you could construct the pool first and then index it with `[-2:]`.
        reverse: Only valid if `num_dice` is provided.
            If not `True` (default), the outcomes will be evaluated in ascending order.
            If `True`, outcomes will be evaluated in descending order.
    """
    if (num_dice is not None) + (min_outcomes is not None) + (max_outcomes is not None) != 1:
        raise ValueError('Exactly one of num_dice, min_outcomes, or max_outcomes must be provided.')

    if num_dice is not None:
        if reverse is not True:
            max_outcomes = (die.max_outcome(),) * num_dice
        else:
            min_outcomes = (die.min_outcome(),) * num_dice
    elif min_outcomes is not None:
        if reverse is not None:
            raise ValueError('reverse is not valid if min_outcomes is provided.')
        min_outcomes = tuple(sorted(max(outcome, die.min_outcome()) for outcome in min_outcomes))
        num_dice = len(min_outcomes)
    else:  # max_outcomes is not None
        if reverse is not None:
            raise ValueError('reverse is not valid if max_outcomes is provided.')
        max_outcomes = tuple(sorted(min(outcome, die.max_outcome()) for outcome in max_outcomes))
        num_dice = len(max_outcomes)
    
    if min_outcomes is not None:
        raise NotImplementedError('min_outcomes not yet implemented for pools.')
    
    if select_dice is None:
        select_dice = (True,) * num_dice
    else:
        select_dice = hdroller.indexing.select_bools(num_dice, select_dice)
    
    return DicePool(die, select_dice, min_outcomes, max_outcomes)

@die_cache
def _pool_cached_unchecked(die, select_dice, min_outcomes, max_outcomes):
    return DicePool(die, select_dice, min_outcomes, max_outcomes)

class DicePool():
    def __init__(self, die, select_dice, min_outcomes, max_outcomes):
        """ Unchecked constructor. """
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
        
    def direction(self):
        """ Returns 1 if the outcomes are evaluated in ascending order, 
        or -1 if they are evaluated in descending order.
        """
        if self.max_outcomes() is not None:
            return 1
        else:
            return -1
    
    def _iter_pops(self):
        """
        Yields:
            From 0 to the number of dice that can roll this outcome inclusive:
            * pool: A `DicePool` resulting from removing that many dice from this `DicePool`, while also removing the max outcome.
                If there is only one outcome with weight remaining, only one result will be yielded, corresponding to all dice rolling that outcome.
                If the outcome has zero weight, only one result will be yielded, corresponding to zero dice rolling that outcome.
                If there are no outcomes remaining, this will be `None`.
            * count: An `int` indicating the number of selected dice that rolled the removed outcome.
            * weight: An `int` indicating the weight of that many dice rolling the removed outcome.
        """
        remaining_selected_dice = sum(self.select_dice())

        num_possible_dice = self.num_dice() - bisect.bisect_left(self.max_outcomes(), self.die().max_outcome())
        num_unused_dice = self.num_dice() - num_possible_dice
        popped_die, outcome, single_weight = self.die().pop_max()
        
        if len(popped_die) == 0:
            # This is the last outcome. All dice must roll this outcome.
            weight = single_weight ** num_possible_dice
            yield None, remaining_selected_dice, weight
            return
        
        if popped_die.total_weight() == 0:
            # This is the last outcome with positive weight. All dice must roll this outcome.
            weight = single_weight ** num_possible_dice
            pool = _pool_cached_unchecked(popped_die, (), None, ())
            yield pool, remaining_selected_dice, weight
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
    
    def select_all_dice(self):
        """ Returns a pool with all dice selected. """
        return DicePool(self.die(), (True,) * self.num_dice(), self.min_outcomes(), self.max_outcomes())
    
    def __getitem__(self, select_dice):
        """ Returns a pool with only selected dice counted. 
        
        If a selection was already applied to the pool, this is applied only to the previously selected dice.
        For example, pool[-2:][:1] would select the top two dice, then the bottom die of those,
        with the final result being a pool with the second-highest die counted.
        """
        prev_indexes = tuple(i for i, selected in enumerate(self.select_dice()) if selected)
        new_indexes = hdroller.indexing.select_from(prev_indexes, select_dice)
        new_select = hdroller.indexing.select_bools(self.num_dice(), new_indexes)
        return DicePool(self.die(), new_select, self.min_outcomes(), self.max_outcomes())
    
    @cached_property
    def _pops(self):
        return tuple(self._iter_pops())
    
    def pops(self):
        return self._pops
    
    @cached_property
    def _key_tuple(self):
        return self.die().key_tuple(), self.min_outcomes(), self.max_outcomes(), self.select_dice()
    
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