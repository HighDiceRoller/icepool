import numpy
from scipy.special import comb, factorial

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

def convolve_along_last_axis(a, v, mode='full'):
    conv_length = a.shape[-1] + v.shape[-1] - 1
    new_shape = a.shape[:-1] + (conv_length,)
    result = numpy.zeros(new_shape)
    for indexes in numpy.ndindex(a.shape[:-1]):
        result[indexes] = numpy.convolve(a[indexes], v[indexes], mode)
    return result
