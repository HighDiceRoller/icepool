import icepool

import math
from collections import defaultdict

from typing import Any, Callable, MutableMapping

Exit = object()
"""Special value for indicating an exit from the Markov chain."""


class SparseRow(MutableMapping[Any, int]):

    def __init__(self):
        self._data = {}

    def __setitem__(self, key, value: int) -> None:
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

    def __mul__(self, n: int) -> 'SparseRow':
        result = SparseRow()
        result._data = {k: v * n for k, v in self.items()}
        return result

    def __rmul__(self, n: int) -> 'SparseRow':
        return self.__mul__(n)

    def __sub__(self, other: 'SparseRow') -> 'SparseRow':
        result = SparseRow()
        result._data = self._data.copy()
        for k, v in other.items():
            result[k] -= v
        return result

    def simplify(self):
        divisor = math.gcd(*self.values())
        for k in self:
            self[k] //= divisor

    def __str__(self) -> str:
        return str(self._data)


def _is_absorbing(outcome, next_outcome) -> bool:
    if outcome == next_outcome:
        return True
    if isinstance(next_outcome, icepool.Die) and next_outcome.quantity(
            outcome) == next_outcome.denominator():
        return True
    return False


def absorbing_markov_chain(die: icepool.Die, func: Callable):

    # Find all reachable states.

    # outcome -> Die representing the next distribution
    transients: MutableMapping[Any, icepool.Die] = {}
    absorbing_states = set()

    frontier = list(die.outcomes())
    while frontier:
        outcome = frontier.pop()
        next_outcome = func(outcome)
        if _is_absorbing(outcome, next_outcome):
            absorbing_states.add(next_outcome)
        elif outcome not in transients:
            transients[outcome] = icepool.Die([next_outcome]).simplify()
            frontier += list(next_outcome.outcomes())

    # Create the transient matrix to be solved.
    t = len(transients)

    outcome_to_index = {
        outcome: i for i, outcome in enumerate(transients.keys())
    }

    # [dst_index][src]
    transient_solve = [SparseRow() for _ in transients.keys()]
    # [src_index][absorbing state]
    absorption_matrix = [SparseRow() for _ in transients.keys()]
    for src_index, (src, transition) in enumerate(transients.items()):
        transient_solve[src_index][src] += transition.denominator()
        for dst, quantity in transition.items():
            if dst in transients:
                dst_index = outcome_to_index[dst]
                transient_solve[dst_index][src] -= quantity
            else:
                absorption_matrix[src_index][dst] = quantity
    for src_index, src in enumerate(transients.keys()):
        transient_solve[src_index][Exit] = die.quantity(src)

    # Normalize absorption matrix.
    absorption_denominator = math.lcm(
        *(transition.denominator() for transition, absorption_row in zip(
            transients.values(), absorption_matrix) if len(absorption_row) > 0))
    for i, transition in enumerate(transients.values()):
        absorption_matrix[
            i] *= absorption_denominator // transition.denominator()

    # Solve the matrix using Gaussian elimination.

    # Put into upper triangular form.

    for pivot_index, pivot in enumerate(transients.keys()):
        pivot_row = None
        for i in range(pivot_index, t):
            row = transient_solve[i]
            if row[pivot] != 0:
                pivot_row = transient_solve[i]
                transient_solve[i] = transient_solve[pivot_index]
                transient_solve[pivot_index] = pivot_row
                break
        else:
            raise RuntimeError('Matrix has deficient rank.')

        for i in range(pivot_index + 1, t):
            transient_solve[i] = transient_solve[i] * pivot_row[
                pivot] - pivot_row * transient_solve[i][pivot]
            transient_solve[i].simplify()

    # Solve for the exit variables.
    for pivot_index, pivot in reversed(list(enumerate(transients.keys()))):
        pivot_row = transient_solve[pivot_index]
        for i in range(pivot_index):
            transient_solve[i] = transient_solve[i] * pivot_row[
                pivot] - pivot_row * transient_solve[i][pivot]
            transient_solve[i].simplify()

    results = {}
    for pivot_index, (pivot, absorption_row) in enumerate(
            zip(transients.keys(), absorption_matrix)):
        n = transient_solve[pivot_index][Exit]
        if n == 0:
            continue
        if len(absorption_row) == 0:
            continue

        d = transient_solve[pivot_index][pivot]
        results[pivot] = (n * absorption_row, d)

    results_denominator = math.lcm(*(d for _, d in results.values()))
    normalized_results: MutableMapping[Any, int] = defaultdict(int)
    for row, d in results.values():
        for outcome, quantity in row.items():
            normalized_results[outcome] += quantity * results_denominator // d

    return icepool.Die(normalized_results).simplify()
