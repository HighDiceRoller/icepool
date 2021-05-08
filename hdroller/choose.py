import numpy
from scipy.special import comb, factorial

def _partial_iter_multichoose_sorted_outcomes(n, k, head):
    if k == 1:
        for x in range(head, n):
            yield (x,)
    else:
        for x in range(head, n):
            for tail in _partial_iter_multichoose_sorted_outcomes(n, k-1, x):
                yield (x,) + tail

def iter_multichoose_sorted_outcomes(n, k):
    yield from _partial_iter_multichoose_sorted_outcomes(n, k, 0)

def multinom(n, ks):
    if len(ks) == 0:
        return 1
    else:
        return comb(n, ks[0]) * multinom(n-ks[0], ks[1:])

def multinom_outcomes(n, outcomes):
    _, counts = numpy.unique(outcomes, return_counts=True)
    return multinom(n, counts)
