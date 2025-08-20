__docformat__ = 'google'

from icepool.expression.multiset_expression_base import Q, Dungeonlet, MultisetExpressionBase, Questlet, MultisetSourceBase
from icepool.expression.multiset_tuple_expression import MultisetTupleExpression, IntTupleOut
from icepool.order import Order
from icepool.expression.multiset_expression import MultisetExpression

from typing import Any, Generic, Iterator, MutableSequence, Sequence

from icepool.typing import T


class MultisetParameterBase(Generic[T, Q]):
    _children: 'tuple[MultisetExpressionBase[T, Any], ...]' = ()

    _name: str
    _arg_index: int
    _star_index: int | None

    def __str__(self) -> str:
        return self._name

    def _prepare(
        self
    ) -> Iterator[tuple['tuple[Dungeonlet[T, Any], ...]',
                        'tuple[Questlet[T, Any], ...]',
                        'tuple[MultisetSourceBase[T, Q], ...]', int]]:
        dungeonlet = MultisetParameterDungeonlet[T, Q](self._arg_index,
                                                       self._star_index)
        questlet = MultisetParameterQuestlet[T, Q](self._arg_index,
                                                   self._star_index)
        yield (dungeonlet, ), (questlet, ), (), 1

    @property
    def _has_parameter(self):
        return True

    @property
    def _static_keepable(self):
        return False

    @property
    def hash_key(self):
        return type(self), self._arg_index, self._star_index


class MultisetParameter(MultisetParameterBase[T, int], MultisetExpression[T]):
    """A multiset parameter with a count of a single `int`."""

    def __init__(self, name: str, arg_index: int, star_index: int | None):
        self._name = name
        self._arg_index = arg_index
        self._star_index = star_index


class MultisetTupleParameter(MultisetParameterBase[T, IntTupleOut],
                             MultisetTupleExpression[T, IntTupleOut]):
    """A multiset parameter with a count of a tuple of `int`s."""

    def __init__(self, name: str, arg_index: int, length: int):
        self._name = name
        self._arg_index = arg_index
        self._star_index = None
        self._length = length

    def __len__(self):
        return self._length


class MultisetParameterDungeonlet(Dungeonlet[T, Q]):
    child_indexes = ()

    def __init__(self, arg_index: int, star_index: int | None):
        self.arg_index = arg_index
        self.star_index = star_index

    def next_state(self, state, order, outcome, child_counts, source_counts,
                   arg_sizes):
        if self.star_index is None:
            return None, arg_sizes[self.arg_index]
        else:
            return None, arg_sizes[self.arg_index][self.star_index]

    @property
    def hash_key(self):
        return type(self), self.arg_index, self.star_index


class MultisetParameterQuestlet(Questlet[T, Q]):
    child_indexes = ()

    def __init__(self, index: int, star_index: int | None):
        self.arg_index = index
        self.star_index = star_index

    def initial_state(self, order: Order, outcomes: Sequence[T],
                      child_sizes: Sequence, source_sizes: Iterator,
                      arg_sizes: Sequence):
        if self.star_index is None:
            return None, arg_sizes[self.arg_index]
        else:
            return None, arg_sizes[self.arg_index][self.star_index]
