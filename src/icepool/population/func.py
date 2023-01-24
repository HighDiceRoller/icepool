__docformat__ = 'google'

import icepool
from icepool.typing import Outcome, T, U

from collections import defaultdict
from functools import cache
import itertools
import math

from typing import Any, Callable, Final, Hashable, Iterable, Iterator, Literal, Sequence, TypeAlias, overload


@cache
def d(sides: int, /) -> 'icepool.Die[int]':
    """A standard die.

    Specifically, the outcomes are `int`s from `1` to `sides` inclusive,
    with quantity 1 each.

    Don't confuse this with `icepool.Die()`:

    * `icepool.Die([6])`: A `Die` that always rolls the integer 6.
    * `icepool.d(6)`: A d6.
    """
    if not isinstance(sides, int):
        raise TypeError('Argument to standard() must be an int.')
    elif sides < 1:
        raise ValueError('Standard die must have at least one side.')
    return icepool.Die(range(1, sides + 1))


def __getattr__(key: str) -> 'icepool.Die[int]':
    """Implements the `dX` syntax for standard die with no parentheses.

    For example, `icepool.d6`.

    Note that this behavior can't be imported into the global scope, but the
    function `d()` can be.
    """
    if key[0] == 'd':
        try:
            return d(int(key[1:]))
        except ValueError:
            pass
    raise AttributeError(key)


def coin(n: int, d: int, /) -> 'icepool.Die[bool]':
    """A `Die` that rolls `True` with probability `n / d`, and `False` otherwise.

    If `n == 0` or `n == d` the result will have only one outcome.
    """
    data = {}
    if n != d:
        data[False] = d - n
    if n != 0:
        data[True] = n
    return icepool.Die(data)


def one_hot(sides: int, /) -> 'icepool.Die[tuple[bool, ...]]':
    """A `Die` with tuple outcomes with one element set to `True` uniformly at random and the rest `False`.

    This is an easy (if expensive) way of representing how many dice in a pool
    rolled each number. For example, the outcomes of `10 @ one_hot(6)` are
    the `(ones, twos, threes, fours, fives, sixes)` rolled in 10d6.
    """
    data = []
    for i in range(sides):
        outcome = [False] * sides
        outcome[i] = True
        data.append(tuple(outcome))
    return icepool.Die(data)


def cartesian_product(*dice: 'icepool.Die | Outcome') -> 'icepool.Die[tuple]':
    """Produces a `Die` whose outcomes are tuples of the outcomes of each of the inputs.

    E.g. `outer_product(d6, d6)` would produce tuples
    `(1, 1), (1, 2), ... (6, 6)`.
    """
    return apply(lambda *outcomes: outcomes, *dice)


def from_cumulative_quantities(outcomes: Sequence[T],
                               cumulative_quantities: Sequence[int],
                               *,
                               reverse: bool = False) -> 'icepool.Die[T]':
    """Constructs a `Die` from a sequence of cumulative quantities.

    Args:
        outcomes: The outcomes of the resulting die. Sorted order is recommended
            but not necessary.
        cumulative_quantities: The cumulative quantities (inclusive) of the
            outcomes in the order they are given to this function.
        reverse: Iff true, both of the arguments will be reversed. This allows
            e.g. constructing using a survival distribution.
    """

    prev = 0
    d = {}
    for outcome, quantity in zip((reversed(outcomes) if reverse else outcomes),
                                 (reversed(cumulative_quantities)
                                  if reverse else cumulative_quantities)):
        d[outcome] = quantity - prev
        prev = quantity
    return icepool.Die(d)


@overload
def from_rv(rv, outcomes: Sequence[int], denominator: int,
            **kwargs) -> 'icepool.Die[int]':
    ...


@overload
def from_rv(rv, outcomes: Sequence[float], denominator: int,
            **kwargs) -> 'icepool.Die[float]':
    ...


