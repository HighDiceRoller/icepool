__docformat__ = 'google'

import icepool
from icepool.map_tools.common import TransitionType
from icepool.map_tools.core_impl import TransitionCache

import enum
import math
from collections import defaultdict

from icepool.typing import Outcome, T
from fractions import Fraction
from typing import Callable, MutableMapping


class SpecialValue(enum.Enum):
    Visit = 'Visit'
    """Indicates the numerator of the number of visits to a particular state."""
    Restart = 'Restart'
    """Indicates that a Restart was triggered."""


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


def absorbing_markov_chain_impl(
    transition_cache: TransitionCache[T],
    initial_state: 'T | icepool.Die[T]',
) -> 'tuple[icepool.Die[T], Fraction | None]':
    """Computes the absorption distribution of an absorbing Markov chain.

    Zero-weight outcomes will not be preserved.

    Args:
        die: A die representing the initial state.
        function: A transition function. Any state that leads only to itself will
            be considered absorbing.

    Returns:
        A `Die` in simplest form reprensenting the absorption distribution,
        and the mean absorption time.
    """

    # Find all reachable states.

    # outcome -> Die representing the next distribution
    # The outcomes of the Die are (is_absorbing, outcome)
    transients: MutableMapping[T, icepool.Die[tuple[TransitionType, T]]] = {}

    initial_die: 'icepool.Die' = icepool.Die([initial_state])
    initial_transition_types = transition_cache.self_loop_die(
        initial_die).group_by[0]
    if TransitionType.DEFAULT in initial_transition_types:
        initial_transient = initial_transition_types[
            TransitionType.DEFAULT].marginals[1]
    else:
        # No transients; everything is absorbed immediately.
        return initial_die.simplify(), Fraction(0, 1)
    if TransitionType.BREAK in initial_transition_types:
        initial_absorb = initial_transition_types[
            TransitionType.BREAK].marginals[1]
    else:
        initial_absorb = icepool.Die([])

    frontier = set()
    for outcome in initial_transient:
        frontier.add(outcome)
    while frontier:
        curr_state = frontier.pop()
        transients[curr_state] = transition_cache.step_state(curr_state)
        for transition_type, next_outcome in transients[curr_state]:
            if transition_type is TransitionType.DEFAULT and next_outcome not in transients:
                frontier.add(next_outcome)

    # Create the transient matrix to be solved.
    t = len(transients)

    outcome_to_index = {
        outcome: i
        for i, outcome in enumerate(transients.keys())
    }
    """Supposing the transition matrix has the form
    
    ```
    Q 0
    A I
    ```
    with the state vector on the right, then `fundamental_solve` is solving
    the equation
    `(I - Q) v = s`
    where `s` is the starting state vector, and `v` is the visit vector which
    gives the number of visits to each transient state.
    We solve this in unnormalized form, so instead of being 1, `I` is equal to
    the denominator of the transition from the source state.
    """
    # [dst_index][src]
    fundamental_solve: list[SparseVector[T]] = [
        SparseVector() for _ in transients.keys()
    ]
    # [src_index][absorbing state]
    absorption_matrix: list[SparseVector[T]] = [
        SparseVector() for _ in transients.keys()
    ]
    has_restart = False
    for src_index, (src, transition) in enumerate(transients.items()):
        # The identity term.
        fundamental_solve[src_index][src] += transition.denominator()
        for (transition_type, dst), quantity in transition.items():
            if transition_type is TransitionType.BREAK:
                absorption_matrix[src_index][dst] = quantity
            elif transition_type is TransitionType.RESTART:
                # transition to nowhere
                has_restart = True
            else:
                # Minus Q.
                dst_index = outcome_to_index[dst]
                fundamental_solve[dst_index][src] -= quantity
    for src_index, src in enumerate(transients.keys()):
        # Setting `s`.
        fundamental_solve[src_index][
            SpecialValue.Visit] = initial_transient.quantity(src)

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

    # Solve for the visit vector `v`.
    for pivot_index, pivot in reversed(list(enumerate(transients.keys()))):
        pivot_row = fundamental_solve[pivot_index]
        for i in range(pivot_index):
            fundamental_solve[i] = fundamental_solve[i] * pivot_row[
                pivot] - pivot_row * fundamental_solve[i][pivot]
            fundamental_solve[i].simplify()

    mean_absorption_time = Fraction(0, 1)

    results = {}
    for pivot_index, (pivot, absorption_row) in enumerate(
            zip(transients.keys(), absorption_matrix)):
        # n / d is an element of the visit vector `v`.
        n = fundamental_solve[pivot_index][SpecialValue.Visit]
        if n == 0:
            continue
        d = fundamental_solve[pivot_index][pivot]

        # Compared to the normalized formula, I and Q were scaled up by a
        # factor transients[pivot].denominator() so (I - Q)^-1 was reduced
        # by the same factor. So we put the factor back here.
        mean_absorption_time += Fraction(n,
                                         d) * transients[pivot].denominator()

        if len(absorption_row) > 0:
            results[pivot] = (n * absorption_row, d)

    results_denominator = math.lcm(*(d for _, d in results.values()))
    normalized_results: MutableMapping[T, int] = defaultdict(int)
    for row, d in results.values():
        factor = results_denominator // d
        for outcome, quantity in row.items():
            normalized_results[outcome] += quantity * factor

    # Inference to Die[T] seems to fail here.
    transient_absorb: 'icepool.Die' = icepool.Die(
        normalized_results).simplify()
    result: 'icepool.Die' = icepool.Die(
        [initial_absorb, transient_absorb],
        [initial_absorb.denominator(),
         initial_transient.denominator()]).simplify()

    if has_restart:
        mean_absorption_time = None  # type: ignore
    else:
        # The starting vector `s` was not normalized, so we divide it out here.
        mean_absorption_time /= initial_die.denominator()

    return result, mean_absorption_time


def absorbing_markov_chain_die(
    transition_cache: TransitionCache[T],
    initial_state: 'T | icepool.Die[T]',
) -> 'icepool.Die[T]':
    return absorbing_markov_chain_impl(transition_cache, initial_state)[0]


def absorbing_markov_chain_mean_absorption_time(
    transition_cache: TransitionCache[T],
    initial_state: 'T | icepool.Die[T]',
) -> Fraction:
    time = absorbing_markov_chain_impl(transition_cache, initial_state)[1]
    if time is None:
        raise NotImplementedError(
            'Restart not implemented for mean_time_to_absorb.')
    return time
