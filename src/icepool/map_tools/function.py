__docformat__ = 'google'

import icepool
import icepool.map_tools.markov_chain
from icepool.map_tools.common import TransitionType, transition_and_star
from icepool.map_tools.core_impl import TransitionCache, map_simple

from collections import defaultdict
from fractions import Fraction
from functools import partial, update_wrapper

from typing import Any, Callable, Iterable, Iterator, Literal, Mapping, MutableMapping, Sequence, cast, overload
from icepool.typing import Outcome, T


def final_map(transition_type: TransitionType,
              outcome: T) -> T | icepool.RerollType:
    if transition_type in [TransitionType.DEFAULT, TransitionType.BREAK]:
        return outcome
    else:
        return icepool.Reroll


@overload
def map(
        repl:
    'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression] | Mapping[Any, T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression]',
        /,
        *args: 'Outcome | icepool.Die | icepool.MultisetExpression',
        star: bool | None = None,
        repeat: None = None,
        again_count: int | None = None,
        again_depth: int | None = None,
        again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None,
        **kwargs) -> 'icepool.Die[T]':
    ...


@overload
def map(
        repl:
    'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression] | Mapping[Any, T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression]',
        /,
        *args: 'T | icepool.Die[T] | icepool.MultisetExpression[T]',
        star: bool | None = None,
        repeat: int | Literal['inf'],
        **kwargs) -> 'icepool.Die[T]':
    ...


def map(
        repl:
    'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression] | Mapping[Any, T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression]',
        /,
        *args: 'Outcome | icepool.Die | icepool.MultisetExpression',
        star: bool | None = None,
        repeat: int | Literal['inf'] | None = None,
        again_count: int | None = None,
        again_depth: int | None = None,
        again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None,
        **kwargs) -> 'icepool.Die[T]':
    """Applies `func(outcome_of_die_0, outcome_of_die_1, ...)` for all joint outcomes, returning a Die.

    See `map_function` for a decorator version of this.

    Example: `map(lambda a, b: a + b, d6, d6)` is the same as d6 + d6.

    `map()` is flexible but not very efficient for more than a few dice.
    If at all possible, use `reduce()`, `MultisetExpression` methods, and/or
    `MultisetEvaluator`s. Even `Pool.expand()` (which sorts rolls) is more
    efficient than using `map` on the dice in order.

    `Again` can be used but can't be combined with `repeat`.

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
        *args: `repl` will be called with all joint outcomes of these.
            Allowed arg types are:
            * Single outcome.
            * `Die`. All outcomes will be sent to `repl`.
            * `MultisetExpression`. All sorted tuples of outcomes will be sent
                to `repl`, as `MultisetExpression.expand()`.
        star: If `True`, the first of the args will be unpacked before giving
            them to `repl`.
            If not provided, it will be inferred based on the signature of `repl`
            and the number of arguments.
        repeat: If provided, `map` will be repeated with the same arguments on 
            the result this many times, except the first of `args` will be 
            replaced by the result of the previous iteration. In other words,
            this produces the result of a Markov process.

            `map(repeat)` will stop early if the entire state distribution has
            converged to absorbing states. You can force an absorption to a 
            desired state using `Break(state)`. Furthermore, if a state only
            leads to itself, reaching that state is considered an absorption.

            `Reroll` can be used to reroll the current stage, while `Restart`
            restarts the process from the beginning, effectively conditioning
            against that sequence of state transitions.

            `repeat` is not compatible with `Again`.

            EXPERIMENTAL: If set to `'inf'`, the result will be as if this
            were repeated an infinite number of times. In this case, the
            result will be in simplest form.
        again_count, again_depth, again_end: Forwarded to the final die constructor.
        **kwargs: Keyword-only arguments can be forwarded to a callable `repl`.
            Unlike *args, outcomes will not be expanded, i.e. `Die` and
            `MultisetExpression` will be passed as-is. This is invalid for
            non-callable `repl`.
    """

    if len(args) == 0:
        if repeat is not None:
            raise ValueError(
                'If no arguments are given, repeat cannot be used.')
        if isinstance(repl, Mapping):
            raise ValueError(
                'If no arguments are given, repl must be a callable.')
        return icepool.Die([repl(**kwargs)])

    # Here len(args) is at least 1.
    die_args: 'Sequence[T | icepool.Die[T]]' = [
        (
            arg.expand() if isinstance(arg, icepool.MultisetExpression) else
            arg  # type: ignore
        ) for arg in args
    ]

    first_arg = die_args[0]
    extra_args = die_args[1:]

    if repeat is None:
        return map_simple(repl,
                          first_arg,
                          *extra_args,
                          star=star,
                          again_count=again_count,
                          again_depth=again_depth,
                          again_end=again_end,
                          **kwargs)

    # No Agains allowed past here.
    repl = cast('Callable[..., T | icepool.Die[T] | icepool.RerollType]', repl)
    transition_cache = TransitionCache(repl, *extra_args, star=star, **kwargs)

    if repeat == 'inf':
        # Infinite repeat.
        # T_co and U should be the same in this case.
        return icepool.map_tools.markov_chain.absorbing_markov_chain_die(
            transition_cache, first_arg)
    elif repeat < 0:
        raise ValueError('repeat cannot be negative.')
    elif repeat == 0:
        return icepool.Die([first_arg])
    else:
        transition_die = transition_cache.self_loop_die(
            icepool.Die([first_arg]))
        for i in range(repeat):
            transition_die = transition_cache.step_transition_die(
                transition_die)
            if not any(transition_type == TransitionType.DEFAULT
                       for transition_type, _ in transition_die):
                break
        return transition_die.map(final_map, star=True)


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
        repeat: int | Literal['inf'] | None = None,
        again_count: int | None = None,
        again_depth: int | None = None,
        again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None,
        **kwargs) -> 'Callable[..., Callable[..., icepool.Die[T]]]':
    ...


