try:
    from functools import cache
except ImportError:
    import functools
    cache = functools.lru_cache(maxsize=None)

from functools import cached_property