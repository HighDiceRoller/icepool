__docformat__ = 'google'

import icepool
import icepool.itertools.markov_chain
from icepool.itertools.common import (TransitionCache, transition_and_star)

from collections import defaultdict
from fractions import Fraction
from functools import partial, update_wrapper

from typing import Any, Callable, Iterable, Iterator, Literal, Mapping, MutableMapping, Sequence, overload
from icepool.typing import Outcome, T


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
        again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None,
        _append_time: bool = False,
        **kwargs) -> 'icepool.Die[T]':
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
        repeat: This will be repeated with the same arguments on the
            result this many times, except the first of `args` will be replaced
            by the result of the previous iteration.

            Note that returning `Reroll` from `repl` will effectively reroll all
            arguments, including the first argument which represents the result
            of the process up to this point. If you only want to reroll the
            current stage, you can nest another `map` inside `repl`.

            EXPERIMENTAL: If set to `'inf'`, the result will be as if this
            were repeated an infinite number of times. In this case, the
            result will be in simplest form.
        time_limit: Similar to `repeat`, but will return early if a fixed point
            is reached. If both `repeat` and `time_limit` are provided
            (not recommended), `time_limit` takes priority.
        again_count, again_depth, again_end: Forwarded to the final die constructor.
        **kwargs: Keyword-only arguments can be forwarded to a callable `repl`.
            Unlike *args, outcomes will not be expanded, i.e. `Die` and
            `MultisetExpression` will be passed as-is. This is invalid for
            non-callable `repl`.
    """

    if len(args) == 0:
        if repeat != 1:
            raise ValueError('If no arguments are given, repeat must be 1.')
        if isinstance(repl, Mapping):
            raise ValueError(
                'If no arguments are given, repl must be a Mapping.')
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

    transition_cache = TransitionCache(repl, *extra_args, star=star, **kwargs)

    if time_limit is not None:
        repeat = time_limit

    if repeat == 'inf':
        # Infinite repeat.
        # T_co and U should be the same in this case.

        result: 'icepool.Die[T]'

        result, _ = icepool.itertools.markov_chain.absorbing_markov_chain(
            transition_cache, first_arg)
        return result
    elif repeat < 0:
        raise ValueError('repeat cannot be negative.')
    elif repeat == 0:
        return icepool.Die([first_arg])
    else:
        # TODO: starting states that are already absorbing
        total_non_break_die: 'icepool.Die[T]' = icepool.Die([first_arg])
        total_non_break_weight = 1
        total_break_die: 'icepool.Die[T]' = icepool.Die([])
        total_break_weight = 0
        non_break_outcomes: list
        break_outcomes: list
        # TODO: repeat vs. time_limit
        for i in range(repeat):
            if i < repeat - 1:
                (non_break_outcomes, non_break_quantities, break_outcomes,
                 break_quantities, reroll_quantity
                 ) = transition_cache.step_die(total_non_break_die)
                if _append_time:
                    break_outcomes = [
                        icepool.tupleize(outcome, i)
                        for outcome in break_outcomes
                    ]
                non_break_denominator = sum(non_break_quantities)
                break_denominator = sum(break_quantities)
                # TODO: reroll one level versus restart
                denominator = non_break_denominator + break_denominator + reroll_quantity
                if non_break_denominator > 0:
                    break_outcomes.append(total_break_die)
                    break_quantities.append(total_break_weight * denominator //
                                            total_non_break_weight)
                    total_break_die = icepool.Die(break_outcomes,
                                                  break_quantities)
                    total_break_weight = total_break_weight * (
                        denominator //
                        total_non_break_weight) + break_denominator
                    total_non_break_die = icepool.Die(non_break_outcomes,
                                                      non_break_quantities)
                    total_non_break_weight = non_break_denominator
                else:
                    if _append_time:
                        non_break_outcomes = [
                            icepool.tupleize(outcome, i)
                            for outcome in non_break_outcomes
                        ]
                    break_outcomes += non_break_outcomes
                    break_quantities += non_break_quantities
                    break_outcomes.append(total_break_die)
                    break_quantities.append(total_break_weight * denominator //
                                            total_non_break_weight)
                    return icepool.Die(break_outcomes,
                                       break_quantities,
                                       again_count=again_count,
                                       again_depth=again_depth,
                                       again_end=again_end)
            else:
                (final_outcomes, final_quantites, reroll_quantity
                 ) = transition_cache.step_final(total_non_break_die)
                if _append_time:
                    final_outcomes = [
                        icepool.tupleize(outcome, i)  # type: ignore
                        for outcome in final_outcomes
                    ]
                denominator = sum(final_quantites) + reroll_quantity
                final_outcomes.append(total_break_die)
                final_quantites.append(total_break_weight * denominator //
                                       total_non_break_weight)
                return icepool.Die(final_outcomes,
                                   final_quantites,
                                   again_count=again_count,
                                   again_depth=again_depth,
                                   again_end=again_end)

        raise RuntimeError('Should not be reached.')


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
    repeat: int | Literal['inf'] = 1,
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
    repeat: int | Literal['inf'] = 1,
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
    'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression] | Mapping[Any, T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression]',
        initial_state: 'T | icepool.Die[T]',
        /,
        *extra_args,
        star: bool | None = None,
        time_limit: int,
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
        time_limit: This will be repeated with the same arguments on the result
            up to this many times.
        **kwargs: Keyword-only arguments can be forwarded to a callable `repl`.
            Unlike *args, outcomes will not be expanded, i.e. `Die` and
            `MultisetExpression` will be passed as-is. This is invalid for
            non-callable `repl`.

    Returns:
        The `Die` after the modification.
    """
    # Use hidden _append_time argument.
    return map(
        repl,  # type: ignore
        initial_state,
        *extra_args,
        star=star,
        time_limit=time_limit,
        _append_time=True,
        **kwargs)


def mean_time_to_absorb(
        repl:
    'Callable[..., T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression] | Mapping[Any, T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression]',
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
            The special value `icepool.Reroll` will reroll that old outcome.
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

    _, result = icepool.itertools.markov_chain.absorbing_markov_chain(
        transition_cache, initial_state)
    return result


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
        if pool is icepool.Reroll:
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
