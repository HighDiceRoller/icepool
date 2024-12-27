__docformat__ = 'google'

import icepool
from icepool.multiset_expression import MultisetExpression, InitialMultisetGeneration, PopMultisetGeneration, MultisetArityError

import itertools
import math

from icepool.typing import T
from typing import Sequence

from abc import abstractmethod


class MultisetOperator(MultisetExpression[T]):
    """Internal node of an expression taking one or more counts and producing a single count."""

    @abstractmethod
    def _copy(
        self, new_children: 'tuple[MultisetExpression[T], ...]'
    ) -> 'MultisetExpression[T]':
        """Creates a copy of self with the given children.
        
        I considered using `copy.copy` but this doesn't play well with
        incidental members such as in `@cached_property`.
        """

    @abstractmethod
    def _transform_next(
            self, new_children: 'tuple[MultisetExpression[T], ...]',
            outcome: T,
            counts: 'tuple[int, ...]') -> 'tuple[MultisetExpression[T], int]':
        """Produce the next state of this expression.

        Args:
            new_children: The children of the result are to be set to this.
            outcome: The outcome being processed.
            counts: One count per child.

        Returns:
            An expression representing the next state and the count produced by
            this expression.

        Raises:
            UnboundMultisetExpressionError if this is called on an expression
            with free variables.
        """

    def outcomes(self) -> Sequence[T]:
        return icepool.sorted_union(*(child.outcomes()
                                      for child in self._children))

    def output_arity(self) -> int:
        """Operators only output 1 count.

        Each input to `MultisetOperator` must only output 1 count as well.

        For multiple outputs, use @multiset_function.
        """
        if any(child.output_arity() != 1 for child in self._children):
            raise MultisetArityError(
                'Each input to MultisetOperator must output exactly 1 count.')
        return 1

    def _is_resolvable(self) -> bool:
        return all(child._is_resolvable() for child in self._children)

    def _generate_initial(self) -> InitialMultisetGeneration:
        for t in itertools.product(*(child._generate_initial()
                                     for child in self._children)):
            new_children, weights = zip(*t)
            next_self = self._copy(new_children)
            yield next_self, math.prod(weights)

    def _generate_min(self, min_outcome: T) -> PopMultisetGeneration:
        for t in itertools.product(*(child._generate_min(min_outcome)
                                     for child in self._children)):
            new_children, counts, weights = zip(*t)
            counts = tuple(c[0] for c in counts)
            next_self, count = self._transform_next(new_children, min_outcome,
                                                    counts)
            yield next_self, (count, ), math.prod(weights)

    def _generate_max(self, max_outcome: T) -> PopMultisetGeneration:
        for t in itertools.product(*(child._generate_max(max_outcome)
                                     for child in self._children)):
            new_children, counts, weights = zip(*t)
            counts = tuple(c[0] for c in counts)
            next_self, count = self._transform_next(new_children, max_outcome,
                                                    counts)
            yield next_self, (count, ), math.prod(weights)

    def has_free_variables(self) -> bool:
        return any(child.has_free_variables() for child in self._children)

    def denominator(self) -> int:
        return math.prod(child.denominator() for child in self._children)

    def _unbind(
            self,
            bound_inputs: 'list[MultisetExpression]' = []
    ) -> 'MultisetExpression':
        if self.has_free_variables():
            unbound_children = tuple(
                child._unbind(bound_inputs) for child in self._children)
            return self._copy(unbound_children)
        else:
            result = icepool.MultisetVariable(False, len(bound_inputs))
            bound_inputs.append(self)
            return result

    def _apply_variables(
            self, outcome: T, bound_counts: tuple[int, ...],
            free_counts: tuple[int,
                               ...]) -> 'tuple[MultisetExpression[T], int]':
        new_children, counts = zip(
            *(child._apply_variables(outcome, bound_counts, free_counts)
              for child in self._children))
        return self._transform_next(new_children, outcome, counts)
