import numpy
from scipy.special import comb, factorial

MAX_INT_FLOAT = 2 ** 53

def multinom(n, ks):
    """
    Multinomial coefficient.
    """
    if len(ks) == 0:
        return 1
    else:
        return comb(n, ks[0]) * multinom(n-ks[0], ks[1:])

def reverse_cumsum(a, axis=None, *args, **kwargs):
    """
    Applies a cumsum in reverse direction along the specified axis.
    Any additional arguments are sent to cumsum.
    """
    return numpy.flip(numpy.cumsum(numpy.flip(a, axis=axis), axis=axis, *args, **kwargs), axis=axis)

def convolve_along_last_axis(a, v):
    if a.shape[-1] < v.shape[-1]:
        a, v = v, a
    conv_count = numpy.prod(a.shape[:-1])
    conv_length = a.shape[-1] + v.shape[-1] - 1
    new_shape = a.shape[:-1] + (conv_length,)
    result = numpy.zeros(new_shape)
    
    # This seems to be almost always faster than convolving each slice.
    for i in range(v.shape[-1]):
        result[..., i:i+a.shape[-1]] += a * v[..., i:i+1]
    
    return result
    