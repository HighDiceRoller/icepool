__docformat__ = 'google'

from icepool.order import Order, OrderReason
from abc import abstractmethod

from icepool.typing import T, MaybeHashKeyed
from typing import (TYPE_CHECKING, Any, Callable, Generic, Hashable, Iterator,
                    MutableSequence, NamedTuple, Sequence, Type, TypeVar)

if TYPE_CHECKING:
    from icepool.expression.multiset_parameter import MultisetParameterBase

Q = TypeVar('Q')
"""The type of count emitted by a MultisetExpression."""


class MultisetExpressionBase(Generic[T, Q], MaybeHashKeyed):
    """Abstract methods are protected so as to not be distracting."""

    @abstractmethod
    def _prepare(
        self
    ) -> Iterator[tuple['tuple[Dungeonlet[T, Any], ...]',
                        'tuple[Questlet[T, Any], ...]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        """Prepare for evaluation.

        Yields:
            dungeonlet_flat, questlet_flat, sources, weight
        """

    @property
    @abstractmethod
    def _has_parameter(self) -> bool:
        """Whether this expression tree contains any parameter."""

    @abstractmethod
    def _make_param(
            self,
            name: str,
            arg_index: int,
            star_index: int | None = None) -> 'MultisetParameterBase[T, Any]':
        """Creates a parameter corresponding to the output of this expression.
        
        This is used to determine the input types to multiset functions.

        Args:
            name: The name of the parameter, taken from the function definition.
            index: The index of the argument which is passed to this parameter.
                In the case of starring this may be different than the
                parameter index.
            star_index: If provided, the argument will be subscripted before
                sending its value to the parameter.
        """

    @property
    @abstractmethod
    def _static_keepable(self) -> bool:
        """Whether this expression supports keep operations via static analysis."""


class Dungeonlet(Generic[T, Q], MaybeHashKeyed):
    child_indexes: tuple[int, ...]
    """The relative (therefore negative) indexes of this node's children."""

    @abstractmethod
    def next_state(self, state: Hashable, order: Order, outcome: T,
                   child_counts: Sequence, source_counts: Iterator,
                   arg_counts: Sequence) -> tuple[Hashable, Q]:
        """Advances the state of this dungeonlet.
        
        Args:
            state: The local state.
            order: The order in which outcomes are seen by this method.
            outcome: The current outcome.
            child_counts: The counts of the child nodes.
            source_counts: The counts produced by sources.
                This is an iterator which will be progressively consumed by
                free variables.
            arg_counts: The counts produced by args.

        Returns:
            The next local state and the count produced by this node.

        Raises:
            UnsupportedOrder if the order is not supported.
        """


class BodyDungeonlet(Dungeonlet[T, Q]):
    """A dungeonlet from the body of an expression, i.e. not originating from a generator or parameter."""
    # Will be filled in by the constructor.
    next_state = None  # type: ignore

    def __init__(self, next_state: Callable, hash_key: Hashable,
                 child_indexes: tuple[int, ...]):
        self.next_state = next_state  # type: ignore
        self._hash_key = (hash_key, child_indexes)
        self.child_indexes = child_indexes

    @property
    def hash_key(self):
        return self._hash_key


class MultisetFreeVariable(Dungeonlet[T, Q]):
    """A dungeonlet left behind in place of a freed source."""
    child_indexes = ()

    def next_state(self, state, order, outcome, child_counts, source_counts,
                   arg_counts):
        return None, next(source_counts)

    @property
    def hash_key(self):
        return MultisetFreeVariable


class MultisetSourceBase(Generic[T, Q], MaybeHashKeyed):

    @abstractmethod
    def outcomes(self) -> tuple[T, ...]:
        """The possible outcomes that could be generated, in ascending order."""

    @abstractmethod
    def size(self) -> Q | None:
        """The total number of elements output by this source, if only non-negative counts are output.
        
        If total number of elements is not constant or unknown, or if there
        could be negative counts, the result is `None`.
        """

    @abstractmethod
    def pop(self, order: Order,
            outcome: T) -> Iterator[tuple['MultisetSourceBase', Q, int]]:
        """
        Args:
            order: The order in which the pop occurs.
            outcome: The outcome to pop.
        
        Yields:
            * This source with the outcome popped.
            * The count of that outcome.
            * The weight for this many of the outcome appearing.

            If the argument does not match the outcome for the given order,
            the result is:

            * `self`
            * Zero count.
            * weight = 1.
        """

    @abstractmethod
    def order_preference(self) -> tuple[Order, OrderReason]:
        """The preferred order of this source and a reason why the order is preferred."""

    @abstractmethod
    def is_resolvable(self) -> bool:
        """Whether this source contains any probability."""

    def min_outcome(self) -> T:
        return self.outcomes()[0]

    def max_outcome(self) -> T:
        return self.outcomes()[-1]


class Questlet(Generic[T, Q]):
    child_indexes: tuple[int, ...]
    """The relative (therefore negative) indexes of this node's children."""

    @abstractmethod
    def initial_state(self, order: Order, outcomes: Sequence[T],
                      child_sizes: Sequence, source_sizes: Iterator,
                      arg_sizes: Sequence) -> tuple[Hashable, Q | None]:
        """Optional: the initial state of this node.

        Args:
            order: The order in which `next_state` will see outcomes.
            outcomes: All outcomes that will be seen by `next_state` in ascending order.
            child_counts: The sizes of the child nodes.
            source_counts: The sizes produced by sources.
                This is an iterator which will be progressively consumed by
                free variables.
            arg_sizes: The sizes produced by args.

        Returns:
            The initial state, and the size of this node.

        Raises:
            UnsupportedOrder if the given order is not supported.
        """


class BodyQuestlet(Questlet[T, Q]):
    """A questlet from the body of an expression, i.e. not originating from a generator or parameter."""
    # Will be filled in by the constructor.
    initial_state = None  # type: ignore

    def __init__(self, initial_state: Callable, child_indexes: tuple[int,
                                                                     ...]):
        self.initial_state = initial_state  # type: ignore
        self.child_indexes = child_indexes


class DungeonletCallTree(Generic[T], NamedTuple):
    flats: 'tuple[tuple[Dungeonlet[T, Any], ...], ...]'
    calls: 'tuple[DungeonletCallTree, ...]'

    def next_state(self, statelet_tree: 'StateletCallTree', order: Order,
                   outcome: T, source_counts: Iterator,
                   arg_counts: Sequence) -> 'tuple[StateletCallTree, tuple]':
        """Advances the statelet tree for this call tree.

        Args:
            order: The order in which the evaluation will see outcomes.
            source_counts: The count from each source, which will be consumed in
                traversal order.
            arg_counts: The counts of the args to this call.

        Returns:
            An next statelet call tree, and a arg count call tree.
            Each node in the latter is either a non-leaf node corresponding to
            a multiset function, in which case it is a tuple of subtrees,
            or it is a leaf node corresponding to a final evaluation, in which
            case it is the actual arg counts to that evaluation.
        """
        next_flats = []
        output_counts: MutableSequence = []
        for dungeonlets, statelets in zip(self.flats, statelet_tree.flats):
            next_statelets = []
            countlets: MutableSequence = []
            for dungeonlet, statelet in zip(dungeonlets, statelets):
                child_counts = [countlets[i] for i in dungeonlet.child_indexes]
                next_statelet, countlet = dungeonlet.next_state(
                    statelet, order, outcome, child_counts, source_counts,
                    arg_counts)
                next_statelets.append(next_statelet)
                countlets.append(countlet)
            next_flats.append(tuple(next_statelets))
            output_counts.append(countlets[-1])
        if self.calls:
            next_statelet_calls = []
            countlet_calls = []
            for call_dungeonlet_tree, call_statelet_tree in zip(
                    self.calls, statelet_tree.calls):
                next_call_statelet_tree, call_countlet_tree = call_dungeonlet_tree.next_state(
                    call_statelet_tree, order, outcome, source_counts,
                    output_counts)
                next_statelet_calls.append(next_call_statelet_tree)
                countlet_calls.append(call_countlet_tree)
            next_statelet_tree = StateletCallTree(tuple(next_flats),
                                                  tuple(next_statelet_calls))
            count_tree = tuple(countlet_calls)
        else:
            next_statelet_tree = StateletCallTree(tuple(next_flats), ())
            count_tree = tuple(output_counts)
        return next_statelet_tree, count_tree


class StateletCallTree(NamedTuple):
    flats: 'tuple[tuple[Hashable, ...], ...]'
    calls: 'tuple[StateletCallTree, ...]'


class QuestletCallTree(Generic[T], NamedTuple):
    flats: 'tuple[tuple[Questlet[T, Any], ...], ...]'
    calls: 'tuple[QuestletCallTree, ...]'

    def initial_state(self, order: Order, outcomes: tuple[T, ...],
                      source_sizes: Iterator,
                      arg_sizes: Sequence) -> 'tuple[StateletCallTree, tuple]':
        """Generates the initial statelet tree for this call tree.

        Args:
            order: The order in which the evaluation will see outcomes.
            source_sizes: The size of each source, which will be consumed in
                traversal order.
            arg_sizes: The sizes of the args to this call.

        Returns:
            An initial statelet call tree, and a arg size call tree.
            Each node in the latter is either a non-leaf node corresponding to
            a multiset function, in which case it is a tuple of subtrees,
            or it is a leaf node corresponding to a final evaluation, in which
            case it is the actual arg sizes to that evaluation.
        """
        statelet_flats = []
        output_sizes: MutableSequence = []
        for questlets in self.flats:
            statelets = []
            countlets: MutableSequence = []
            for questlet in questlets:
                child_sizes = [countlets[i] for i in questlet.child_indexes]
                next_statelet, countlet = questlet.initial_state(
                    order, outcomes, child_sizes, source_sizes, arg_sizes)
                statelets.append(next_statelet)
                countlets.append(countlet)
            statelet_flats.append(tuple(statelets))
            output_sizes.append(countlets[-1])
        if self.calls:
            statelet_calls = []
            countlet_calls = []
            for call_questlet_tree in self.calls:
                call_statelet_flats, call_countlet = call_questlet_tree.initial_state(
                    order, outcomes, source_sizes, output_sizes)
                statelet_calls.append(call_statelet_flats)
                countlet_calls.append(call_countlet)
            statelet_tree = StateletCallTree(tuple(statelet_flats),
                                             tuple(statelet_calls))
            countlet_tree = tuple(countlet_calls)
        else:
            statelet_tree = StateletCallTree(tuple(statelet_flats), ())
            countlet_tree = tuple(output_sizes)
        return statelet_tree, countlet_tree
