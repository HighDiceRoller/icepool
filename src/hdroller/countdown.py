"""
"Countdown" algorithm for computing dice pools.
"""

import hdroller
import hdroller.math

import numpy

def _countdown(die_sizes, keep_mask, weights=None):
    """
    die_sizes: an array of integers, one per die, denoting how many faces that die has.
    keep: Specifies which indexes of dice to keep. Should be of the same size as die_sizes.
    weights: an array of size at least equal to the largest of die_sizes, denoting the weight of each face.
        If omitted, all faces will be given a weight of 1.
    """
    
    keep_mask_desc = numpy.flip(keep_mask)
    num_keep = numpy.count_nonzero(keep_mask)
    num_dice = len(die_sizes)
    
    die_sizes_desc = numpy.flip(numpy.sort(die_sizes))
    max_face = die_sizes_desc[0] - 1
    max_totals = numpy.insert(numpy.cumsum((die_sizes_desc-1) * keep_mask_desc), 0, 0.0)
    if weights is None:
        weights = numpy.ones((max_face + 1,))
    if not hdroller.math.product_of_total_weights_is_exact(weights[:die_size] for die_size in die_sizes):
        weights = weights / numpy.cumsum(weights)[-1]
    weights_below = numpy.insert(numpy.cumsum(weights), 0, 0.0)
        
    # (number of consumed dice, running total) -> weight of having this running total. Denominator is equal to product of weights of the remaining dice and sizes.
    state = numpy.zeros((num_dice + 1, max_totals[-1] + 1))
    state[0, 0] = 1.0
    
    prev_num_dice = 0
    for curr_face in range(max_face, -1, -1):
        next_state = numpy.zeros_like(state)
        # The total number of dice that are large enough to roll the current face.
        curr_num_dice = numpy.count_nonzero(die_sizes > curr_face)
        weight = weights[curr_face]
        weight_below = weights_below[curr_face]
        for prev_num_consumed_dice in range(0, prev_num_dice+1):
            num_active_dice = curr_num_dice - prev_num_consumed_dice
            prev_max_total = max_totals[prev_num_consumed_dice]
            for new_num_consumed_dice in range(0, num_active_dice+1):
                next_num_consumed_dice = prev_num_consumed_dice + new_num_consumed_dice
                comb = hdroller.math.comb(num_active_dice, new_num_consumed_dice) * numpy.power(weight, new_num_consumed_dice)
                increase = numpy.count_nonzero(keep_mask_desc[prev_num_consumed_dice:next_num_consumed_dice]) * curr_face
                prev_dist = state[prev_num_consumed_dice, :prev_max_total+1]
                next_state[next_num_consumed_dice, increase:len(prev_dist)+increase] += prev_dist * comb
        state = next_state
        prev_num_dice = curr_num_dice
    
    return state[-1, :]
    
    """
    for each stage:
        for each number of remaining dice:
            for each number of dice rolling within range:
                compute convolution of sum
                compute chance of rolling within range
                    normalized: binom * chance of rolling within range ** number of dice rolled within range * (1 - chance of roling within range) ** number of eligible dice not rolled within range
                    non-normalized: chance of rolling within range = weights within range / remaining weight, so denominator must be multiple of remaining weight ** number of eligible dice?
                update state transition
                
                example: d5, d5, d3, d3, d2
                first stage:
                    state 0, ...: weight of both d5s rolling 3 or less, total weight = 9 * 18 / 450
                    state 1, ...: weight of one d5 rolling 3 or less, total weight = 12 * 18 / 450
                    state 2, ...: weight of both d5s rolling 4-5, total weight = 4 * 18 / 450
                second stage:
                    state 0: we have 4x d3s -> denominator of 81 * 2.
                    state 1: we have 3x d3s -> denominator of 27 * 2.
                    state 2: we have 2x d3s -> denominator of 9 * 2.
                    
                    
                what does state represent? conditioned on this many dice used/remaining, weight of running total? final denominator = remaining weight ** number of eligible dice?
    """

def _keep_pool(die, num_dice, keep_mask, die_sizes=None):
    if die_sizes is None:
        die_sizes = numpy.array([len(die)] * num_dice)
    min_outcome = numpy.count_nonzero(keep_mask) * die.min_outcome()
    return hdroller.Die(_countdown(die_sizes, keep_mask, weights=die.weights()), min_outcome)

def _keep_standard(die_sizes, keep_mask):
    min_outcome = numpy.count_nonzero(keep_mask)
    return hdroller.Die(_countdown(die_sizes, keep_mask), min_outcome)
