"""Free functions."""

__docformat__ = 'google'

import icepool
import icepool.population.markov_chain
from icepool.collection.vector import iter_cartesian_product
from icepool.typing import Outcome, T, U, guess_star

from fractions import Fraction
from collections import defaultdict
from functools import cache, partial, update_wrapper, wraps
import itertools
import math

from typing import Any, Callable, Final, Hashable, Iterable, Iterator, Literal, Mapping, MutableMapping, Sequence, TypeAlias, cast, overload


@cache
def d(sides: int, /) -> 'icepool.Die[int]':
    """A standard die, uniformly distributed from `1` to `sides` inclusive.

    Don't confuse this with `icepool.Die()`:

    * `icepool.Die([6])`: A `Die` that always rolls the integer 6.
    * `icepool.d(6)`: A d6.

    You can also import individual standard dice from the `icepool` module, e.g.
    `from icepool import d6`.
    """
    if not isinstance(sides, int):
        raise TypeError('sides must be an int.')
    elif sides < 1:
        raise ValueError('sides must be at least 1.')
    return icepool.Die(range(1, sides + 1))


@cache
def z(sides: int, /) -> 'icepool.Die[int]':
    """A die uniformly distributed from `0` to `sides - 1` inclusive.
    
    Equal to d(sides) - 1.
    """
    if not isinstance(sides, int):
        raise TypeError('sides must be an int.')
    elif sides < 1:
        raise ValueError('sides must be at least 1.')
    return icepool.Die(range(0, sides))


def __getattr__(key: str) -> 'icepool.Die[int]':
    """Implements the `dX` syntax for standard die with no parentheses.

    For example, `icepool.d6`.

    Note that this behavior can't be imported into the global scope, but the
    function `d()` can be.

    Similar for `zX` and `z()`.
    """
    if key[0] == 'd':
        try:
            return d(int(key[1:]))
        except ValueError:
            pass
    elif key[0] == 'z':
        try:
            return z(int(key[1:]))
        except ValueError:
            pass
    raise AttributeError(key)


def coin(n: int | float | Fraction,
         d: int = 1,
         /,
         *,
         max_denominator: int | None = None) -> 'icepool.Die[bool]':
    """A `Die` that rolls `True` with probability `n / d`, and `False` otherwise.

    If `n <= 0` or `n >= d` the result will have only one outcome.

    Args:
        n: An int numerator, or a non-integer probability.
        d: An int denominator. Should not be provided if the first argument is
            not an int.
    """
    if not isinstance(n, int):
        if d != 1:
            raise ValueError(
                'If a non-int numerator is provided, a denominator must not be provided.'
            )
        fraction = Fraction(n)
        if max_denominator is not None:
            fraction = fraction.limit_denominator(max_denominator)
        n = fraction.numerator
        d = fraction.denominator
    data = {}
    if n < d:
        data[False] = min(d - n, d)
    if n > 0:
        data[True] = min(n, d)

    return icepool.Die(data)


def stochastic_round(x,
                     /,
                     *,
                     max_denominator: int | None = None) -> 'icepool.Die[int]':
    """Randomly rounds a value up or down to the nearest integer according to the two distances.
        
    Specificially, rounds `x` up with probability `x - floor(x)` and down
    otherwise, producing a `Die` with up to two outcomes.

    Args:
        max_denominator: If provided, each rounding will be performed
            using `fractions.Fraction.limit_denominator(max_denominator)`.
            Otherwise, the rounding will be performed without
            `limit_denominator`.
    """
    integer_part = math.floor(x)
    fractional_part = x - integer_part
    return integer_part + coin(fractional_part,
                               max_denominator=max_denominator)


def one_hot(sides: int, /) -> 'icepool.Die[tuple[bool, ...]]':
    """A `Die` with `Vector` outcomes with one element set to `True` uniformly at random and the rest `False`.

    This is an easy (if somewhat expensive) way of representing how many dice
    in a pool rolled each number. For example, the outcomes of `10 @ one_hot(6)`
    are the `(ones, twos, threes, fours, fives, sixes)` rolled in 10d6.
    """
    data = []
    for i in range(sides):
        outcome = [False] * sides
        outcome[i] = True
        data.append(icepool.Vector(outcome))
    return icepool.Die(data)


