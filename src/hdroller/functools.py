import functools

def die_cache(func):
    """ Workaround for `BaseDie.__eq__()` not being usable for hashing.
    
    Uses the `BaseDie`'s alternative hash key to create something hashable.
    """
    cache = {}
    @functools.wraps(func)
    def wrapped(die, *args, **kwargs):
        key = (die.key_tuple(),) + args + tuple(kwargs.items())
        if key in cache:
            return cache[key]
        else:
            result = func(die, *args, **kwargs)
            cache[key] = result
            return result
    
    return wrapped
