import numpy
import math

MAX_INT_FLOAT = 2 ** 53

factorial = math.factorial

def comb(n, k, exact=True, repetition=False):
    """
    Same signature as scipy.comb with exact = True; only accepts integers.
    """
    if repetition:
        return math.comb(n + k - 1, k)
    else:
        return math.comb(n, k)

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

def should_normalize_weight_product(weight_arrays):
    total_prod = 1.0
    for weights in weight_arrays:
        total_prod *= numpy.cumsum(weights)[-1]
        if total_prod >= MAX_INT_FLOAT:
            return True
    return False
    