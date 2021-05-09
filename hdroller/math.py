import numpy
from scipy.special import comb, factorial

def multinom(n, ks):
    if len(ks) == 0:
        return 1
    else:
        return comb(n, ks[0]) * multinom(n-ks[0], ks[1:])

def reverse_cumsum(a, axis=None, *args, **kwargs):
    return numpy.flip(numpy.cumsum(numpy.flip(a, axis=axis), axis=axis, *args, **kwargs), axis=axis)

def convolve_along_axis(a, v, axis, *args, **kwargs):
    def f(s, *args, **kwargs):
        return numpy.convolve(s, v, *args, **kwargs)
    return numpy.apply_along_axis(f, axis, *args, **kwargs)
    
    