@overload
def map_function(
    function:
    'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression] | None' = None,
    /,
    *,
    star: bool | None = None,
    repeat: int | Literal['inf'] | None = None,
    again_count: int | None = None,
    again_depth: int | None = None,
    again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None,
    **kwargs
) -> 'Callable[..., icepool.Die[T]] | Callable[..., Callable[..., icepool.Die[T]]]':
    ...


def map_function(
    function:
    'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression] | None' = None,
    /,
    *,
    star: bool | None = None,
    repeat: int | Literal['inf'] | None = None,
    again_count: int | None = None,
    again_depth: int | None = None,
    again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None,
    **kwargs
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
        return update_wrapper(partial(map, function, **kwargs), function)
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
                        again_end=again_end,
                        **kwargs), function)

        return decorator


def map_and_time(
        repl:
    'Callable[..., T | icepool.Die[T] | icepool.RerollType] | Mapping[Any, T | icepool.Die[T] | icepool.RerollType]',
        initial_state: 'T | icepool.Die[T]',
        /,
        *extra_args,
        star: bool | None = None,
        repeat: int,
        **kwargs) -> 'icepool.Die[tuple[T, int]]':
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
        repeat: This will be repeated with the same arguments on the result
            up to this many times.
        **kwargs: Keyword-only arguments can be forwarded to a callable `repl`.
            Unlike *args, outcomes will not be expanded, i.e. `Die` and
            `MultisetExpression` will be passed as-is. This is invalid for
            non-callable `repl`.

    Returns:
        The `Die` after the modification.
    """
    # Here len(args) is at least 1.
    extra_dice: 'Sequence[T | icepool.Die[T]]' = [
        (
            arg.expand() if isinstance(arg, icepool.MultisetExpression) else
            arg  # type: ignore
        ) for arg in extra_args
    ]

    transition_cache = TransitionCache(repl, *extra_dice, star=star, **kwargs)

    transition_die = transition_cache.self_loop_die_with_zero_time(
        icepool.Die([initial_state]))
    for i in range(repeat):
        transition_die = transition_cache.step_transition_die_with_time(
            transition_die)
        if not any(transition_type == TransitionType.DEFAULT
                   for transition_type, state, time in transition_die):
            break
    return transition_die.marginals[1:]


def mean_time_to_absorb(
        repl:
    'Callable[..., T | icepool.Die[T] | icepool.RerollType] | Mapping[Any, T | icepool.Die[T] | icepool.RerollType]',
        initial_state: 'T | icepool.Die[T]',
        /,
        *extra_args,
        star: bool | None = None,
        **kwargs) -> Fraction:
    """EXPERIMENTAL: The mean time for the process to reach an absorbing state.
    
    An absorbing state is one that maps to itself with unity probability.

    Args:
        repl: One of the following:
            * A callable returning a new outcome for each old outcome.
            * A mapping from old outcomes to new outcomes.
                Unmapped old outcomes stay the same.
            The new outcomes may be dice rather than just single outcomes.
            The special value `Reroll` will reroll that old outcome.
            Currently, `mean_time_to_absorb` does not support `Restart`.
        initial_state: The initial state of the process, which could be a
            single state or a `Die`.
        extra_args: Extra arguments to use, as per `map`. Note that these are
            rerolled at every time step.
        star: If `True`, the first of the args will be unpacked before giving
            them to `func`.
            If not provided, it will be guessed based on the signature of `func`
            and the number of arguments.
        **kwargs: Keyword-only arguments can be forwarded to a callable `repl`.
            Unlike *args, outcomes will not be expanded, i.e. `Die` and
            `MultisetExpression` will be passed as-is. This is invalid for
            non-callable `repl`.

    Returns:
        The mean time to absorption.
    """
    transition_cache = TransitionCache(repl, *extra_args, star=star, **kwargs)

    # Infinite repeat.
    # T_co and U should be the same in this case.

    return icepool.map_tools.markov_chain.absorbing_markov_chain_mean_absorption_time(
        transition_cache, initial_state)


def map_to_pool(
        repl:
    'Callable[..., icepool.MultisetExpression | Sequence[icepool.Die[T] | T] | Mapping[icepool.Die[T], int] | Mapping[T, int] | icepool.RerollType] | Mapping[Any, icepool.MultisetExpression | Sequence[icepool.Die[T] | T] | Mapping[icepool.Die[T], int] | Mapping[T, int] | icepool.RerollType]',
        /,
        *args: 'Outcome | icepool.Die | icepool.MultisetExpression',
        star: bool | None = None,
        **kwargs) -> 'icepool.MultisetExpression[T]':
    """EXPERIMENTAL: Applies `repl(outcome_of_die_0, outcome_of_die_1, ...)` for all joint outcomes, producing a MultisetExpression.
    
    Args:
        repl: One of the following:
            * A callable that takes in one outcome per element of args and
                produces a `MultisetExpression` or something convertible to a `Pool`.
            * A mapping from old outcomes to `MultisetExpression` 
                or something convertible to a `Pool`.
                In this case args must have exactly one element.
            The new outcomes may be dice rather than just single outcomes.
            The special value `icepool.Reroll` will reroll that old outcome.
        star: If `True`, the first of the args will be unpacked before giving
            them to `repl`.
            If not provided, it will be guessed based on the signature of `repl`
            and the number of arguments.
        **kwargs: Keyword-only arguments can be forwarded to a callable `repl`.
            Unlike *args, outcomes will not be expanded, i.e. `Die` and
            `MultisetExpression` will be passed as-is. This is invalid for
            non-callable `repl`.

    Returns:
        A `MultisetExpression` representing the mixture of `Pool`s. Note  
        that this is not technically a `Pool`, though it supports most of 
        the same operations.

    Raises:
        ValueError: If `denominator` cannot be made consistent with the 
            resulting mixture of pools.
    """
    transition_function, star = transition_and_star(repl, len(args), star)

    data: 'MutableMapping[icepool.MultisetExpression[T], int]' = defaultdict(
        int)
    for outcomes, quantity in icepool.iter_cartesian_product(*args):
        if star:
            pool = transition_function(*outcomes[0], *outcomes[1:], **kwargs)
        else:
            pool = transition_function(*outcomes, **kwargs)
        if pool in icepool.REROLL_TYPES:
            continue
        elif isinstance(pool, icepool.MultisetExpression):
            data[pool] += quantity
        else:
            data[icepool.Pool(pool)] += quantity
    # I couldn't get the covariance / contravariance to work.
    return icepool.MultisetMixture(data)  # type: ignore


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