def from_rv(rv, outcomes: Sequence[int] | Sequence[float], denominator: int,
            **kwargs) -> 'icepool.Die[int] | icepool.Die[float]':
    """Constructs a `Die` from a rv object (as `scipy.stats`).
    Args:
        rv: A rv object (as `scipy.stats`).
        outcomes: An iterable of `int`s or `float`s that will be the outcomes
            of the resulting `Die`.
            If the distribution is discrete, outcomes must be `int`s.
        denominator: The denominator of the resulting `Die` will be set to this.
        **kwargs: These will be forwarded to `rv.cdf()`.
    """
    if hasattr(rv, 'pdf'):
        # Continuous distributions use midpoints.
        midpoints = [(a + b) / 2 for a, b in zip(outcomes[:-1], outcomes[1:])]
        cdf = rv.cdf(midpoints, **kwargs)
        quantities_le = tuple(
            int(round(x * denominator)) for x in cdf) + (denominator,)
    else:
        cdf = rv.cdf(outcomes, **kwargs)
        quantities_le = tuple(int(round(x * denominator)) for x in cdf)
    return from_cumulative_quantities(outcomes, quantities_le)


def min_outcome(*dice: 'T | icepool.Die[T]') -> T:
    """The minimum outcome among the dice. """
    converted_dice = [icepool.implicit_convert_to_die(die) for die in dice]
    return min(die.outcomes()[0] for die in converted_dice)


def max_outcome(*dice: 'T | icepool.Die[T]') -> T:
    """The maximum outcome among the dice. """
    converted_dice = [icepool.implicit_convert_to_die(die) for die in dice]
    return max(die.outcomes()[-1] for die in converted_dice)


def align(*dice: 'T | icepool.Die[T]') -> tuple['icepool.Die[T]', ...]:
    """Pads dice with zero quantities so that all have the same set of outcomes.

    Args:
        *dice: One `Die` per argument.

    Returns:
        A tuple of aligned dice.
    """
    converted_dice = [icepool.implicit_convert_to_die(die) for die in dice]
    outcomes = set(
        itertools.chain.from_iterable(die.outcomes() for die in converted_dice))
    return tuple(die.set_outcomes(outcomes) for die in converted_dice)


def align_range(
        *dice: 'int | icepool.Die[int]') -> tuple['icepool.Die[int]', ...]:
    """Pads dice with zero quantities so that all have the same set of consecutive `int` outcomes.

    Args:
        *dice: One `Die` per argument.

    Returns:
        A tuple of aligned dice.
    """
    converted_dice = [icepool.implicit_convert_to_die(die) for die in dice]
    outcomes = range(icepool.min_outcome(*converted_dice),
                     icepool.max_outcome(*converted_dice) + 1)
    return tuple(die.set_outcomes(outcomes) for die in converted_dice)


def reduce(func: 'Callable[[T, T], T | icepool.Die[T] | icepool.RerollType]',
           dice: 'Iterable[T | icepool.Die[T]]',
           *,
           initial: 'T | icepool.Die[T] | None' = None) -> 'icepool.Die[T]':
    """Applies a function of two arguments cumulatively to a sequence of dice.

    Analogous to
    [`functools.reduce()`](https://docs.python.org/3/library/functools.html#functools.reduce).

    The function is applied non-elementwise to tuple outcomes.

    Args:
        func: The function to apply. The function should take two arguments,
            which are an outcome from each of two dice, and produce an outcome
            of the same type. It may also return `Reroll`, in which case the
            entire sequence is effectively rerolled.
        dice: A sequence of dice to apply the function to, from left to right.
        initial: If provided, this will be placed at the front of the sequence
            of dice.
        again_depth: Forwarded to the final die constructor.
        again_end: Forwarded to the final die constructor.
    """
    # Conversion to dice is not necessary since apply() takes care of that.
    iter_dice = iter(dice)
    if initial is not None:
        result: 'icepool.Die[T]' = icepool.implicit_convert_to_die(initial)
    else:
        result = icepool.implicit_convert_to_die(next(iter_dice))
    for die in iter_dice:
        result = apply(func, result, die)
    return result


