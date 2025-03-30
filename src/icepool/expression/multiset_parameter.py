__docformat__ = 'google'

from icepool.expression.multiset_expression_base import Q, Dungeonlet, MultisetExpressionBase, Questlet, MultisetSourceBase
from icepool.expression.multiset_tuple_expression import MultisetTupleExpression, IntTupleOut
from icepool.order import Order
from icepool.expression.multiset_expression import MultisetExpression

from typing import Any, Generic, Iterator, MutableSequence, Sequence

from icepool.typing import T


class MultisetParameterBase(Generic[T, Q]):
    _children: 'tuple[MultisetExpressionBase[T, Any], ...]' = ()
    _index: int
    _name: str

    def __str__(self) -> str:
        return self._name

    def _prepare(
        self
    ) -> Iterator[tuple['tuple[Dungeonlet[T, Any], ...]',
                        'tuple[Questlet[T, Any], ...]',
                        'tuple[MultisetSourceBase[T, Q], ...]', int]]:
        dungeonlet = MultisetParameterDungeonlet[T, Q](self._index)
        questlet = MultisetParameterQuestlet[T, Q](self._index)
        yield (dungeonlet, ), (questlet, ), (), 1

    @property
    def _has_param(self):
        return True

    @property
    def _static_keepable(self):
        return False

    @property
    def hash_key(self):
        return type(self), self._index


class MultisetParameter(MultisetParameterBase[T, int], MultisetExpression[T]):
    """A multiset param with a count of a single `int`."""

    def __init__(self, index: int, name: str):
        self._index = index
        self._name = name


class MultisetTupleParameter(MultisetParameterBase[T, IntTupleOut],
                             MultisetTupleExpression[T, IntTupleOut]):
    """A multiset param with a count of a tuple of `int`s."""

    def __init__(self, index: int, name: str, length: int):
        self._index = index
        self._name = name
        self._length = length

    def __len__(self):
        return self._length


class MultisetParameterDungeonlet(Dungeonlet[T, Q]):
    child_indexes = ()

    def __init__(self, index: int):
        self.index = index

    def next_state(self, state, order, outcome, child_counts, source_counts,
                   param_counts):
        return None, param_counts[self.index]

    @property
    def hash_key(self):
        return MultisetParameterDungeonlet, self.index


class MultisetParameterQuestlet(Questlet[T, Q]):
    child_indexes = ()

    def __init__(self, index: int):
        self.index = index

    def initial_state(self, order: Order, outcomes: Sequence[T],
                      child_sizes: MutableSequence, source_sizes: Iterator,
                      param_sizes: Sequence):
        return None, param_sizes[self.index]
