"""Meta-evaluators that adjust counts or outcomes before sending them to an inner evaluator."""

__docformat__ = 'google'

from icepool.evaluator.outcome_count_evaluator import OutcomeCountEvaluator

from icepool.typing import Outcome
from typing import Callable, Generic, Mapping, TypeVar

T_contra = TypeVar('T_contra', bound=Outcome, contravariant=True)
"""Type variable representing the input outcome type."""

U_co = TypeVar('U_co', bound=Outcome, covariant=True)
"""Type variable representing the final outcome type."""

Q_contra = TypeVar('Q_contra', contravariant=True)
"""Type variable representing the count type. This may be replaced with a `TypeVarTuple` in the future."""

V = TypeVar('V', bound=Outcome)
"""Invariant intermediate outcome type."""


class FinalOutcomeMapEvaluator(Generic[T_contra, V, Q_contra, U_co],
                               OutcomeCountEvaluator[T_contra, Q_contra, U_co]):
    """Maps outcomes to other outcomes before sending them to an inner evaluator.

    Note that the outcomes will be seen in their original order, and outcomes
    that map to the same value will still be considered in separate calls to
    `next_state`. For this reason it's best to nest it inside
    `AdjustIntCountEvaluator`, and the `map` argument should be presented last.
    """

    _inner: OutcomeCountEvaluator[V, Q_contra, U_co]
    _map: Callable[[T_contra], V]

    # May return inner unmodified.
    def __new__(  # type: ignore
        cls,
        inner: OutcomeCountEvaluator[V, Q_contra, U_co],
        map: Callable[[T_contra], V] | Mapping[T_contra, V] | None = None
    ) -> OutcomeCountEvaluator[T_contra, Q_contra, U_co]:
        """Constructor. This wraps an inner evaluator.

        May return inner unmodified.

        Args:
            inner: The evaluator to wrap.
            map: A `Callable` or `Mapping` that takes an original outcome and
                produces the outcome that should be sent to the inner evaluator.
        """
        if map is None or (not callable(map) and len(map) == 0):
            # Here V = T_contra.
            return inner  # type: ignore

        self = super(FinalOutcomeMapEvaluator, cls).__new__(cls)

        self._inner = inner
        if callable(map):
            self._map = map
        else:
            map_dict = {k: v for k, v in map.items()}

            def map_func(outcome: T_contra) -> V:
                return map_dict[outcome]

        self._map = map_func

        return self

    def next_state(self, state, outcome, count):
        """Adjusts the outcome, then forwards to inner."""
        outcome = self._map(outcome)
        return self._inner.next_state(state, outcome, count)

    def final_outcome(self, final_state, *generators):
        """Forwards to inner."""
        return self._inner.final_outcome(final_state, *generators)

    def order(self, *generators):
        """Forwards to inner."""
        return self._inner.order(*generators)

    def alignment(self, *generators):
        """Forwards to inner."""
        return self._inner.alignment(*generators)
