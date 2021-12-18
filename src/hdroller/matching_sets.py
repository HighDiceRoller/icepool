import hdroller.math

from functools import lru_cache
import numpy

@lru_cache(maxsize=None)
def largest_matching_set(num_dice, num_faces):
    """
    The result is an array of length num_dice where the ith element is the chance of the largest matching set being at least i+1 dice.
    """
    
    if num_faces == 1:
        sf = numpy.ones((num_dice,))
        sf.setflags(write=False)
        return sf
    
    sf = numpy.zeros((num_dice,))
    num_rolled_ones = numpy.arange(num_dice+1)
    weights = hdroller.math.comb(num_dice, num_rolled_ones) * numpy.power(float(num_faces), -num_rolled_ones) * numpy.power(num_faces / (num_faces-1), (num_rolled_ones - num_dice))
    for num_rolled_one in num_rolled_ones:
        num_rolled_other = num_dice - num_rolled_one
        partial_sf = numpy.pad(largest_matching_set(num_rolled_other, num_faces - 1), (0, num_rolled_one))
        partial_sf[:num_rolled_one] = 1.0
        sf += partial_sf * weights[num_rolled_one]
    sf.setflags(write=False)
    return sf
