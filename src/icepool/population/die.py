__docformat__ = 'google'

import icepool
import icepool.population.again
import icepool.population.format
import icepool.creation_args
import icepool.population.markov_chain
from icepool.collection.counts import Counts, CountsKeysView, CountsValuesView, CountsItemsView
from icepool.population.base import Population
from icepool.typing import U, Outcome, T_co, guess_star

import bisect
from collections import defaultdict
from functools import cached_property
import itertools
import math
import operator

from typing import Any, Callable, Collection, Container, Iterable, Iterator, Literal, Mapping, MutableMapping, Sequence, cast


def implicit_convert_to_die(
        outcome: T_co | 'Die[T_co]' | icepool.RerollType) -> 'Die[T_co]':
    """Converts a single outcome to a `Die` that always rolls that outcome.

    If the outcome is already a `Die`, it is returned as-is (even if it has
    multiple outcomes).

    Raises:
        `TypeError` if `Again` is given.
    """
    if isinstance(outcome, Die):
        return outcome
    if isinstance(outcome, icepool.AgainExpression):
        raise TypeError(
            'Again expression cannot be implicitly converted to a Die.')
    return Die([outcome])


class Die(Population[T_co]):
    """Sampling with replacement. Quantities represent weights.

    Dice are immutable. Methods do not modify the `Die` in-place;
    rather they return a `Die` representing the result.

    It *is* (mostly) well-defined to have a `Die` with zero-quantity outcomes.
    These can be useful in a few cases, such as:

    * `MultisetEvaluator` will iterate through zero-quantity outcomes,
        rather than possibly skipping that outcome. (Though in most cases it's
        better to use `MultisetEvaluator.alignment()`.)
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

    _data: Counts[T_co]

    @property
    def _new_type(self) -> type:
        return Die

    def __new__(
        cls,
        outcomes: Sequence | Mapping[Any, int],
        times: Sequence[int] | int = 1,
        *,
        again_depth: int = 1,
        again_end: 'Outcome | Die | icepool.RerollType | None' = None
    ) -> 'Die[T_co]':
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

        EXPERIMENTAL: Use `icepool.Again` to roll the dice again, usually with
        some modification. For example,

        ```
        Die([1, 2, 3, 4, 5, 6 + Again])
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
                * A `Sequence` of outcomes. Duplicates will contribute
                    quantity for each appearance.
                * A `Mapping` from outcomes to quantities.

                Individual outcomes can each be one of the following:

                * An outcome, which must be hashable and totally orderable.
                * A `Die`, which will be flattened into the result.
                    The quantity assigned to a `Die` is shared among its
                    outcomes. The total denominator will be scaled up if
                    necessary.
                * `icepool.Reroll`, which will drop itself from consideration.
                * EXPERIMENTAL: `icepool.Again`. See the main text for
                    explanation.
            times: Multiplies the quantity of each element of `outcomes`.
                `times` can either be a sequence of the same length as
                `outcomes` or a single `int` to apply to all elements of
                `outcomes`.
        Raises:
            ValueError: `None` is not a valid outcome for a `Die`.
        """
        if again_depth < 0:
            raise ValueError('again_depth cannot be negative.')

        # Check for Again.
        if icepool.population.again.contains_again(outcomes):
            if again_end is None:
                # Create a test die with `Again`s removed,
                # then find the zero.
                test: Die[T_co] = Die(outcomes,
                                      again_depth=0,
                                      again_end=icepool.Reroll)
                if len(test) == 0:
                    raise ValueError(
                        'If all outcomes contain Again, an explicit again_end must be provided.'
                    )
                again_end = test.zero().simplify()
            else:
                again_end = implicit_convert_to_die(again_end)
                if icepool.population.again.contains_again(again_end):
                    raise ValueError('again_end cannot itself contain Again.')

            if again_depth == 0:
                # Base case.
                outcomes = icepool.population.again.replace_agains(
                    outcomes, again_end)
            else:
                tail: Die[T_co] = Die(outcomes,
                                      times,
                                      again_depth=0,
                                      again_end=again_end)
                for _ in range(again_depth):
                    tail = Die(outcomes, times, again_depth=0, again_end=tail)
                return tail

        outcomes, times = icepool.creation_args.itemize(outcomes, times)
        # Agains have been replaced by this point.
        outcomes = cast(Sequence[T_co | Die[T_co] | icepool.RerollType],
                        outcomes)

        if len(outcomes) == 1 and times[0] == 1 and isinstance(
                outcomes[0], Die):
            return outcomes[0]

        counts: Counts[T_co] = icepool.creation_args.expand_args_for_die(
            outcomes, times)

        return Die._new_raw(counts)

    @classmethod
    def _new_raw(cls, data: Counts[T_co]) -> 'Die[T_co]':
        """Creates a new `Die` using already-processed arguments.

        Args:
            data: At this point, this is a Counts.
        """
        self = super(Population, cls).__new__(cls)
        self._data = data
        return self

    # Defined separately from the superclass to help typing.
    def unary_operator(self: 'icepool.Die[T_co]', op: Callable[..., U], *args,
                       **kwargs) -> 'icepool.Die[U]':
        """Performs the unary operation on the outcomes.

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
        return self._unary_operator(op, *args, **kwargs)

    def binary_operator(self, other: 'Die', op: Callable[..., U], *args,
                        **kwargs) -> 'Die[U]':
        """Performs the operation on pairs of outcomes.

        By the time this is called, the other operand has already been
        converted to a `Die`.

        If one side of a binary operator is a tuple and the other is not, the
        binary operator is applied to each element of the tuple with the
        non-tuple side. For example, the following are equivalent:

        ```
        cartesian_product(d6, d8) * 2
        cartesian_product(d6 * 2, d8 * 2)
        ```

        This is used for the standard binary operators
        `+, -, *, /, //, %, **, <<, >>, &, |, ^`
        and the standard binary comparators
        `<, <=, >=, >, ==, !=, cmp`.

        `==` and `!=` additionally set the truth value of the `Die` according to
        whether the dice themselves are the same or not.

        The `@` operator does NOT use this method directly.
        It rolls the left `Die`, which must have integer outcomes,
        then rolls the right `Die` that many times and sums the outcomes.

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
            new_outcome = op(outcome_self, outcome_other, *args, **kwargs)
            data[new_outcome] += quantity_self * quantity_other
        return self._new_type(data)

    # Basic access.

    def keys(self) -> CountsKeysView[T_co]:
        return self._data.keys()

    def values(self) -> CountsValuesView:
        return self._data.values()

    def items(self) -> CountsItemsView[T_co]:
        return self._data.items()

    def __getitem__(self, outcome, /) -> int:
        return self._data[outcome]

    def __iter__(self) -> Iterator[T_co]:
        return iter(self.keys())

    def __len__(self) -> int:
        """The number of outcomes. """
        return len(self._data)

    def __contains__(self, outcome) -> bool:
        return outcome in self._data

    # Quantity management.

    def simplify(self) -> 'Die[T_co]':
        """Divides all quantities by their greatest common denominator. """
        return icepool.Die(self._data.simplify())

    # Rerolls and other outcome management.

    def reroll(self,
               which: Callable[..., bool] | Collection[T_co] | None = None,
               /,
               *,
               star: bool | None = None,
               depth: int | None = None) -> 'Die[T_co]':
        """Rerolls the given outcomes.

        Args:
            which: Selects which outcomes to reroll. Options:
                * A single outcome to reroll.
                * A collection of outcomes to reroll.
                * A callable that takes an outcome and returns `True` if it
                    should be rerolled.
                * If not provided, the min outcome will be rerolled.
            star: Whether outcomes should be unpacked into separate arguments
                before sending them to a callable `which`.
                If not provided, this will be guessed based on the function
                signature.
            depth: The maximum number of times to reroll.
                If omitted, rerolls an unlimited number of times.

        Returns:
            A `Die` representing the reroll.
            If the reroll would never terminate, the result has no outcomes.
        """

        if which is None:
            outcome_set = {self.min_outcome()}
        elif callable(which):
            if star is None:
                star = guess_star(which)
            if star:

                # Need TypeVarTuple to check this.
                outcome_set = {
                    outcome for outcome in self.outcomes()
                    if which(*outcome)  # type: ignore
                }
            else:
                outcome_set = {
                    outcome for outcome in self.outcomes() if which(outcome)
                }
        else:
            # Collection.
            outcome_set = set(which)

        if depth is None:
            data = {
                outcome: quantity
                for outcome, quantity in self.items()
                if outcome not in outcome_set
            }
        elif depth < 0:
            raise ValueError('reroll depth cannot be negative.')
        else:
            total_reroll_quantity = sum(
                quantity for outcome, quantity in self.items()
                if outcome in outcome_set)
            total_stop_quantity = self.denominator() - total_reroll_quantity
            rerollable_factor = total_reroll_quantity**depth
            stop_factor = (self.denominator()**(depth + 1) - rerollable_factor *
                           total_reroll_quantity) // total_stop_quantity
            data = {
                outcome: (rerollable_factor *
                          quantity if outcome in outcome_set else stop_factor *
                          quantity) for outcome, quantity in self.items()
            }
        return icepool.Die(data)

    def filter(self,
               which: Callable[..., bool] | Collection[T_co],
               /,
               *,
               star: bool | None = None,
               depth: int | None = None) -> 'Die[T_co]':
        """Rerolls until getting one of the given outcomes.

        Essentially the complement of `reroll()`.

        Args:
            which: Selects which outcomes to reroll until. Options:
                * A callable that takes an outcome and returns `True` if it
                    should be accepted.
                * A collection of outcomes to reroll until.
            star: Whether outcomes should be unpacked into separate arguments
                before sending them to a callable `which`.
                If not provided, this will be guessed based on the function
                signature.
            depth: The maximum number of times to reroll.
                If omitted, rerolls an unlimited number of times.

        Returns:
            A `Die` representing the reroll.
            If the reroll would never terminate, the result has no outcomes.
        """

        if callable(which):
            if star is None:
                star = guess_star(which)
            if star:

                not_outcomes = {
                    outcome for outcome in self.outcomes()
                    if not which(*outcome)  # type: ignore
                }
            else:
                not_outcomes = {
                    outcome for outcome in self.outcomes() if not which(outcome)
                }
        else:
            not_outcomes = {
                not_outcome for not_outcome in self.outcomes()
                if not_outcome not in which
            }
        return self.reroll(not_outcomes, depth=depth)

    def truncate(self, min_outcome=None, max_outcome=None) -> 'Die[T_co]':
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

    def clip(self, min_outcome=None, max_outcome=None) -> 'Die[T_co]':
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

    def set_range(self: 'Die[int]',
                  min_outcome: int | None = None,
                  max_outcome: int | None = None) -> 'Die[int]':
        """Sets the outcomes of this `Die` to the given `int` range (inclusive).

        This may remove outcomes (if they are not within the range)
        and/or add zero-quantity outcomes (if they are in range but not present
        in this `Die`).

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

    def set_outcomes(self, outcomes: Iterable[T_co]) -> 'Die[T_co]':
        """Sets the set of outcomes to the argument.

        This may remove outcomes (if they are not present in the argument)
        and/or add zero-quantity outcomes (if they are not present in this `Die`).
        """
        data = {x: self.quantity(x) for x in outcomes}
        return icepool.Die(data)

    def trim(self) -> 'Die[T_co]':
        """Removes all zero-quantity outcomes. """
        data = {k: v for k, v in self.items() if v > 0}
        return icepool.Die(data)

    @cached_property
    def _popped_min(self) -> tuple['Die[T_co]', int]:
        die = Die._new_raw(self._data.remove_min())
        return die, self.quantities()[0]

    def _pop_min(self) -> tuple['Die[T_co]', int]:
        """A `Die` with the min outcome removed, and the quantity of the removed outcome.

        Raises:
            IndexError: If this `Die` has no outcome to pop.
        """
        return self._popped_min

    @cached_property
    def _popped_max(self) -> tuple['Die[T_co]', int]:
        die = Die._new_raw(self._data.remove_max())
        return die, self.quantities()[-1]

    def _pop_max(self) -> tuple['Die[T_co]', int]:
        """A `Die` with the max outcome removed, and the quantity of the removed outcome.

        Raises:
            IndexError: If this `Die` has no outcome to pop.
        """
        return self._popped_max

    # Mixtures.

    def map(
            self,
            repl:
        'Callable[..., U | Die[U] | icepool.RerollType | icepool.AgainExpression] | Mapping[T_co, U | Die[U] | icepool.RerollType | icepool.AgainExpression]',
            /,
            *extra_args,
            star: bool | None = None,
            repeat: int | None = 1,
            again_depth: int = 1,
            again_end: 'U | Die[U] | icepool.RerollType | None' = None
    ) -> 'Die[U]':
        """Maps outcomes of the `Die` to other outcomes.

        This is also useful for representing processes.

        As `icepool.map(repl, self, ...)`.
        """
        return icepool.map(repl,
                           self,
                           *extra_args,
                           star=star,
                           repeat=repeat,
                           again_depth=again_depth,
                           again_end=again_end)

    def map_and_time(
            self,
            repl:
        'Callable[..., T_co | Die[T_co] | icepool.RerollType] | Mapping[T_co, T_co | Die[T_co] | icepool.RerollType]',
            /,
            *extra_args,
            star: bool | None = None,
            repeat: int) -> 'Die[tuple[T_co, int]]':
        """Repeatedly map outcomes of the state to other outcomes, while also
        counting timesteps.

        This is useful for representing processes.

        As `map_and_time(repl, self, ...)`.
        """
        return icepool.map_and_time(repl,
                                    self,
                                    *extra_args,
                                    star=star,
                                    repeat=repeat)

    def explode(self,
                which: Collection[T_co] | Callable[..., bool] | None = None,
                *,
                star: bool | None = None,
                depth: int = 9,
                end=None) -> 'Die[T_co]':
        """Causes outcomes to be rolled again and added to the total.

        Args:
            which: Which outcomes to explode. Options:
                * A single outcome to explode.
                * An collection of outcomes to explode.
                * A callable that takes an outcome and returns `True` if it
                    should be exploded.
                * If not supplied, the max outcome will explode.
            star: Whether outcomes should be unpacked into separate arguments
                before sending them to a callable `which`.
                If not provided, this will be guessed based on the function
                signature.
            depth: The maximum number of additional dice to roll.
                If not supplied, a default value will be used.
            end: Once depth is reached, further explosions will be treated
                as this value. By default, a zero value will be used.
        """

        if which is None:
            outcome_set = {self.max_outcome()}
        elif callable(which):
            if star is None:
                star = guess_star(which)
            if star:
                # Need TypeVarTuple to type-check this.
                outcome_set = {
                    outcome for outcome in self.outcomes()
                    if which(*outcome)  # type: ignore
                }
            else:
                outcome_set = {
                    outcome for outcome in self.outcomes() if which(outcome)
                }
        else:
            if not which:
                return self
            outcome_set = set(which)

        if depth < 0:
            raise ValueError('depth cannot be negative.')
        elif depth == 0:
            return self

        def map_final(outcome):
            if outcome in outcome_set:
                return outcome + icepool.Again
            else:
                return outcome

        return self.map(map_final, again_depth=depth, again_end=end)

    def if_else(
            self,
            outcome_if_true: U | 'Die[U]',
            outcome_if_false: U | 'Die[U]',
            *,
            again_depth: int = 1,
            again_end: 'U | Die[U] | icepool.RerollType | None' = None
    ) -> 'Die[U]':
        """Ternary conditional operator.

        This replaces truthy outcomes with the first argument and falsy outcomes
        with the second argument.

        Args:
            again_depth: Forwarded to the final die constructor.
            again_end: Forwarded to the final die constructor.
        """
        return self.map(lambda x: bool(x)).map(
            {
                True: outcome_if_true,
                False: outcome_if_false
            },
            again_depth=again_depth,
            again_end=again_end)

    def is_in(self, target: Container[T_co], /) -> 'Die[bool]':
        """A die that returns True iff the roll of the die is contained in the target."""
        return self.map(lambda x: x in target)

    def count(self, rolls: int, target: Container[T_co], /) -> 'Die[int]':
        """Roll this dice a number of times and count how many are in the target."""
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
        their sum, use `die.map(sum)`.
        """
        if rolls in self._sum_cache:
            return self._sum_cache[rolls]

        if rolls < 0:
            result = -self._sum_all(-rolls)
        elif rolls == 0:
            result = self.zero().simplify()
        elif rolls == 1:
            result = self
        else:
            # Binary split seems to perform much worse.
            result = self + self._sum_all(rolls - 1)

        self._sum_cache[rolls] = result
        return result

    def __matmul__(self: 'Die[int]', other) -> 'Die':
        """Roll the left `Die`, then roll the right `Die` that many times and sum the outcomes."""
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

    def __rmatmul__(self, other: 'int | Die[int]') -> 'Die':
        """Roll the left `Die`, then roll the right `Die` that many times and sum the outcomes."""
        other = implicit_convert_to_die(other)
        return other.__matmul__(self)

    def pool(self, rolls: int | Sequence[int] = 1, /) -> 'icepool.Pool[T_co]':
        """Creates a `Pool` from this `Die`.

        You might subscript the pool immediately afterwards, e.g.
        `d6.pool(5)[-1, ..., 1]` takes the difference between the highest and
        lowest of 5d6.

        Args:
            rolls: The number of copies of this `Die` to put in the pool.
                Or, a sequence of one `int` per die acting as
                `keep_tuple`. Note that `...` cannot be used in the
                argument to this method, as the argument determines the size of
                the pool.
        """
        if isinstance(rolls, int):
            return icepool.Pool({self: rolls})
        else:
            pool_size = len(rolls)
            return icepool.Pool({self: pool_size})[rolls]

    def lowest(self, rolls: int, /, keep: int = 1, drop: int = 0) -> 'Die':
        """Roll several of this `Die` and return the lowest result, or the sum of some of the lowest.

        The outcomes should support addition and multiplication if `keep != 1`.

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
            return self._lowest_single(rolls)

        start = drop if drop > 0 else None
        stop = keep + (drop or 0)
        index = slice(start, stop)
        # Expression evaluators are difficult to type.
        return self.pool(rolls)[index].sum()  # type: ignore

    def _lowest_single(self, rolls: int, /) -> 'Die':
        """Roll this die several times and keep the lowest."""
        if rolls == 0:
            return self.zero().simplify()
        return icepool.from_cumulative(self.outcomes(),
                                       [x**rolls for x in self.quantities_ge()],
                                       reverse=True)

    def highest(self,
                rolls: int,
                /,
                keep: int = 1,
                drop: int = 0) -> 'Die[T_co]':
        """Roll several of this `Die` and return the highest result, or the sum of some of the highest.

        The outcomes should support addition and multiplication if `keep != 1`.

        Args:
            rolls: The number of dice to roll.
            keep: The number of dice to keep.
            drop: If provided, this many highest dice will be dropped before
                keeping.

        Returns:
            A `Die` representing the probability distribution of the sum.
        """
        if keep == 1 and drop == 0:
            return self._highest_single(rolls)
        start = -(keep + (drop or 0))
        stop = -drop if drop > 0 else None
        index = slice(start, stop)
        # Expression evaluators are difficult to type.
        return self.pool(rolls)[index].sum()  # type: ignore

    def _highest_single(self, rolls: int, /) -> 'Die[T_co]':
        """Roll this die several times and keep the highest."""
        if rolls == 0:
            return self.zero().simplify()
        return icepool.from_cumulative(self.outcomes(),
                                       [x**rolls for x in self.quantities_le()])

    def middle(self,
               rolls: int,
               /,
               keep: int = 1,
               *,
               tie: Literal['error', 'high', 'low'] = 'error') -> 'icepool.Die':
        """Roll several of this `Die` and sum the sorted results in the middle.

        The outcomes should support addition and multiplication if `keep != 1`.

        Args:
            rolls: The number of dice to roll.
            keep: The number of outcomes to sum. If this is greater than the
                current keep_size, all are kept.
            tie: What to do if `keep` is odd but the current keep_size
                is even, or vice versa.
                * 'error' (default): Raises `IndexError`.
                * 'high': The higher outcome is taken.
                * 'low': The lower outcome is taken.
        """
        # Expression evaluators are difficult to type.
        return self.pool(rolls).middle(keep, tie=tie).sum()  # type: ignore

    # Unary operators.

    def __neg__(self) -> 'Die[T_co]':
        return self.unary_operator(operator.neg)

    def __pos__(self) -> 'Die[T_co]':
        return self.unary_operator(operator.pos)

    def __invert__(self) -> 'Die[T_co]':
        return self.unary_operator(operator.invert)

    def abs(self) -> 'Die[T_co]':
        return self.unary_operator(operator.abs)

    __abs__ = abs

    def round(self, ndigits: int | None = None) -> 'Die':
        return self.unary_operator(round, ndigits)

    __round__ = round

    def trunc(self) -> 'Die':
        return self.unary_operator(math.trunc)

    __trunc__ = trunc

    def floor(self) -> 'Die':
        return self.unary_operator(math.floor)

    __floor__ = floor

    def ceil(self) -> 'Die':
        return self.unary_operator(math.ceil)

    __ceil__ = ceil

    @staticmethod
    def _zero(x):
        return x * 0

    def zero(self) -> 'Die[T_co]':
        """Zeros all outcomes of this die.

        This is done by multiplying all outcomes by `0`.

        The result will have the same denominator as this die.

        Raises:
            ValueError: If the zeros did not resolve to a single outcome.
        """
        result = self.unary_operator(Die._zero)
        if len(result) != 1:
            raise ValueError('zero() did not resolve to a single outcome.')
        return result

    def zero_outcome(self) -> T_co:
        """A zero-outcome for this die.

        E.g. `0` for a `Die` whose outcomes are `int`s.
        """
        return self.zero().outcomes()[0]

    # Binary operators.

    def __add__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.add)

    def __radd__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_operator(self, operator.add)

    def __sub__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.sub)

    def __rsub__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_operator(self, operator.sub)

    def __mul__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.mul)

    def __rmul__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_operator(self, operator.mul)

    def __truediv__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.truediv)

    def __rtruediv__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_operator(self, operator.truediv)

    def __floordiv__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.floordiv)

    def __rfloordiv__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_operator(self, operator.floordiv)

    def __pow__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.pow)

    def __rpow__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_operator(self, operator.pow)

    def __mod__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.mod)

    def __rmod__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_operator(self, operator.mod)

    def __lshift__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.lshift)

    def __rlshift__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_operator(self, operator.lshift)

    def __rshift__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.rshift)

    def __rrshift__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_operator(self, operator.rshift)

    def __and__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.and_)

    def __rand__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_operator(self, operator.and_)

    def __or__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.or_)

    def __ror__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_operator(self, operator.or_)

    def __xor__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.xor)

    def __rxor__(self, other) -> 'Die':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.binary_operator(self, operator.xor)

    # Comparators.

    def __lt__(self, other) -> 'Die[bool]':
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.lt)

    def __le__(self, other) -> 'Die[bool]':
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.le)

    def __ge__(self, other) -> 'Die[bool]':
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.ge)

    def __gt__(self, other) -> 'Die[bool]':
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.gt)

    # Equality operators. These produce a `DieWithTruth`.

    # The result has a truth value, but is not a bool.
    def __eq__(self, other) -> 'icepool.DieWithTruth[bool]':  # type: ignore
        other_die: Die = implicit_convert_to_die(other)

        def data_callback() -> Counts[bool]:
            return self.binary_operator(other_die, operator.eq)._data

        def truth_value_callback() -> bool:
            return self.equals(other)

        return icepool.DieWithTruth(data_callback, truth_value_callback)

    # The result has a truth value, but is not a bool.
    def __ne__(self, other) -> 'icepool.DieWithTruth[bool]':  # type: ignore
        other_die: Die = implicit_convert_to_die(other)

        def data_callback() -> Counts[bool]:
            return self.binary_operator(other_die, operator.ne)._data

        def truth_value_callback() -> bool:
            return not self.equals(other)

        return icepool.DieWithTruth(data_callback, truth_value_callback)

    def cmp(self, other) -> 'Die[int]':
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

    def sign(self) -> 'Die[int]':
        """Outcomes become 1 if greater than `zero()`, -1 if less than `zero()`, and 0 otherwise.

        Note that for `float`s, +0.0, -0.0, and nan all become 0.
        """
        return self.unary_operator(Die._sign)

    # Equality and hashing.

    def __bool__(self) -> bool:
        raise TypeError(
            'A `Die` only has a truth value if it is the result of == or !=. '
            'This could result from trying to use a die in an if-statement, '
            'in which case you should use `die.if_else()` instead. '
            'Or it could result from trying to use a `Die` inside a tuple or '
            'vector outcome, '
            'in which case you should use `tupleize()` or `vectorize().')

    @cached_property
    def _key_tuple(self) -> tuple:
        """A tuple that uniquely (as `equals()`) identifies this die.

        Apart from being hashable and totally orderable, this is not guaranteed
        to be in any particular format or have any other properties.
        """
        return tuple(self.items())

    @cached_property
    def _hash(self) -> int:
        return hash(self._key_tuple)

    def __hash__(self) -> int:
        return self._hash

    def equals(self, other, *, simplify: bool = False) -> bool:
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
            return self.simplify()._key_tuple == other.simplify()._key_tuple
        else:
            return self._key_tuple == other._key_tuple

    # Strings.

    def __repr__(self) -> str:
        inner = ', '.join(
            f'{outcome}: {weight}' for outcome, weight in self.items())
        return type(self).__qualname__ + '({' + inner + '})'
