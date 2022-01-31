__docformat__ = 'google'

"""numpy-like indexing."""

def slice_range(n, select):
    if select.start is None:
        start = 0
    elif select.start < 0:
        start = n + select.start
    else:
        start = select.start
    
    if select.stop is None:
        stop = n
    elif select.stop < 0:
        stop = n + select.stop
    else:
        stop = select.stop
    
    if select.step is None:
        step = 1
    else:
        step = select.step
    
    return range(start, stop, step)

def select_from(a, select):
    """
    
    Args:
        n: The number of elements to return.
        select: An object to select elements. Options are:
            slice: Selects a slice.
            integer: Selects a single index.
            iterable: Each element is either an index to select,
                or a bool stating that the current iteration index is to be selected.
    
    Returns:
        The single selected element if the input was an integer.
        Otherwise, a tuple of selected elements.
    """
    if isinstance(select, slice):
        result = []
        for i in slice_range(len(a), select):
            result.append(a[i])
        return tuple(result)

    try:
        i = int(select)
        return a[i]
    except TypeError:
        pass
    
    is_bool = False
    for i, v in enumerate(select):
        if v is True:
            is_bool = True
            result.append(a[i])
        elif v is False:
            is_bool = True
        else:
            if is_bool:
                raise TypeError('Selection cannot mix bools and ints.')
            result.append(a[v])
    if is_bool and len(select) != len(a):
        raise IndexError('bool selection must have the same length as the sequence being selected from.')
    return tuple(result)
    
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
        for i in slice_range(n, select):
            result[i] = True
        return tuple(result)
    
    try:
        i = int(select)
        result[i] = True
        return tuple(result)
    except TypeError:
        pass
    
    is_bool = False
    for i, v in enumerate(select):
        if v is True:
            is_bool = True
            result[i] = True
        elif v is False:
            is_bool = True
        else:
            if is_bool:
                raise TypeError('Selection cannot mix bools and ints.')
            result[v] = True
    if is_bool and len(select) != n:
        raise IndexError('bool selection must have length n.')
    return tuple(result)
