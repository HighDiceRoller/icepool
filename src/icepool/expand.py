__docformat__ = 'google'

import icepool

import itertools
import math
from typing import Any, Iterator, Protocol, Sequence, Type, overload

from icepool.typing import A_co, Outcome, S, T


# We don't use @runtime_checkable due to poor performance and the validation is
# limited anyways.
class Expandable(Protocol[A_co]):
    """Objects that can be expanded in Cartesian products."""

    @property
    def _items_for_cartesian_product(self) -> Sequence[tuple[A_co, int]]:
        """Returns a sequence of (outcome, quantity) pairs."""
        ...


def iter_cartesian_product(
    *args: 'Outcome | icepool.Population | icepool.MultisetExpression'
) -> Iterator[tuple[tuple, int]]:
    """Yields the independent joint distribution of the arguments.

    Args:
        *args: These may be dice, which will be expanded into their joint
            outcomes. Non-dice are left as-is.

    Yields:
        Tuples containing one outcome per arg and the joint quantity.
    """
    if len(args) == 0:
        yield (), 1
        return

    def arg_items(arg) -> Sequence[tuple[Any, int]]:
        items = getattr(arg, '_items_for_cartesian_product', None)
        if items is not None:
            return items
        else:
            return [(arg, 1)]

    for t in itertools.product(*(arg_items(arg) for arg in args)):
        outcomes, quantities = zip(*t)
        final_quantity = math.prod(quantities)
        yield outcomes, final_quantity


# Typing: there is currently no way to intersect a type bound, and Protocol
# can't be used with Sequence.
def cartesian_product(
    *args: 'Outcome | icepool.Population | icepool.RerollType',
    outcome_type: Type[S]
) -> 'S | icepool.Population[S] | icepool.RerollType':  #type: ignore
    """Computes the Cartesian product of the arguments as a sequence, or a `Population` thereof.

    If `Population`s are provided, they must all be `Die` or all `Deck` and not
    a mixture of the two.

    If any argument is `icepool.Reroll`, the result is `icepool.Reroll`.

    Returns:
        If none of the outcomes is a `Population`, the result is a sequence
        with one element per argument. Otherwise, the result is a `Population`
        of the same type as the input `Population`, and the outcomes are
        sequences with one element per argument.
    """
    population_type: Type | None = None
    for arg in args:
        if arg in icepool.REROLL_TYPES:
            return arg  # type: ignore
        new_type = getattr(arg, '_new_type', None)
        if new_type is not None and hasattr(arg,
                                            '_items_for_cartesian_product'):
            if population_type is None:
                population_type = new_type
            elif population_type != new_type:
                raise TypeError(
                    'Arguments to vector() of type Population must all be Die or all be Deck, not a mixture of the two.'
                )

    if population_type is None:
        return outcome_type(args)  # type: ignore
    else:
        data = {}
        for outcomes, final_quantity in iter_cartesian_product(
                *args):  # type: ignore
            data[outcome_type(outcomes)] = final_quantity  # type: ignore
        return population_type(data)


@overload
def tupleize(
    *args: 'T | icepool.Population[T]'
) -> 'tuple[T, ...] | icepool.Population[tuple[T, ...]]':
    ...


@overload
def tupleize(
    *args: 'T | icepool.Population[T] | icepool.RerollType'
) -> 'tuple[T, ...] | icepool.Population[tuple[T, ...]] | icepool.RerollType':
    ...


def tupleize(
    *args: 'T | icepool.Population[T] | icepool.RerollType'
) -> 'tuple[T, ...] | icepool.Population[tuple[T, ...]] | icepool.RerollType':
    """Returns the Cartesian product of the arguments as `tuple`s or a `Population` thereof.

    For example:
    * `tupleize(1, 2)` would produce `(1, 2)`.
    * `tupleize(d6, 0)` would produce a `Die` with outcomes `(1, 0)`, `(2, 0)`,
        ... `(6, 0)`.
    * `tupleize(d6, d6)` would produce a `Die` with outcomes `(1, 1)`, `(1, 2)`,
        ... `(6, 5)`, `(6, 6)`.

    If `Population`s are provided, they must all be `Die` or all `Deck` and not
    a mixture of the two.

    If any argument is `icepool.Reroll`, the result is `icepool.Reroll`.

    Returns:
        If none of the outcomes is a `Population`, the result is a `tuple`
        with one element per argument. Otherwise, the result is a `Population`
        of the same type as the input `Population`, and the outcomes are
        `tuple`s with one element per argument.
    """
    return cartesian_product(*args, outcome_type=tuple)


@overload
def vectorize(
    *args: 'T | icepool.Population[T]'
) -> 'icepool.Vector[T] | icepool.Population[icepool.Vector[T]]':
    ...


@overload
def vectorize(
    *args: 'T | icepool.Population[T] | icepool.RerollType'
) -> 'icepool.Vector[T] | icepool.Population[icepool.Vector[T]] | icepool.RerollType':
    ...


def vectorize(
    *args: 'T | icepool.Population[T] | icepool.RerollType'
) -> 'icepool.Vector[T] | icepool.Population[icepool.Vector[T]] | icepool.RerollType':
    """Returns the Cartesian product of the arguments as `Vector`s or a `Population` thereof.

    For example:
    * `vectorize(1, 2)` would produce `Vector(1, 2)`.
    * `vectorize(d6, 0)` would produce a `Die` with outcomes `Vector(1, 0)`,
        `Vector(2, 0)`, ... `Vector(6, 0)`.
    * `vectorize(d6, d6)` would produce a `Die` with outcomes `Vector(1, 1)`,
        `Vector(1, 2)`, ... `Vector(6, 5)`, `Vector(6, 6)`.

    If `Population`s are provided, they must all be `Die` or all `Deck` and not
    a mixture of the two.

    If any argument is `icepool.Reroll`, the result is `icepool.Reroll`.

    Returns:
        If none of the outcomes is a `Population`, the result is a `Vector`
        with one element per argument. Otherwise, the result is a `Population`
        of the same type as the input `Population`, and the outcomes are
        `Vector`s with one element per argument.
    """
    return cartesian_product(*args, outcome_type=icepool.Vector)
