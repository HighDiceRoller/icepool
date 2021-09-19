import hdroller
import hdroller.math

from functools import lru_cache
import numpy

"""
These deal with all sorted tuples of tuple_length whose elements are between 0 and num_values-1 inclusive.
Tuples are indexed in lexicographic order.
"""

def num_sorted_tuples(tuple_length, num_values):
    return hdroller.math.comb(num_values, tuple_length, exact=True, repetition=True)

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

@lru_cache(maxsize=None)
def ravel_sorted_tuple(tuple, num_values, start_value=0):
    """
    Given a sorted tuple, returns the index of that tuple.
    """
    if len(tuple) == 0:
        return 0
    elif len(tuple) == 1:
        return tuple[0] - start_value
    result = 0
    for head_value in range(start_value, tuple[0]):
        result += num_sorted_tuples(len(tuple) - 1, num_values - head_value)
    return result + ravel_sorted_tuple(tuple[1:], num_values, tuple[0])

@lru_cache(maxsize=None)
def keep_transition(tuple_length, num_values, transition_slice):
    """
    [new_value, sorted_tuple_index] -> next_sorted_tuple_index
    transition_slice is a tuple of arguments to slice().
    """
    transition_slice = slice(*transition_slice)
    num_tuples = num_sorted_tuples(tuple_length, num_values)
    result = numpy.zeros((num_values, num_tuples), dtype=int)
    for value in range(num_values):
        for sorted_tuple_index, sorted_tuple in enumerate(iter_sorted_tuples(tuple_length, num_values)):
            next_sorted_tuple = sorted((value,) + sorted_tuple)[transition_slice]
            next_sorted_tuple_index = ravel_sorted_tuple(tuple(next_sorted_tuple), num_values)
            result[value, sorted_tuple_index] = next_sorted_tuple_index
    result.setflags(write=False)
    return result
    
def keep(num_keep, *dice, transition_slice, final_slice):
    if num_keep == 0:
        return hdroller.Die(0)
    dice = hdroller.Die._align(*dice)
    
    num_values = len(dice[0])
    sorted_pmf_length = num_sorted_tuples(num_keep, num_values)
    sorted_pmf = numpy.zeros((sorted_pmf_length,))
    
    # Initial state.
    unsorted_shape = (num_values,) * num_keep
    for faces in numpy.ndindex(unsorted_shape):
        mass = numpy.product([die.pmf()[face] for die, face in zip(dice[:num_keep], faces)])
        faces = tuple(sorted(faces))
        index = ravel_sorted_tuple(faces, num_values)
        sorted_pmf[index] += mass
    
    # Step through the remaining dice.
    transition = keep_transition(num_keep, num_values, transition_slice)
    for die in dice[num_keep:]:
        next_sorted_pmf = numpy.zeros_like(sorted_pmf)
        for face in range(num_values):
            mass = die.pmf()[face]
            if mass <= 0.0: continue
            indices = transition[face, :]
            next_masses = mass * sorted_pmf
            # bincount appears to be faster than add.at.
            next_sorted_pmf += numpy.bincount(indices, next_masses, len(next_sorted_pmf))
        sorted_pmf = next_sorted_pmf
    
    # Sum the faces.
    final_slice = slice(*final_slice)
    
    sum_pmf_length = num_keep * (num_values - 1) + 1
    sum_pmf = numpy.zeros((sum_pmf_length,))
    
    for faces, mass in zip(iter_sorted_tuples(num_keep, num_values), sorted_pmf):
        sum_pmf[sum(faces[final_slice])] += mass
        
    sum_min_outcome = len(faces[final_slice]) * dice[0].min_outcome()
    
    return hdroller.Die(sum_pmf, sum_min_outcome)._trim()

def keep_highest(num_keep, *dice, drop_highest=0):
    return keep(num_keep, *dice, transition_slice=(1, None), final_slice=(None, num_keep - drop_highest))
    
def keep_lowest(num_keep, *dice, drop_lowest=0):
    return keep(num_keep, *dice, transition_slice=(None, -1), final_slice=(drop_lowest, None))
