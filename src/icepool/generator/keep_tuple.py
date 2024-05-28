__docformat__ = 'google'

from types import EllipsisType
from typing import Sequence, cast


def make_keep_tuple(
        pool_size: int,
        index: int | slice | Sequence[int | EllipsisType]) -> tuple[int, ...]:
    """Expresses `index` as a keep_tuple.

    See `Pool.set_keep_tuple()` for details.

    Args:
        `pool_size`: An `int` specifying the size of the pool.
        `keep_tuple`: Raw specification for how the dice are to be counted.
    Raises:
        IndexError: If:
            * More than one `Ellipsis` is used.
            * An `Ellipsis` is used in the center with too few `pool_size`.
    """
    if isinstance(index, int):
        result = [0] * pool_size
        result[index] = 1
        return tuple(result)
    elif isinstance(index, slice):
        if index.step is not None:
            raise IndexError('step is not supported for pool subscripting')
        result = [0] * pool_size
        result[index] = [1] * len(result[index])
        return tuple(result)
    else:
        split = None
        for i, x in enumerate(index):
            if x is Ellipsis:
                if split is None:
                    split = i
                else:
                    raise IndexError(
                        'Cannot use more than one Ellipsis (...) for keep_tuple.'
                    )

        # The following code is designed to replace Ellipsis with actual zeros.
        index = cast('Sequence[int]', index)

        if split is None:
            if len(index) != pool_size:
                raise IndexError(
                    f'Length of {index} does not match pool size of {pool_size}'
                )
            return tuple(index)

        extra_dice = pool_size - len(index) + 1

        if split == 0:
            # Ellipsis on left.
            index = index[1:]
            if extra_dice < 0:
                return tuple(index[-extra_dice:])
            else:
                return (0, ) * extra_dice + tuple(index)
        elif split == len(index) - 1:
            # Ellipsis on right.
            index = index[:-1]
            if extra_dice < 0:
                return tuple(index[:extra_dice])
            else:
                return tuple(index) + (0, ) * extra_dice
        else:
            # Ellipsis in center.
            if extra_dice < 0:
                result = [0] * pool_size
                for i in range(min(split, pool_size)):
                    result[i] += index[i]
                reverse_split = split - len(index)
                for i in range(-1, max(reverse_split - 1, -pool_size - 1), -1):
                    result[i] += index[i]
                return tuple(result)
            else:
                return tuple(index[:split]) + (0, ) * extra_dice + tuple(
                    index[split + 1:])


def pop_min_from_keep_tuple(keep_tuple: tuple[int, ...], count: int):
    """Pops elements off the front of the keep tuple, returning the remaining tuple and the sum of the elements."""
    return keep_tuple[count:], sum(keep_tuple[:count])


def pop_max_from_keep_tuple(keep_tuple: tuple[int, ...], count: int):
    """Pops elements off the back of the keep tuple, returning the remaining tuple and the sum of the elements."""
    if count == 0:
        return keep_tuple, 0
    else:
        return keep_tuple[:-count], sum(keep_tuple[-count:])


def compose_keep_tuples(base: tuple[int, ...], apply: tuple[int, ...]):
    """Applies a keep tuple on top of a base keep tuple."""
    result: list[int] = []
    for x in base:
        result.append(sum(apply[:x]))
        apply = apply[x:]
    return tuple(result)
