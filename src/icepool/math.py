__docformat__ = 'google'

from collections.abc import MutableMapping

# b -> list of rows
comb_row_cache: MutableMapping[int, list[tuple[int, ...]]] = {}


def comb_row(n: int, b: int) -> tuple[int, ...]:
    """Returns a tuple of n+1 elements, where the kth element is equal to math.comb(n, k) * b ** k.

    The results are cached.
    """
    if b not in comb_row_cache:
        comb_row_cache[b] = [(1,)]
    rows = comb_row_cache[b]
    while len(rows) < n + 1:
        prev = rows[-1]
        next = (1,) + tuple(
            x + b * y for x, y in zip(prev[1:], prev[:-1])) + (b * prev[-1],)
        rows.append(next)
    return rows[n]


def comb(n: int, k: int, b: int = 1) -> int:
    """As `math.comb()`, but using the cached `comb_row()`."""
    return comb_row(n, b)[k]
