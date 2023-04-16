__docformat__ = 'google'

import math
import operator
from typing import Callable, Hashable, Iterable, Sequence, overload

from icepool.typing import U, T_co

class Vector(Hashable, Sequence[T_co]):
    """Immutable tuple-like class that applies most operators elementwise.

    May become a variadic generic type in the future.
    """
    _data: tuple[T_co, ...]

    def __init__(self, elements: Iterable[T_co]) -> None:
        self._data = tuple(elements)

    def __hash__(self) -> int:
        return hash((Vector, self._data))

    def __len__(self) -> int:
        return len(self._data)

    @overload
    def __getitem__(self, index: int) -> T_co: ...

    @overload
    def __getitem__(self, index: slice) -> 'Vector[T_co]': ...

    def __getitem__(self, index: int | slice) -> 'T_co | Vector[T_co]':
        if isinstance(index, int):
            return self._data[index]
        else:
            return Vector(self._data[index])

    # Unary operators.

    def unary_operator(self, op: Callable[..., U], *args, **kwargs)-> 'Vector[U]':
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

    def binary_operator(self, other, op: Callable[..., U], *args,
                        **kwargs) -> 'Vector[U]':
        """Binary operators on `Vector` are applied elementwise.

        If the other operand is also a `Vector`, the operator is applied to each
        pair of elements from `self` and `other`. Both must have the same
        length.

        Otherwise the other operand is broadcast to each element of `self`.

        This is used for the standard binary operators
        `+, -, *, /, //, %, **, <<, >>, &, |, ^`.

        `@` is not included due to its different meaning in `Die`.

        Comparators use a lexicographic ordering instead.
        This may change in the future.
        """
        if isinstance(other, Vector):
            if len(self) == len(other):
                return Vector(op(x, y, *args, **kwargs) for x, y in zip(self, other))
            else:
                raise IndexError('Binary operators on Vectors are only valid if both are the same length.')
        else:
            return Vector(op(x, other, *args, **kwargs) for x in self)

    def reverse_binary_operator(self, other, op: Callable[..., U], *args,
                        **kwargs) -> 'Vector[U]':
        """Binary operators on `Vector` are applied elementwise.

        If the other operand is also a `Vector`, the operator is applied to each
        pair of elements from `self` and `other`. Both must have the same
        length.

        Otherwise the other operand is broadcast to each element of `self`.

        This is used for the standard binary operators
        `+, -, *, /, //, %, **, <<, >>, &, |, ^`.

        `@` is not included due to its different meaning in `Die`.

        Comparators use a lexicographic ordering.
        This may change in the future.
        """
        if isinstance(other, Vector):
            if len(self) == len(other):
                return Vector(op(y, x, *args, **kwargs) for x, y in zip(self, other))
            else:
                raise IndexError('Binary operators on Vectors are only valid if both are the same length.')
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

    def __lt__(self, other) -> bool:
        if not isinstance(other, Vector):
            return NotImplemented
        return self._data < other._data

    def __le__(self, other) -> bool:
        if not isinstance(other, Vector):
            return NotImplemented
        return self._data <= other._data

    def __gt__(self, other) -> bool:
        if not isinstance(other, Vector):
            return NotImplemented
        return self._data > other._data

    def __ge__(self, other) -> bool:
        if not isinstance(other, Vector):
            return NotImplemented
        return self._data >= other._data

    def __eq__(self, other) -> bool:
        if not isinstance(other, Vector):
            return False
        return self._data == other._data

    def __ne__(self, other) -> bool:
        if not isinstance(other, Vector):
            return True
        return self._data != other._data

    def __repr__(self) -> str:
        return type(self).__qualname__ + '(' + repr(self._data) + ')'

    def __str__(self) -> str:
        return '<' + ', '.join(str(x) for x in self._data) + '>'
