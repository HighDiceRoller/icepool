__docformat__ = 'google'

from abc import ABC, abstractmethod

from typing import Generator
from collections.abc import Sequence


class OutcomeCountGenerator(ABC):
    """Abstract base class for incrementally generating (outcome, count, weight)s.

    The archetypical example is a dice pool (`Pool`).
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
    ) -> Generator[tuple['OutcomeCountGenerator', int, int], None, None]:
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
    ) -> Generator[tuple['OutcomeCountGenerator', int, int], None, None]:
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
        """All `OutcomeCountGenerator`s must implement equality."""

    @abstractmethod
    def __hash__(self):
        """All `OutcomeCountGenerator`s must be hashable."""
