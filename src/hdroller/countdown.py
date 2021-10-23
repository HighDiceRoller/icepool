"""
"Countdown" algorithm for computing dice pools.
"""

import hdroller
import hdroller.math

import numpy

# TODO: faces vs. outcomes
def countdown(keep_mask, die_sizes=None, die=None):
    """
    keep_mask: A mask of one boolean per die from lowest to highest, denoting whether to keep that sorted die.
    die: A reference Die which weights each possible outcome of each individual die.
        If omitted, outcomes will be 1 ... max(die_sizes) inclusive with a weight of 1 per outcome.
    die_sizes: An array of integers, one per die.
        Individual dice will have faces equal to the first die_size faces of the reference die.
        If omitted, every die will have size equal to the reference die.
    """
    if die is None and die_sizes is None:
        raise ValueError('At least one of die and die_sizes must be provided.')
    
    num_keep = numpy.count_nonzero(keep_mask)
    if num_keep == 0:
        return hdroller.Die(0)
    
    keep_mask_desc = numpy.flip(keep_mask)
    keep_mask_desc_cumsum = numpy.insert(numpy.cumsum(keep_mask_desc), 0, 0.0)
    num_dice = len(keep_mask)
    
    if die_sizes is None:
        die_sizes = numpy.array([len(die)] * num_dice)
        die_sizes_desc = die_sizes
    else:
        die_sizes = numpy.array(die_sizes)
        if len(die_sizes) != len(keep_mask):
            raise ValueError('die_sizes must have same len as keep_mask.')
        die_sizes_desc = numpy.flip(numpy.sort(die_sizes))
        
    max_face = die_sizes_desc[0] - 1
    max_totals = numpy.insert(numpy.cumsum((die_sizes_desc-1) * keep_mask_desc), 0, 0.0)
    
    if die is None:
        die = hdroller.Die.standard(max_face + 1)
    
    weights = die.weights()
    
    if hdroller.math.should_normalize_weight_product(weights[:die_size] for die_size in die_sizes):
        weights = weights / numpy.cumsum(weights)[-1]
        
    # TODO: terminate early if there are no more dice to keep.
    weights_below = numpy.insert(numpy.cumsum(weights), 0, 0.0)
        
    # (number of consumed dice, running sum) -> number of ways of rolling this running sum with all consumed dice greater than curr_face.
    state = numpy.zeros((num_dice + 1, max_totals[-1] + 1))
    state[0, 0] = 1.0
    
    prev_num_dice = 0
    for curr_face in range(max_face, -1, -1):
        next_state = numpy.zeros_like(state)
        # The total number of dice that are large enough to roll the current face.
        curr_num_dice = numpy.count_nonzero(die_sizes > curr_face)
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
