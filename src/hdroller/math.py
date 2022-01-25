import numpy
from functools import lru_cache

MAX_INT_FLOAT = 2 ** 53

def reverse_cumsum(a, axis=None, *args, **kwargs):
    """
    Applies a cumsum in reverse direction along the specified axis.
    Any additional arguments are sent to cumsum.
    """
    return numpy.flip(numpy.cumsum(numpy.flip(a, axis=axis), axis=axis, *args, **kwargs), axis=axis)

@lru_cache(maxsize=None)
def binom_row(n, b):
    """
    Returns an immutable vector of n+1 elements, where the kth element is binom(n, k) * power(b, k).
    """
    if n == 0:
        result = numpy.ones((1,))
    else:
        prev = binom_row(n-1, b)
        result = numpy.append(prev, 0.0) + numpy.insert(b * prev, 0, 0.0)
    result.setflags(write=False)
    return result
