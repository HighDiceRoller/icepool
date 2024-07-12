__docformat__ = 'google'

import icepool
from icepool.generator.multiset_generator import InitialMultisetGenerator, NextMultisetGenerator, MultisetGenerator

import operator
from collections import defaultdict
from functools import cached_property, reduce

from abc import ABC, abstractmethod
from types import EllipsisType
from typing import Hashable, Literal, Mapping, MutableMapping, Sequence, cast, overload, TYPE_CHECKING
from icepool.typing import ImplicitConversionError, Outcome, T

if TYPE_CHECKING:
    from icepool.expression import MultisetExpression


class KeepGenerator(MultisetGenerator[T, tuple[int]]):
    """`MultisetGenerator`s that support a `keep_tuple`.

    These generators have the following properties:
    * Always outputs the same number of elements.
        This number can be queried using `keep_size()`.
    * Closed under `keep`-like operations
        (`keep`, `[]`, `lowest`, `highest`, `middle`).
        Note that these operations can only be applied if the current
        `keep_tuple` has only non-negative elements.
    * Also closed under `+` (if `keep_tuple` has only non-negative elements),
        `*`, unary `-`.
    * `keep`-like operations can be performed regardless of multiset evaluation
        order.
    """
    _keep_tuple: tuple[int, ...]

    @abstractmethod
    def _set_keep_tuple(self, keep_tuple: tuple[int,
                                                ...]) -> 'KeepGenerator[T]':
        """Produces a copy with a modified keep_tuple."""

    @cached_property
    def _keep_size(self) -> int:
        return sum(self._keep_tuple)

    def keep_size(self) -> int:
        """The total count produced by this generator."""
        return self._keep_size

    def keep_tuple(self) -> tuple[int, ...]:
        """The tuple indicating which elements will be counted."""
        return self._keep_tuple

    def has_negative_keeps(self) -> bool:
        """Whether any element of the keep tuple is negative."""
        return any(x < 0 for x in self._keep_tuple)

    @property
    def _can_keep(self) -> bool:
        return True

    @overload
    def keep(
            self,
            index: slice | Sequence[int | EllipsisType]) -> 'KeepGenerator[T]':
        ...

    @overload
    def keep(self, index: int) -> 'icepool.Die[T]':
        ...

    def keep(
        self, index: slice | Sequence[int | EllipsisType] | int
    ) -> 'KeepGenerator[T] | icepool.Die[T]':
        """Modifies the generator by counting elements in sorted order.

        Use `g[index]` for the same effect as this method.

        The rolls are sorted in ascending order for this purpose,
        regardless of which order the outcomes are evaluated in.

        For example, here are some ways of selecting the two highest rolls out
        of five:

        * `g[3:5]`
        * `g[3:]`
        * `g[-2:]`
        * `g[..., 1, 1]`
        * `g[0, 0, 0, 1, 1]`

        These will count the highest as a positive and the lowest as a negative:

        * `g[-1, 0, 0, 0, 1]`
        * `g[-1, ..., 1]`

        The valid types of argument are:

        * An `int`. This will count only the roll at the specified index.
            In this case, the result is a `Die` rather than a generator.
        * A `slice`. The selected dice are counted once each.
        * A sequence of one `int` for each `Die`.
            Each roll is counted that many times, which could be multiple or
            negative times.

            Up to one `...` (`Ellipsis`) may be used.
            `...` will be replaced with a number of zero
            counts depending on the `keep_size`.
            This number may be "negative" if more `int`s are provided than
            the `keep_size` of the generator. Specifically:

            * If `index` is shorter than `size`, `...`
                acts as enough zero counts to make up the difference.
                E.g. `g[1, ..., 1]` on five dice would act as
                `g[1, 0, 0, 0, 1]`.
            * If `index` has length equal to `size`, `...` has no effect.
                E.g. `g[1, ..., 1]` on two dice would act as `g[1, 1]`.
            * If `index` is longer than `size` and `...` is on one side,
                elements will be dropped from `index` on the side with `...`.
                E.g. `g[..., 1, 2, 3]` on two dice would act as `g[2, 3]`.
            * If `index` is longer than `size` and `...`
                is in the middle, the counts will be as the sum of two
                one-sided `...`.
                E.g. `g[-1, ..., 1]` acts like `[-1, ...]` plus `[..., 1]`.
                On a `g` consisting of a single `Die` this would have
                the -1 and 1 cancel each other out.

        If this is called more than once, the selection is applied relative
        to the previous `keep_tuple`. For example, applying `[:2][-1]` would
        produce the second-lowest roll.

        Raises:
            IndexError: If:
                * More than one `...` is used.
                * The current `keep_tuple` has negative counts.
                * The `index` specifies a fixed length that is
                    different than the total of the counts in the current
                    `keep_tuple`.
        """
        convert_to_die = isinstance(index, int)

        if any(x < 0 for x in self.keep_tuple()):
            raise IndexError(
                'A KeepGenerator with negative counts cannot be further indexed.'
            )

        relative_keep_tuple = make_keep_tuple(self.keep_size(), index)

        keep_tuple = compose_keep_tuples(self.keep_tuple(),
                                         relative_keep_tuple)

        result = self._set_keep_tuple(keep_tuple)

        if convert_to_die:
            return cast(icepool.Die[T],
                        icepool.evaluator.KeepEvaluator().evaluate(result))
        else:
            return result

    @overload
    def __getitem__(
            self,
            index: slice | Sequence[int | EllipsisType]) -> 'KeepGenerator[T]':
        ...

    @overload
    def __getitem__(self, index: int) -> 'icepool.Die[T]':
        ...

    def __getitem__(
        self, index: slice | Sequence[int | EllipsisType] | int
    ) -> 'KeepGenerator[T] | icepool.Die[T]':
        return self.keep(index)

    def middle(self,
               keep: int = 1,
               *,
               tie: Literal['error', 'high',
                            'low'] = 'error') -> 'KeepGenerator[T]':
        """Keep some of the middle elements from this multiset and drop the rest.

        In contrast to the die and free function versions, this does not
        automatically sum the dice. Use `.sum()` afterwards if you want to sum.
        Alternatively, you can perform some other evaluation.

        Args:
            keep: The number of elements to keep. If this is greater than the
                current keep_size, all are kept.
            tie: What to do if `keep` is odd but the current keep_size
                is even, or vice versa.
                * 'error' (default): Raises `IndexError`.
                * 'low': The lower of the two possible elements is taken.
                * 'high': The higher of the two possible elements is taken.
        """
        if keep < 0:
            raise ValueError(f'keep={keep} cannot be negative.')

        if keep % 2 == self.keep_size() % 2:
            # The "good" case.
            start = (self.keep_size() - keep) // 2
        else:
            # Need to consult the tiebreaker.
            match tie:
                case 'error':
                    raise IndexError(
                        f'The middle {keep} of {self.keep_size()} elements is ambiguous.\n'
                        "Specify tie='low' or tie='high' to determine what to pick."
                    )
                case 'high':
                    start = (self.keep_size() + 1 - keep) // 2
                case 'low':
                    start = (self.keep_size() - 1 - keep) // 2
                case _:
                    raise ValueError(
                        f"Invalid value for tie {tie}. Expected 'error', 'low', or 'high'."
                    )
        stop = start + keep
        return self[start:stop]

    def __add__(
        self, other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'MultisetExpression[T]':
        try:
            return self.additive_union(other)
        except ImplicitConversionError:
            return NotImplemented

    def __radd__(
        self, other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'MultisetExpression[T]':
        try:
            return self.additive_union(other)
        except ImplicitConversionError:
            return NotImplemented

    def additive_union(
        *args: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'MultisetExpression[T]':
        args = tuple(
            icepool.expression.implicit_convert_to_expression(arg)
            for arg in args)
        if all(isinstance(arg, KeepGenerator) for arg in args):
            generators = cast(tuple[KeepGenerator, ...], args)
            if not any(generator.has_negative_keeps()
                       for generator in generators):
                keep_tuple = (1, ) * sum(generator.keep_size()
                                         for generator in generators)
                return icepool.CompoundKeepGenerator(generators, keep_tuple)
        return icepool.MultisetExpression.additive_union(*args)

    def __mul__(self, other: int) -> 'KeepGenerator[T]':
        if not isinstance(other, int):
            return NotImplemented
        return self.multiply_counts(other)

    def multiply_counts(self, constant: int, /) -> 'KeepGenerator[T]':
        return self._set_keep_tuple(
            tuple(n * constant for n in self._keep_tuple))

    # Commutable in this case.
    def __rmul__(self, other: int) -> 'KeepGenerator[T]':
        if not isinstance(other, int):
            return NotImplemented
        return self.multiply_counts(other)

    def __neg__(self) -> 'KeepGenerator[T]':
        return -1 * self


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
