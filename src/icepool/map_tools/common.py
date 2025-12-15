__docformat__ = 'google'

import icepool

import enum

from typing import Any, Callable, Generic, Literal, Mapping, MutableMapping, cast
from icepool.typing import T, infer_star


class TransitionType(enum.IntEnum):
    DEFAULT = 0
    BREAK = 1
    # Reroll gets pruned immediately, so doesn't get a transition type.
    RESTART = 2


class Break(Generic[T]):
    """EXPERIMENTAL: Wrapper around a return value for triggering an early exit from `map(repeat)`.
    
    For example, to add successive dice until the total reaches 10:
    ```python
    def example(total, new_roll):
        if total >= 10:
            return Break()  # same as Break(total)
        else:
            return total + new_roll
    map(example, 0, d(6))
    ```
    """

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
