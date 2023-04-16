__docformat__ = 'google'

import icepool

import itertools
import math
import operator
from typing import Callable, Hashable, Iterable, Sequence, Type, cast, overload

from icepool.typing import Outcome, S, T, T_co, U


# Typing: there is currently no way to intersect a type bound, and Protocol
# can't be used with Sequence.
def cartesian_product(
        *args: 'Outcome | icepool.Population',
        outcome_type: Type[S]) -> 'S | icepool.Population[S]':  #type: ignore
    """Computes the Cartesian product of the arguments as a sequence, or a `Population` thereof.

    If `Population`s are provided, they must all be `Die` or all `Deck` and not
    a mixture of the two.

    Returns:
        If none of the outcomes is a `Population`, the result is a sequence
        with one element per argument. Otherwise, the result is a `Population`
        of the same type as the input `Population`, and the outcomes are
        sequences with one element per argument.
    """
    population_type = None
    for arg in args:
        if isinstance(arg, icepool.Population):
            if population_type is None:
                population_type = arg._new_type
            elif population_type != arg._new_type:
                raise TypeError(
                    'Arguments to vector() of type Population must all be Die or all be Deck, not a mixture of the two.'
                )

    if population_type is None:
        return outcome_type(args)  # type: ignore
    else:
        data = {}
        for outcomes, final_quantity in icepool.iter_cartesian_product(*args):
            data[outcome_type(outcomes)] = final_quantity  # type: ignore
        return population_type(data)


def tupleize(
    *args: 'T | icepool.Population[T]'
) -> 'tuple[T, ...] | icepool.Population[tuple[T, ...]]':
    """Returns the Cartesian product of the arguments as `tuple`s or a `Population` thereof.

    For example:
    * `tupleize(1, 2)` would produce `(1, 2)`.
    * `tupleize(d6, 0)` would produce a `Die` with outcomes `(1, 0)`, `(2, 0)`,
        ... `(6, 0)`.
    * `tupleize(d6, d6)` would produce a `Die` with outcomes `(1, 1)`, `(1, 2)`,
        ... `(6, 5)`, `(6, 6)`.

    If `Population`s are provided, they must all be `Die` or all `Deck` and not
    a mixture of the two.

    Returns:
        If none of the outcomes is a `Population`, the result is a `tuple`
        with one element per argument. Otherwise, the result is a `Population`
        of the same type as the input `Population`, and the outcomes are
        `tuple`s with one element per argument.
    """
    return cartesian_product(*args, outcome_type=tuple)


def vectorize(
    *args: 'T | icepool.Population[T]'
) -> 'Vector[T] | icepool.Population[Vector[T]]':
    """Returns the Cartesian product of the arguments as `Vector`s or a `Population` thereof.

    For example:
    * `vectorize(1, 2)` would produce `Vector(1, 2)`.
    * `vectorize(d6, 0)` would produce a `Die` with outcomes `Vector(1, 0)`,
        `Vector(2, 0)`, ... `Vector(6, 0)`.
    * `vectorize(d6, d6)` would produce a `Die` with outcomes `Vector(1, 1)`,
        `Vector(1, 2)`, ... `Vector(6, 5)`, `Vector(6, 6)`.

    If `Population`s are provided, they must all be `Die` or all `Deck` and not
    a mixture of the two.

    Returns:
        If none of the outcomes is a `Population`, the result is a `Vector`
        with one element per argument. Otherwise, the result is a `Population`
        of the same type as the input `Population`, and the outcomes are
        `Vector`s with one element per argument.
    """
    return cartesian_product(*args, outcome_type=Vector)


