__docformat__ = 'google'

from icepool.expression.multiset_expression import MultisetExpression
from icepool.operator.multiset_operator import MultisetOperator

import operator
from abc import abstractmethod

from typing import Callable, Iterator, Literal, MutableSequence, Sequence
from icepool.typing import T


class MultisetMapCounts(MultisetOperator[T]):
    """Maps outcomes and counts to new counts."""

    _function: Callable[..., int]

    def __init__(self, *children: MultisetExpression[T],
                 function: Callable[..., int]) -> None:
        """Constructor.

        Args:
            children: The children expression(s).
            function: A function that takes `outcome, *counts` and produces a
                combined count.
        """
        self._children = children
        self._function = function

    def _next_state(self, state, order, outcome, child_counts, source_counts,
                    arg_counts):
        count = self._function(outcome, *child_counts)
        return None, count

    @property
    def _expression_key(self):
        return type(self), self._function


class MultisetCountOperator(MultisetOperator[T]):

    def __init__(self, child: MultisetExpression[T], /, *,
                 constant: int) -> None:
        self._children = (child, )
        self._constant = constant

    @abstractmethod
    def operator(self, count: int) -> int:
        """Operation to apply to the counts."""

    def _next_state(self, state, order, outcome, child_counts, source_counts,
                    arg_counts):
        count = self.operator(child_counts[0])
        return None, count

    @property
    def _expression_key(self):
        return type(self), self._constant


class MultisetMultiplyCounts(MultisetCountOperator):
    """Multiplies all counts by the constant."""

    def operator(self, count: int) -> int:
        return count * self._constant

    def __str__(self) -> str:
        return f'({self._children[0]} * {self._constant})'

    def _initial_state(self, order, outcomes, child_sizes: Sequence,
                       source_sizes: Iterator, arg_sizes: Sequence):
        child_size = child_sizes[0]
        if child_size is None:
            return None, None
        else:
            return None, child_sizes[0] * self._constant


class MultisetFloordivCounts(MultisetCountOperator):
    """Divides all counts by the constant, rounding down."""

    def operator(self, count: int) -> int:
        return count // self._constant

    def __str__(self) -> str:
        return f'({self._children[0]} // {self._constant})'


class MultisetModuloCounts(MultisetCountOperator):
    """Modulo all counts by the constant."""

    def operator(self, count: int) -> int:
        return count % self._constant

    def __str__(self) -> str:
        return f'({self._children[0]} % {self._constant})'


class MultisetUnique(MultisetCountOperator):
    """Limits the count produced by each outcome."""

    def operator(self, count: int) -> int:
        return min(count, self._constant)

    def __str__(self) -> str:
        if self._constant == 1:
            return f'{self._children[0]}.unique()'
        else:
            return f'{self._children[0]}.unique({self._constant})'


class MultisetKeepCounts(MultisetOperator[T]):

    def __init__(self, child: MultisetExpression[T], /, *,
                 comparison: Literal['==', '!=', '<=', '<', '>=',
                                     '>'], constant: int):
        self._children = (child, )
        self._constant = constant
        operators = {
            '==': operator.eq,
            '!=': operator.ne,
            '<=': operator.le,
            '<': operator.lt,
            '>=': operator.ge,
            '>': operator.gt,
        }
        if comparison not in operators:
            raise ValueError(f'Invalid comparison {comparison}')
        self._comparison = comparison
        self._op = operators[comparison]

    def _next_state(self, state, order, outcome, child_counts, source_counts,
                    arg_counts):
        if self._op(child_counts[0], self._constant):
            count = child_counts[0]
        else:
            count = 0
        return None, count

    @property
    def _expression_key(self):
        return type(self), self._comparison, self._constant

    def __str__(self) -> str:
        return f"{self._children[0]}.keep_counts('{self._comparison}', {self._constant})"
