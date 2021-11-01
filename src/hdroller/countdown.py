"""
"Countdown" algorithm for computing dice pools.
"""

import hdroller
import hdroller.math
import hdroller.convolution_series

import numpy

def keep(num_dice, keep_indexes, die=None, max_outcomes=None):
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
    # TODO: flip if max_outcomes is None and it is more efficient to do so?
    last_keep_index = numpy.nonzero(keep_mask_desc)[0][-1]
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
    
    # num_consumed_dice -> maximum (kept) total on those dice
    max_totals = numpy.insert(numpy.cumsum((die_sizes_desc-1) * keep_mask_desc), 0, 0)
    weights = die.weights()
    
    if hdroller.math.should_normalize_weight_product(weights[:die_size] for die_size in die_sizes_desc):
        weights = weights / numpy.cumsum(weights)[-1]
        
    weights_below = numpy.insert(numpy.cumsum(weights), 0, 0.0)
        
    # (number of consumed dice, running sum) -> number of ways of rolling this running sum with all consumed dice greater than curr_face.
    state = numpy.zeros((last_keep_index+1, max_totals[last_keep_index] + 1))
    state[0, 0] = 1.0
    result_weights = numpy.zeros((max_totals[-1] + 1,))
    
    # The total number of dice that are large enough to roll the current face.
    curr_num_dice = 0
    prev_num_dice = 0
    for curr_face in range(max_face, -1, -1):
        next_state = numpy.zeros_like(state)
        while curr_num_dice < num_dice and die_sizes_desc[curr_num_dice] > curr_face:
            curr_num_dice += 1
        weight = weights[curr_face]
        
        die_sizes_below = numpy.minimum(die_sizes_desc, curr_face)
        # num_consumed_dice -> number of ways of rolling the remaining dice
        factor_below = numpy.append(hdroller.math.reverse_cumprod(weights_below[die_sizes_below]), 1.0)
        
        conv = numpy.array([1.0])
        for num_active_dice in range(0, curr_num_dice+1):
            prev_num_consumed_dice = curr_num_dice - num_active_dice
            if prev_num_consumed_dice <= last_keep_index:
                prev_min_total = keep_mask_desc_cumsum[prev_num_consumed_dice] * (curr_face+1)
                prev_max_total = max_totals[prev_num_consumed_dice]
                prev_dist = state[prev_num_consumed_dice, prev_min_total:prev_max_total+1]
                for new_num_consumed_dice in range(0, num_active_dice+1):
                    next_num_consumed_dice = prev_num_consumed_dice + new_num_consumed_dice
                    increase = (keep_mask_desc_cumsum[next_num_consumed_dice] - keep_mask_desc_cumsum[prev_num_consumed_dice]) * curr_face
                    if next_num_consumed_dice > last_keep_index:
                        # TODO: Is there a way of doing this outside the inner loop? Perhaps as part of the convolution?
                        result_weights[prev_min_total+increase:prev_max_total+increase+1] += prev_dist * conv[new_num_consumed_dice] * factor_below[next_num_consumed_dice]
                    else:
                        next_state[next_num_consumed_dice, prev_min_total+increase:prev_max_total+increase+1] += prev_dist * conv[new_num_consumed_dice]
            conv = numpy.convolve(conv, [1.0, weight])
        state = next_state
        prev_num_dice = curr_num_dice
    
    result_min_outcome = num_keep * die.min_outcome()
    return hdroller.Die(result_weights, result_min_outcome)

def best_set(die, num_dice, match_func=None, straight_func=None):
    """
    die: The die to roll.
    num_dice: The number of dice to roll.
    match_func: A function match_size, set_outcome -> score.
    straight_func: A function straight_size, start_outcome -> score.
      Increasing the length of a straight should never decrease its score.
    
    Returns:
        A Die representing the highest scoring set.
    """
    if not (match_func or straight_func):
        raise ValueError('At least one of match_func or straight_func must be provided.')
    
    if num_dice == 0:
        return hdroller.Die(0)
    
    # TODO: normalize if necessary
    
    min_score = (match_func or straight_func)(1, die.min_outcome())
    max_score = (match_func or straight_func)(1, die.min_outcome())
    
    for size in range(1, num_dice+1):
        for outcome in die.outcomes():
            if match_func:
                score = match_func(size, outcome)
                min_score = min(min_score, score)
                max_score = max(max_score, score)
            if straight_func and size + outcome - 1 <= die.max_outcome():
                score = straight_func(size, outcome)
                min_score = min(min_score, score)
                max_score = max(max_score, score)
    
    # (straight size, number of consumed dice, running best score) -> number of ways of rolling this straight size and running score with all consumed dice before the current face.
    max_straight_size = 0 if straight_func is None else num_dice
    state = numpy.zeros((max_straight_size+1, num_dice+1, max_score-min_score+1))
    state[0, 0, 0] = 1.0
    
    for outcome_index, (outcome, weight) in enumerate(zip(die.outcomes(), die.weights())):
        next_state = numpy.zeros_like(state)
        conv = numpy.array([1.0])
        for num_remaining_dice in range(0, num_dice+1):
            prev_num_consumed_dice = num_dice - num_remaining_dice
            max_prev_straight_size = min(outcome_index, prev_num_consumed_dice, max_straight_size)
            # No dice rolled this outcome. All straights are broken, everything else remains the same.
            next_state[0, prev_num_consumed_dice, :] = numpy.sum(state[:outcome_index+1, prev_num_consumed_dice, :], axis=0) * conv[0]
            # At least one die rolled this outcome.
            for match_size in range(1, num_remaining_dice+1):
                match_score = match_func(match_size, outcome) if match_func else min_score
                next_num_consumed_dice = match_size + prev_num_consumed_dice
                for prev_straight_size in range(max_prev_straight_size+1):
                    next_straight_size = min(prev_straight_size + 1, max_straight_size) if straight_func else 0
                    straight_score = straight_func(next_straight_size, outcome - prev_straight_size) if straight_func else min_score

                    next_score = max(match_score, straight_score)
                    next_index = next_score - min_score
                    next_state[next_straight_size, next_num_consumed_dice, next_index] += numpy.sum(state[prev_straight_size, prev_num_consumed_dice, :next_index]) * conv[match_size]
                    next_state[next_straight_size, next_num_consumed_dice, next_index:] += state[prev_straight_size, prev_num_consumed_dice, next_index:] * conv[match_size]
            conv = numpy.convolve(conv, [1.0, weight])
        state = next_state
    result_weights = numpy.sum(state[:, num_dice, :], axis=0)
    return hdroller.Die(result_weights, min_score).trim()