def accumulate(
        func: 'Callable[[T, T], T | icepool.Die[T]]',
        dice: 'Iterable[T | icepool.Die[T]]',
        *,
        initial: 'T | icepool.Die[T] | None' = None
) -> Iterator['icepool.Die[T]']:
    """Applies a function of two arguments cumulatively to a sequence of dice, yielding each result in turn.

    Analogous to
    [`itertools.accumulate()`](https://docs.python.org/3/library/itertools.html#itertools.accumulate)
    , though with no default function and
    the same parameter order as `reduce()`.

    The number of results is equal to the number of elements of `dice`, with
    one additional element if `initial` is provided.

    The function is applied non-elementwise to tuple outcomes.

    Args:
        func: The function to apply. The function should take two arguments,
            which are an outcome from each of two dice.
        dice: A sequence of dice to apply the function to, from left to right.
        initial: If provided, this will be placed at the front of the sequence
            of dice.
    """
    # Conversion to dice is not necessary since apply() takes care of that.
    iter_dice = iter(dice)
    if initial is not None:
        result: 'icepool.Die[T]' = icepool.implicit_convert_to_die(initial)
    else:
        try:
            result = icepool.implicit_convert_to_die(next(iter_dice))
        except StopIteration:
            return
    yield result
    for die in iter_dice:
        result = apply(func, result, die)
        yield result


def iter_cartesian_product(
    *args: 'Outcome | icepool.Die | icepool.Pool'
) -> Iterator[tuple[tuple, int]]:
    """Yields the independent joint distribution of the arguments.

    Args:
        *args: These may be dice, which will be expanded into their joint
            outcomes. Non-dice are left as-is.

    Yields:
        Tuples containing one outcome per arg and the joint quantity.
    """

    def arg_items(arg) -> Sequence[tuple[Any, int]]:
        if isinstance(arg, icepool.Die):
            return arg.items()
        elif isinstance(arg, icepool.Pool):
            # Expression evaluators are difficult to type.
            return arg.expand().items()  # type: ignore
        else:
            return [(arg, 1)]

    for t in itertools.product(*(arg_items(arg) for arg in args)):
        outcomes, quantities = zip(*t)
        final_quantity = math.prod(quantities)
        yield outcomes, final_quantity


def apply(
    func:
    'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.Again]',
    *args: 'Outcome | icepool.Die | icepool.Pool',
    again_depth: int = 1,
    again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None
) -> 'icepool.Die[T]':
    """Applies `func(outcome_of_die_0, outcome_of_die_1, ...)` for all outcomes of the dice.

    Example: `apply(lambda a, b: a + b, d6, d6)` is the same as d6 + d6.

    `apply()` is flexible but not very efficient for more than a few dice.
    Instead of using several arguments:

    * If the problem is easy to solve by considering how many dice rolled each
        outcome, one outcome at a time, try using
        `icepool.Pool` and `icepool.MultisetEvaluator`.
    * If the problem is easy to solve by considering one additional `Die` at a
        time, try using `reduce()` instead.
    * If the order in which the dice are rolled is not important, you can use
        `apply_sorted()`. This is less efficient than either of the above two,
        but is still more efficient than `apply()`.

    Args:
        func: A function that takes one argument per input `Die` and returns an
            argument to `Die()`.
        *args: `func` will be called with all joint outcomes of these.
            Allowed arg types are:
            * Single outcome.
            * `Die`. All outcomes will be sent to `func`.
            * `Pool`. All sorted tuples of outcomes will be sent to `func`,
                as `pool.expand()`.
        again_depth: Forwarded to the final die constructor.
        again_end: Forwarded to the final die constructor.

    Returns:
        A `Die` constructed from the outputs of `func` and the product of the
        quantities of the dice.
    """
    if not callable(func):
        raise TypeError(
            'The first argument must be callable. Did you forget to provide a function?'
        )
    if len(args) == 0:
        return icepool.Die([func()],
                           again_depth=again_depth,
                           again_end=again_end)
    final_outcomes = []
    final_quantities = []
    for outcomes, final_quantity in iter_cartesian_product(*args):
        final_outcome = func(*outcomes)
        if final_outcome is not icepool.Reroll:
            final_outcomes.append(final_outcome)
            final_quantities.append(final_quantity)

    return icepool.Die(final_outcomes,
                       final_quantities,
                       again_depth=again_depth,
                       again_end=again_end)


