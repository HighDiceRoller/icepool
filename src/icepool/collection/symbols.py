__docformat__ = 'google'

import itertools
import re

from collections import defaultdict
from functools import cached_property
from typing import Iterable, Iterator, Mapping


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
    cost for further operations.

    Duplicate symbols have no extra effect here, except that e.g. `symbols.aa`
    will produce a `Symbols` rather than an `int`. In order to avoid confusion
    with methods, try not to spell words when using attribute-style access.

    `Population.marginals` forwards attribute access, so you can use e.g.
    `die.marginals.a` to get the marginal distribution of `a`s.

    Note that attribute access only works with valid identifiers,
    so e.g. emojis would need to use the subscript method.
    """
    _data: defaultdict[str, int]

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
            self._data = defaultdict(int)
            positive, *negative = re.split(r'\s*-\s*', symbols)
            for s in positive:
                self._data[s] += 1
            if len(negative) > 1:
                raise ValueError('Multiple dashes not allowed.')
            if len(negative) == 1:
                for s in negative[0]:
                    self._data[s] -= 1
        elif isinstance(symbols, Mapping):
            self._data = defaultdict(int, symbols)
        else:
            self._data = defaultdict(int)
            for s in symbols:
                self._data[s] += 1

        for s in self._data:
            if len(s) != 1:
                raise ValueError(f'Symbol {s} is not a single character.')
            if re.match(r'[\s_-]', s):
                raise ValueError(
                    f'{s} (U+{ord(s):04X}) is not a legal symbol.')
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
        data = defaultdict(int, self._data)
        for other in args:
            for s, count in Symbols(other).items():
                data[s] += count
        return Symbols._new_raw(data)

    __add__ = additive_union
    __radd__ = additive_union

    def difference(self, *args:
                   Iterable[str] | Mapping[str, int]) -> 'Symbols':
        data = defaultdict(int, self._data)
        for other in args:
            for s, count in Symbols(other).items():
                data[s] -= count
        return Symbols._new_raw(data)

    __sub__ = difference

    def __rsub__(self, other: Iterable[str] | Mapping[str, int]) -> 'Symbols':
        data = defaultdict(int, Symbols(other)._data)
        for s, count in self.items():
            data[s] -= count
        return Symbols._new_raw(data)

    def intersection(self, *args:
                     Iterable[str] | Mapping[str, int]) -> 'Symbols':
        data = defaultdict(int, self._data)
        for other in args:
            for s, count in Symbols(other).items():
                data[s] = min(data[s], count)
        return Symbols._new_raw(data)

    __and__ = intersection
    __rand__ = intersection

    def union(self, *args: Iterable[str] | Mapping[str, int]) -> 'Symbols':
        data = defaultdict(int, self._data)
        for other in args:
            for s, count in Symbols(other).items():
                data[s] = max(data[s], count)
        return Symbols._new_raw(data)

    __or__ = union
    __ror__ = union

    def symmetric_difference(
            self, other: Iterable[str] | Mapping[str, int]) -> 'Symbols':
        data = defaultdict(int, self._data)
        for s, count in Symbols(other).items():
            data[s] = abs(data[s] - count)
        return Symbols._new_raw(data)

    __xor__ = symmetric_difference
    __rxor__ = symmetric_difference

    def multiply_counts(self, other: int) -> 'Symbols':
        """Multiplies all counts by an integer."""
        if not isinstance(other, int):
            return NotImplemented
        data = defaultdict(int, {
            s: count * other
            for s, count in self.items()
        })
        return Symbols._new_raw(data)

    __mul__ = multiply_counts
    __rmul__ = multiply_counts

    def divide_counts(self, other: int) -> 'Symbols':
        """Divides all counts by an integer, rounding down."""
        if not isinstance(other, int):
            return NotImplemented
        data = defaultdict(int, {
            s: count // other
            for s, count in self.items()
        })
        return Symbols._new_raw(data)

    __floordiv__ = divide_counts

    def __lt__(self, other: 'Symbols') -> bool:
        if not isinstance(other, Symbols):
            return NotImplemented
        return str(self) < str(other)

    def __gt__(self, other: 'Symbols') -> bool:
        if not isinstance(other, Symbols):
            return NotImplemented
        return str(self) > str(other)

    def issubset(self, other: Iterable[str] | Mapping[str, int]) -> bool:
        """Whether `self` is a subset of the other.

        Same as `<=`.
        
        Note that the `<` and `>` operators are lexicographic orderings,
        not proper subset relations.
        """
        other = Symbols(other)
        return all(self[s] <= other[s]  # type: ignore
                   for s in itertools.chain(self, other))

    __le__ = issubset

    def issuperset(self, other: Iterable[str] | Mapping[str, int]) -> bool:
        """Whether `self` is a superset of the other.

        Same as `>=`.
        
        Note that the `<` and `>` operators are lexicographic orderings,
        not proper subset relations.
        """
        other = Symbols(other)
        return all(self[s] >= other[s]  # type: ignore
                   for s in itertools.chain(self, other))

    __ge__ = issuperset

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
        try:
            other = Symbols(other)
        except TypeError:
            return NotImplemented
        return all(self[s] == other[s]  # type: ignore
                   for s in itertools.chain(self, other))

    def __ne__(self, other) -> bool:
        try:
            other = Symbols(other)
        except TypeError:
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
