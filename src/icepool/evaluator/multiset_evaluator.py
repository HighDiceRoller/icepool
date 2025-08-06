__docformat__ = 'google'

import icepool
from icepool.evaluator.multiset_evaluator_base import MultisetEvaluatorBase, Dungeon, Quest
from icepool.expression.multiset_expression_base import MultisetExpressionBase
from icepool.order import Order

from abc import abstractmethod
import itertools
import math

from icepool.typing import T, MaybeHashKeyed, U_co
from typing import (Any, Callable, Collection, Hashable, Iterator, Mapping,
                    Sequence, cast, TYPE_CHECKING)

if TYPE_CHECKING:
    from icepool.expression.multiset_expression_base import MultisetExpressionBase, MultisetSourceBase, Dungeonlet, Questlet


class MultisetEvaluator(MultisetEvaluatorBase[T, U_co]):
    """Evaluates a multiset based on a state transition function."""

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

        States must be hashable. At current, they do not have to be orderable.
        However, this may change in the future, and if they are not totally
        orderable, you must override `final_outcome` to create totally orderable
        final outcomes.

        Returning a `Die` is not supported.

        Args:
            state: A hashable object indicating the state before rolling the
                current outcome. If `initial_state()` is not overridden, the
                initial state is `None`.
            order: The order in which outcomes are seen. You can raise an 
                `UnsupportedOrder` if you don't want to support the current 
                order. In this case, the opposite order will then be attempted
                (if it hasn't already been attempted).
            outcome: The current outcome.
                If there are multiple inputs, the set of outcomes is at 
                least the union of the outcomes of the invididual inputs. 
                You can use `extra_outcomes()` to add extra outcomes.
            *counts: One value (usually an `int`) for each input indicating how
                many of the current outcome were produced. You may replace this
                with a fixed series of parameters.

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

    def initial_state(self, order: Order, outcomes: Sequence[T], /, *sizes,
                      **kwargs: Hashable):
        """Optional method to produce an initial evaluation state.

        If not overriden, the initial state is `None`. Note that this is not a
        valid `final_outcome()`.

        All non-keyword arguments will be given positionally, so you are free
        to:
        * Rename any of them.
        * Replace `sizes` with a fixed series of arguments.
        * Replace trailing positional arguments with `*_` if you don't care
            about them.

        Args:
            order: The order in which outcomes will be seen by `next_state()`.
            outcomes: All outcomes that will be seen by `next_state()`.
            sizes: The sizes of the input multisets, provided
                that the multiset has inferrable size with non-negative
                counts. If not, the corresponding size is None.
            kwargs: Non-multiset arguments that were provided to `evaluate()`.
                You may replace `**kwargs` with a fixed set of keyword
                parameters; `final_outcome()` should take the same set of
                keyword parameters.

        Raises:
            UnsupportedOrder if the given order is not supported.
        """
        return None

    def final_outcome(
            self, final_state: Hashable, order: Order, outcomes: tuple[T, ...],
            /, *sizes, **kwargs: Hashable
    ) -> 'U_co | icepool.Die[U_co] | icepool.RerollType':
        """Optional method to generate a final output outcome from a final state.

        By default, the final outcome is equal to the final state.
        Note that `None` is not a valid outcome for a `Die`,
        and if there are no outcomes, `final_outcome` will be immediately
        be callled with `final_state=None`.
        Subclasses that want to handle this case should explicitly define what
        happens.

        All non-keyword arguments will be given positionally, so you are free
        to:
        * Rename any of them.
        * Replace `sizes` with a fixed series of arguments.
        * Replace trailing positional arguments with `*_` if you don't care
            about them.

        Args:
            final_state: A state after all outcomes have been processed.
            order: The order in which outcomes were seen by `next_state()`.
            outcomes: All outcomes that were seen by `next_state()`.
            sizes: The sizes of the input multisets, provided
                that the multiset has inferrable size with non-negative
                counts. If not, the corresponding size is None.
            kwargs: Non-multiset arguments that were provided to `evaluate()`.
                You may replace `**kwargs` with a fixed set of keyword
                parameters; `initial_state()` should take the same set of
                keyword parameters.

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

    @property
    def next_state_key(self) -> Hashable:
        """Subclasses may optionally provide a key that uniquely identifies the `next_state()` computation.

        This is used to persistently cache intermediate results between calls
        to `evaluate()`. By default, `next_state_key` is `None`, which only
        caches if not inside a `@multiset_function`.
        
        If you do implement this, `next_state_key` should include any members 
        used in `next_state()` but does NOT need to include members that are 
        only used in other methods, i.e. 
        * `extra_outcomes()`
        * `initial_state()`
        * `final_outcome()`.
        
        For example, if `next_state()` is a pure function other than being 
        defined by its evaluator class, you can use `type(self)`.

        If you want to disable caching between calls to `evaluate()` even
        outside of `@multiset_function`, return the special value 
        `icepool.NoCache`.
        """
        return None

    def _prepare(
        self,
        input_exps: tuple[MultisetExpressionBase[T, Any], ...],
        kwargs: Mapping[str, Hashable],
    ) -> Iterator[tuple['Dungeon[T]', 'Quest[T, U_co]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:

        for t in itertools.product(*(exp._prepare() for exp in input_exps)):
            if t:
                dungeonlet_flats, questlet_flats, sources, weights = zip(*t)
            else:
                dungeonlet_flats = ()
                questlet_flats = ()
                sources = ()
                weights = ()
            next_state_key: Hashable
            if self.next_state_key is None:
                # This should only get cached inside this evaluator, but add
                # self id to be safe.
                next_state_key = id(self)
                multiset_function_can_cache = False
            elif self.next_state_key is icepool.NoCache:
                next_state_key = icepool.NoCache
                multiset_function_can_cache = False
            else:
                next_state_key = self.next_state_key
                multiset_function_can_cache = True
            dungeon: MultisetEvaluatorDungeon[T] = MultisetEvaluatorDungeon(
                self.next_state, next_state_key, multiset_function_can_cache,
                dungeonlet_flats)
            quest: MultisetEvaluatorQuest[T, U_co] = MultisetEvaluatorQuest(
                self.initial_state, self.extra_outcomes, self.final_outcome,
                questlet_flats)
            sources = tuple(itertools.chain.from_iterable(sources))
            weight = math.prod(weights)
            yield dungeon, quest, sources, weight

    def _should_cache(self, dungeon: 'Dungeon[T]') -> bool:
        return dungeon.__hash__ is not None


class MultisetEvaluatorDungeon(Dungeon[T]):
    calls = ()

    # Will be filled in by constructor.
    next_state_main = None  # type: ignore

    def __init__(
            self, next_state_main: Callable[..., Hashable],
            next_state_key: Hashable, multiset_function_can_cache: bool,
            dungeonlet_flats: 'tuple[tuple[Dungeonlet[T, Any], ...], ...]'):
        self.next_state_main = next_state_main  # type: ignore
        self.next_state_key = next_state_key
        self._multiset_function_can_cache = multiset_function_can_cache
        self.dungeonlet_flats = dungeonlet_flats

        if next_state_key is icepool.NoCache:
            self.__hash__ = None  # type: ignore

    @property
    def hash_key(self):
        if self.__hash__ is None or self.next_state_key is None:
            return None
        return MultisetEvaluatorDungeon, self.dungeonlet_flats, self.next_state_key


class MultisetEvaluatorQuest(Quest[T, U_co]):
    calls = ()
    # These are filled in by the constructor.
    extra_outcomes = None  # type: ignore
    initial_state_main = None  # type: ignore
    final_outcome = None  # type: ignore

    def __init__(self, initial_state_main: Callable[..., Hashable],
                 extra_outcomes: Callable, final_outcome: Callable,
                 questlet_flats: 'tuple[tuple[Questlet[T, Any], ...], ...]'):
        self.extra_outcomes = extra_outcomes  # type: ignore
        self.initial_state_main = initial_state_main  # type: ignore
        self.final_outcome = final_outcome  # type: ignore
        self.questlet_flats = questlet_flats
