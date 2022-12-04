__docformat__ = 'google'

import icepool
import icepool.again
import icepool.format
import icepool.creation_args
import icepool.markov_chain
from icepool.counts import Counts, CountsKeysView, CountsValuesView, CountsItemsView
from icepool.elementwise import unary_elementwise, binary_elementwise
from icepool.population import Population

import bisect
from collections import defaultdict
from functools import cached_property
import itertools
import math
import operator

from typing import Any, Callable, Container, Iterator, Mapping, MutableMapping, Sequence


def is_bare_outcome(outcome):
    """Returns `True` iff the outcome is not a `Mapping` or `Sequence` of a type that holds multiple outcomes.

    Currently product tuples are allowed.
    """
    if isinstance(outcome, Mapping):
        return False
    if isinstance(outcome, Sequence) and not isinstance(outcome,
                                                        (str, bytes, tuple)):
        return False
    return True


def implicit_convert_to_die(outcome) -> 'Die':
    """Converts a single outcome to a `Die` that always rolls that outcome.

    If the outcome is already a Die, it is returned as-is (even if it has
    multiple outcomes).

    Raises:
        `TypeError` if `Again` or multiple outcomes are given.
    """
    if isinstance(outcome, Die):
        return outcome
    if isinstance(outcome, icepool.Again):
        raise TypeError('Again object cannot be implicitly converted to a Die.')
    if not is_bare_outcome(outcome):
        raise TypeError(
            'Only single outcomes may be implicitly converted to a Die. '
            'Explicitly construct a Die for multiple outcomes.')
    return Die([outcome])


