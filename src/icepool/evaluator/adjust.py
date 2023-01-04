"""Meta-evaluators that adjust counts or outcomes before sending them to an inner evaluator."""

__docformat__ = 'google'

from icepool.evaluator.outcome_count_evaluator import OutcomeCountEvaluator

import math
from collections import defaultdict

from icepool.typing import Outcome
from typing import Callable, Collection, Generic, Mapping, Set, TypeVar

T_contra = TypeVar('T_contra', bound=Outcome, contravariant=True)
"""Type variable representing the input outcome type."""

U_co = TypeVar('U_co', bound=Outcome, covariant=True)
"""Type variable representing the final outcome type."""

Q_contra = TypeVar('Q_contra', contravariant=True)
"""Type variable representing the count type. This may be replaced with a `TypeVarTuple` in the future."""

V = TypeVar('V', bound=Outcome)
"""Invariant intermediate outcome type."""


class AdjustIntCountEvaluator(OutcomeCountEvaluator[T_contra, U_co, int]):
    """Applies a standard set of possible adjustments to `int` counts."""

    _inner: OutcomeCountEvaluator[T_contra, U_co, int]
    _adjust_count: Callable[[T_contra, int], int]

    # May return inner unmodified.
    def __new__(  # type: ignore
        cls,
        inner: OutcomeCountEvaluator[T_contra, U_co, int],
        target: Mapping[Outcome, int] | Set[Outcome] | Collection[Outcome] |
        None = None,
        *,
        invert: bool = False,
        min_count: int | None = None,
        div_count: int | None = None,
        max_count: int |
        None = None) -> OutcomeCountEvaluator[T_contra, U_co, int]:
        """Constructor. This wraps an inner evaluator.

        May return inner unmodified.

        The args are applied in the order presented above and below.

        Args:
            inner: The evaluator to call after adjustment.
            target: If provided, an intersection or difference will be taken
                with this. Possible types:
                * A `Mapping` from outcomes to `int`s, representing a multiset
                    with counts as the values.
                * A `Set` of outcomes. All outcomes in the target effectively
                    have unlimited multiplicity.
                * Any other `Collection`, which will be treated as a multiset.
            invert: If `False` (default), the intersection will be taken with
                `target`. Otherwise, the difference will be taken. If `target`
                is not provided, this value is ignored.
            min_count: If provided, any outcome with less than this count will
                produce a 0 count. For example, `min_count=2` will ignore
                anything that's not a matching pair or better.
            div_count: If provided, counts will be divided by this value
                (rounding down). For example, `floordiv=2` will count the number
                of matching pairs.
            max_count: Any outcome with greater than this count will be treated
                as having this count. For example, `max_count=1` will count
                duplicates only once.

                `max_count` can be less than `min_count`. For example,
                `min_count=2, max_count=1` will count outcomes that are pairs
                or better, but only contributing a count of 1 per pair.
        """
        if target is None and min_count is None and div_count is None and max_count is None:
            return inner

        self = super(AdjustIntCountEvaluator, cls).__new__(cls)

        self._inner = inner

        if target is None:
            invert = True
            target_dict = {}
        elif isinstance(target, Mapping):
            target_dict = {k: v for k, v in target.items()}
        elif isinstance(target, Set):
            target_dict = {k: math.inf for k in target}
        else:
            target_dict = defaultdict(int)
            for outcome in target:
                target_dict[outcome] += 1

        def adjust_count(outcome: T_contra, count: int) -> int:
            """Adjusts the count based on arguments to a constructed TargetSetEvaluator."""
            if invert:
                # Set difference.
                count = max(count - target_dict.get(outcome, 0), 0)
            else:
                # Set intersection.
                count = min(count, target_dict.get(outcome, 0))
            if min_count is not None and count < min_count:
                return 0
            if div_count is not None:
                count //= div_count
            if max_count is not None:
                count = min(count, max_count)
            return count

        self._adjust_count = adjust_count

        return self

    def next_state(self, state, outcome, count):
        """Adjust the count, then forwards to inner."""
        count = self._adjust_count(outcome, count)
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


class FinalOutcomeMapEvaluator(Generic[T_contra, U_co, Q_contra, V],
                               OutcomeCountEvaluator[T_contra, U_co, Q_contra]):
    """Maps outcomes to other outcomes before sending them to an inner evaluator.

    Note that the outcomes will be seen in their original order, and outcomes
    that map to the same value will still be considered in separate calls to
    `next_state`. For this reason it's best to nest it inside
    `AdjustIntCountEvaluator`, and the `map` argument should be presented last.
    """

    _inner: OutcomeCountEvaluator[V, U_co, Q_contra]
    _map: Callable[[T_contra], V]

    # May return inner unmodified.
    def __new__(  # type: ignore
        cls,
        inner: OutcomeCountEvaluator[V, U_co, Q_contra],
        map: Callable[[T_contra], V] | Mapping[T_contra, V] | None = None
    ) -> OutcomeCountEvaluator[T_contra, U_co, Q_contra]:
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
