__docformat__ = 'google'

import icepool

import itertools
from enum import Enum

from typing import Any, Callable, Generic, Literal, Mapping, MutableMapping, cast, overload
from icepool.typing import T, infer_star


class Break(Generic[T]):
    """Wrapper around a return value for triggering an early exit from `map(repeat)`."""

    def __init__(self, outcome: T | None = None):
        """Constructor.
        
        Args:
            outcome: The wrapped outcome. If `None`, it is considered to be
                equal to the first argument to the current iteration of `map()`.
        """
        self.outcome = outcome

    def __hash__(self) -> int:
        return hash((Break, self.outcome))

    def __repr__(self) -> str:
        return f'Break({repr(self.outcome)})'

    def __str__(self) -> str:
        return f'Break({str(self.outcome)})'


def transition_and_star(repl: 'Callable | Mapping', arg_count: int,
                        star: bool | None) -> 'tuple[Callable, bool]':
    """Expresses repl as a function and infers star."""
    if callable(repl):
        if star is None:
            star = infer_star(repl, arg_count)
        return repl, star
    elif isinstance(repl, Mapping):
        if arg_count != 1:
            raise ValueError(
                'If a mapping is provided for repl, len(args) must be 1.')
        mapping = cast(Mapping, repl)
        return lambda o: mapping.get(o, o), False
    else:
        raise TypeError('repl must be a callable or a mapping.')


class TransitionCache(Generic[T]):

    _cache: MutableMapping[Any, tuple]
    _is_pure_self_loop: MutableMapping[T, bool]

    def __init__(
            self, repl:
        'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression] | Mapping[Any, T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression]',
            *extra_args, star: bool | None, **kwargs):
        self._cache = {}
        self._is_pure_self_loop = {}
        self._extra_args = extra_args
        self._kwargs = kwargs
        self._transition, self._star = transition_and_star(
            repl,
            len(extra_args) + 1, star)

    def is_pure_self_loop(self,
                          curr_state_or_die: 'T | icepool.Die[T]') -> bool:
        """Determines whether the given state is a self-loop.
        
        This only works if the input is the same as the output type.
        """
        if isinstance(curr_state_or_die, icepool.Die):
            if len(curr_state_or_die) != 1:
                return False
            curr_state = curr_state_or_die.outcomes()[0]
        else:
            curr_state = curr_state_or_die

        if curr_state in self._is_pure_self_loop:
            return self._is_pure_self_loop[curr_state]

        result = True
        for extra_outcomes, quantity in icepool.iter_cartesian_product(
                *self._extra_args):
            if self._star:
                next_state = self._transition(
                    *curr_state,  # type: ignore
                    *extra_outcomes,
                    **self._kwargs)
            else:
                next_state = self._transition(curr_state, *extra_outcomes,
                                              **self._kwargs)
            if next_state is icepool.Reroll:
                result = False  # Might restart, therefore not a self-loop
                break
            elif isinstance(next_state, Break):
                # Unwrap Breaks.
                if next_state.outcome is None:
                    # Breaks to the current outcome
                    continue
                else:
                    next_state = next_state.outcome

            if isinstance(next_state, icepool.Die):
                if next_state.probability(curr_state) == 1:
                    continue
            else:
                if next_state == curr_state:
                    continue
            result = False
            break

        self._is_pure_self_loop[curr_state] = result
        return result

    def step_state(
        self, curr_state: T
    ) -> 'tuple[list[T | icepool.Die[T]], list[int], list[T | icepool.Die[T]], list[int], int]':
        """Computes and caches a single step of the transition function.

        This only works if the input is the same as the output type.

        Returns:
            A tuple with the following elements:
            * `non_break_states`: A list of all non-break states.
            * `non_break_quantities`: A list of corresponding `int` quantities.
            * `break_states`: A list of break states. These comprise the
                following:
                * Explicit `Break()`s.
                * Pure self-loops, i.e. the state transitions to itself with
                    probability 1 and no chance of `Reroll`.
            * `break_quantities`: A list of corresponding `int` quantities.
            * `reroll_quantity`: An `int` representing the total quantity of
                `Reroll`.
        """
        if curr_state in self._cache:
            return self._cache[curr_state]
        non_break_states: list[T | icepool.Die[T]] = []
        non_break_quantities: list[int] = []
        break_states: list[T | icepool.Die[T]] = []
        break_quantities: list[int] = []
        reroll_quantity = 0
        for extra_outcomes, quantity in icepool.iter_cartesian_product(
                *self._extra_args):
            if self._star:
                next_state = self._transition(
                    *curr_state,  # type: ignore
                    *extra_outcomes,
                    **self._kwargs)
            else:
                next_state = self._transition(curr_state, *extra_outcomes,
                                              **self._kwargs)
            if next_state is icepool.Reroll:
                reroll_quantity += quantity
            elif isinstance(next_state, Break):
                if next_state.outcome is None:
                    break_states.append(curr_state)
                    break_quantities.append(quantity)
                else:
                    break_states.append(next_state.outcome)
                    break_quantities.append(quantity)
            elif self.is_pure_self_loop(next_state):
                break_states.append(next_state)
                break_quantities.append(quantity)
            else:
                non_break_states.append(next_state)
                non_break_quantities.append(quantity)
        result = (non_break_states, non_break_quantities, break_states,
                  break_quantities, reroll_quantity)
        self._cache[curr_state] = result
        return result

    def step_die(self, curr_die: 'icepool.Die[T]'):
        result_non_break_states: list[T | icepool.Die[T]] = []
        result_non_break_quantities: list[int] = []
        result_break_states: list[T | icepool.Die[T]] = []
        result_break_quantities: list[int] = []
        result_reroll_quantity = 0
        for curr_state, quantity in curr_die.items():
            (non_break_states, non_break_quantities, break_states,
             break_quantities, reroll_quantity) = self.step_state(curr_state)
            result_non_break_states += non_break_states
            result_non_break_quantities += [
                quantity * q for q in non_break_quantities
            ]
            result_break_states += break_states
            result_break_quantities += [quantity * q for q in break_quantities]
            result_reroll_quantity += reroll_quantity * quantity
        return (result_non_break_states, result_non_break_quantities,
                result_break_states, result_break_quantities,
                result_reroll_quantity)

    def step_last(
        self, curr_die: 'icepool.Die[T]'
    ) -> 'tuple[ list[T | icepool.Die[T]], list[int], int]':
        final_states: list[T | icepool.Die[T]] = []
        final_quantites: list[int] = []
        reroll_quantity = 0
        for (curr_state,
             *extra_outcomes), quantity in icepool.iter_cartesian_product(
                 curr_die, *self._extra_args):
            if self._star:
                final_state = self._transition(
                    *curr_state,  # type: ignore
                    *extra_outcomes,
                    **self._kwargs)
            else:
                final_state = self._transition(curr_state, *extra_outcomes,
                                               **self._kwargs)
            if final_state is icepool.Reroll:
                reroll_quantity += quantity
            elif isinstance(final_state, Break):
                if final_state.outcome is None:
                    final_states.append(curr_state)
                    final_quantites.append(quantity)
                else:
                    final_states.append(final_state.outcome)
                    final_quantites.append(quantity)
            else:
                final_states.append(final_state)
                final_quantites.append(quantity)
        return (final_states, final_quantites, reroll_quantity)
