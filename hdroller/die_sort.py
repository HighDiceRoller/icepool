import hdroller
import hdroller.math

from functools import cache
from scipy.special import comb
import numpy

"""
These deal with all sorted tuples of tuple_length whose elements are between 0 and num_values-1 inclusive.
"""
def iter_sorted_tuples(tuple_length, num_values, start_value=0):
    """
    Iterates through all sorted tuples.
    """
    if tuple_length == 0:
        yield ()
        return
    
    for head_value in range(start_value, num_values):
        for tail in iter_sorted_tuples(tuple_length - 1, num_values, head_value):
            yield (head_value,) + tail
    
def unravel_sorted_tuple_index(indices, tuple_length, num_values, start_value=0):
    """
    Turns indices into their corresponding sorted tuples.
    """
    if tuple_length == 1:
        return indices
    
    if numpy.isscalar(indices):
        indices = numpy.array([indices])
    else:
        indices = numpy.copy(indices)
    
    result = numpy.zeros((len(indices), tuple_length))
    
    for head_value in range(start_value, num_values):
        tail_size = comb(num_values - head_value, tuple_length, repeated=True)
        mask = (indices >= 0) & (indices < tail_size)
        result[mask][0] = head_value
        result[mask][1:] = unravel_sorted_tuple_index(indices[mask], tuple_length - 1, head_value)
        indices -= tail_size
    return result

def ravel_sorted_tuple(tuple, num_values):
    if len(tuple) == 1:
        return tuple[0]
    result = 0
    for head_value in range(tuple[0]):
        result += comb(num_values - head_value, len(tuple), repeated=True)
    return result + ravel_sorted_tuple(tuple[1:], num_values)

@cache
def keep_transition(tuple_length, num_values, keep_slice):
    """
    [new_value, sorted_tuple_index] -> next_sorted_tuple_index
    """
    num_tuples = comb(num_values, tuple_length, repeated=True)
    result = numpy.zeros((num_values, num_tuples))
    for value in num_values:
        for sorted_tuple_index, sorted_tuple in enumerate(hdroller.math.iter_sorted_tuples(tuple_length, num_values)):
            next_sorted_tuple = sorted((value,) + sorted_tuple)[keep_slice]
            next_sorted_tuple_index = hdroller.math.ravel_sorted_tuple(next_sorted_tuple, tuple_length, num_values)
            result[value, sorted_tuple_index] = next_sorted_tuple_index
    result.setflags(write=False)
    return result

def keep_highest_transition(tuple_length, num_values):
    return keep_highest_transition(tuple_length, num_values, slice(1, None))
    
def keep_lowest_transition(tuple_length, num_values):
    return keep_highest_transition(tuple_length, num_values, slice(None, -1))

def SortedDicePool():
    def __init__(*dice):
        dice = hdroller.Die._union_outcomes(*dice)
        self._min_outcome = dice[0].min_outcome()
        shape = tuple(len(die) for die in dice)
        self._pmf = numpy.zeros(shape)
        for outcomes in numpy.ndindex(shape):
            mass = numpy.product(die.pmf()[outcome] for die, outcome in zip(dice, outcomes))
            outcomes = tuple(sorted(outcomes))
            self._pmf[outcomes] += mass
