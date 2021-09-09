import hdroller.math
import numpy

class ConvolutionSeries():
    """
    A series of arrays where array i is computed by convolving array i-1 with array 1 along the last axis.
    All intermediate results are cached.
    """
    def __init__(self, a1):
        self._items = [numpy.ones_like(a1[..., 0:1]), a1]
        self._reverse_cumsums = []
        
    def __getitem__(self, index):
        while len(self._items) < index + 1:
            next = hdroller.math.convolve_along_last_axis(self._items[-1], self._items[1])
            self._items.append(next)
        return self._items[index]
    
    def reverse_cumsum(self, index):
        while len(self._reverse_cumsums) < index+1:
            item = self[len(self._reverse_cumsums)]
            next = hdroller.math.reverse_cumsum(item, axis=1)
            self._reverse_cumsums.append(next)
        return self._reverse_cumsums[index]
    