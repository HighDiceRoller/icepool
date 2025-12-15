__docformat__ = 'google'

import icepool
from icepool.map_tools.common import Break, TransitionType, transition_and_star

import enum

from typing import Any, Callable, Generic, Literal, Mapping, MutableMapping, cast
from icepool.typing import T, infer_star


def map_simple(
        repl:
    'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression] | Mapping[Any, T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression]',
        first_arg,
        *extra_args,
        star: bool | None,
        again_count: int | None = None,
        again_depth: int | None = None,
        again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None,
        **kwargs) -> 'icepool.Die[T]':
    """Computes a single step of the transition function with no distinction between breaking and non-breaking outcomes.
    
    Returns:
        * A list of final outcomes with `Break`s unwrapped.
        * A list of final quantities.
    """
    transition, star = transition_and_star(repl, len(extra_args) + 1, star)
    final_states: list[T | icepool.Die[T] | icepool.AgainExpression
                       | icepool.RerollType] = []
    final_quantites: list[int] = []
    for (first_outcome,
         *extra_outcomes), quantity in icepool.iter_cartesian_product(
             first_arg, *extra_args):
        if star:
            final_state = transition(*first_outcome, *extra_outcomes, **kwargs)
        else:
            final_state = transition(first_outcome, *extra_outcomes, **kwargs)
        if isinstance(final_state, Break):
            if final_state.outcome is None:
                final_states.append(first_outcome)
                final_quantites.append(quantity)
            else:
                final_states.append(final_state.outcome)
                final_quantites.append(quantity)
        else:
            final_states.append(final_state)
            final_quantites.append(quantity)
    return icepool.Die(final_states,
                       final_quantites,
                       again_count=again_count,
                       again_depth=again_depth,
                       again_end=again_end)


class TransitionCache(Generic[T]):
    """Helper class for caching a transition function for map(repeat)."""

    _cache: 'MutableMapping[T, icepool.Die[tuple[TransitionType, T]]]'
    # state -> DEFAULT or BREAK
    _self_loop_cache: MutableMapping[T, TransitionType]

    def __init__(
            self, repl:
        'Callable[..., T | icepool.Die[T] | icepool.RerollType] | Mapping[Any, T | icepool.Die[T] | icepool.RerollType]',
            *extra_args, star: bool | None, **kwargs):
        self._cache = {}
        self._self_loop_cache = {}
        self._extra_args = extra_args
        self._kwargs = kwargs
        self._transition, self._star = transition_and_star(
            repl,
            len(extra_args) + 1, star)

    def is_self_loop(self, curr_state: T, /) -> TransitionType:
        """Returns `TransitionType.BREAK` if the state is a self-loop, or `DEFAULT` otherwise."""
        if curr_state in self._self_loop_cache:
            return self._self_loop_cache[curr_state]

        result = TransitionType.BREAK
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
                # Ignored.
                continue
            elif next_state is icepool.Restart:
                # Might restart, therefore not a self-loop.
                result = TransitionType.DEFAULT
                break
            elif isinstance(next_state, Break):
                # Unwrap Break.
                if next_state.outcome is None:
                    # Break to the current outcome.
                    continue
                else:
                    next_state = next_state.outcome

            if isinstance(next_state, icepool.Die):
                if next_state.probability(curr_state) == 1:
                    continue
            else:
                if next_state == curr_state:
                    continue
            result = TransitionType.DEFAULT
            break

        self._self_loop_cache[curr_state] = result
        return result

    def self_loop_die(self, die: 'icepool.Die[T]',
                      /) -> 'icepool.Die[tuple[TransitionType, T]]':
        """Returns a die whose outcomes are (transition_type, outcome) according to whether the states are self-loops."""
        return icepool.Die([(self.is_self_loop(o), o) for o in die.outcomes()],
                           die.quantities())

    def self_loop_die_with_zero_time(
            self, die: 'icepool.Die[T]',
            /) -> 'icepool.Die[tuple[TransitionType, T, int]]':
        """As self_loop_die, but also appends a zero time."""
        return icepool.Die([(self.is_self_loop(o), o, 0)
                            for o in die.outcomes()], die.quantities())

    def step_state(self, curr_state: T,
                   /) -> 'icepool.Die[tuple[TransitionType, T]]':
        """Computes and caches a single step of the transition function for a single state.

        This only works if the input is the same as the output type.

        Args:
            curr_state: The current state.
            include_reroll: Whether `TransitionType.REROLL`s are included in the result.

        Returns:
            A die whose outcomes are `(transition_type, next_state)`.
        """
        if curr_state in self._cache:
            return self._cache[curr_state]
        next_state: T | icepool.Die[T]
        next_states: list[tuple[TransitionType, T]
                          | icepool.Die[tuple[TransitionType, T]]] = []
        next_quantities: list[int] = []
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
                continue  # Pruned immediately.
            elif next_state is icepool.Restart:
                # Will prune at end.
                next_states.append((TransitionType.RESTART, None))
            elif isinstance(next_state, Break):
                if next_state.outcome is None:
                    next_states.append((TransitionType.BREAK, curr_state))
                else:
                    next_states.append(
                        (TransitionType.BREAK, next_state.outcome))
            elif isinstance(next_state, icepool.Die):
                # If the next state is a die, we need to conditionally break.
                # This is why we keep the result as a single die rather than
                # separate non-break and break dice.
                next_states.append(self.self_loop_die(next_state))
            else:
                next_states.append((self.is_self_loop(next_state), next_state))
            next_quantities.append(quantity)
        result: 'icepool.Die[tuple[TransitionType, T]]' = icepool.Die(
            next_states, next_quantities)
        self._cache[curr_state] = result
        return result

    def step_transition_die(self,
                            curr_die: 'icepool.Die[tuple[TransitionType, T]]',
                            /) -> 'icepool.Die[tuple[TransitionType, T]]':
        """Advances the (transition_type, state) by one time step.
        
        Args:
            curr_die: The current distribution as a die whose outcomes are
            `(transition_type, next_state)`.

        Returns:
            The next state distribution as a die whose outcomes are
            `(transition_type, next_state)`.
        """
        next_states = [(self.step_state(curr_state)
                        if transition_type == TransitionType.DEFAULT else
                        (transition_type, curr_state))
                       for transition_type, curr_state in curr_die.outcomes()]
        return icepool.Die(next_states, curr_die.quantities())

    def step_transition_die_with_time(
            self, curr_die: 'icepool.Die[tuple[TransitionType, T, int]]',
            /) -> 'icepool.Die[tuple[TransitionType, T, int]]':
        """As step_transition_die, but keeps track of the break time in the last element."""
        next_states = [
            (self.step_state(curr_state) +
             (time + 1, ) if transition_type == TransitionType.DEFAULT else
             (transition_type, curr_state, time))
            for transition_type, curr_state, time in curr_die.outcomes()
        ]
        return icepool.Die(next_states, curr_die.quantities())
