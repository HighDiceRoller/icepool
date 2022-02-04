__docformat__ = 'google'

import hdroller.math
from hdroller.functools import die_cache

import bisect
from functools import cached_property
import math

def Pool(die, num_dice=None, count_dice=None, reverse=None, *, min_outcomes=None, max_outcomes=None):
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
        count_dice: Determines which of the **sorted** dice will be counted, and how many times.
            The dice are sorted in ascending order for this purpose,
            regardless of which order the outcomes are evaluated in.
            
            This can be an `int` or a `slice`, in which case the selected dice are counted once each.
            For example, `slice(-2, None)` would count the two highest dice.
            
            Or this can be a sequence of `int`s, one for each die in order.
            Each die is counted that many times.
            For example, `[0, 0, 2, 0, 0]` would count the middle out of five dice twice.
            
            You can also use the [] operator to select dice from an existing pool.
            This is always an absolute selection on all `num_dice`,
            not a relative selection on already-selected dice,
            which would be ambiguous in the presence of multiple or negative counts.
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
    
    if count_dice is None:
        count_dice = (1,) * num_dice
    else:
        count_dice = _compute_select_dice(num_dice, count_dice)
    
    return DicePool(die, count_dice, min_outcomes, max_outcomes)

def _compute_select_dice(num_dice, count_dice):
    if isinstance(count_dice, int):
        result = [0] * num_dice
        result[count_dice] = 1
        return tuple(result)
    elif isinstance(count_dice, slice):
        result = [0] * num_dice
        result[count_dice] = [1] * len(result[count_dice])
        return tuple(result)
    else:
        if len(count_dice) != num_dice:
            raise ValueError('count_dice must either be a slice, or a sequence of length equal to num_dice.')
        if not all(isinstance(x, int) for x in count_dice):
            raise TypeError('count_dice must be a sequence of ints.')
        return tuple(count_dice)

@die_cache
def _pool_cached_unchecked(die, count_dice, min_outcomes, max_outcomes):
    return DicePool(die, count_dice, min_outcomes, max_outcomes)

class DicePool():
    def __init__(self, die, count_dice, min_outcomes, max_outcomes):
        """ Unchecked constructor. """
        self._die = die
        self._select_dice = count_dice
        self._min_outcomes = min_outcomes
        self._max_outcomes = max_outcomes
    
    def die(self):
        return self._die
        
    def count_dice(self):
        return self._select_dice
        
    def __getitem__(self, count_dice):
        """ Returns a pool with the selected dice counted, as the `count_dice` argument to `Pool()`.
        
            Determines which of the **sorted** dice will be counted, and how many times.
            The dice are sorted in ascending order for this purpose,
            regardless of which order the outcomes are evaluated in.
            
            This can be an `int` or a `slice`, in which case the selected dice are counted once each.
            For example, `slice(-2, None)` would count the two highest dice.
            
            Or this can be a sequence of `int`s, one for each die in order.
            Each die is counted that many times.
            For example, `[0, 0, 2, 0, 0]` would count the middle out of five dice twice.
            
            This is always an absolute selection on all `num_dice`,
            not a relative selection on already-selected dice,
            which would be ambiguous in the presence of multiple or negative counts.
        """
        new_select = _compute_select_dice(self.num_dice(), count_dice)
        return DicePool(self.die(), new_select, self.min_outcomes(), self.max_outcomes())
    
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
        remaining_count = sum(self.count_dice())

        num_possible_dice = self.num_dice() - bisect.bisect_left(self.max_outcomes(), self.die().max_outcome())
        num_unused_dice = self.num_dice() - num_possible_dice
        popped_die, outcome, single_weight = self.die().pop_max()
        
        if len(popped_die) == 0:
            # This is the last outcome. All dice must roll this outcome.
            weight = single_weight ** num_possible_dice
            yield None, remaining_count, weight
            return
        
        if popped_die.total_weight() == 0:
            # This is the last outcome with positive weight. All dice must roll this outcome.
            weight = single_weight ** num_possible_dice
            pool = _pool_cached_unchecked(popped_die, (), None, ())
            yield pool, remaining_count, weight
            return
        
        if not any(self.count_dice()):
            # No selected dice remain. All dice must roll somewhere below, so empty all dice in one go.
            # We could follow the staircase of max_outcomes more closely but this is unlikely to be relevant in most cases.
            pool = _pool_cached_unchecked(popped_die, (), None, ())
            weight = math.prod(self.die().weight_le(max_outcome) for max_outcome in self.max_outcomes())
            yield pool, 0, weight
            return
        
        popped_max_outcomes = self.max_outcomes()[:num_unused_dice] + (outcome-1,) * num_possible_dice
        popped_select_dice = self.count_dice()
        
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
        return self.die().key_tuple(), self.min_outcomes(), self.max_outcomes(), self.count_dice()
    
    def __eq__(self, other):
        if not isinstance(other, DicePool): return False
        return self._key_tuple == other._key_tuple
    
    @cached_property
    def _hash(self):
        return hash(self._key_tuple)
        
    def __hash__(self):
        return self._hash

    def __str__(self):
        return '\n'.join([str(self.die()), str(self.min_outcomes()), str(self.max_outcomes()), str(self.count_dice())])