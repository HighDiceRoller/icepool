__docformat__ = 'google'

import icepool

import enum

from typing import Any, Callable, Generic, Literal, Mapping, MutableMapping, cast
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


class TransitionType(enum.Enum):
    DEFAULT = 0
    BREAK = 1
    REROLL = 2


class TransitionCache(Generic[T]):

    _cache: 'MutableMapping[T, icepool.Die[tuple[TransitionType, T]]]'
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
                # Unwrap Break
                if next_state.outcome is None:
                    # Break to the current outcome
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
                   curr_state: T) -> 'icepool.Die[tuple[TransitionType, T]]':
        """Computes and caches a single step of the transition function for a single state.

        This only works if the input is the same as the output type.

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
                next_states.append((TransitionType.REROLL, ))  # type: ignore
            elif isinstance(next_state, Break):
                if next_state.outcome is None:
                    next_states.append((TransitionType.BREAK, curr_state))
                else:
                    next_states.append(
                        (TransitionType.BREAK, next_state.outcome))
            elif isinstance(next_state, icepool.Die):
                # if the next state is a die, we need to conditionally break
                sub_states = [
                    (TransitionType.BREAK if self.is_pure_self_loop(o) else
                     TransitionType.DEFAULT, o) for o in next_state.outcomes()
                ]
                next_states.append(
                    icepool.Die(sub_states, next_state.quantities()))
            else:
                next_states.append((TransitionType.DEFAULT, next_state))
            next_quantities.append(quantity)
        result: 'icepool.Die[tuple[TransitionType, T]]' = icepool.Die(
            next_states, next_quantities)
        self._cache[curr_state] = result
        return result

    def step_die(
            self, curr_die: 'icepool.Die[T]'
    ) -> 'icepool.Die[tuple[TransitionType, T]]':
        """Computes and caches a single step of the transition function for a die representing the current state distribution.

        This only works if the input is the same as the output type.

        Returns:
            A die whose outcomes are `(transition_type, next_state)`.
        """
        next_states = [self.step_state(curr_state) for curr_state in curr_die]
        return icepool.Die(next_states, curr_die.quantities())

    def step_simple(
            self, curr_die: 'icepool.Die[T]') -> 'tuple[icepool.Die[T], int]':
        """Computes a single step of the transition function with no distinction between breaking and non-breaking outcomes.
        
        Returns:
            * `final_die` with outcomes of type `T`
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
        if not final_states:
            return icepool.Die([]), reroll_quantity
        final_die: 'icepool.Die[T]' = icepool.Die(final_states,
                                                  final_quantites)
        reroll_quantity *= final_die.denominator() // sum(final_quantites)
        return final_die, reroll_quantity
