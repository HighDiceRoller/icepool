__docformat__ = 'google'

import icepool
import icepool.again
import icepool.math
import icepool.creation_args
from icepool.counts import Counts, CountsKeysView, CountsValuesView, CountsItemsView
from icepool.population import Population

from collections import defaultdict
from functools import cached_property
import operator

from typing import Any, Callable, Iterator, Mapping, MutableMapping, Sequence, overload


class Deck(Population):
    """Sampling without replacement (within a single evaluation).

    Quantities represent duplicates.
    """

    _data: Counts
    _deal: int

    def _new_type(self) -> type:
        return Deck

    def __new__(cls,
                outcomes: Mapping[Any, int] | Sequence,
                times: Sequence[int] | int = 1) -> 'Deck':
        """Constructor for a `Deck`.

        Args:
            outcomes: The cards of the `Deck`. This can be one of the following:
                * A `Mapping` from outcomes to quantities.
                * A sequence of outcomes.

                Note that `Die` and `Deck` both count as `Mapping`s.

                Each card may be one of the following:
                * A `Mapping` from outcomes to quantities.
                    The outcomes of the `Mapping` will be "flattened" into the
                    result. This option will be taken in preference to treating
                    the `Mapping` itself as an outcome even if the `Mapping`
                    itself is hashable and totally orderable. This means that
                    `Die` and `Deck` will never be outcomes.
                * A tuple of outcomes.
                    Any tuple elements that are `Mapping`s will expand the
                    tuple according to their independent joint distribution.
                    For example, `(d6, d6)` will expand to 36 ordered tuples
                    with dup 1 each. Use this carefully since it may create a
                    large number of outcomes.
                * `str` or `bytes`, which will be treated as a single outcome.
                * Any other sequence. Each element will be weighted equally.
                * Anything else will be treated as a single outcome.
                    Each outcome must be hashable, and the
                    set of outcomes must be totally orderable (after expansion).
                    The same outcome can appear multiple times, in which case
                    the corresponding quantities will be accumulated.
            times: Multiplies the number of times each element of `outcomes`
                will be put into the `Deck`.
                `times` can either be a sequence of the same length as
                `outcomes` or a single `int` to apply to all elements of
                `outcomes`.
        """
        if isinstance(outcomes, Deck):
            if times == 1:
                return outcomes
            else:
                outcomes = outcomes._data

        if icepool.again.contains_again(outcomes):
            raise ValueError('Again cannot be used with Decks.')

        outcomes, times = icepool.creation_args.itemize(outcomes, times)

        if len(outcomes) == 1 and times[0] == 1 and isinstance(
                outcomes[0], Deck):
            return outcomes[0]

        data = icepool.creation_args.expand_args_for_deck(outcomes, times)
        return Deck._new_deck(data)

    @classmethod
    def _new_deck(cls, data: Counts) -> 'Deck':
        """Creates a new `Deck` using already-processed arguments.

        Args:
            data: At this point, this is a Counts.
        """
        self = super(Population, cls).__new__(cls)
        self._data = data
        return self

    def keys(self) -> CountsKeysView:
        return self._data.keys()

    def values(self) -> CountsValuesView:
        return self._data.values()

    def items(self) -> CountsItemsView:
        return self._data.items()

    def __getitem__(self, outcome) -> int:
        return self._data[outcome]

    def __iter__(self) -> Iterator:
        return iter(self.keys())

    def __len__(self) -> int:
        return len(self._data)

    size = icepool.Population.denominator

    @cached_property
    def _popped_min(self) -> tuple['Deck', int]:
        return self._new_deck(self._data.remove_min()), self.quantities()[0]

    def _pop_min(self) -> tuple['Deck', int]:
        """A `Deck` with the min outcome removed."""
        return self._popped_min

    @cached_property
    def _popped_max(self) -> tuple['Deck', int]:
        return self._new_deck(self._data.remove_max()), self.quantities()[-1]

    def _pop_max(self) -> tuple['Deck', int]:
        """A `Deck` with the max outcome removed."""
        return self._popped_max

    def deal(self, *hand_sizes: int) -> 'icepool.Deal':
        """Creates a `Deal` object from this deck.

        See `Deal()` for details.
        """
        return icepool.Deal(self, *hand_sizes)

    def sub(self, repl: Callable | Mapping, /, star: int = 0) -> 'Deck':
        """Changes outcomes of the `Deck` to other outcomes.

        You can think of this as `sub`stituting outcomes of this `Deck` for
        other outcomes.

        Args:
            repl: One of the following:
                * A callable returning a new outcome for each old outcome.
                * A map from old outcomes to new outcomes.
                    Unmapped old outcomes stay the same.
                The new outcomes may be `Deck`s, in which case one card is
                replaced with several. This is not recommended.
            star: If set to `True` or 1, outcomes of `self` will be unpacked as
                `*outcome` before giving it to the `repl` function. `extra_dice`
                are not unpacked. If `repl` is not a callable, this has no
                effect.
        """
        # Convert to a single-argument function.
        if callable(repl):
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