class Die(Population):
    """Sampling with replacement. Quantities represent weights.

    Dice are immutable. Methods do not modify the `Die` in-place;
    rather they return a `Die` representing the result.

    It *is* (mostly) well-defined to have a `Die` with zero-quantity outcomes.
    These can be useful in a few cases, such as:

    * `OutcomeCountEvaluator` will iterate through zero-quantity outcomes,
        rather than possibly skipping that outcome. (Though in most cases it's
        better to use `OutcomeCountEvaluator.alignment()`.)
    * `icepool.align()` and the like are convenient for making dice share the
        same set of outcomes.

    However, zero-quantity outcomes have a computational cost like any other
    outcome. Unless you have a specific use case in mind, it's best to leave
    them out.

    Most operators and methods will not introduce zero-quantity outcomes if
    their arguments do not have any; nor remove zero-quantity outcomes.

    It's also possible to have "empty" dice with no outcomes at all,
    though these have little use other than being sentinel values.
    """

    _data: Counts

    def _new_type(self) -> type:
        return Die

    def __new__(cls,
                outcomes: Mapping[Any, int] | Sequence,
                times: Sequence[int] | int = 1,
                *,
                again_depth: int = 1,
                again_end=None) -> 'Die':
        """Constructor for a `Die`.

        Don't confuse this with `d()`:

        * `Die([6])`: A `Die` that always rolls the `int` 6.
        * `d(6)`: A d6.

        Also, don't confuse this with `Pool()`:

        * `Die([1, 2, 3, 4, 5, 6])`: A d6.
        * `Pool([1, 2, 3, 4, 5, 6])`: A `Pool` of six dice that always rolls one
            of each number.

        Here are some different ways of constructing a d6:

        * Just import it: `from icepool import d6`
        * Use the `d()` function: `icepool.d(6)`
        * Use a d6 that you already have: `Die(d6)` or `Die([d6])`
        * Mix a d3 and a d3+3: `Die([d3, d3+3])`
        * Use a dict: `Die({1:1, 2:1, 3:1, 4:1, 5:1, 6:1})`
        * Give the faces as a sequence: `Die([1, 2, 3, 4, 5, 6])`

        All quantities must be non-negative, though they can be zero.

        Several methods and functions foward **kwargs to this constructor.
        However, these only affect the construction of the returned or yielded
        dice. Any other implicit conversions of arguments or operands to dice
        will be done with the default keyword arguments.

        EXPERIMENTAL: Use `icepool.Again()` to roll the dice again, usually with
        some modification. For example,

        ```
        Die([1, 2, 3, 4, 5, 6 + Again()])
        ```

        would be an exploding d6. Use the `again_depth` parameter to control
        the maximum depth. `again_depth` does not apply to `Reroll`.

        If the roll reaches the maximum depth, the `again_end` is used instead
        of rolling again. Options for `again_end` include:

        * No value (`None`), which will attempt to determine a zero value from
            the outcomes that don't involve `Again`.
        * A single outcome, or a `Die`.
        * `Reroll`, which will reroll any end roll involving `Again`.
        * You could also consider some sort of placeholder value such as
            `math.inf`.

        Denominator: For a flat set of outcomes, the denominator is just the
        sum of the corresponding quantities. If the outcomes themselves have
        secondary denominators, then the overall denominator is the primary
        denominator times the LCM of the outcome denominators.

        For example, `Die([d3, d4, d6])` has a final denominator of 36: 3 for
        the primary selection between the three secondary dice, times 12 for
        the LCM of 3, 4, and 6.

        Args:
            outcomes: The faces of the `Die`. This can be one of the following:
                * A `Mapping` from outcomes to quantities.
                    The outcomes of the `Mapping` will be "flattened" into the
                    result. This option will be taken in preference to treating
                    the `Mapping` itself as an outcome even if the `Mapping`
                    itself is hashable and totally orderable. This means that
                    `Die` and `Deck` will never be outcomes.
                * A tuple. Operators on dice with tuple outcomes
                    are performed element-wise. See `Die.unary_op` and
                    `Die.binary_op` for details.

                    Any tuple elements that indicate multiple outcomes will
                    expand the tuple according to their independent product
                    distribution. For example, `(d6, d6)` will expand to 36
                    ordered tuples with quantity 1 each. Use this carefully
                    since it may create a large number of outcomes.

                    Otherwise, the tuple is a single outcome. For example,
                    `Die((1, 2, 3, 4))` is *not* a d4, but a die that always
                    rolls the tuple `(1, 2, 3, 4)`.
                * `str` or `bytes`, which will be treated as a single outcome.
                * Any other sequence, such as a `list`. Each element will be
                    treated as a separate outcome, weighted once per occurrence
                    (unless it is at the top level and `times` is provided).
                * `icepool.Reroll`, which will drop itself from consideration.
                * Anything else will be treated as a single outcome.
                    Each outcome must be hashable, and the set of outcomes must
                    be totally orderable (after expansion). The same outcome can
                    appear multiple times, in which case the corresponding
                    quantities will be accumulated.
            times: Multiplies the quantity of each element of `outcomes`.
                `times` can either be a sequence of the same length as
                `outcomes` or a single `int` to apply to all elements of
                `outcomes`.
        Raises:
            ValueError: `None` is not a valid outcome for a `Die`.
        """
        if isinstance(outcomes, Die):
            if times == 1:
                return outcomes
            else:
                outcomes = outcomes._data
        else:
            if is_bare_outcome(outcomes):
                outcomes = [outcomes]
            # Check for Again.
            if icepool.again.contains_again(outcomes):
                if again_end is None:
                    # Create a test die with `Again`s removed,
                    # then find the zero.
                    test = Die(outcomes,
                               again_depth=0,
                               again_end=icepool.Reroll)
                    if len(test) == 0:
                        raise ValueError(
                            'If all outcomes contain Again, an explicit again_end must be provided.'
                        )
                    again_end = test.zero().simplify()
                else:
                    again_end = implicit_convert_to_die(again_end)
                    if icepool.again.contains_again(again_end):
                        raise ValueError(
                            'again_end cannot itself contain Again.')
                if again_depth == 0:
                    # Base case.
                    outcomes = icepool.again.sub_agains(outcomes, again_end)
                else:
                    tail = Die(outcomes,
                               times,
                               again_depth=again_depth - 1,
                               again_end=again_end)
                    outcomes = icepool.again.sub_agains(outcomes, tail)

        outcomes, times = icepool.creation_args.itemize(outcomes, times)

        if len(outcomes) == 1 and times[0] == 1 and isinstance(
                outcomes[0], Die):
            return outcomes[0]

        self = super(Population, cls).__new__(cls)
        self._data = icepool.creation_args.expand_args_for_die(outcomes, times)
        return self

    def unary_op(self, op: Callable, *args, **kwargs) -> 'Die':
        """Performs the unary operation on the outcomes.

        Operations on tuples are performed elementwise recursively. If you need
        some other specific behavior, use your own outcome class, or use `sub()`
        rather than an operator.

        This is used for the standard unary operators
        `-, +, abs, ~, round, trunc, floor, ceil`
        as well as the additional methods
        `zero, bool`.

        This is NOT used for the `[]` operator; when used directly, this is
        interpreted as a `Mapping` operation and returns the count corresponding
        to a given outcome. See `marginals()` for applying the `[]` operator to
        outcomes.

        Returns:
            A `Die` representing the result.

        Raises:
            ValueError: If tuples are of mismatched length.
        """
        data: MutableMapping[Any, int] = defaultdict(int)
        for outcome, quantity in self.items():
            new_outcome = unary_elementwise(outcome, op, *args, **kwargs)
            data[new_outcome] += quantity
        return icepool.Die(data)

    def binary_op(self, other: 'Die', op: Callable, *args, **kwargs) -> 'Die':
        """Performs the operation on pairs of outcomes.

        Operations on tuples are performed elementwise recursively. If you need
        some other specific behavior, use your own outcome class, or use `sub()`
        rather than an operator.

        By the time this is called, the other operand has already been
        converted to a `Die`.

        This is used for the standard binary operators
        `+, -, *, /, //, %, **, <<, >>, &, |, ^`.
        Note that `*` multiplies outcomes directly;
        it is not the same as `@`, which rolls the right side multiple times,
        or `d()`, which creates a standard die.

        The comparators (`<, <=, >=, >, ==, !=, cmp`) use a linear algorithm
        using the fact that outcomes are totally ordered.

        `==` and `!=` additionally set the truth value of the `Die` according to
        whether the dice themselves are the same or not.

        The `@` operator does NOT use this method directly.
        It rolls the left `Die`, which must have integer outcomes,
        then rolls the right `Die` that many times and sums the outcomes.
        Only the sum is performed element-wise.

        Returns:
            A `Die` representing the result.

        Raises:
            ValueError: If tuples are of mismatched length within one of the
                dice or between the dice.
        """
        data: MutableMapping[Any, int] = defaultdict(int)
        for (outcome_self,
             quantity_self), (outcome_other,
                              quantity_other) in itertools.product(
                                  self.items(), other.items()):
            new_outcome = binary_elementwise(outcome_self, outcome_other, op,
                                             *args, **kwargs)
            data[new_outcome] += quantity_self * quantity_other
        return icepool.Die(data)

    # Basic access.

    def keys(self) -> CountsKeysView:
        return self._data.keys()

    def values(self) -> CountsValuesView:
        return self._data.values()

    def items(self) -> CountsItemsView:
        return self._data.items()

    def __getitem__(self, outcome, /) -> int:
        return self._data[outcome]

    def __iter__(self) -> Iterator:
        return iter(self.keys())

    def __len__(self) -> int:
        """The number of outcomes. """
        return len(self._data)

    def __contains__(self, outcome) -> bool:
        return outcome in self._data

    # Quantity management.

    def simplify(self) -> 'Die':
        """Divides all quantities by their greatest common denominator. """
        return icepool.Die(self._data.simplify())

    # Rerolls and other outcome management.

    def reroll(self,
               outcomes: Callable[..., bool] | Container | None = None,
               *extra_args,
               depth: int | None = None,
               star: int = 0) -> 'Die':
        """Rerolls the given outcomes.

        Args:
            outcomes: Selects which outcomes to reroll. Options:
                * A callable that takes an outcome and returns `True` if it
                    should be rerolled.
                * A container of outcomes to reroll.
                * If not provided, the min outcome will be rerolled.
            *extra_args: These will be supplied to `outcomes` as extra
                positional arguments after the outcome argument(s).
                `extra_args` can only be supplied if `outcomes` is callable.
            depth: The maximum number of times to reroll.
                If omitted, rerolls an unlimited number of times.
            star: If set to `True` or 1, outcomes will be unpacked as
                `*outcome` before giving it to the `outcomes` function.
                If `outcomes` is not a callable, this has no effect.

        Returns:
            A `Die` representing the reroll.
            If the reroll would never terminate, the result has no outcomes.

        Raises:
            ValueError: If `extra_args` are supplied with a non-callable `outcomes`.
        """
        if extra_args and not callable(outcomes):
            raise ValueError(
                'Extra positional arguments are only valid if outcomes is callable.'
            )

        if outcomes is None:
            outcomes = {self.min_outcome()}
        elif callable(outcomes):
            if star:
                outcomes = {
                    outcome for outcome in self.outcomes()
                    if outcomes(*outcome, *extra_args)
                }
            else:
                outcomes = {
                    outcome for outcome in self.outcomes()
                    if outcomes(outcome, *extra_args)
                }

        if depth is None:
            data = {
                outcome: quantity
                for outcome, quantity in self.items()
                if outcome not in outcomes
            }
        else:
            total_reroll_quantity = sum(
                quantity for outcome, quantity in self.items()
                if outcome in outcomes)
            rerollable_factor = total_reroll_quantity**depth
            stop_factor = (self.denominator()**depth +
                           total_reroll_quantity**depth)
            data = {
                outcome:
                (rerollable_factor *
                 quantity if outcome in outcomes else stop_factor * quantity)
                for outcome, quantity in self.items()
            }
        return icepool.Die(data)

    def reroll_until(self,
                     outcomes: Callable[..., bool] | Container,
                     *extra_args,
                     depth: int | None = None,
                     star: int = 0) -> 'Die':
        """Rerolls until getting one of the given outcomes.

        Essentially the complement of `reroll()`.

        Args:
            outcomes: Selects which outcomes to reroll until. Options:
                * A callable that takes an outcome and returns `True` if it
                    should be accepted.
                * A container of outcomes to reroll until.
            *extra_args: These will be supplied to `outcomes` as extra
                positional arguments after the outcome argument(s).
                `extra_args` can only be supplied if `outcomes` is callable.
            depth: The maximum number of times to reroll.
                If omitted, rerolls an unlimited number of times.
            star: If set to `True` or 1, outcomes will be unpacked as
                `*outcome` before giving it to the `outcomes` function.
                If `outcomes` is not a callable, this has no effect.

        Returns:
            A `Die` representing the reroll.
            If the reroll would never terminate, the result has no outcomes.

        Raises:
            ValueError: If `extra_args` are supplied with a non-callable `outcomes`.
        """
        if extra_args and not callable(outcomes):
            raise ValueError(
                'Extra positional arguments are only valid if outcomes is callable.'
            )

        if callable(outcomes):
            if star:
                not_outcomes = {
                    outcome for outcome in self.outcomes()
                    if not outcomes(*outcome, *extra_args)
                }
            else:
                not_outcomes = {
                    outcome for outcome in self.outcomes()
                    if not outcomes(outcome, *extra_args)
                }
        else:
            not_outcomes = {
                not_outcome for not_outcome in self.outcomes()
                if not_outcome not in outcomes
            }
        return self.reroll(not_outcomes, depth=depth)

    def truncate(self, min_outcome=None, max_outcome=None) -> 'Die':
        """Truncates the outcomes of this `Die` to the given range.

        The endpoints are included in the result if applicable.
        If one of the arguments is not provided, that side will not be truncated.

        This effectively rerolls outcomes outside the given range.
        If instead you want to replace those outcomes with the nearest endpoint,
        use `clip()`.

        Not to be confused with `trunc(die)`, which performs integer truncation
        on each outcome.
        """
        if min_outcome is not None:
            start = bisect.bisect_left(self.outcomes(), min_outcome)
        else:
            start = None
        if max_outcome is not None:
            stop = bisect.bisect_right(self.outcomes(), max_outcome)
        else:
            stop = None
        data = {k: v for k, v in self.items()[start:stop]}
        return icepool.Die(data)

    def clip(self, min_outcome=None, max_outcome=None) -> 'Die':
        """Clips the outcomes of this `Die` to the given values.

        The endpoints are included in the result if applicable.
        If one of the arguments is not provided, that side will not be clipped.

        This is not the same as rerolling outcomes beyond this range;
        the outcome is simply adjusted to fit within the range.
        This will typically cause some quantity to bunch up at the endpoint.
        If you want to reroll outcomes beyond this range, use `truncate()`.
        """
        data: MutableMapping[Any, int] = defaultdict(int)
        for outcome, quantity in self.items():
            if min_outcome is not None and outcome <= min_outcome:
                data[min_outcome] += quantity
            elif max_outcome is not None and outcome >= max_outcome:
                data[max_outcome] += quantity
            else:
                data[outcome] += quantity
        return icepool.Die(data)

    def set_range(self,
                  min_outcome: int | None = None,
                  max_outcome: int | None = None) -> 'Die':
        """Sets the outcomes of this `Die` to the given `int` range (inclusive).

        Args:
            min_outcome: The min outcome of the result.
                If omitted, the min outcome of this `Die` will be used.
            max_outcome: The max outcome of the result.
                If omitted, the max outcome of this `Die` will be used.
        """
        if min_outcome is None:
            min_outcome = self.min_outcome()
        if max_outcome is None:
            max_outcome = self.max_outcome()

        return self.set_outcomes(range(min_outcome, max_outcome + 1))

    def set_outcomes(self, outcomes) -> 'Die':
        """Sets the set of outcomes to the argument.

        This may remove outcomes (if they are not present in the argument)
        and/or add zero-quantity outcomes (if they are not present in this `Die`).
        """
        data = {x: self.quantity(x) for x in outcomes}
        return icepool.Die(data)

    def trim(self) -> 'Die':
        """Removes all zero-quantity outcomes. """
        data = {k: v for k, v in self.items() if v > 0}
        return icepool.Die(data)

    @cached_property
    def _popped_min(self) -> tuple['Die', int]:
        die = icepool.Die(self._data.remove_min())
        return die, self.quantities()[0]

    def _pop_min(self) -> tuple['Die', int]:
        """A `Die` with the min outcome removed, and the quantity of the removed outcome.

        Raises:
            IndexError: If this `Die` has no outcome to pop.
        """
        return self._popped_min

    @cached_property
    def _popped_max(self) -> tuple['Die', int]:
        die = icepool.Die(self._data.remove_max())
        return die, self.quantities()[-1]

    def _pop_max(self) -> tuple['Die', int]:
        """A `Die` with the max outcome removed, and the quantity of the removed outcome.

        Raises:
            IndexError: If this `Die` has no outcome to pop.
        """
        return self._popped_max

    # Mixtures.

    def sub(self,
            repl: Callable | Mapping,
            /,
            repeat: int | None = 1,
            star: int = 0,
            again_depth: int = 1,
            again_end=None) -> 'Die':
        """Changes outcomes of the `Die` to other outcomes.

        You can think of this as `sub`stituting outcomes of this `Die` for other
        outcomes or dice. Or, as executing a `sub`routine based on the roll of
        this `Die`.

        EXPERIMENTAL: `Again`, `again_depth`, and `again_end` can be used as the
        `Die()` constructor. It is not advised to use these with `repeat` other
        than 1.

        Args:
            repl: One of the following:
                * A callable returning a new outcome for each old outcome.
                * A map from old outcomes to new outcomes.
                    Unmapped old outcomes stay the same.
                The new outcomes may be dice rather than just single outcomes.
                The special value `icepool.Reroll` will reroll that old outcome.
            repeat: `sub()` will be repeated with the same argument on the
                result this many times.

                EXPERIMENTAL: If set to `None`, the result will be as if `sub()`
                    were repeated an infinite number of times. In this case, the
                    result will be in simplest form.
            star: If set to `True` or 1, outcomes of `self` will be unpacked as
                `*outcome` before giving it to the `repl` function. `extra_dice`
                are not unpacked. If `repl` is not a callable, this has no
                effect.
            again_depth: Forwarded to the final die constructor.
            again_end: Forwarded to the final die constructor.

        Returns:
            The `Die` after the modification.
        """

        if repeat == 0:
            return self

        # Convert to a single-argument function.
        if callable(repl):
            if star:

                def transition_function(outcome):
                    return repl(*outcome)
            else:

                def transition_function(outcome):
                    return repl(outcome)
        else:
            # repl is a mapping.
            def transition_function(outcome):
                if outcome in repl:
                    return repl[outcome]
                else:
                    return outcome

        if repeat is not None:
            result = self
            for _ in range(repeat):
                result = icepool.apply(transition_function,
                                       result,
                                       again_depth=again_depth,
                                       again_end=again_end)
            return result
        else:
            # Infinite repeat.
            return icepool.markov_chain.absorbing_markov_chain(
                self, transition_function)

    def explode(self,
                outcomes: Container | Callable[..., bool] | None = None,
                *extra_args,
                depth: int = 9,
                end=None,
                star: int = 0) -> 'Die':
        """Causes outcomes to be rolled again and added to the total.

        Args:
            outcomes: Which outcomes to explode. Options:
                * An container of outcomes to explode.
                * A callable that takes an outcome and returns `True` if it
                    should be exploded.
                * If not supplied, the max outcome will explode.
            *extra_args: These will be supplied to `outcomes` as extra
                positional arguments after the outcome argument(s).
                `extra_args` can only be supplied if `outcomes` is callable.
            depth: The maximum number of additional dice to roll.
                If not supplied, a default value will be used.
            end: Once depth is reached, further explosions will be treated
                as this value. By default, a zero value will be used.
            star: If set to `True` or 1, outcomes will be unpacked as
                `*outcome` before giving it to the `outcomes` function.
                If `outcomes` is not a callable, this has no effect.

        Raises:
            ValueError: If `extra_args` are supplied with a non-callable `outcomes`.
        """
        if extra_args and not callable(outcomes):
            raise ValueError(
                'Extra positional arguments are only valid if outcomes is callable.'
            )

        if outcomes is None:
            outcomes = {self.max_outcome()}
        elif callable(outcomes):
            if star:
                outcomes = {
                    outcome for outcome in self.outcomes()
                    if outcomes(*outcome, *extra_args)
                }
            else:
                outcomes = {
                    outcome for outcome in self.outcomes()
                    if outcomes(outcome, *extra_args)
                }
        else:
            if not outcomes:
                return self

        if depth < 0:
            raise ValueError('depth cannot be negative.')
        elif depth == 0:
            return self

        def sub_func(outcome):
            if outcome in outcomes:
                return outcome + icepool.Again()
            else:
                return outcome

        return self.sub(sub_func, again_depth=depth, again_end=end)

    def if_else(self,
                outcome_if_true,
                outcome_if_false,
                /,
                again_depth: int = 1,
                again_end=None) -> 'Die':
        """Ternary conditional operator.

        This replaces truthy outcomes with the first argument and falsy outcomes
        with the second argument.

        Args:
            again_depth: Forwarded to the final die constructor.
            again_end: Forwarded to the final die constructor.
        """
        return self.bool().sub(lambda x: outcome_if_true
                               if x else outcome_if_false,
                               again_depth=again_depth,
                               again_end=again_end)

    def is_in(self, target: Container, /) -> 'Die':
        """A die that returns True iff the roll of the die is contained in the target."""
        return self.sub(lambda x: x in target)

    def count(self, rolls: int, target, /) -> 'Die':
        """Roll this dice a number of time and count how many are == the target."""
        return rolls @ (self == target)

    def count_in(self, rolls: int, target: Container, /) -> 'Die':
        """Roll this dice a number of time and count how many are in the target."""
        return rolls @ self.is_in(target)

    # Pools and sums.

    @cached_property
    def _sum_cache(self) -> MutableMapping[int, 'Die']:
        return {}

    def _sum_all(self, rolls: int, /) -> 'Die':
        """Roll this `Die` `rolls` times and sum the results.

        If `rolls` is negative, roll the `Die` `abs(rolls)` times and negate
        the result.

        If you instead want to replace tuple (or other sequence) outcomes with
        their sum, use `die.sub(sum)`.
        """
        if rolls in self._sum_cache:
            return self._sum_cache[rolls]

        if rolls < 0:
            result = -self._sum_all(-rolls)
        elif rolls == 0:
            result = self.zero()
        elif rolls == 1:
            result = self
        else:
            # Binary split seems to perform much worse.
            result = self + self._sum_all(rolls - 1)

        self._sum_cache[rolls] = result
        return result

    def __matmul__(self, other) -> 'Die':
        """Roll the left `Die`, then roll the right `Die` that many times and sum the outcomes."""
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)

        data: MutableMapping[int, Any] = defaultdict(int)

        max_abs_die_count = max(abs(self.min_outcome()),
                                abs(self.max_outcome()))
        for die_count, die_count_quantity in self.items():
            factor = other.denominator()**(max_abs_die_count - abs(die_count))
            subresult = other._sum_all(die_count)
            for outcome, subresult_quantity in subresult.items():
                data[
                    outcome] += subresult_quantity * die_count_quantity * factor

        return icepool.Die(data)

    def __rmatmul__(self, other) -> 'Die':
        """Roll the left `Die`, then roll the right `Die` that many times and sum the outcomes."""
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.__matmul__(self)

    def pool(self, rolls: int | Sequence[int], /) -> 'icepool.Pool':
        """Creates a `Pool` from this `Die`.

        You might subscript the pool immediately afterwards, e.g.
        `d6.pool(5)[-1, ..., 1]` takes the difference between the highest and
        lowest of 5d6.

        Args:
            rolls: The number of copies of this `Die` to put in the pool.
                Or, a sequence of one `int` per die acting as
                `sorted_roll_counts`. Note that `...` cannot be used in the
                argument to this method, as the argument determines the size of
                the pool.
        """
        if isinstance(rolls, int):
            return icepool.Pool({self: rolls})
        else:
            pool_size = len(rolls)
            return icepool.Pool({self: pool_size})[rolls]

    def keep_lowest(self, rolls: int, /, keep: int = 1, drop: int = 0) -> 'Die':
        """Roll several of this `Die` and sum the sorted results from the lowest.

        Args:
            rolls: The number of dice to roll. All dice will have the same
                outcomes as `self`.
            keep: The number of dice to keep.
            drop: If provided, this many lowest dice will be dropped before
                keeping.

        Returns:
            A `Die` representing the probability distribution of the sum.
        """
        if keep == 1 and drop == 0:
            return self._keep_lowest_single(rolls)

        start = drop if drop > 0 else None
        stop = keep + (drop or 0)
        sorted_roll_counts = slice(start, stop)
        return self.pool(rolls)[sorted_roll_counts].sum()

    def _keep_lowest_single(self, rolls: int, /) -> 'Die':
        """Faster algorithm for keeping just the single lowest `Die`. """
        if rolls == 0:
            return self.zero()
        return icepool.from_cumulative_quantities(
            self.outcomes(), [x**rolls for x in self.quantities_ge()],
            reverse=True)

    def keep_highest(self,
                     rolls: int,
                     /,
                     keep: int = 1,
                     drop: int = 0) -> 'Die':
        """Roll several of this `Die` and sum the sorted results from the highest.

        Args:
            rolls: The number of dice to roll.
            keep: The number of dice to keep.
            drop: If provided, this many highest dice will be dropped before
                keeping.

        Returns:
            A `Die` representing the probability distribution of the sum.
        """
        if keep == 1 and drop == 0:
            return self._keep_highest_single(rolls)
        start = -(keep + (drop or 0))
        stop = -drop if drop > 0 else None
        sorted_roll_counts = slice(start, stop)
        return self.pool(rolls)[sorted_roll_counts].sum()

    def _keep_highest_single(self, rolls: int, /) -> 'Die':
        """Faster algorithm for keeping just the single highest `Die`. """
        if rolls == 0:
            return self.zero()
        return icepool.from_cumulative_quantities(
            self.outcomes(), [x**rolls for x in self.quantities_le()])

    # Unary operators.

    def __neg__(self) -> 'Die':
        return self.unary_op(operator.neg)

    def __pos__(self) -> 'Die':
        return self.unary_op(operator.pos)

    def __invert__(self) -> 'Die':
        return self.unary_op(operator.invert)

    def abs(self) -> 'Die':
        return self.unary_op(operator.abs)

    __abs__ = abs

    def round(self, ndigits: int = None) -> 'Die':
        return self.unary_op(round, ndigits)

    __round__ = round

    def trunc(self) -> 'Die':
        return self.unary_op(math.trunc)

    __trunc__ = trunc

    def floor(self) -> 'Die':
        return self.unary_op(math.floor)

    __floor__ = floor

    def ceil(self) -> 'Die':
        return self.unary_op(math.ceil)

    __ceil__ = ceil

    @staticmethod
    def _zero(x):
        return type(x)()

    def zero(self) -> 'Die':
        """Zeros all outcomes of this die.

        This is done by calling the constructor for each outcome's type with no
        arguments.

        The result will have the same denominator as this die.

        Raises:
            ValueError: If the zeros did not resolve to a single outcome.
        """
        result = self.unary_op(Die._zero)
        if len(result) != 1:
            raise ValueError('zero() did not resolve to a single outcome.')
        return result

    def zero_outcome(self):
        """A zero-outcome for this die.

        E.g. `0` for a `Die` whose outcomes are `int`s.
        """
        return self.zero().outcomes()[0]

    # Binary operators.

    def __add__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_op(other, operator.add)

    def __radd__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_op(self, operator.add)

    def __sub__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_op(other, operator.sub)

    def __rsub__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_op(self, operator.sub)

    def __mul__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_op(other, operator.mul)

    def __rmul__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_op(self, operator.mul)

    def __truediv__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_op(other, operator.truediv)

    def __rtruediv__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_op(self, operator.truediv)

    def __floordiv__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_op(other, operator.floordiv)

    def __rfloordiv__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_op(self, operator.floordiv)

    def __pow__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_op(other, operator.pow)

    def __rpow__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_op(self, operator.pow)

    def __mod__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_op(other, operator.mod)

    def __rmod__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_op(self, operator.mod)

    def __lshift__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_op(other, operator.lshift)

    def __rlshift__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_op(self, operator.lshift)

    def __rshift__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_op(other, operator.rshift)

    def __rrshift__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_op(self, operator.rshift)

    def __and__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_op(other, operator.and_)

    def __rand__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_op(self, operator.and_)

    def __or__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_op(other, operator.or_)

    def __ror__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_op(self, operator.or_)

    def __xor__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_op(other, operator.xor)

    def __rxor__(self, other) -> 'Die':
        if isinstance(other, icepool.Again):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_op(self, operator.xor)

    # Comparators.

    @staticmethod
    def _lt_le(op: Callable, lo: 'Die', hi: 'Die') -> 'Die':
        """Linear algorithm for < and <=.

        Args:
            op: Either `operator.lt` or `operator.le`.
            lo: The `Die` on the left of `op`.
            hi: The `Die` on the right of `op`.
        """
        if lo.is_empty() or hi.is_empty():
            return icepool.Die([])

        d = lo.denominator() * hi.denominator()

        # One-outcome cases.

        if op(lo.max_outcome(), hi.min_outcome()):
            return icepool.Die({True: d})

        if not op(lo.min_outcome(), hi.max_outcome()):
            return icepool.Die({False: d})

        n = 0

        lo_cweight = 0
        lo_iter = iter(zip(lo.outcomes(), lo.quantities_le()))
        lo_outcome, next_lo_cweight = next(lo_iter)
        for hi_outcome, hi_weight in hi.items():
            while op(lo_outcome, hi_outcome):
                try:
                    lo_cweight = next_lo_cweight
                    lo_outcome, next_lo_cweight = next(lo_iter)
                except StopIteration:
                    break
            n += lo_cweight * hi_weight

        # We don't use bernoulli because it trims zero-quantity outcomes.
        return icepool.Die({False: d - n, True: n})

    def __lt__(self, other) -> 'Die':
        other = implicit_convert_to_die(other)
        return Die._lt_le(operator.lt, self, other)

    def __le__(self, other) -> 'Die':
        other = implicit_convert_to_die(other)
        return Die._lt_le(operator.le, self, other)

    def __ge__(self, other) -> 'Die':
        other = implicit_convert_to_die(other)
        return Die._lt_le(operator.le, other, self)

    def __gt__(self, other) -> 'Die':
        other = implicit_convert_to_die(other)
        return Die._lt_le(operator.lt, other, self)

    # Equality operators. These produce a `DieWithTruth`.

    @staticmethod
    def _eq(invert: bool, a: 'Die', b: 'Die') -> 'Counts':
        """Linear algorithm for == and !=.

        Args:
            invert: If `False`, this computes ==; if `True` this computes !=.
            a, b: The dice.
        """
        if a.is_empty() or b.is_empty():
            return Counts([])

        d = a.denominator() * b.denominator()

        # Single-outcome case.
        if (a.keys().isdisjoint(b.keys())):
            return Counts([(invert, d)])

        n = 0

        a_iter = iter(a.items())
        b_iter = iter(b.items())

        a_outcome, a_quantity = next(a_iter)
        b_outcome, b_quantity = next(b_iter)

        while True:
            try:
                if a_outcome == b_outcome:
                    n += a_quantity * b_quantity
                    a_outcome, a_quantity = next(a_iter)
                    b_outcome, b_quantity = next(b_iter)
                elif a_outcome < b_outcome:
                    a_outcome, a_quantity = next(a_iter)
                else:
                    b_outcome, b_quantity = next(b_iter)
            except StopIteration:
                if invert:
                    return Counts([(False, n), (True, d - n)])
                else:
                    return Counts([(False, d - n), (True, n)])

    def __eq__(self, other):
        other_die = implicit_convert_to_die(other)

        def data_callback():
            return Die._eq(False, self, other_die)

        def truth_value_callback():
            return self.equals(other)

        return icepool.DieWithTruth(data_callback, truth_value_callback)

    def __ne__(self, other):
        other_die = implicit_convert_to_die(other)

        def data_callback():
            return Die._eq(True, self, other_die)

        def truth_value_callback():
            return not self.equals(other)

        return icepool.DieWithTruth(data_callback, truth_value_callback)

    def cmp(self, other) -> 'Die':
        """A `Die` with outcomes 1, -1, and 0.

        The quantities are equal to the positive outcome of `self > other`,
        `self < other`, and the remainder respectively.

        This will include all three outcomes even if they have zero quantity.
        """
        other = implicit_convert_to_die(other)

        data = {}

        lt = self < other
        if True in lt:
            data[-1] = lt[True]
        eq = self == other
        if True in eq:
            data[0] = eq[True]
        gt = self > other
        if True in gt:
            data[1] = gt[True]

        return Die(data)

    @staticmethod
    def _sign(x) -> int:
        z = Die._zero(x)
        if x > z:
            return 1
        elif x < z:
            return -1
        else:
            return 0

    def sign(self) -> 'Die':
        """Outcomes become 1 if greater than `zero()`, -1 if less than `zero()`, and 0 otherwise.

        Note that for `float`s, +0.0, -0.0, and nan all become 0.
        """
        return self.unary_op(Die._sign)

    def bool(self) -> 'Die':
        """Takes `bool()` of all outcomes.

        Note that a `Die` as a whole is not considered to have a truth value
        unless it is the result of the `==` or `!=` operators.
        """
        return self.unary_op(bool)

    # Equality and hashing.

    def __bool__(self):
        raise ValueError(
            'A `Die` only has a truth value if it is the result of == or !=. '
            'If this is in the conditional of an if-statement, you probably '
            'want to use die.if_else() instead.')

    @cached_property
    def _key_tuple(self) -> tuple:
        return tuple(self.items())

    def key_tuple(self) -> tuple:
        """A tuple that uniquely (as `equals()`) identifies this die.

        Apart from being hashable and totally orderable, this is not guaranteed
        to be in any particular format or have any other properties.
        """
        return self._key_tuple

    @cached_property
    def _hash(self) -> int:
        return hash(self.key_tuple())

    def __hash__(self) -> int:
        return self._hash

    def equals(self, other, *, simplify=False):
        """`True` iff both dice have the same outcomes and quantities.

        This is `False` if `other` is not a `Die`, even if it would convert
        to an equal `Die`.

        Truth value does NOT matter.

        If one `Die` has a zero-quantity outcome and the other `Die` does not
        contain that outcome, they are treated as unequal by this function.

        The `==` and `!=` operators have a dual purpose; they return a `Die`
        with a truth value determined by this method.
        Only dice returned by these methods have a truth value. The data of
        these dice is lazily evaluated since the caller may only be interested
        in the `Die` value or the truth value.

        Args:
            simplify: If `True`, the dice will be simplified before comparing.
                Otherwise, e.g. a 2:2 coin is not `equals()` to a 1:1 coin.
        """
        if not isinstance(other, Die):
            return False

        if simplify:
            return self.simplify().key_tuple() == other.simplify().key_tuple()
        else:
            return self.key_tuple() == other.key_tuple()

    # Strings.

    def __repr__(self) -> str:
        inner = ', '.join(
            f'{outcome}: {weight}' for outcome, weight in self.items())
        return type(self).__qualname__ + '({' + inner + '})'
