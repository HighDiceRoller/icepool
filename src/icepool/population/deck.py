__docformat__ = 'google'

import icepool
import icepool.population.again
import icepool.math
import icepool.creation_args
from icepool.collection.counts import Counts, CountsKeysView, CountsValuesView, CountsItemsView
from icepool.population.base import Population
from icepool.typing import U, Outcome, T_co, guess_star

from functools import cached_property

from typing import Any, Callable, Iterator, Mapping, Sequence, Type


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

    def deal(self, *hand_sizes: int) -> 'icepool.Deal[T_co, tuple[int, ...]]':
        """Creates a `Deal` object from this deck.

        See `Deal()` for details.
        """
        return icepool.Deal(self, *hand_sizes)

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
    def _key_tuple(self) -> tuple:
        return Deck, tuple(self.items())

    def __eq__(self, other) -> bool:
        if not isinstance(other, Deck):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self) -> int:
        return hash(self._key_tuple)

    def __hash__(self) -> int:
        return self._hash

    def __repr__(self) -> str:
        inner = ', '.join(
            f'{outcome}: {quantity}' for outcome, quantity in self.items())
        return type(self).__qualname__ + '({' + inner + '})'
