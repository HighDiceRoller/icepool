__docformat__ = 'google'

from functools import cached_property


class EvalPoolAlignment():
    """Internal class for managing `EvalPool` alignment.

    The interface is similar but not identical to `Pool`.

    We can't use the actual `Pool` class since it is permitted to skip 0-count
    outcomes.
    """

    def __init__(self, outcomes):
        self._outcomes = tuple(sorted(outcomes))

    def is_empty(self) -> bool:
        return len(self._outcomes) == 0

    def min_outcome(self):
        return self._outcomes[0]

    def max_outcome(self):
        return self._outcomes[-1]

    def _pop_min(self, min_outcome) -> 'EvalPoolAlignment':
        """Unlike the `Pool` version, this only returns another EvalPoolAlignment."""
        if self.is_empty() or min_outcome != self.min_outcome():
            return self
        else:
            return EvalPoolAlignment(self._outcomes[1:])

    def _pop_max(self, max_outcome) -> 'EvalPoolAlignment':
        """Unlike the `Pool` version, this only returns another EvalPoolAlignment."""
        if self.is_empty() or max_outcome != self.max_outcome():
            return self
        else:
            return EvalPoolAlignment(self._outcomes[:-1])

    def __eq__(self, other) -> bool:
        if not isinstance(other, EvalPoolAlignment):
            return False
        return self._outcomes == other._outcomes

    @cached_property
    def _hash(self) -> int:
        return hash(self._outcomes)

    def __hash__(self) -> int:
        return self._hash
