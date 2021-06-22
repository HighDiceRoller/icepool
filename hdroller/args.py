
"""
Functions for handling arguments.
"""

def flatten_first_arg(args):
    if len(args) == 1 and hasattr(args[0], '__iter__'):
        return args[0]
    return args

def process_keep_args(n, **kwargs):
    """
    Processes keep_highest, keep_lowest, etc. keyword arguments.
    Result is two integers between 0 and n indicating the slice to be kept.
    """
    start = None
    stop = None
    for k, v in kwargs.items():
        if k in ['keep_highest', 'kh']:
            if start is None: start = n - v
            else: raise ValueError('Keep specification has more than one start value.')
        elif k in ['keep_lowest', 'kl']:
            if stop is None: stop = v
            else: raise ValueError('Keep specification has more than one stop value.')
        elif k in ['drop_highest', 'dh']:
            if stop is None: stop = n - v
            else: raise ValueError('Keep specification has more than one stop value.')
        elif k in ['drop_lowest', 'dl']:
            if start is None: start = v
            else: raise ValueError('Keep specification has more than one start value.')
        elif k in ['keep_middle', 'km']:
            if not(start is None and stop is None):
                raise ValueError(k + ' is not compatible with other keep specifications.')
            if n % 2 != v % 2:
                raise ValueError(k + ' must have the same parity as n.')
            v = (n - v) // 2
            start = v
            stop = n - v
        elif k in ['drop_outer', 'do']:
            if not(start is None and stop is None):
                raise ValueError(k + ' is not compatible with other keep specifications.')
            start = v
            stop = n - v
        elif k in ['keep_index', 'ki']:
            if not(start is None and stop is None):
                raise ValueError(k + ' is not compatible with other keep specifications.')
            if v < 0:
                v = n + v
            start = v
            stop = v + 1
        else:
            pass  # allow other arguments to pass through
    if start is None: start = 0
    if stop is None: stop = n
    return start, stop
