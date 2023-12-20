__docformat__ = 'google'

from fractions import Fraction
import numbers
from typing import Iterator, MutableMapping

# b -> list of rows
comb_row_cache: MutableMapping[int, list[tuple[int, ...]]] = {}


def comb_row(n: int, b: int) -> tuple[int, ...]:
    """A tuple of n+1 elements, where the kth element is equal to math.comb(n, k) * b ** k.

    The results are cached.
    """
    if b not in comb_row_cache:
        comb_row_cache[b] = [(1, )]
    rows = comb_row_cache[b]
    while len(rows) < n + 1:
        prev = rows[-1]
        next = (1, ) + tuple(
            x + b * y for x, y in zip(prev[1:], prev[:-1])) + (b * prev[-1], )
        rows.append(next)
    return rows[n]


def comb(n: int, k: int, b: int = 1) -> int:
    """As `math.comb()`, but using the cached `comb_row()`."""
    return comb_row(n, b)[k]


def iter_hypergeom(deck: tuple[int, ...],
                   draws: int) -> Iterator[tuple[tuple[int, ...], int]]:
    """Iterates over the (hand, weight)s in the given `Deck`.

    Args:
        deck: The number of duplicates of each card in the `Deck`.
        draws: The total number of cards to draw.

    Yields:
        hand: A tuple of how many of each card were drawn.
        weight: The weight of drawing that hand.
    """
    if len(deck) == 0:
        yield (), 1
        return

    deck_count = deck[0]
    deck_size = sum(deck)  # assume deck is small?

    min_count = max(0, deck_count + draws - deck_size)
    max_count = min(deck_count, draws)

    for count in range(min_count, max_count + 1):
        weight = comb(draws, count)
        for tail_count, tail_weight in iter_hypergeom(deck[1:], draws - count):
            yield (count, ) + tail_count, weight * tail_weight


def try_fraction(numerator, denominator) -> Fraction | float:
    """Attempts to form a `Fraction` from the arguments.
    
    If the arguments are not rational, returns a `float` instead.
    """
    try:
        return Fraction(numerator, denominator)
    except TypeError:
        return numerator / denominator
