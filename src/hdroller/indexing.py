"""numpy-like indexing."""

import itertools

def select_bools(n, select):
    """
    
    Args:
        n: The number of elements to return.
        select: An object to select elements. Options are:
            slice: Selects a slice.
            integer: Selects a single index.
            iterable: Each element is either an index to select,
                or a bool stating that the current iteration index is to be selected.
    
    Returns:
        A bool tuple of n elements which are True iff that element was selected.
    """
    result = [False] * n
    
    if isinstance(select, slice):
        for i in itertools.islice(range(n), slice.start, slice.stop, slice.step):
            result[i] = True
            return tuple(result)
    
    try:
        i = int(select)
        result[i] = True
        return tuple(result)
    except TypeError:
        pass
    
    for i, v in enumerate(select):
        if v is True:
            result[i] = True
        elif v is False:
            result[i] = False
        else:
            result[v] = True
    return tuple(result)