__docformat__ = 'google'

import icepool

from abc import ABC, abstractmethod

from typing import Callable, Generator, Sequence, TypeAlias, TypeVar

GenGenerator: TypeAlias = Generator[tuple['OutcomeGroupGenerator',
                                          Sequence[int], int], None, None]
"""The generator type returned by `_gen_min` and `_gen_max`."""


class OutcomeGroupGenerator(ABC):
    """Abstract base class for incrementally generating `(outcome, counts, weight)`s.

    These include dice pools (`Pool`) and card decks (`Deck`).
    """

    @abstractmethod
    def outcomes(self) -> Sequence:
        """The set of possible outcomes, in sorted order."""

    @abstractmethod
    def _is_resolvable(self) -> bool:
        """Returns `True` iff the generator is capable of producing an overall outcome.

        For example, a dice pool will return `False` if it contains any dice
        with no outcomes.
        """

    @abstractmethod
    def _gen_min(self, min_outcome) -> GenGenerator:
        """Pops the min outcome from this generator if it matches the argument.

        Yields:
            A generator with the min outcome popped.
            A tuple of counts for the min outcome.
            The weight for this many of the min outcome appearing.

            If the argument does not match the min outcome, or this generator
            has no outcomes, only the single tuple `(self, 0, 1)` is yielded.
        """

    @abstractmethod
    def _gen_max(self, max_outcome) -> GenGenerator:
        """Pops the max outcome from this generator if it matches the argument.

        Yields:
            A generator with the max outcome popped.
            A tuple of counts for the max outcome.
            The weight for this many of the max outcome appearing.

            If the argument does not match the max outcome, or this generator
            has no outcomes, only the single tuple `(self, 0, 1)` is yielded.
        """

    @abstractmethod
    def _estimate_direction_costs(self) -> tuple[int, int]:
        """Estimates the cost of popping from the min and max sides during an evaluation.

        Returns:
            pop_min_cost: A positive `int`.
            pop_max_cost: A positive `int`.
        """

    @abstractmethod
    def denominator(self) -> int:
        """The total weight of all paths through this gen."""

    @abstractmethod
    def __eq__(self, other) -> bool:
        """All `OutcomeGroupGenerator`s must implement equality."""

    @abstractmethod
    def __hash__(self) -> int:
        """All `OutcomeGroupGenerator`s must be hashable."""

    def eval(self, eval_or_func: 'icepool.OutcomeGroupEvaluator' | Callable,
             /) -> 'icepool.Die':
        """Evaluates this gen using the given `OutcomeGroupEval` or function.

        Note that each `OutcomeGroupEval` instance carries its own cache;
        if you plan to use an evaluation multiple times,
        you may want to explicitly create an `OutcomeGroupEval` instance
        rather than passing a function to this method directly.

        Args:
            func: This can be an `OutcomeGroupEval`, in which case it evaluates
                the gen directly. Or it can be a `OutcomeGroupEval.next_state()`
                -like function, taking in `state, outcome, *counts` and
                returning the next state. In this case a temporary `WrapFuncEval`
                is constructed and used to evaluate this gen.
        """
        if not isinstance(eval_or_func, icepool.OutcomeGroupEvaluator):
            eval_or_func = icepool.WrapFuncEval(eval_or_func)
        return eval_or_func.eval(self)

    def min_outcome(self):
        return self.outcomes()[0]

    def max_outcome(self):
        return self.outcomes()[-1]

    def sum(self) -> 'icepool.Die':
        """Convenience method to simply sum the dice in this gen.

        This uses `icepool.sum_pool`.

        Returns:
            A die representing the sum.
        """
        return icepool.sum_gen(self)
