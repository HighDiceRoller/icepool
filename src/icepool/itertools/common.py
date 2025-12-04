__docformat__ = 'google'

import icepool

from typing import Any, Callable, Generic, Mapping, MutableMapping, cast
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

    _cache: 'MutableMapping[T, tuple[icepool.Die[tuple[bool, T]], int]]'
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

    def is_pure_self_loop(self, curr_state: T) -> bool:
        """Determines whether the given state is a self-loop.
        
        This only works if the input is the same as the output type.
        """
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

    def step_state(self,
                   curr_state: T) -> 'tuple[icepool.Die[tuple[bool, T]], int]':
        """Computes and caches a single step of the transition function.

        This only works if the input is the same as the output type.

        Returns:
            A tuple with the following elements:
            * `break_and_next_state`: A die whose outcomes are (break, next_state).
            * `reroll_quantity`: An `int` representing the total quantity of
                `Reroll`. This is relative to the denominator of the main result.
        """
        if curr_state in self._cache:
            return self._cache[curr_state]
        next_states: list[tuple[bool, T] | icepool.Die[tuple[bool, T]]] = []
        next_quantities: list[int] = []
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
                    next_states.append((True, curr_state))
                    next_quantities.append(quantity)
                else:
                    next_states.append(
                        icepool.tupleize(True, next_state.outcome))
                    next_quantities.append(quantity)
            elif isinstance(next_state, icepool.Die):
                # if the next state is a die, we need to conditionally break
                next_states.append(
                    next_state.map(lambda o: (self.is_pure_self_loop(o), o)))
                next_quantities.append(quantity)
            else:
                next_states.append((False, next_state))
                next_quantities.append(quantity)
        break_and_next_state: 'icepool.Die[tuple[bool, T]]' = icepool.Die(
            next_states, next_quantities)
        reroll_quantity *= break_and_next_state.denominator() // sum(
            next_quantities)
        result = (break_and_next_state, reroll_quantity)
        self._cache[curr_state] = result
        return result

    # TODO: how to merge different denominators + rerolls?
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

    def step_final(
        self, curr_die: 'icepool.Die[T]'
    ) -> 'tuple[list[T | icepool.Die[T]], list[int], int]':
        """
        
        Returns:
            * `final_states`
            * `final_quantites`
            * `reroll_quantity`
        """
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
