__docformat__ = 'google'

import icepool
import icepool.population.again
import icepool.math
import icepool.creation_args
from icepool.collection.counts import Counts, CountsKeysView, CountsValuesView, CountsItemsView
from icepool.population.base import Population
from icepool.typing import U, Outcome, T_co, guess_star

import functools
import operator

from collections import Counter, defaultdict
from functools import cached_property
from typing import Any, Callable, Iterable, Iterator, Mapping, MutableSequence, Sequence, Type, overload


class Deck(Population[T_co]):
    """Sampling without replacement (within a single evaluation).

    Quantities represent duplicates.
    """

    _data: Counts[T_co]
    _deal: int

    @property
    def _new_type(self) -> type:
        return Deck

    def __new__(cls,
                outcomes: Sequence | Mapping[Any, int],
                times: Sequence[int] | int = 1) -> 'Deck[T_co]':
        """Constructor for a `Deck`.

        All quantities must be non-negative. Outcomes with zero quantity will be
        omitted.

        Args:
            outcomes: The cards of the `Deck`. This can be one of the following:
                * A `Sequence` of outcomes. Duplicates will contribute
                    quantity for each appearance.
                * A `Mapping` from outcomes to quantities.

                Each outcome may be one of the following:
                * An outcome, which must be hashable and totally orderable.
                * A `Deck`, which will be flattened into the result. If a
                    `times` is assigned to the `Deck`, the entire `Deck` will
                    be duplicated that many times.
            times: Multiplies the number of times each element of `outcomes`
                will be put into the `Deck`.
                `times` can either be a sequence of the same length as
                `outcomes` or a single `int` to apply to all elements of
                `outcomes`.
        """

        if icepool.population.again.contains_again(outcomes):
            raise ValueError('Again cannot be used with Decks.')

        outcomes, times = icepool.creation_args.itemize(outcomes, times)

        if len(outcomes) == 1 and times[0] == 1 and isinstance(
                outcomes[0], Deck):
            return outcomes[0]

        counts: Counts[T_co] = icepool.creation_args.expand_args_for_deck(
            outcomes, times)

        return Deck._new_raw(counts)

    @classmethod
    def _new_raw(cls, data: Counts[T_co]) -> 'Deck[T_co]':
        """Creates a new `Deck` using already-processed arguments.

        Args:
            data: At this point, this is a Counts.
        """
        self = super(Population, cls).__new__(cls)
        self._data = data
        return self

    def keys(self) -> CountsKeysView[T_co]:
        return self._data.keys()

    def values(self) -> CountsValuesView:
        return self._data.values()

    def items(self) -> CountsItemsView[T_co]:
        return self._data.items()

    def __getitem__(self, outcome) -> int:
        return self._data[outcome]

    def __iter__(self) -> Iterator[T_co]:
        return iter(self.keys())

    def __len__(self) -> int:
        return len(self._data)

    size = icepool.Population.denominator

    @cached_property
    def _popped_min(self) -> tuple['Deck[T_co]', int]:
        return self._new_raw(self._data.remove_min()), self.quantities()[0]

    def _pop_min(self) -> tuple['Deck[T_co]', int]:
        """A `Deck` with the min outcome removed."""
        return self._popped_min

    @cached_property
    def _popped_max(self) -> tuple['Deck[T_co]', int]:
        return self._new_raw(self._data.remove_max()), self.quantities()[-1]

    def _pop_max(self) -> tuple['Deck[T_co]', int]:
        """A `Deck` with the max outcome removed."""
        return self._popped_max

    @overload
    def deal(self, hand_size: int, /) -> 'icepool.Deal[T_co]':
        ...

    @overload
    def deal(
            self, hand_size: int, hand_size_2: int, /, *more_hand_sizes:
        int) -> 'icepool.MultiDeal[T_co, tuple[int, ...]]':
        ...

    @overload
    def deal(
        self, *hand_sizes: int
    ) -> 'icepool.Deal[T_co] | icepool.MultiDeal[T_co, tuple[int, ...]]':
        ...

    def deal(
        self, *hand_sizes: int
    ) -> 'icepool.Deal[T_co] | icepool.MultiDeal[T_co, tuple[int, ...]]':
        """Creates a `Deal` object from this deck.

        See `Deal()` for details.
        """
        if len(hand_sizes) == 1:
            return icepool.Deal(self, *hand_sizes)
        else:
            return icepool.MultiDeal(self, *hand_sizes)

    # Binary operators.

    def additive_union(
            self, *args: Iterable[T_co] | Mapping[T_co, int]) -> 'Deck[T_co]':
        """Both decks merged together."""
        return functools.reduce(operator.add, args, initial=self)

    def __add__(self,
                other: Iterable[T_co] | Mapping[T_co, int]) -> 'Deck[T_co]':
        data = Counter(self._data)
        for outcome, count in Counter(other).items():
            data[outcome] += count
        return Deck(+data)

    __radd__ = __add__

    def difference(self, *args:
                   Iterable[T_co] | Mapping[T_co, int]) -> 'Deck[T_co]':
        """This deck with the other cards removed (but not below zero of each card)."""
        return functools.reduce(operator.sub, args, initial=self)

    def __sub__(self,
                other: Iterable[T_co] | Mapping[T_co, int]) -> 'Deck[T_co]':
        data = Counter(self._data)
        for outcome, count in Counter(other).items():
            data[outcome] -= count
        return Deck(+data)

    def __rsub__(self,
                 other: Iterable[T_co] | Mapping[T_co, int]) -> 'Deck[T_co]':
        data = Counter(other)
        for outcome, count in self.items():
            data[outcome] -= count
        return Deck(+data)

    def intersection(
            self, *args: Iterable[T_co] | Mapping[T_co, int]) -> 'Deck[T_co]':
        """The cards that both decks have."""
        return functools.reduce(operator.and_, args, initial=self)

    def __and__(self,
                other: Iterable[T_co] | Mapping[T_co, int]) -> 'Deck[T_co]':
        data: Counter[T_co] = Counter()
        for outcome, count in Counter(other).items():
            data[outcome] = min(self.get(outcome, 0), count)
        return Deck(+data)

    __rand__ = __and__

    def union(self, *args:
              Iterable[T_co] | Mapping[T_co, int]) -> 'Deck[T_co]':
        """As many of each card as the deck that has more of them."""
        return functools.reduce(operator.or_, args, initial=self)

    def __or__(self,
               other: Iterable[T_co] | Mapping[T_co, int]) -> 'Deck[T_co]':
        data = Counter(self._data)
        for outcome, count in Counter(other).items():
            data[outcome] = max(data[outcome], count)
        return Deck(+data)

    __ror__ = __or__

    def symmetric_difference(
            self, other: Iterable[T_co] | Mapping[T_co, int]) -> 'Deck[T_co]':
        """As many of each card as the deck that has more of them."""
        return self ^ other

    def __xor__(self,
                other: Iterable[T_co] | Mapping[T_co, int]) -> 'Deck[T_co]':
        data = Counter(self._data)
        for outcome, count in Counter(other).items():
            data[outcome] = abs(data[outcome] - count)
        return Deck(+data)

    def __mul__(self, other: int) -> 'Deck[T_co]':
        if not isinstance(other, int):
            return NotImplemented
        return self.multiply_quantities(other)

    __rmul__ = __mul__

    def __floordiv__(self, other: int) -> 'Deck[T_co]':
        if not isinstance(other, int):
            return NotImplemented
        return self.divide_quantities(other)

    def __mod__(self, other: int) -> 'Deck[T_co]':
        if not isinstance(other, int):
            return NotImplemented
        return self.modulo_quantities(other)

    def map(
            self,
            repl:
        'Callable[..., U | Deck[U] | icepool.RerollType] | Mapping[T_co, U | Deck[U] | icepool.RerollType]',
            /,
            star: bool | None = None) -> 'Deck[U]':
        """Maps outcomes of this `Deck` to other outcomes.

        Args:
            repl: One of the following:
                * A callable returning a new outcome for each old outcome.
                * A map from old outcomes to new outcomes.
                    Unmapped old outcomes stay the same.
                The new outcomes may be `Deck`s, in which case one card is
                replaced with several. This is not recommended.
            star: Whether outcomes should be unpacked into separate arguments
                before sending them to a callable `repl`.
                If not provided, this will be guessed based on the function
                signature.
        """
        # Convert to a single-argument function.
        if callable(repl):
            if star is None:
                star = guess_star(repl)
            if star:

                def transition_function(outcome):
                    return repl(*outcome)
            else:

                def transition_function(outcome):
                    return repl(outcome)
        else:
            # repl is a mapping.
            def transition_function(outcome):
                if outcome in repl:
                    return repl[outcome]
                else:
                    return outcome

        return Deck(
            [transition_function(outcome) for outcome in self.outcomes()],
            times=self.quantities())

    @cached_property
    def _sequence_cache(
            self) -> 'MutableSequence[icepool.Die[tuple[T_co, ...]]]':
        return [icepool.Die([()])]

    def sequence(self, deals: int, /) -> 'icepool.Die[tuple[T_co, ...]]':
        """Possible sequences produced by dealing from this deck a number of times.
        
        This is extremely expensive computationally. If you don't care about
        order, use `deal()` instead.
        """
        if deals < 0:
            raise ValueError('The number of cards dealt cannot be negative.')
        for i in range(len(self._sequence_cache), deals + 1):

            def transition(curr):
                remaining = icepool.Die(self - curr)
                return icepool.map(lambda curr, next: curr + (next, ), curr,
                                   remaining)

            result: 'icepool.Die[tuple[T_co, ...]]' = self._sequence_cache[
                i - 1].map(transition)
            self._sequence_cache.append(result)
        return result

    @cached_property
    def _hash_key(self) -> tuple:
        return Deck, tuple(self.items())

    def __eq__(self, other) -> bool:
        if not isinstance(other, Deck):
            return False
        return self._hash_key == other._hash_key

    @cached_property
    def _hash(self) -> int:
        return hash(self._hash_key)

    def __hash__(self) -> int:
        return self._hash

    def __repr__(self) -> str:
        inner = ', '.join(f'{repr(outcome)}: {quantity}'
                          for outcome, quantity in self.items())
        return type(self).__qualname__ + '({' + inner + '})'
