__docformat__ = 'google'

import icepool
import icepool.population.markov_chain

from collections import defaultdict
from fractions import Fraction
from functools import partial, update_wrapper

from typing import Any, Callable, Iterable, Iterator, Literal, Mapping, MutableMapping, Sequence, cast, overload
from icepool.typing import Outcome, T, infer_star


def _canonicalize_transition_function(repl: 'Callable | Mapping',
                                      arg_count: int,
                                      star: bool | None) -> 'Callable':
    """Expresses repl as a function that takes arg_count variables."""
    if callable(repl):
        if star is None:
            star = infer_star(repl, arg_count)
        if star:
            func = cast(Callable, repl)
            return lambda o, *extra_args, **kwargs: func(
                *o, *extra_args, **kwargs)
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
        again_end: 'T | icepool.Die[T] | icepool.RerollType | None' = None,
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
            If not provided, it will be guessed based on the signature of `repl`
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
    transition_function = _canonicalize_transition_function(
        repl, len(args), star)

    if len(args) == 0:
        if repeat != 1:
            raise ValueError('If no arguments are given, repeat must be 1.')
        return icepool.Die([transition_function(**kwargs)],
                           again_count=again_count,
                           again_depth=again_depth,
                           again_end=again_end)

    # Here len(args) is at least 1.

    first_arg = args[0]
    extra_args = args[1:]

    if time_limit is not None:
        repeat = time_limit

    result: 'icepool.Die[T]'

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
                       again_end=again_end,
                       **kwargs)

        result, _ = icepool.population.markov_chain.absorbing_markov_chain(
            icepool.Die([first_arg]), unary_transition_function)
        return result
    else:
        if repeat < 0:
            raise ValueError('repeat cannot be negative.')

        if repeat == 0:
            return icepool.Die([first_arg])
        elif repeat == 1 and time_limit is None:
            final_outcomes: 'list[T | icepool.Die[T] | icepool.RerollType | icepool.AgainExpression]' = []
            final_quantities: list[int] = []
            for outcomes, final_quantity in icepool.iter_cartesian_product(
                    *args):
                final_outcome = transition_function(*outcomes, **kwargs)
                if final_outcome is not icepool.Reroll:
                    final_outcomes.append(final_outcome)
                    final_quantities.append(final_quantity)
            return icepool.Die(final_outcomes,
                               final_quantities,
                               again_count=again_count,
                               again_depth=again_depth,
                               again_end=again_end)
        else:
            result = icepool.Die([first_arg])
            for _ in range(repeat):
                next_result = map(transition_function,
                                  result,
                                  *extra_args,
                                  star=False,
                                  again_count=again_count,
                                  again_depth=again_depth,
                                  again_end=again_end,
                                  **kwargs)
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
    transition_function = _canonicalize_transition_function(
        repl, 1 + len(extra_args), star)

    result: 'icepool.Die[tuple[T, int]]' = map(lambda x: (x, 0), initial_state)

    # Note that we don't expand extra_args during the outer map.
    # This is needed to correctly evaluate whether each outcome is absorbing.
    def transition_with_steps(outcome_and_steps, extra_args):
        outcome, steps = outcome_and_steps
        next_outcome = map(transition_function,
                           outcome,
                           *extra_args,
                           star=False,
                           **kwargs)
        if icepool.population.markov_chain.is_absorbing(outcome, next_outcome):
            return outcome, steps
        else:
            return icepool.tupleize(next_outcome, steps + 1)

    return map(transition_with_steps,
               result,
               extra_args,
               time_limit=time_limit)


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
    transition_function = _canonicalize_transition_function(
        repl, 1 + len(extra_args), star)

    # Infinite repeat.
    # T_co and U should be the same in this case.
    def unary_transition_function(state):
        return map(transition_function,
                   state,
                   *extra_args,
                   star=False,
                   **kwargs)

    _, result = icepool.population.markov_chain.absorbing_markov_chain(
        icepool.Die([initial_state]), unary_transition_function)
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
    transition_function = _canonicalize_transition_function(
        repl, len(args), star)

    data: 'MutableMapping[icepool.MultisetExpression[T], int]' = defaultdict(
        int)
    for outcomes, quantity in icepool.iter_cartesian_product(*args):
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
