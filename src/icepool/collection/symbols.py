__docformat__ = 'google'

from collections import Counter
from functools import cached_property
from typing import Iterable, Iterator, Mapping


class Symbols(Mapping[str, int]):
    """EXPERIMENTAL: Immutable multiset of single characters.
    
    Supports most non-mutating methods that `collections.Counter` does,
    with implicit conversion of `Iterable`s and `Mapping`s.

    Subscripting with a single character returns the count of that character
    as an `int`. E.g. `symbols['a']` -> number of `a`s as an `int`.
    You can also access it as an attribute, e.g.  `symbols.a`.

    Subscripting with multiple characters returns a `Symbols` with only those
    characters, dropping the rest.
    E.g. `symbols['ab']` -> number of `a`s and `b`s as a `Symbols`.
    Again you can also access it as an attribute, e.g. `symbols.ab`.

    Note that attribute access only works with valid identifiers that don't
    start with an underscore, so e.g. emojis will need to use the subscript
    method.
    """
    _data: Counter[str]

    def __new__(cls, symbols: Iterable[str] | Mapping[str, int]):
        self = super(Symbols, cls).__new__(cls)
        self._data = Counter(symbols)
        return self

    @classmethod
    def _new_raw(cls, data: Counter[str]) -> 'Symbols':
        self = super(Symbols, cls).__new__(cls)
        self._data = data
        return self

    # Mapping interface.

    def __getitem__(self, key: str) -> 'int | Symbols':  # type: ignore
        if len(key) == 1:
            return self._data[key]
        else:
            return Symbols._new_raw(Counter({s: self._data[s] for s in key}))

    def __getattr__(self, key: str):
        if key[0] == '_':
            return AttributeError(key)
        return self[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    # Counter interface.

    def most_common(self, n: int | None = None) -> list[tuple[str, int]]:
        return self._data.most_common(n)

    def total(self) -> int:
        return self._data.total()

    def elements(self) -> str:
        """All symbols, including duplicates, in ascending order as a str.
        
        Same as str(self)."""
        return str(self)

    # Operators.

    def additive_union(self,
                       other: Iterable[str] | Mapping[str, int]) -> 'Symbols':
        return Symbols._new_raw(self._data + Counter(other))

    __add__ = additive_union
    __radd__ = additive_union

    def difference(self,
                   other: Iterable[str] | Mapping[str, int]) -> 'Symbols':
        return Symbols._new_raw(self._data - Counter(other))

    __sub__ = difference

    def __rsub__(self, other: Iterable[str] | Mapping[str, int]) -> 'Symbols':
        return Symbols._new_raw(Counter(other) - self._data)

    def intersection(self,
                     other: Iterable[str] | Mapping[str, int]) -> 'Symbols':
        return Symbols._new_raw(self._data & Counter(other))

    __and__ = intersection
    __rand__ = intersection

    def union(self, other: Iterable[str] | Mapping[str, int]) -> 'Symbols':
        return Symbols._new_raw(self._data | Counter(other))

    __or__ = union
    __ror__ = union

    def __mul__(self, other: int) -> 'Symbols':
        if not isinstance(other, int):
            return NotImplemented
        return Symbols._new_raw(
            Counter({
                k: v * other
                for k, v in self._data.items()
            }))

    def __rmul__(self, other: int) -> 'Symbols':
        if not isinstance(other, int):
            return NotImplemented
        return Symbols._new_raw(
            Counter({
                k: v * other
                for k, v in self._data.items()
            }))

    def __lt__(self, other: 'Symbols') -> bool:
        if not isinstance(other, Symbols):
            return NotImplemented
        return str(self) < str(other)

    def __gt__(self, other: 'Symbols') -> bool:
        if not isinstance(other, Symbols):
            return NotImplemented
        return str(self) > str(other)

    def issubset(self, other: Iterable[str] | Mapping[str, int]) -> bool:
        """Whether this Symbols is a subset of the other.

        Same as `<=`.
        
        Note that the `<` and `>` operators are lexicographic orderings,
        not proper subset relations.
        """
        return self._data <= Counter(other)

    __le__ = issubset

    def issuperset(self, other: Iterable[str] | Mapping[str, int]) -> bool:
        """Whether this Symbols is a superset of the other.

        Same as `>=`.
        
        Note that the `<` and `>` operators are lexicographic orderings,
        not proper subset relations.
        """
        return self._data >= Counter(other)

    __ge__ = issuperset

    def __eq__(self, other):
        if not isinstance(other, Symbols):
            return False
        return self._data == other._data

    def __ne__(self, other):
        if not isinstance(other, Symbols):
            return True
        return self._data != other._data

    @cached_property
    def _hash(self) -> int:
        return hash((Symbols, str(self)))

    def __hash__(self) -> int:
        return self._hash

    @cached_property
    def _str(self) -> str:
        return ''.join(s * self._data[s] for s in sorted(self._data))

    def __str__(self) -> str:
        return self._str

    def __repr__(self) -> str:
        return f"Symbols('{str(self)}')"
