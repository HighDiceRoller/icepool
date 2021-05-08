import numpy
from scipy.misc import factorial
from scipy.special import comb

class MultichooseArray():
    def __init__(self, n, k):
        self._n = n
        self._k = k
        self._data = numpy.zeros(comb(n, k, exact=True, repetition=True))

    def n(self):
        return self._n
    
    def k(self):
        return self._k

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        yield from self._data

    def masses(self):
        yield from self._data
        
    @staticmethod
    def _partial_index_by_diffs(diffs, n, k):
        if k == 1:
            return diffs[0]
        else:
            offset = 0
            for i in range(diffs[0]):
                offset += comb(n-i, k-1, exact=True, repetition=True)
            return offset + MultichooseArray._partial_index_by_diffs(diffs[1:], n-diffs[0], k-1)

    def index_by_diffs(self, diffs):
        return MultichooseArray._partial_index_by_diffs(diffs, self._n, self._k)

    def index_by_sorted_cumsums(self, scs):
        diffs = numpy.diff(scs, prepend=0)
        return self.index_by_diffs(diffs)

    @staticmethod
    def _partial_diffs(n, k):
        if k == 1:
            for size in range(n):
                yield (size,)
        else:
            for size in range(n):
                for tail in MultichooseArray._partial_diffs(n-size, k-1):
                    yield (size,) + tail

    def diffs(self):
        yield from MultichooseArray._partial_diffs(self._n, self._k)

    @staticmethod
    def _partial_sorted_cumsums(n, k, head):
        if k == 1:
            for x in range(head, n):
                yield (x,)
        else:
            for x in range(head, n):
                for tail in MultichooseArray._partial_sorted_cumsums(n, k-1, x):
                    yield (x,) + tail
    
    def cumsums(self):
        yield from MultichooseArray._partial_sorted_cumsum(self._n, self._k, 0)
    
    def multinomial_divisor(self, cumsum):
        _, counts = numpy.unique(cumsum, return_counts=True)
        return numpy.prod(factorial(counts))

    def __getitem__(self, cumsum):
        index = self.index_by_sorted_cumsums(sorted(cumsum))
        return self._data[index]

    def __setitem__(self, cumsum, mass):
        index = self.index_by_sorted_cumsums(sorted(cumsum))
        self._data[index] = mass
