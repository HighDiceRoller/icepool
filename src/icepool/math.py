__docformat__ = 'google'

from functools import cache


@cache
def comb_row(n: int, b: int) -> tuple[int, ...]:
    """Returns a tuple of n+1 elements, where the kth element is equal to math.comb(n, k) * b ** k.

    The results are cached.
    """
    if n == 0:
        return (1,)
    else:
        prev = comb_row(n - 1, b)
        return (1,) + tuple(
            x + b * y for x, y in zip(prev[1:], prev[:-1])) + (b * prev[-1],)


def comb(n: int, k: int, b: int = 1) -> int:
    """As `math.comb()`, but using the cached `comb_row()`."""
    return comb_row(n, b)[k]