class Vector(Outcome, Sequence[T_co]):
    """Immutable tuple-like class that applies most operators elementwise.

    May become a variadic generic type in the future.
    """
    _data: tuple[T_co, ...]

    def __init__(self,
                 elements: Iterable[T_co],
                 *,
                 truth_value: bool | None = None) -> None:
        self._data = tuple(elements)
        if any(isinstance(x, icepool.AgainExpression) for x in self._data):
            raise TypeError('Again is not a valid element of Vector.')
        self._truth_value = truth_value

    def __hash__(self) -> int:
        return hash((Vector, self._data))

    def __len__(self) -> int:
        return len(self._data)

    @overload
    def __getitem__(self, index: int) -> T_co:
        ...

    @overload
    def __getitem__(self, index: slice) -> 'Vector[T_co]':
        ...

    def __getitem__(self, index: int | slice) -> 'T_co | Vector[T_co]':
        if isinstance(index, int):
            return self._data[index]
        else:
            return Vector(self._data[index])

    # Unary operators.

    def unary_operator(self, op: Callable[..., U], *args,
                       **kwargs) -> 'Vector[U]':
        """Unary operators on `Vector` are applied elementwise.

        This is used for the standard unary operators
        `-, +, abs, ~, round, trunc, floor, ceil`
        """
        return Vector(op(x, *args, **kwargs) for x in self)

    def __neg__(self) -> 'Vector[T_co]':
        return self.unary_operator(operator.neg)

    def __pos__(self) -> 'Vector[T_co]':
        return self.unary_operator(operator.pos)

    def __invert__(self) -> 'Vector[T_co]':
        return self.unary_operator(operator.invert)

    def abs(self) -> 'Vector[T_co]':
        return self.unary_operator(operator.abs)

    __abs__ = abs

    def round(self, ndigits: int | None = None) -> 'Vector':
        return self.unary_operator(round, ndigits)

    __round__ = round

    def trunc(self) -> 'Vector':
        return self.unary_operator(math.trunc)

    __trunc__ = trunc

    def floor(self) -> 'Vector':
        return self.unary_operator(math.floor)

    __floor__ = floor

    def ceil(self) -> 'Vector':
        return self.unary_operator(math.ceil)

    __ceil__ = ceil

    # Binary operators.

    def binary_operator(self,
                        other,
                        op: Callable[..., U],
                        *args,
                        compare_for_truth: bool = False,
                        **kwargs) -> 'Vector[U]':
        """Binary operators on `Vector` are applied elementwise.

        If the other operand is also a `Vector`, the operator is applied to each
        pair of elements from `self` and `other`. Both must have the same
        length.

        Otherwise the other operand is broadcast to each element of `self`.

        This is used for the standard binary operators
        `+, -, *, /, //, %, **, <<, >>, &, |, ^`.

        `@` is not included due to its different meaning in `Die`.

        This is also used for the comparators
        `<, <=, >, >=, ==, !=`.

        In this case, the result also has a truth value based on lexicographic
        ordering.
        """
        if isinstance(other, (icepool.Population, icepool.AgainExpression)):
            return NotImplemented  # delegate to the other
        if isinstance(other, Vector):
            if len(self) == len(other):
                if compare_for_truth:
                    truth_value = cast(bool, op(self._data, other._data))
                else:
                    truth_value = None
                return Vector(
                    (op(x, y, *args, **kwargs) for x, y in zip(self, other)),
                    truth_value=truth_value)
            else:
                raise IndexError(
                    f'Binary operators on Vectors are only valid if both are the same length ({len(self)} vs. {len(other)}).'
                )
        else:
            return Vector((op(x, other, *args, **kwargs) for x in self))

    def reverse_binary_operator(self, other, op: Callable[..., U], *args,
                                **kwargs) -> 'Vector[U]':
        """Reverse version of `binary_operator()`."""
        if isinstance(other, (icepool.Population, icepool.AgainExpression)):
            return NotImplemented  # delegate to the other
        if isinstance(other, Vector):
            if len(self) == len(other):
                return Vector(
                    op(y, x, *args, **kwargs) for x, y in zip(self, other))
            else:
                raise IndexError(
                    f'Binary operators on Vectors are only valid if both are the same length ({len(self)} vs. {len(other)}).'
                )
        else:
            return Vector(op(other, x, *args, **kwargs) for x in self)

    def __add__(self, other) -> 'Vector':
        return self.binary_operator(other, operator.add)

    def __radd__(self, other) -> 'Vector':
        return self.reverse_binary_operator(other, operator.add)

    def __sub__(self, other) -> 'Vector':
        return self.binary_operator(other, operator.sub)

    def __rsub__(self, other) -> 'Vector':
        return self.reverse_binary_operator(other, operator.sub)

    def __mul__(self, other) -> 'Vector':
        return self.binary_operator(other, operator.mul)

    def __rmul__(self, other) -> 'Vector':
        return self.reverse_binary_operator(other, operator.mul)

    def __truediv__(self, other) -> 'Vector':
        return self.binary_operator(other, operator.truediv)

    def __rtruediv__(self, other) -> 'Vector':
        return self.reverse_binary_operator(other, operator.truediv)

    def __floordiv__(self, other) -> 'Vector':
        return self.binary_operator(other, operator.floordiv)

    def __rfloordiv__(self, other) -> 'Vector':
        return self.reverse_binary_operator(other, operator.floordiv)

    def __pow__(self, other) -> 'Vector':
        return self.binary_operator(other, operator.pow)

    def __rpow__(self, other) -> 'Vector':
        return self.reverse_binary_operator(other, operator.pow)

    def __mod__(self, other) -> 'Vector':
        return self.binary_operator(other, operator.mod)

    def __rmod__(self, other) -> 'Vector':
        return self.reverse_binary_operator(other, operator.mod)

    def __lshift__(self, other) -> 'Vector':
        return self.binary_operator(other, operator.lshift)

    def __rlshift__(self, other) -> 'Vector':
        return self.reverse_binary_operator(other, operator.lshift)

    def __rshift__(self, other) -> 'Vector':
        return self.binary_operator(other, operator.rshift)

    def __rrshift__(self, other) -> 'Vector':
        return self.reverse_binary_operator(other, operator.rshift)

    def __and__(self, other) -> 'Vector':
        return self.binary_operator(other, operator.and_)

    def __rand__(self, other) -> 'Vector':
        return self.reverse_binary_operator(other, operator.and_)

    def __or__(self, other) -> 'Vector':
        return self.binary_operator(other, operator.or_)

    def __ror__(self, other) -> 'Vector':
        return self.reverse_binary_operator(other, operator.or_)

    def __xor__(self, other) -> 'Vector':
        return self.binary_operator(other, operator.xor)

    def __rxor__(self, other) -> 'Vector':
        return self.reverse_binary_operator(other, operator.xor)

    # Comparators.
    # These returns a value with a truth value, but not a bool.

    def __lt__(self, other) -> 'Vector':  # type: ignore
        if not isinstance(other, Vector):
            return NotImplemented
        return self.binary_operator(other, operator.lt, compare_for_truth=True)

    def __le__(self, other) -> 'Vector':  # type: ignore
        if not isinstance(other, Vector):
            return NotImplemented
        return self.binary_operator(other, operator.le, compare_for_truth=True)

    def __gt__(self, other) -> 'Vector':  # type: ignore
        if not isinstance(other, Vector):
            return NotImplemented
        return self.binary_operator(other, operator.gt, compare_for_truth=True)

    def __ge__(self, other) -> 'Vector':  # type: ignore
        if not isinstance(other, Vector):
            return NotImplemented
        return self.binary_operator(other, operator.ge, compare_for_truth=True)

    def __eq__(self, other) -> 'Vector | bool':  # type: ignore
        if not isinstance(other, Vector):
            return False
        return self.binary_operator(other, operator.eq, compare_for_truth=True)

    def __ne__(self, other) -> 'Vector | bool':  # type: ignore
        if not isinstance(other, Vector):
            return True
        return self.binary_operator(other, operator.ne, compare_for_truth=True)

    def __bool__(self) -> bool:
        if self._truth_value is None:
            raise TypeError(
                'Vector only has a truth value if it is the result of a comparison operator.'
            )
        return self._truth_value

    # Sequence manipulation.

    def append(self, other) -> 'Vector':
        return Vector(self._data + (other,))

    def concatenate(self, other: 'Iterable') -> 'Vector':
        return Vector(itertools.chain(self, other))

    # Strings.

    def __repr__(self) -> str:
        return type(self).__qualname__ + '(' + repr(self._data) + ')'

    def __str__(self) -> str:
        return type(self).__qualname__ + '(' + str(self._data) + ')'
