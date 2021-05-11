import numpy

class PowerSeries():
    """
    A series of arrays where array i is equal to array 1 raised to the ith power element-wise.
    Results are cached.
    """
    def __init__(self, a1):
        self._items = [numpy.ones_like(a1), a1]
    
    def __getitem__(self, index):
        if len(self._items) < index+1:
            self._items += [None] * (index + 1 - len(self._items))
        if self._items[index] is None:
            self._items[index] = numpy.power(self._items[1], index)
        return self._items[index]
    