def from_cumulative(outcomes: Sequence[T],
                    cumulative: 'Sequence[int] | Sequence[icepool.Die[bool]]',
                    *,
                    reverse: bool = False) -> 'icepool.Die[T]':
    """Constructs a `Die` from a sequence of cumulative values.

    Args:
        outcomes: The outcomes of the resulting die. Sorted order is recommended
            but not necessary.
        cumulative: The cumulative values (inclusive) of the outcomes in the
            order they are given to this function. These may be:
            * `int` cumulative quantities.
            * Dice representing the cumulative distribution at that point.
        reverse: Iff true, both of the arguments will be reversed. This allows
            e.g. constructing using a survival distribution.
    """
    if len(outcomes) == 0:
        return icepool.Die({})

    if reverse:
        outcomes = list(reversed(outcomes))
        cumulative = list(reversed(cumulative))  # type: ignore

    prev = 0
    d = {}

    if isinstance(cumulative[0], icepool.Die):
        cumulative = commonize_denominator(*cumulative)
        for outcome, die in zip(outcomes, cumulative):
            d[outcome] = die.quantity('!=', False) - prev
            prev = die.quantity('!=', False)
    elif isinstance(cumulative[0], int):
        cumulative = cast(Sequence[int], cumulative)
        for outcome, quantity in zip(outcomes, cumulative):
            d[outcome] = quantity - prev
            prev = quantity
    else:
        raise TypeError(
            f'Unsupported type {type(cumulative)} for cumulative values.')

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

    This is done using the CDF.

    Args:
        rv: A rv object (as `scipy.stats`).
        outcomes: An iterable of `int`s or `float`s that will be the outcomes
            of the resulting `Die`.
            If the distribution is discrete, outcomes must be `int`s.
            Some outcomes may be omitted if their probability is too small
            compared to the denominator.
        denominator: The denominator of the resulting `Die` will be set to this.
        **kwargs: These will be forwarded to `rv.cdf()`.
    """
    if hasattr(rv, 'pdf'):
        # Continuous distributions use midpoints.
        midpoints = [(a + b) / 2 for a, b in zip(outcomes[:-1], outcomes[1:])]
        cdf = rv.cdf(midpoints, **kwargs)
        quantities_le = tuple(int(round(x * denominator))
                              for x in cdf) + (denominator, )
    else:
        cdf = rv.cdf(outcomes, **kwargs)
        quantities_le = tuple(int(round(x * denominator)) for x in cdf)
    return from_cumulative(outcomes, quantities_le)


def _iter_outcomes(
        *args: 'Iterable[T | icepool.Population[T]] | T') -> Iterator[T]:
    if len(args) == 1:
        iter_args = cast('Iterable[T | icepool.Population[T]]', args[0])
    else:
        iter_args = cast('Iterable[T | icepool.Population[T]]', args)
    for arg in iter_args:
        if isinstance(arg, icepool.Population):
            yield from arg
        else:
            yield arg


@overload
def pointwise_max(
    arg0: 'Iterable[icepool.Die[T]]',
    /,
) -> 'icepool.Die[T]':
    ...


@overload
def pointwise_max(arg0: 'icepool.Die[T]', arg1: 'icepool.Die[T]', /, *args:
                  'icepool.Die[T]') -> 'icepool.Die[T]':
    ...


def pointwise_max(arg0, /, *more_args: 'icepool.Die[T]') -> 'icepool.Die[T]':
    """Selects the highest chance of rolling >= each outcome among the arguments.

    Naming not finalized.

    Specifically, for each outcome, the chance of the result rolling >= to that 
    outcome is the same as the highest chance of rolling >= that outcome among
    the arguments.

    Equivalently, any quantile in the result is the highest of that quantile
    among the arguments.

    This is useful for selecting from several possible moves where you are
    trying to get >= a threshold that is known but could change depending on the
    situation.
    
    Args:
        dice: Either an iterable of dice, or two or more dice as separate
            arguments.
    """
    if len(more_args) == 0:
        args = arg0
    else:
        args = (arg0, ) + more_args
    args = commonize_denominator(*args)
    outcomes = sorted_union(*args)
    cumulative = [
        min(die.quantity('<=', outcome) for die in args)
        for outcome in outcomes
    ]
    return from_cumulative(outcomes, cumulative)


@overload
def pointwise_min(
    arg0: 'Iterable[icepool.Die[T]]',
    /,
) -> 'icepool.Die[T]':
    ...


@overload
def pointwise_min(arg0: 'icepool.Die[T]', arg1: 'icepool.Die[T]', /, *args:
                  'icepool.Die[T]') -> 'icepool.Die[T]':
    ...


def pointwise_min(arg0, /, *more_args: 'icepool.Die[T]') -> 'icepool.Die[T]':
    """Selects the highest chance of rolling <= each outcome among the arguments.

    Naming not finalized.
    
    Specifically, for each outcome, the chance of the result rolling <= to that 
    outcome is the same as the highest chance of rolling <= that outcome among
    the arguments.

    Equivalently, any quantile in the result is the lowest of that quantile
    among the arguments.

    This is useful for selecting from several possible moves where you are
    trying to get <= a threshold that is known but could change depending on the
    situation.
    
    Args:
        dice: Either an iterable of dice, or two or more dice as separate
            arguments.
    """
    if len(more_args) == 0:
        args = arg0
    else:
        args = (arg0, ) + more_args
    args = commonize_denominator(*args)
    outcomes = sorted_union(*args)
    cumulative = [
        max(die.quantity('<=', outcome) for die in args)
        for outcome in outcomes
    ]
    return from_cumulative(outcomes, cumulative)


@overload
def min_outcome(arg: 'Iterable[T | icepool.Population[T]]', /) -> T:
    ...


@overload
def min_outcome(*args: 'T | icepool.Population[T]') -> T:
    ...


def min_outcome(*args: 'Iterable[T | icepool.Population[T]] | T') -> T:
    """The minimum possible outcome among the populations.
    
    Args:
        Populations or single outcomes. Alternatively, a single iterable argument of such.
    """
    return min(_iter_outcomes(*args))


@overload
def max_outcome(arg: 'Iterable[T | icepool.Population[T]]', /) -> T:
    ...


@overload
def max_outcome(*args: 'T | icepool.Population[T]') -> T:
    ...


def max_outcome(*args: 'Iterable[T | icepool.Population[T]] | T') -> T:
    """The maximum possible outcome among the populations.
    
    Args:
        Populations or single outcomes. Alternatively, a single iterable argument of such.
    """
    return max(_iter_outcomes(*args))


def consecutive(*args: Iterable[int]) -> Sequence[int]:
    """A minimal sequence of consecutive ints covering the argument sets."""
    start = min((x for x in itertools.chain(*args)), default=None)
    if start is None:
        return ()
    stop = max(x for x in itertools.chain(*args))
    return tuple(range(start, stop + 1))


def sorted_union(*args: Iterable[T]) -> tuple[T, ...]:
    """Merge sets into a sorted sequence."""
    if not args:
        return ()
    return tuple(sorted(set.union(*(set(arg) for arg in args))))


def commonize_denominator(
        *dice: 'T | icepool.Die[T]') -> tuple['icepool.Die[T]', ...]:
    """Scale the quantities of the dice so that all of them have the same denominator.

    The denominator is the LCM of the denominators of the arguments.

    Args:
        *dice: Any number of dice or single outcomes convertible to dice.

    Returns:
        A tuple of dice with the same denominator.
    """
    converted_dice = [icepool.implicit_convert_to_die(die) for die in dice]
    denominator_lcm = math.lcm(*(die.denominator() for die in converted_dice
                                 if die.denominator() > 0))
    return tuple(
        die.multiply_quantities(denominator_lcm //
                                die.denominator() if die.denominator() >
                                0 else 1) for die in converted_dice)


def reduce(
        function: 'Callable[[T, T], T | icepool.Die[T] | icepool.RerollType]',
        dice: 'Iterable[T | icepool.Die[T]]',
        *,
        initial: 'T | icepool.Die[T] | None' = None) -> 'icepool.Die[T]':
    """Applies a function of two arguments cumulatively to a sequence of dice.

    Analogous to the
    [`functools` function of the same name.](https://docs.python.org/3/library/functools.html#functools.reduce)

    Args:
        function: The function to map. The function should take two arguments,
            which are an outcome from each of two dice, and produce an outcome
            of the same type. It may also return `Reroll`, in which case the
            entire sequence is effectively rerolled.
        dice: A sequence of dice to map the function to, from left to right.
        initial: If provided, this will be placed at the front of the sequence
            of dice.
        again_count, again_depth, again_end: Forwarded to the final die constructor.
    """
    # Conversion to dice is not necessary since map() takes care of that.
    iter_dice = iter(dice)
    if initial is not None:
        result: 'icepool.Die[T]' = icepool.implicit_convert_to_die(initial)
    else:
        result = icepool.implicit_convert_to_die(next(iter_dice))
    for die in iter_dice:
        result = map(function, result, die)
    return result


def accumulate(
        function: 'Callable[[T, T], T | icepool.Die[T]]',
        dice: 'Iterable[T | icepool.Die[T]]',
        *,
        initial: 'T | icepool.Die[T] | None' = None
) -> Iterator['icepool.Die[T]']:
    """Applies a function of two arguments cumulatively to a sequence of dice, yielding each result in turn.

    Analogous to the
    [`itertools function of the same name`](https://docs.python.org/3/library/itertools.html#itertools.accumulate)
    , though with no default function and
    the same parameter order as `reduce()`.

    The number of results is equal to the number of elements of `dice`, with
    one additional element if `initial` is provided.

    Args:
        function: The function to map. The function should take two arguments,
            which are an outcome from each of two dice.
        dice: A sequence of dice to map the function to, from left to right.
        initial: If provided, this will be placed at the front of the sequence
            of dice.
    """
    # Conversion to dice is not necessary since map() takes care of that.
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
        result = map(function, result, die)
        yield result


def _canonicalize_transition_function(repl: 'Callable | Mapping',
                                      arg_count: int,
                                      star: bool | None) -> 'Callable':
    """Expresses repl as a function that takes arg_count variables."""
    if callable(repl):
        if star is None:
            star = guess_star(repl, arg_count)
        if star:
            func = cast(Callable, repl)
            return lambda o, *extra_args: func(*o, *extra_args)
        else:
            return repl
    elif isinstance(repl, Mapping):
        if arg_count != 1:
            raise ValueError(
                'If a mapping is provided for repl, len(args) must be 1.')
        mapping = cast(Mapping, repl)
        return lambda o: mapping.get(o, o)
    else:
        raise TypeError('repl must be a callable or a mapping.')


def map(
    repl:
    'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression] | Mapping[Any, T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression]',
    /,
    *args: 'Outcome | icepool.Die | icepool.MultisetExpression',
    star: bool | None = None,
    repeat: int | Literal['inf'] = 1,
    time_limit: int | Literal['inf'] | None = None,
    again_count: int | None = None,
    again_depth: int | None = None,
    again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None
) -> 'icepool.Die[T]':
    """Applies `func(outcome_of_die_0, outcome_of_die_1, ...)` for all joint outcomes, returning a Die.

    See `map_function` for a decorator version of this.

    Example: `map(lambda a, b: a + b, d6, d6)` is the same as d6 + d6.

    `map()` is flexible but not very efficient for more than a few dice.
    If at all possible, use `reduce()`, `MultisetExpression` methods, and/or
    `MultisetEvaluator`s. Even `Pool.expand()` (which sorts rolls) is more
    efficient than using `map` on the dice in order.

    `Again` can be used but is not recommended with `repeat` other than 1.

    Args:
        repl: One of the following:
            * A callable that takes in one outcome per element of args and
                produces a new outcome.
            * A mapping from old outcomes to new outcomes.
                Unmapped old outcomes stay the same.
                In this case args must have exactly one element.
            As with the `Die` constructor, the new outcomes:
            * May be dice rather than just single outcomes.
            * The special value `icepool.Reroll` will reroll that old outcome.
            * `tuples` containing `Population`s will be `tupleize`d into
                `Population`s of `tuple`s.
                This does not apply to subclasses of `tuple`s such as `namedtuple`
                or other classes such as `Vector`.
        *args: `func` will be called with all joint outcomes of these.
            Allowed arg types are:
            * Single outcome.
            * `Die`. All outcomes will be sent to `func`.
            * `MultisetExpression`. All sorted tuples of outcomes will be sent
                to `func`, as `MultisetExpression.expand()`. The expression must
                be fully bound.
        star: If `True`, the first of the args will be unpacked before giving
            them to `func`.
            If not provided, it will be guessed based on the signature of `func`
            and the number of arguments.
        repeat: This will be repeated with the same arguments on the
            result this many times, except the first of `args` will be replaced
            by the result of the previous iteration.

            Note that returning `Reroll` from `repl` will effectively reroll all
            arguments, including the first argument which represents the result
            of the process up to this point. If you only want to reroll the
            current stage, you can nest another `map` inside `repl`.

            EXPERIMENTAL: If set to `None`, the result will be as if this
            were repeated an infinite number of times. In this case, the
            result will be in simplest form.
        time_limit: Similar to `repeat`, but will return early if a fixed point
             is reached. If both `repeat` and `time_limit` are provided
             (not recommended), `time_limit` takes priority.
        again_count, again_depth, again_end: Forwarded to the final die constructor.
    """
    transition_function = _canonicalize_transition_function(
        repl, len(args), star)

    if len(args) == 0:
        if repeat != 1:
            raise ValueError('If no arguments are given, repeat must be 1.')
        return icepool.Die([transition_function()],
                           again_count=again_count,
                           again_depth=again_depth,
                           again_end=again_end)

    # Here len(args) is at least 1.

    first_arg = args[0]
    extra_args = args[1:]

    if time_limit is not None:
        repeat = time_limit

    if repeat == 'inf':
        # Infinite repeat.
        # T_co and U should be the same in this case.
        def unary_transition_function(state):
            return map(transition_function,
                       state,
                       *extra_args,
                       star=False,
                       again_count=again_count,
                       again_depth=again_depth,
                       again_end=again_end)

        return icepool.population.markov_chain.absorbing_markov_chain(
            icepool.Die([args[0]]), unary_transition_function)
    else:
        if repeat < 0:
            raise ValueError('repeat cannot be negative.')

        if repeat == 0:
            return icepool.Die([first_arg])
        elif repeat == 1 and time_limit is None:
            final_outcomes: 'list[T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression]' = []
            final_quantities: list[int] = []
            for outcomes, final_quantity in iter_cartesian_product(*args):
                final_outcome = transition_function(*outcomes)
                if final_outcome is not icepool.Reroll:
                    final_outcomes.append(final_outcome)
                    final_quantities.append(final_quantity)
            return icepool.Die(final_outcomes,
                               final_quantities,
                               again_count=again_count,
                               again_depth=again_depth,
                               again_end=again_end)
        else:
            result: 'icepool.Die[T]' = icepool.Die([first_arg])
            for _ in range(repeat):
                next_result = icepool.map(transition_function,
                                          result,
                                          *extra_args,
                                          star=False,
                                          again_count=again_count,
                                          again_depth=again_depth,
                                          again_end=again_end)
                if time_limit is not None and result.simplify(
                ) == next_result.simplify():
                    return result
                result = next_result
            return result


@overload
def map_function(
        function:
    'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression]',
        /) -> 'Callable[..., icepool.Die[T]]':
    ...


@overload
def map_function(
    function: None,
    /,
    *,
    star: bool | None = None,
    repeat: int | Literal['inf'] = 1,
    again_count: int | None = None,
    again_depth: int | None = None,
    again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None
) -> 'Callable[..., Callable[..., icepool.Die[T]]]':
    ...


@overload
def map_function(
    function:
    'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression] | None' = None,
    /,
    *,
    star: bool | None = None,
    repeat: int | Literal['inf'] = 1,
    again_count: int | None = None,
    again_depth: int | None = None,
    again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None
) -> 'Callable[..., icepool.Die[T]] | Callable[..., Callable[..., icepool.Die[T]]]':
    ...


def map_function(
    function:
    'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression] | None' = None,
    /,
    *,
    star: bool | None = None,
    repeat: int | Literal['inf'] = 1,
    again_count: int | None = None,
    again_depth: int | None = None,
    again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None
) -> 'Callable[..., icepool.Die[T]] | Callable[..., Callable[..., icepool.Die[T]]]':
    """Decorator that turns a function that takes outcomes into a function that takes dice.

    The result must be a `Die`.

    This is basically a decorator version of `map()` and produces behavior
    similar to AnyDice functions, though Icepool has different typing rules
    among other differences.

    `map_function` can either be used with no arguments:

    ```python
    @map_function
    def explode_six(x):
        if x == 6:
            return 6 + Again
        else:
            return x

    explode_six(d6, again_depth=2)
    ```

    Or with keyword arguments, in which case the extra arguments are bound:

    ```python
    @map_function(again_depth=2)
    def explode_six(x):
        if x == 6:
            return 6 + Again
        else:
            return x

    explode_six(d6)
    ```

    Args:
        again_count, again_depth, again_end: Forwarded to the final die constructor.
    """

    if function is not None:
        return update_wrapper(partial(map, function), function)
    else:

        def decorator(
            function:
            'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression]'
        ) -> 'Callable[..., icepool.Die[T]]':

            return update_wrapper(
                partial(map,
                        function,
                        star=star,
                        repeat=repeat,
                        again_count=again_count,
                        again_depth=again_depth,
                        again_end=again_end), function)

        return decorator


def map_and_time(
        repl:
    'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression] | Mapping[Any, T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression]',
        initial_state: 'T | icepool.Die[T]',
        /,
        *extra_args,
        star: bool | None = None,
        time_limit: int) -> 'icepool.Die[tuple[T, int]]':
    """Repeatedly map outcomes of the state to other outcomes, while also
    counting timesteps.

    This is useful for representing processes.

    The outcomes of the result are  `(outcome, time)`, where `time` is the
    number of repeats needed to reach an absorbing outcome (an outcome that
    only leads to itself), or `repeat`, whichever is lesser.

    This will return early if it reaches a fixed point.
    Therefore, you can set `repeat` equal to the maximum number of
    time you could possibly be interested in without worrying about
    it causing extra computations after the fixed point.

    Args:
        repl: One of the following:
            * A callable returning a new outcome for each old outcome.
            * A mapping from old outcomes to new outcomes.
                Unmapped old outcomes stay the same.
            The new outcomes may be dice rather than just single outcomes.
            The special value `icepool.Reroll` will reroll that old outcome.
        initial_state: The initial state of the process, which could be a
            single state or a `Die`.
        extra_args: Extra arguments to use, as per `map`. Note that these are
            rerolled at every time step.
        star: If `True`, the first of the args will be unpacked before giving
            them to `func`.
            If not provided, it will be guessed based on the signature of `func`
            and the number of arguments.
        time_limit: This will be repeated with the same arguments on the result
            up to this many times.

    Returns:
        The `Die` after the modification.
    """
    transition_function = _canonicalize_transition_function(
        repl, 1 + len(extra_args), star)

    result: 'icepool.Die[tuple[T, int]]' = map(lambda x: (x, 0), initial_state)

    # Note that we don't expand extra_args during the outer map.
    # This is needed to correctly evaluate whether each outcome is absorbing.
    def transition_with_steps(outcome_and_steps, extra_args):
        outcome, steps = outcome_and_steps
        next_outcome = map(transition_function, outcome, *extra_args)
        if icepool.population.markov_chain.is_absorbing(outcome, next_outcome):
            return outcome, steps
        else:
            return icepool.tupleize(next_outcome, steps + 1)

    return map(transition_with_steps,
               result,
               extra_args,
               time_limit=time_limit)


def map_to_pool(
    repl:
    'Callable[..., icepool.MultisetGenerator | Sequence[icepool.Die[T] | T] | Mapping[icepool.Die[T], int] | Mapping[T, int] | icepool.RerollType] | Mapping[Any, icepool.MultisetGenerator | Sequence[icepool.Die[T] | T] | Mapping[icepool.Die[T], int] | Mapping[T, int] | icepool.RerollType]',
    /,
    *args: 'Outcome | icepool.Die | icepool.MultisetExpression',
    star: bool | None = None,
    denominator: int | None = None
) -> 'icepool.MultisetGenerator[T, tuple[int]]':
    """EXPERIMENTAL: Applies `repl(outcome_of_die_0, outcome_of_die_1, ...)` for all joint outcomes, producing a MultisetGenerator.
    
    Args:
        repl: One of the following:
            * A callable that takes in one outcome per element of args and
                produces a `MultisetGenerator` or something convertible to a `Pool`.
            * A mapping from old outcomes to `MultisetGenerator` 
                or something convertible to a `Pool`.
                In this case args must have exactly one element.
            The new outcomes may be dice rather than just single outcomes.
            The special value `icepool.Reroll` will reroll that old outcome.
        star: If `True`, the first of the args will be unpacked before giving
            them to `repl`.
            If not provided, it will be guessed based on the signature of `repl`
            and the number of arguments.
        denominator: If provided, the denominator of the result will be this
            value. Otherwise it will be the minimum to correctly weight the
            pools.

    Returns:
        A `MultisetGenerator` representing the mixture of `Pool`s. Note  
        that this is not technically a `Pool`, though it supports most of 
        the same operations.

    Raises:
        ValueError: If `denominator` cannot be made consistent with the 
            resulting mixture of pools.
    """
    transition_function = _canonicalize_transition_function(
        repl, len(args), star)

    data: 'MutableMapping[icepool.MultisetGenerator[T, tuple[int]], int]' = defaultdict(
        int)
    for outcomes, quantity in iter_cartesian_product(*args):
        pool = transition_function(*outcomes)
        if pool is icepool.Reroll:
            continue
        elif isinstance(pool, icepool.MultisetGenerator):
            data[pool] += quantity
        else:
            data[icepool.Pool(pool)] += quantity
    # I couldn't get the covariance / contravariance to work.
    return icepool.MixtureGenerator(data,
                                    denominator=denominator)  # type: ignore
