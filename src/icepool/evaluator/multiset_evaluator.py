__docformat__ = 'google'

import icepool
from icepool.evaluator.multiset_evaluator_base import MultisetEvaluatorBase, MultisetDungeon, MultisetQuest
from icepool.expression.multiset_expression_base import MultisetExpressionBase
from icepool.expression.multiset_param import MultisetParamBase
from icepool.order import Order

from abc import abstractmethod
from functools import cached_property
import itertools
import math

from icepool.typing import Q, T, U_co
from typing import (Any, Callable, Collection, Generic, Hashable, Iterator,
                    Mapping, MutableMapping, MutableSequence, Sequence, Type,
                    TypeAlias, cast, TYPE_CHECKING, overload)

if TYPE_CHECKING:
    from icepool.expression.multiset_expression_base import MultisetExpressionBase, MultisetSourceBase, MultisetDungeonlet, MultisetQuestlet


class MultisetEvaluator(MultisetEvaluatorBase[T, U_co]):

    def initial_state(self, order: Order, outcomes: Sequence[T], /,
                      **kwargs: Hashable):
        """Optional method to produce an initial evaluation state.

        If not override, the initial state is `None`.

        TODO: Should this get cardinalities?

        Args:
            order: The order in which `next_state` will see outcomes.
            outcomes: All outcomes that will be seen by `next_state` in sorted order.
            kwargs: Any keyword arguments that were passed to `evaluate()`.

        Raises:
            UnsupportedOrderError if the given order is not supported.
        """
        return None

    @abstractmethod
    def next_state(self, state: Hashable, order: Order, outcome: T, /,
                   *counts) -> Hashable:
        """State transition function.

        This should produce a state given the previous state, an outcome,
        the count of that outcome produced by each multiset input, and any
        **kwargs provided to `evaluate()`.

        `evaluate()` will always call this with `state, outcome, *counts` as
        positional arguments. Furthermore, there is no expectation that a 
        subclass be able to handle an arbitrary number of counts. 
        
        Thus, you are free to:
        * Rename `state` or `outcome` in a subclass.
        * Replace `*counts` with a fixed set of parameters.

        Make sure to handle the base case where `state is None`.

        States must be hashable. At current, they do not have to be orderable.
        However, this may change in the future, and if they are not totally
        orderable, you must override `final_outcome` to create totally orderable
        final outcomes.

        The behavior of returning a `Die` from `next_state` is currently
        undefined.

        Args:
            state: A hashable object indicating the state before rolling the
                current outcome. If this is the first outcome being considered,
                `state` will be `None`.
            order: The order in which outcomes are seen. You can raise an 
                `UnsupportedOrderError` if you don't want to support the current 
                order. In this case, the opposite order will then be attempted
                (if it hasn't already been attempted).
            outcome: The current outcome.
                If there are multiple inputs, the set of outcomes is at 
                least the union of the outcomes of the invididual inputs. 
                You can use `extra_outcomes()` to add extra outcomes.
            *counts: One value (usually an `int`) for each input indicating how
                many of the current outcome were produced.

        Returns:
            A hashable object indicating the next state.
            The special value `icepool.Reroll` can be used to immediately remove
            the state from consideration, effectively performing a full reroll.
        """

    def extra_outcomes(self, outcomes: Sequence[T]) -> Collection[T]:
        """Optional method to specify extra outcomes that should be seen as inputs to `next_state()`.

        These will be seen by `next_state` even if they do not appear in the
        input(s). The default implementation returns `()`, or no additional
        outcomes.

        If you want `next_state` to see consecutive `int` outcomes, you can set
        `extra_outcomes = icepool.MultisetEvaluator.consecutive`.
        See `consecutive()` below.

        Args:
            outcomes: The outcomes that could be produced by the inputs, in
            ascending order.
        """
        return ()

    def final_outcome(
            self, final_state: Hashable, order: Order, outcomes: tuple[T, ...],
            /, **kwargs: Hashable
    ) -> 'U_co | icepool.Die[U_co] | icepool.RerollType':
        """Optional method to generate a final output outcome from a final state.

        By default, the final outcome is equal to the final state.
        Note that `None` is not a valid outcome for a `Die`,
        and if there are no outcomes, `final_outcome` will be immediately
        be callled with `final_state=None`.
        Subclasses that want to handle this case should explicitly define what
        happens.

        `**kwargs` are non-multiset arguments that were provided to
        `evaluate()`.
        You may replace `**kwargs` with a fixed set of keyword parameters;
        `final_state()` should take the same set of keyword parameters.

        Args:
            final_state: A state after all outcomes have been processed.
            kwargs: Any kwargs that were passed to the evaluation.

        Returns:
            A final outcome that will be used as part of constructing the result `Die`.
            As usual for `Die()`, this could itself be a `Die` or `icepool.Reroll`.
        """
        # If not overriden, the final_state should have type U_co.
        return cast(U_co, final_state)

    def consecutive(self, outcomes: Sequence[int]) -> Collection[int]:
        """Example implementation of `extra_outcomes()` that produces consecutive `int` outcomes.

        Set `extra_outcomes = icepool.MultisetEvaluator.consecutive` to use this.

        Returns:
            All `int`s from the min outcome to the max outcome among the inputs,
            inclusive.

        Raises:
            TypeError: if any input has any non-`int` outcome.
        """
        if not outcomes:
            return ()

        if any(not isinstance(x, int) for x in outcomes):
            raise TypeError(
                "consecutive cannot be used with outcomes of type other than 'int'."
            )

        return range(outcomes[0], outcomes[-1] + 1)

    dungeon_key: Hashable = None
    """Subclasses may optionally provide this value; if so, intermediate calculations will be persistently cached."""

    def _prepare(
        self,
        input_exps: tuple[MultisetExpressionBase[T, Any], ...],
        kwargs: Mapping[str, Hashable],
    ) -> Iterator[tuple['MultisetDungeon[T]', 'MultisetQuest[T, U_co]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        for t in itertools.product(*(exp._prepare() for exp in input_exps)):
            dungeonlet_flats, questlet_flats, sources, weights = zip(*t)
            dungeon: MultisetEvaluatorDungeon[T] = MultisetEvaluatorDungeon(
                self.next_state, self.dungeon_key, dungeonlet_flats)
            quest: MultisetEvaluatorQuest[T, U_co] = MultisetEvaluatorQuest(
                self.initial_state, self.extra_outcomes, self.final_outcome,
                questlet_flats)
            sources = tuple(itertools.chain.from_iterable(sources))
            weight = math.prod(weights)
            yield dungeon, quest, sources, weight


class MultisetEvaluatorDungeon(MultisetDungeon[T]):

    def __init__(
        self, next_state_eval: Callable[..., Hashable], dungeon_key: Hashable,
        dungeonlet_flats: 'tuple[tuple[MultisetDungeonlet[T, Any], ...], ...]'
    ):
        self.next_state_eval = next_state_eval
        self.dungeon_key = dungeon_key
        self.dungeonlet_flats = dungeonlet_flats

        if dungeon_key is None:
            self.__hash__ = None  # type: ignore

    def next_state_main(self, state, order: Order, outcome: T,
                        source_counts: Iterator,
                        param_counts: Sequence) -> Hashable:
        return self.next_state_eval(state, order, outcome, *param_counts)

    def __eq__(self, other):
        if not isinstance(other, MultisetEvaluatorDungeon):
            return False
        if self is other:
            return True
        if self.dungeon_key is not None and other.dungeon_key is not None:
            return self.dungeon_key == other.dungeon_key
        return False

    def __hash__(self):
        return hash((self.dungeonlet_flats, self.dungeon_key))


class MultisetEvaluatorQuest(MultisetQuest[T, U_co]):
    # These are filled in by the constructor.
    initial_state_main = None  # type: ignore
    extra_outcomes = None  # type: ignore
    final_outcome = None  # type: ignore

    def __init__(
            self, initial_state_main: Callable[..., Hashable],
            extra_outcomes: Callable, final_outcome: Callable,
            questlet_flats: 'tuple[tuple[MultisetQuestlet[T], ...], ...]'):
        self.initial_state_main = initial_state_main  # type: ignore
        self.extra_outcomes = extra_outcomes  # type: ignore
        self.final_outcome = final_outcome  # type: ignore
        self.questlet_flats = questlet_flats
