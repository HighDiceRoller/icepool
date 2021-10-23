"""
"Countdown" algorithm for computing dice pools.
"""

import hdroller
import hdroller.math

import numpy

def keep(num_dice, keep_indexes, max_outcomes=None, die=None):
    """
    num_dice: The number of dice to roll.
    keep_indexes: A specification of which dice to keep from lowest to highest. This can be any way of indexing an array of num_dice elements.
    die: A reference Die which weights each possible outcome of each individual die.
        If omitted, outcomes will be as a standard die, i.e. 1 ... max(max_outcomes) inclusive with a weight of 1 per outcome.
    max_outcomes: An array of integers, one per die.
        Individual dice will have faces from the first face up to max_outcome
        If omitted, every die will have size equal to the reference die.
    """
    if die is None and max_outcomes is None:
        raise ValueError('At least one of die and max_outcomes must be provided.')
        
    keep_mask = numpy.zeros((num_dice,), dtype=bool)
    keep_mask[keep_indexes] = True
    
    num_keep = numpy.count_nonzero(keep_mask)
    if num_keep == 0:
        return hdroller.Die(0)
    
    keep_mask_desc = numpy.flip(keep_mask)
    keep_mask_desc_cumsum = numpy.insert(numpy.cumsum(keep_mask_desc), 0, 0.0)

    if max_outcomes is not None:
        if len(max_outcomes) != num_dice:
            raise ValueError('max_outcomes must have num_dice elements.')
        if die is None:
            die_sizes_desc = numpy.flip(numpy.sort(max_outcomes))
            max_face = die_sizes_desc[0] - 1
            die = hdroller.Die.standard(max_face + 1)
        else:
            die_sizes = numpy.array(max_outcomes) - die.min_outcome() + 1
            die_sizes_desc = numpy.flip(numpy.sort(die_sizes))
            max_face = die_sizes_desc[0] - 1
    else:
        # Die must be provided.
        die_sizes_desc = numpy.array([len(die)] * num_dice)
        max_face = die_sizes_desc[0] - 1
    
    max_totals = numpy.insert(numpy.cumsum((die_sizes_desc-1) * keep_mask_desc), 0, 0.0)
    weights = die.weights()
    
    if hdroller.math.should_normalize_weight_product(weights[:die_size] for die_size in die_sizes_desc):
        weights = weights / numpy.cumsum(weights)[-1]
        
    # TODO: terminate early if there are no more dice to keep?
    weights_below = numpy.insert(numpy.cumsum(weights), 0, 0.0)
        
    # (number of consumed dice, running sum) -> number of ways of rolling this running sum with all consumed dice greater than curr_face.
    state = numpy.zeros((num_dice + 1, max_totals[-1] + 1))
    state[0, 0] = 1.0
    
    prev_num_dice = 0
    for curr_face in range(max_face, -1, -1):
        next_state = numpy.zeros_like(state)
        # The total number of dice that are large enough to roll the current face.
        curr_num_dice = numpy.count_nonzero(die_sizes_desc > curr_face)
        weight = weights[curr_face]
        # The number of ways to roll exactly new_num_consumed_dice of the current face on num_active_dice.
        conv = numpy.array([1.0])
        for num_active_dice in range(0, curr_num_dice+1):
            prev_num_consumed_dice = curr_num_dice - num_active_dice
            prev_min_total = keep_mask_desc_cumsum[prev_num_consumed_dice] * (curr_face+1)
            prev_max_total = max_totals[prev_num_consumed_dice]
            prev_dist = state[prev_num_consumed_dice, prev_min_total:prev_max_total+1]
            for new_num_consumed_dice in range(0, num_active_dice+1):
                next_num_consumed_dice = prev_num_consumed_dice + new_num_consumed_dice
                increase = (keep_mask_desc_cumsum[next_num_consumed_dice] - keep_mask_desc_cumsum[prev_num_consumed_dice]) * curr_face
                next_state[next_num_consumed_dice, prev_min_total+increase:prev_max_total+increase+1] += prev_dist * conv[new_num_consumed_dice]
            conv = numpy.convolve(conv, [1.0, weight])
        state = next_state
        prev_num_dice = curr_num_dice
    
    result_min_outcome = num_keep * die.min_outcome()
    result_weights = state[-1, :]
    return hdroller.Die(result_weights, result_min_outcome)
