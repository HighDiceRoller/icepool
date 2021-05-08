import numpy
from scipy.special import comb, factorial

def multinom(n, ks):
    if len(ks) == 0:
        return 1
    else:
        return comb(n, ks[0]) * multinom(n-ks[0], ks[1:])

