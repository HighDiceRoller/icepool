import hdroller.math

from functools import cache
from scipy.special import comb
import numpy

@cache
def largest_matching_set(num_dice, num_faces):
    """
    The result is an array of length num_dice where the ith element is the chance of the largest matching set being at least i+1 dice.
    """
    
    if num_faces == 1:
        ccdf = numpy.ones((num_dice,))
        ccdf.setflags(write=False)
        return ccdf
    
    ccdf = numpy.zeros((num_dice,))
    num_rolled_ones = numpy.arange(num_dice+1)
    weights = comb(num_dice, num_rolled_ones) * numpy.power(float(num_faces), -num_rolled_ones) * numpy.power(num_faces / (num_faces-1), (num_rolled_ones - num_dice))
    for num_rolled_one in num_rolled_ones:
        num_rolled_other = num_dice - num_rolled_one
        partial_ccdf = numpy.pad(largest_matching_set(num_rolled_other, num_faces - 1), (0, num_rolled_one))
        partial_ccdf[:num_rolled_one] = 1.0
        ccdf += partial_ccdf * weights[num_rolled_one]
    ccdf.setflags(write=False)
    return ccdf
