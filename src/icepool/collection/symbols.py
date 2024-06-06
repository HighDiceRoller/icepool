__docformat__ = 'google'

import icepool

import functools
import itertools
import operator
import re

from collections import Counter, defaultdict
from functools import cached_property
from typing import Iterable, Iterator, Mapping, MutableMapping, overload


class Symbols(Mapping[str, int]):
    """EXPERIMENTAL: Immutable multiset of single characters.

    Spaces, dashes, and underscores cannot be used as symbols.

    Operations include:

    | Operation                   | Count / notes                      |
    |:----------------------------|:-----------------------------------|
    | `additive_union`, `+`       | `l + r`                            |
    | `difference`, `-`           | `l - r`                            |
    | `intersection`, `&`         | `min(l, r)`                        |
    | `union`, `\\|`               | `max(l, r)`                        |
    | `symmetric_difference`, `^` | `abs(l - r)`                       |
    | `multiply_counts`, `*`      | `count * n`                        |
    | `divide_counts`, `//`       | `count // n`                       |
    | `issubset`, `<=`            | all counts l <= r                  |
    | `issuperset`, `>=`          | all counts l >= r                  |
    | `==`                        | all counts l == r                  |
    | `!=`                        | any count l != r                   |
    | unary `+`                   | drop all negative counts           |
    | unary `-`                   | reverses the sign of all counts    |

    `<` and `>` are lexicographic orderings rather than subset relations.
    Specifically, they compare the count of each character in alphabetical
    order. For example:
    * `'a' > ''` since one `'a'` is more than zero `'a'`s.
    * `'a' > 'bb'` since `'a'` is compared first.
    * `'-a' < 'bb'` since the left side has -1 `'a'`s.
    * `'a' < 'ab'` since the `'a'`s are equal but the right side has more `'b'`s.
    
    Binary operators other than `*` and `//` implicitly convert the other
    argument to `Symbols` using the constructor.

    Subscripting with a single character returns the count of that character
    as an `int`. E.g. `symbols['a']` -> number of `a`s as an `int`.
    You can also access it as an attribute, e.g.  `symbols.a`.

    Subscripting with multiple characters returns a `Symbols` with only those
    characters, dropping the rest.
    E.g. `symbols['ab']` -> number of `a`s and `b`s as a `Symbols`.
    Again you can also access it as an attribute, e.g. `symbols.ab`.
    This is useful for reducing the outcome space, which reduces computational
    cost for further operations. If you want to keep only a single character
    while keeping the type as `Symbols`, you can subscript with that character
    plus an unused character.

    Subscripting with duplicate characters currently has no further effect, but
    this may change in the future.

    `Population.marginals` forwards attribute access, so you can use e.g.
    `die.marginals.a` to get the marginal distribution of `a`s.

    Note that attribute access only works with valid identifiers,
    so e.g. emojis would need to use the subscript method.
    """
    _data: Mapping[str, int]

    def __new__(cls,
                symbols: str | Iterable[str] | Mapping[str, int]) -> 'Symbols':
        """Constructor.
        
        The argument can be a string, an iterable of characters, or a mapping of
        characters to counts.
        
        If the argument is a string, negative symbols can be specified using a
        minus sign optionally surrounded by whitespace. For example,
        `a - b` has one positive a and one negative b.
        """
        self = super(Symbols, cls).__new__(cls)
        if isinstance(symbols, str):
            data: MutableMapping[str, int] = defaultdict(int)
            positive, *negative = re.split(r'\s*-\s*', symbols)
            for s in positive:
                data[s] += 1
            if len(negative) > 1:
                raise ValueError('Multiple dashes not allowed.')
            if len(negative) == 1:
                for s in negative[0]:
                    data[s] -= 1
        elif isinstance(symbols, Mapping):
            data = defaultdict(int, symbols)
        else:
            data = defaultdict(int)
            for s in symbols:
                data[s] += 1

        for s in data:
            if len(s) != 1:
                raise ValueError(f'Symbol {s} is not a single character.')
            if re.match(r'[\s_-]', s):
                raise ValueError(
                    f'{s} (U+{ord(s):04X}) is not a legal symbol.')

        self._data = defaultdict(int,
                                 {k: data[k]
                                  for k in sorted(data.keys())})

        return self

    @classmethod
    def _new_raw(cls, data: defaultdict[str, int]) -> 'Symbols':
        self = super(Symbols, cls).__new__(cls)
        self._data = data
        return self

    # Mapping interface.

    def __getitem__(self, key: str) -> 'int | Symbols':  # type: ignore
        if len(key) == 1:
            return self._data[key]
        else:
            return Symbols._new_raw(
                defaultdict(int, {s: self._data[s]
                                  for s in key}))

    def __getattr__(self, key: str) -> 'int | Symbols':
        if key[0] == '_':
            raise AttributeError(key)
        return self[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    # Binary operators.

    def additive_union(self, *args:
                       Iterable[str] | Mapping[str, int]) -> 'Symbols':
        """The sum of counts of each symbol."""
        return functools.reduce(operator.add, args, initial=self)

    def __add__(self, other: Iterable[str] | Mapping[str, int]) -> 'Symbols':
        if isinstance(other, (icepool.Population, icepool.AgainExpression)):
            return NotImplemented  # delegate to the other
        data = defaultdict(int, self._data)
        for s, count in Symbols(other).items():
            data[s] += count
        return Symbols._new_raw(data)

    __radd__ = __add__

    def difference(self, *args:
                   Iterable[str] | Mapping[str, int]) -> 'Symbols':
        """The difference between the counts of each symbol."""
        return functools.reduce(operator.sub, args, initial=self)

    def __sub__(self, other: Iterable[str] | Mapping[str, int]) -> 'Symbols':
        if isinstance(other, (icepool.Population, icepool.AgainExpression)):
            return NotImplemented  # delegate to the other
        data = defaultdict(int, self._data)
        for s, count in Symbols(other).items():
            data[s] -= count
        return Symbols._new_raw(data)

    def __rsub__(self, other: Iterable[str] | Mapping[str, int]) -> 'Symbols':
        if isinstance(other, (icepool.Population, icepool.AgainExpression)):
            return NotImplemented  # delegate to the other
        data = defaultdict(int, Symbols(other)._data)
        for s, count in self.items():
            data[s] -= count
        return Symbols._new_raw(data)

    def intersection(self, *args:
                     Iterable[str] | Mapping[str, int]) -> 'Symbols':
        """The min count of each symbol."""
        return functools.reduce(operator.and_, args, initial=self)

    def __and__(self, other: Iterable[str] | Mapping[str, int]) -> 'Symbols':
        if isinstance(other, (icepool.Population, icepool.AgainExpression)):
            return NotImplemented  # delegate to the other
        data: defaultdict[str, int] = defaultdict(int)
        for s, count in Symbols(other).items():
            data[s] = min(self.get(s, 0), count)
        return Symbols._new_raw(data)

    __rand__ = __and__

    def union(self, *args: Iterable[str] | Mapping[str, int]) -> 'Symbols':
        """The max count of each symbol."""
        return functools.reduce(operator.or_, args, initial=self)

    def __or__(self, other: Iterable[str] | Mapping[str, int]) -> 'Symbols':
        if isinstance(other, (icepool.Population, icepool.AgainExpression)):
            return NotImplemented  # delegate to the other
        data = defaultdict(int, self._data)
        for s, count in Symbols(other).items():
            data[s] = max(data[s], count)
        return Symbols._new_raw(data)

    __ror__ = __or__

    def symmetric_difference(
            self, other: Iterable[str] | Mapping[str, int]) -> 'Symbols':
        """The absolute difference in symbol counts between the two sets."""
        return self ^ other

    def __xor__(self, other: Iterable[str] | Mapping[str, int]) -> 'Symbols':
        if isinstance(other, (icepool.Population, icepool.AgainExpression)):
            return NotImplemented  # delegate to the other
        data = defaultdict(int, self._data)
        for s, count in Symbols(other).items():
            data[s] = abs(data[s] - count)
        return Symbols._new_raw(data)

    __rxor__ = __xor__

    def multiply_counts(self, other: int) -> 'Symbols':
        """Multiplies all counts by an integer."""
        return self * other

    def __mul__(self, other: int) -> 'Symbols':
        if not isinstance(other, int):
            return NotImplemented
        data = defaultdict(int, {
            s: count * other
            for s, count in self.items()
        })
        return Symbols._new_raw(data)

    __rmul__ = __mul__

    def divide_counts(self, other: int) -> 'Symbols':
        """Divides all counts by an integer, rounding down."""
        data = defaultdict(int, {
            s: count // other
            for s, count in self.items()
        })
        return Symbols._new_raw(data)

    def count_subset(self,
                     divisor: Iterable[str] | Mapping[str, int],
                     *,
                     empty_divisor: int | None = None) -> int:
        """The number of times the divisor is contained in this multiset."""
        if not isinstance(divisor, Mapping):
            divisor = Counter(divisor)
        result = None
        for s, count in divisor.items():
            current = self._data[s] // count
            if result is None or current < result:
                result = current
        if result is None:
            if empty_divisor is None:
                raise ZeroDivisionError('Divisor is empty.')
            else:
                return empty_divisor
        else:
            return result

    @overload
    def __floordiv__(self, other: int) -> 'Symbols':
        """Same as divide_counts()."""

    @overload
    def __floordiv__(self, other: Iterable[str] | Mapping[str, int]) -> int:
        """Same as count_subset()."""

    @overload
    def __floordiv__(
            self,
            other: int | Iterable[str] | Mapping[str, int]) -> 'Symbols | int':
        ...

    def __floordiv__(
            self,
            other: int | Iterable[str] | Mapping[str, int]) -> 'Symbols | int':
        if isinstance(other, int):
            return self.divide_counts(other)
        elif isinstance(other, Iterable):
            return self.count_subset(other)
        else:
            return NotImplemented

    def __rfloordiv__(self, other: Iterable[str] | Mapping[str, int]) -> int:
        return Symbols(other).count_subset(self)

    def modulo_counts(self, other: int) -> 'Symbols':
        return self % other

    def __mod__(self, other: int) -> 'Symbols':
        if not isinstance(other, int):
            return NotImplemented
        data = defaultdict(int, {
            s: count % other
            for s, count in self.items()
        })
        return Symbols._new_raw(data)

    def __lt__(self, other: 'Symbols') -> bool:
        if not isinstance(other, Symbols):
            return NotImplemented
        keys = sorted(set(self.keys()) | set(other.keys()))
        for k in keys:
            if self[k] < other[k]:  # type: ignore
                return True
            if self[k] > other[k]:  # type: ignore
                return False
        return False

    def __gt__(self, other: 'Symbols') -> bool:
        if not isinstance(other, Symbols):
            return NotImplemented
        keys = sorted(set(self.keys()) | set(other.keys()))
        for k in keys:
            if self[k] > other[k]:  # type: ignore
                return True
            if self[k] < other[k]:  # type: ignore
                return False
        return False

    def issubset(self, other: Iterable[str] | Mapping[str, int]) -> bool:
        """Whether `self` is a subset of the other.

        Same as `<=`.
        
        Note that the `<` and `>` operators are lexicographic orderings,
        not proper subset relations.
        """
        return self <= other

    def __le__(self, other: Iterable[str] | Mapping[str, int]) -> bool:
        if isinstance(other, (icepool.Population, icepool.AgainExpression)):
            return NotImplemented  # delegate to the other
        other = Symbols(other)
        return all(self[s] <= other[s]  # type: ignore
                   for s in itertools.chain(self, other))

    def issuperset(self, other: Iterable[str] | Mapping[str, int]) -> bool:
        """Whether `self` is a superset of the other.

        Same as `>=`.
        
        Note that the `<` and `>` operators are lexicographic orderings,
        not proper subset relations.
        """
        return self >= other

    def __ge__(self, other: Iterable[str] | Mapping[str, int]) -> bool:
        if isinstance(other, (icepool.Population, icepool.AgainExpression)):
            return NotImplemented  # delegate to the other
        other = Symbols(other)
        return all(self[s] >= other[s]  # type: ignore
                   for s in itertools.chain(self, other))

    def isdisjoint(self, other: Iterable[str] | Mapping[str, int]) -> bool:
        """Whether `self` has any positive elements in common with the other.
        
        Raises:
            ValueError if either has negative elements.
        """
        other = Symbols(other)
        if self.has_negative_counts() or other.has_negative_counts():
            raise ValueError(
                "isdisjoint() is not defined for negative counts.")
        return any(self[s] > 0 and other[s] > 0  # type: ignore
                   for s in self)

    def __eq__(self, other) -> bool:
        if isinstance(other, (icepool.Population, icepool.AgainExpression)):
            return NotImplemented  # delegate to the other
        try:
            other = Symbols(other)
        except ValueError:
            return NotImplemented
        return all(self[s] == other[s]  # type: ignore
                   for s in itertools.chain(self, other))

    def __ne__(self, other) -> bool:
        if isinstance(other, (icepool.Population, icepool.AgainExpression)):
            return NotImplemented  # delegate to the other
        try:
            other = Symbols(other)
        except ValueError:
            return NotImplemented
        return any(self[s] != other[s]  # type: ignore
                   for s in itertools.chain(self, other))

    # Unary operators.

    def has_negative_counts(self) -> bool:
        """Whether any counts are negative."""
        return any(c < 0 for c in self.values())

    def __pos__(self) -> 'Symbols':
        data = defaultdict(int, {
            s: count
            for s, count in self.items() if count > 0
        })
        return Symbols._new_raw(data)

    def __neg__(self) -> 'Symbols':
        data = defaultdict(int, {s: -count for s, count in self.items()})
        return Symbols._new_raw(data)

    @cached_property
    def _hash(self) -> int:
        return hash((Symbols, str(self)))

    def __hash__(self) -> int:
        return self._hash

    def count(self) -> int:
        """The total number of elements."""
        return sum(self._data.values())

    @cached_property
    def _str(self) -> str:
        sorted_keys = sorted(self)
        positive = ''.join(s * self._data[s] for s in sorted_keys
                           if self._data[s] > 0)
        negative = ''.join(s * -self._data[s] for s in sorted_keys
                           if self._data[s] < 0)
        if positive:
            if negative:
                return positive + ' - ' + negative
            else:
                return positive
        else:
            if negative:
                return '-' + negative
            else:
                return ''

    def __str__(self) -> str:
        """All symbols in unary form (i.e. including duplicates) in ascending order.

        If there are negative elements, they are listed following a ` - ` sign.
        """
        return self._str

    def __repr__(self) -> str:
        return type(self).__qualname__ + f"('{str(self)}')"
