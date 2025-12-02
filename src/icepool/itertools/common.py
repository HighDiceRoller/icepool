__docformat__ = 'google'

import icepool
from enum import Enum

from typing import Any, Callable, Generic, Literal, Mapping, cast, overload
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


class OutcomeSpecial(Enum):
    NORMAL = 0
    REROLL = -1
    BREAK = 1


@overload
def outcome_special(
    outcome: 'T | icepool.Die[T] | icepool.AgainExpression | Break[T]',
    first_arg
) -> 'tuple[OutcomeSpecial, T | icepool.Die[T] | icepool.AgainExpression]':
    ...


@overload
def outcome_special(
        outcome: icepool.RerollType,
        first_arg) -> 'tuple[Literal[OutcomeSpecial.REROLL], None]':
    ...


@overload
def outcome_special(
        outcome:
    'T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression | Break[T]',
        first_arg) -> 'tuple[OutcomeSpecial, T | icepool.Die[T] | None]':
    ...


def outcome_special(
    outcome:
    'T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression | Break[T]',
    first_arg
) -> 'tuple[OutcomeSpecial, T | icepool.Die[T] | icepool.AgainExpression | None]':
    """Determines any special treatment to perform on the outcome, and the effective outcome.
    
    If the outcome is == first_arg, it is treated as a BREAK.
    """
    if outcome is icepool.Reroll:
        return OutcomeSpecial.REROLL, None
    elif outcome == first_arg:
        return OutcomeSpecial.BREAK, outcome  # type: ignore
    elif isinstance(outcome, icepool.Die):
        if outcome.probability(first_arg) == 1:
            return OutcomeSpecial.BREAK, outcome
        else:
            return OutcomeSpecial.NORMAL, outcome
    elif isinstance(outcome, Break):
        if outcome.outcome is None:
            return OutcomeSpecial.BREAK, first_arg
        else:
            return OutcomeSpecial.BREAK, outcome.outcome
    else:
        return OutcomeSpecial.NORMAL, outcome
