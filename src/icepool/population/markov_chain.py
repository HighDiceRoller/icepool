import icepool
from icepool.typing import Outcome, T

import enum
import math
from collections import defaultdict

from typing import Callable, MutableMapping


class SpecialValue(enum.Enum):
    Visit = 'Visit'


Visit = SpecialValue.Visit
"""Special value for indicating the numerator of the number of visits to a
particular state."""


class SparseVector(MutableMapping[T, int]):
    """Internal helper class for representing vectors as a sparse mapping.

    Unlike public objects, this class is mutable.
    """

    def __init__(self):
        self._data = {}

    def __setitem__(self, key, value: int):
        if value == 0:
            if key in self._data:
                del self._data[key]
        else:
            self._data[key] = value

    def __getitem__(self, key) -> int:
        return self._data.get(key, 0)

    def __delitem__(self, key):
        del self._data[key]

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __mul__(self, n: int) -> 'SparseVector[T]':
        result: SparseVector[T] = SparseVector()
        result._data = {k: v * n for k, v in self.items()}
        return result

    def __rmul__(self, n: int) -> 'SparseVector':
        return self.__mul__(n)

    def __sub__(self, other: 'SparseVector') -> 'SparseVector[T]':
        result: SparseVector[T] = SparseVector()
        result._data = self._data.copy()
        for k, v in other.items():
            result[k] -= v
        return result

    def simplify(self):
        """Simplifies this vector (using mutation)."""
        divisor = math.gcd(*self.values())
        for k in self:
            self[k] //= divisor

    def __str__(self) -> str:
        return str(self._data)


def is_absorbing(outcome, next_outcome) -> bool:
    if outcome == next_outcome:
        return True
    if isinstance(next_outcome, icepool.Die) and next_outcome.quantity(
            outcome) == next_outcome.denominator():
        return True
    return False


def absorbing_markov_chain(
    die: 'icepool.Die[T]',
    function: 'Callable[..., T | icepool.Die[T] | icepool.RerollType]'
) -> 'icepool.Die[T]':
    """Computes the absorption distribution of an absorbing Markov chain.

    Zero-weight outcomes will not be preserved.

    Args:
        die: A die representing the initial state.
        function: A transition function. Any state that leads only to itself will
            be considered absorbing.

    Returns:
        A `Die` in simplest form reprensenting the absorption distribution.
    """

    # Find all reachable states.

    # outcome -> Die representing the next distribution
    transients: MutableMapping[T, icepool.Die] = {}

    frontier = list(die.outcomes())
    while frontier:
        outcome = frontier.pop()
        next_outcome: icepool.Die[T] = icepool.Die([function(outcome)])
        if is_absorbing(outcome, next_outcome):
            continue
        if outcome not in transients:
            transients[outcome] = icepool.Die([next_outcome]).simplify()
            frontier += list(next_outcome.outcomes())

    # Create the transient matrix to be solved.
    t = len(transients)

    if t == 0:
        # No transients; everything is absorbed immediately.
        return die.simplify()

    outcome_to_index = {
        outcome: i for i, outcome in enumerate(transients.keys())
    }

    # [dst_index][src]
    fundamental_solve: list[SparseVector[T]] = [
        SparseVector() for _ in transients.keys()
    ]
    # [src_index][absorbing state]
    absorption_matrix: list[SparseVector[T]] = [
        SparseVector() for _ in transients.keys()
    ]
    for src_index, (src, transition) in enumerate(transients.items()):
        fundamental_solve[src_index][src] += transition.denominator()
        for dst, quantity in transition.items():
            if dst in transients:
                dst_index = outcome_to_index[dst]
                fundamental_solve[dst_index][src] -= quantity
            else:
                absorption_matrix[src_index][dst] = quantity
    for src_index, src in enumerate(transients.keys()):
        fundamental_solve[src_index][Visit] = die.quantity(src)

    # Solve the matrix using Gaussian elimination.

    # Put into upper triangular form.

    for pivot_index, pivot in enumerate(transients.keys()):
        pivot_row = None
        for i in range(pivot_index, t):
            row = fundamental_solve[i]
            if row[pivot] != 0:
                pivot_row = fundamental_solve[i]
                fundamental_solve[i] = fundamental_solve[pivot_index]
                fundamental_solve[pivot_index] = pivot_row
                break
        else:
            raise ValueError(
                'Matrix has deficient rank. This likely indicates that the Markov process has a chance of not terminating.'
            )

        for i in range(pivot_index + 1, t):
            fundamental_solve[i] = fundamental_solve[i] * pivot_row[
                pivot] - pivot_row * fundamental_solve[i][pivot]
            fundamental_solve[i].simplify()

    # Solve for the exit variables.
    for pivot_index, pivot in reversed(list(enumerate(transients.keys()))):
        pivot_row = fundamental_solve[pivot_index]
        for i in range(pivot_index):
            fundamental_solve[i] = fundamental_solve[i] * pivot_row[
                pivot] - pivot_row * fundamental_solve[i][pivot]
            fundamental_solve[i].simplify()

    mean_absorption_time = 0.0

    results = {}
    for pivot_index, (pivot, absorption_row) in enumerate(
            zip(transients.keys(), absorption_matrix)):
        n = fundamental_solve[pivot_index][Visit]
        if n == 0:
            continue
        d = fundamental_solve[pivot_index][pivot]

        # TODO: Is this right?
        mean_absorption_time += n / d * transients[pivot].denominator()

        if len(absorption_row) > 0:
            results[pivot] = (n * absorption_row, d)

    results_denominator = math.lcm(*(d for _, d in results.values()))
    normalized_results: MutableMapping[T, int] = defaultdict(int)
    for row, d in results.values():
        for outcome, quantity in row.items():
            normalized_results[outcome] += quantity * results_denominator // d

    # Inference to Die[T] seems to fail here.
    return icepool.Die(normalized_results).simplify()  # type: ignore
