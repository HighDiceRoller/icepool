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


def hypergeom(deck_size: int, hand_size: int, deck_matches: int,
              hand_matches: int) -> int:
    """The numerator of a hypergeometric distribution.

    Used for sampling without replacement.

    The denominator is `comb(deck_size, hand_size)`.
    """
    return comb(deck_matches, hand_matches) * comb(deck_size - deck_matches,
                                                   hand_size - hand_matches)