class ApplySorted():
    """Class producing `apply_sorted` functions."""

    def __call__(
        self,
        func:
        'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.Again]',
        *dice: 'Outcome | icepool.Die',
        again_depth: int = 1,
        again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None
    ) -> 'icepool.Die[T]':
        """Calls the function with the sorted rolls of the dice.

        Returns:
            A `Die` with the
        """
        if not callable(func):
            raise TypeError(
                'The first argument must be callable. Did you forget to provide a function?'
            )
        pool = icepool.Pool(dice)
        # Expression evaluators are difficult to type.
        return pool.expand().map(  # type: ignore
            func,
            star=True,
            again_depth=again_depth,
            again_end=again_end)

    def __getitem__(
        self, index: int | slice | tuple[int, ...]
    ) -> 'Callable[..., icepool.Die[T]]':

        def result(
            func:
            'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.Again]',
            *dice: 'Outcome | icepool.Die',
            again_depth: int = 1,
            again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None
        ) -> 'icepool.Die[T]':
            """Calls the function with the with the sorted rolls of the dice with indexing."""
            if not callable(func):
                raise TypeError(
                    'The first argument must be callable. Did you forget to provide a function?'
                )
            if isinstance(index, int):
                return icepool.Pool(dice)[index].map(func,
                                                     again_depth=again_depth,
                                                     again_end=again_end)
            else:
                # Expression evaluators are difficult to type.
                return icepool.Pool(dice)[index].expand().map(  # type: ignore
                    func,
                    star=True,
                    again_depth=again_depth,
                    again_end=again_end)

        return result

    def lowest(self, keep=1, drop=0) -> 'Callable[..., icepool.Die[T]]':
        """Calls the function with the lowest sorted rolls of the dice."""

        def result(
            func:
            'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.Again]',
            *dice: 'Outcome | icepool.Die',
            again_depth: int = 1,
            again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None
        ) -> 'icepool.Die[T]':
            # Expression evaluators are difficult to type.
            return icepool.Pool(dice).lowest(keep,
                                             drop).expand().map(  # type: ignore
                                                 func,
                                                 star=True,
                                                 again_depth=again_depth,
                                                 again_end=again_end)

        return result

    def highest(self, keep=1, *, drop=0) -> 'Callable[..., icepool.Die[T]]':
        """Calls the function with the highest sorted rolls of the dice."""

        def result(
            func:
            'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.Again]',
            *dice: 'Outcome | icepool.Die',
            again_depth: int = 1,
            again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None
        ) -> 'icepool.Die[T]':
            # Expression evaluators are difficult to type.
            return icepool.Pool(dice).highest(
                keep, drop).expand().map(  # type: ignore
                    func,
                    star=True,
                    again_depth=again_depth,
                    again_end=again_end)

        return result

    def middle(
        self,
        keep: int = 1,
        *,
        tie: Literal['error', 'high', 'low'] = 'error'
    ) -> 'Callable[..., icepool.Die[T]]':
        """Calls the function with the middle sorted rolls of the dice."""

        def result(
            func:
            'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.Again]',
            *dice: 'Outcome | icepool.Die',
            again_depth: int = 1,
            again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None
        ) -> 'icepool.Die[T]':
            # Expression evaluators are difficult to type.
            return icepool.Pool(dice).middle(
                keep, tie=tie).expand().map(  # type: ignore
                    func,
                    star=True,
                    again_depth=again_depth,
                    again_end=again_end)

        return result


apply_sorted: Final = ApplySorted()
