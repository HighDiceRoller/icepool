__docformat__ = 'google'

import icepool

from abc import ABC, abstractmethod

from typing import Callable, Generator
from collections.abc import Sequence


class OutcomeCountGen(ABC):
    """Abstract base class for incrementally generating (outcome, count, weight)s.

    These include dice pools (`Pool`) and card decks (`Deck`).
    """

    @abstractmethod
    def outcomes(self) -> Sequence:
        """The set of possible outcomes, in sorted order."""

    def min_outcome(self):
        return self.outcomes()[0]

    def max_outcome(self):
        return self.outcomes()[-1]

    @abstractmethod
    def _is_resolvable(self) -> bool:
        """Returns `True` iff the generator is capable of producing an overall outcome.

        For example, a dice pool will return `False` if it contains any dice
        with no outcomes.
        """

    @abstractmethod
    def _pop_min(
        self, min_outcome
    ) -> Generator[tuple['OutcomeCountGen', int, int], None, None]:
        """Pops the min outcome from this generator if it matches the argument.

        Yields:
            A generator with the min outcome popped.
            The count for the min outcome.
            The weight for this many of the min outcome appearing.

            If the argument does not match the min outcome, or this generator
            has no outcomes, only the single tuple `(self, 0, 1)` is yielded.
        """

    @abstractmethod
    def _pop_max(
        self, max_outcome
    ) -> Generator[tuple['OutcomeCountGen', int, int], None, None]:
        """Pops the max outcome from this generator if it matches the argument.

        Yields:
            A generator with the max outcome popped.
            The count for the max outcome.
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
    def __eq__(self, other):
        """All `OutcomeCountGen`s must implement equality."""

    @abstractmethod
    def __hash__(self):
        """All `OutcomeCountGen`s must be hashable."""

    def eval(self, eval_or_func: 'icepool.OutcomeCountEval' | Callable,
             /) -> 'icepool.Die':
        """Evaluates this gen using the given `OutcomeCountEval` or function.

        Note that each `OutcomeCountEval` instance carries its own cache;
        if you plan to use an evaluation multiple times,
        you may want to explicitly create an `OutcomeCountEval` instance
        rather than passing a function to this method directly.

        Args:
            func: This can be an `OutcomeCountEval`, in which case it evaluates
                the gen directly. Or it can be a `OutcomeCountEval.next_state()`
                -like function, taking in `state, outcome, *counts` and
                returning the next state. In this case a temporary `WrapFuncEval`
                is constructed and used to evaluate this gen.
        """
        if not isinstance(eval_or_func, icepool.OutcomeCountEval):
            eval_or_func = icepool.WrapFuncEval(eval_or_func)
        return eval_or_func.eval(self)

    def sum(self) -> 'icepool.Die':
        """Convenience method to simply sum the dice in this gen.

        This uses `icepool.sum_pool`.

        Returns:
            A die representing the sum.
        """
        return icepool.sum_gen(self)
