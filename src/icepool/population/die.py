__docformat__ = 'google'

from types import EllipsisType
import icepool
import icepool.population.again
import icepool.population.format
import icepool.creation_args
import icepool.population.markov_chain
from icepool.collection.counts import Counts, CountsKeysView, CountsValuesView, CountsItemsView
from icepool.population.base import Population
from icepool.population.keep import lowest_slice, highest_slice, canonical_slice
from icepool.typing import U, ImplicitConversionError, Outcome, T_co, guess_star

import bisect
from collections import defaultdict
from fractions import Fraction
from functools import cached_property
import itertools
import math
import operator

from typing import Any, Callable, Collection, Container, Iterable, Iterator, Literal, Mapping, MutableMapping, Sequence, Set, cast, overload


def implicit_convert_to_die(
        outcome: T_co | 'Die[T_co]' | icepool.RerollType) -> 'Die[T_co]':
    """Converts a single outcome to a `Die` that always rolls that outcome.

    If the outcome is already a `Die`, it is returned as-is (even if it has
    multiple outcomes).

    Raises:
        `ImplicitConversionError` if `Again` is given.
    """
    if isinstance(outcome, Die):
        return outcome
    if isinstance(outcome, icepool.AgainExpression):
        raise ImplicitConversionError(
            'Again expression cannot be implicitly converted to a Die.')
    return Die([outcome])


class Die(Population[T_co]):
    """Sampling with replacement. Quantities represent weights.

    Dice are immutable. Methods do not modify the `Die` in-place;
    rather they return a `Die` representing the result.

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
        again_count: int | None = None,
        again_depth: int | None = None,
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

        All quantities must be non-negative. Outcomes with zero quantity will be
        omitted.

        Several methods and functions foward **kwargs to this constructor.
        However, these only affect the construction of the returned or yielded
        dice. Any other implicit conversions of arguments or operands to dice
        will be done with the default keyword arguments.

        EXPERIMENTAL: Use `icepool.Again` to roll the dice again, usually with
        some modification. See the `Again` documentation for details.

        Denominator: For a flat set of outcomes, the denominator is just the
        sum of the corresponding quantities. If the outcomes themselves have
        secondary denominators, then the overall denominator will be minimized
        while preserving the relative weighting of the primary outcomes.

        Args:
            outcomes: The faces of the `Die`. This can be one of the following:
                * A `Sequence` of outcomes. Duplicates will contribute
                    quantity for each appearance.
                * A `Mapping` from outcomes to quantities.

                Individual outcomes can each be one of the following:

                * An outcome, which must be hashable and totally orderable.
                    * For convenience, `tuple`s containing `Population`s will be
                        `tupleize`d into a `Population` of `tuple`s.
                        This does not apply to subclasses of `tuple`s such as `namedtuple`
                        or other classes such as `Vector`.
                * A `Die`, which will be flattened into the result.
                    The quantity assigned to a `Die` is shared among its
                    outcomes. The total denominator will be scaled up if
                    necessary.
                * `icepool.Reroll`, which will drop itself from consideration.
                * EXPERIMENTAL: `icepool.Again`. See the documentation for
                    `Again` for details.
            times: Multiplies the quantity of each element of `outcomes`.
                `times` can either be a sequence of the same length as
                `outcomes` or a single `int` to apply to all elements of
                `outcomes`.
            again_count, again_depth, again_end: These affect how `Again`
                expressions are handled. See the `Again` documentation for
                details.
        Raises:
            ValueError: `None` is not a valid outcome for a `Die`.
        """
        outcomes, times = icepool.creation_args.itemize(outcomes, times)

        # Check for Again.
        if icepool.population.again.contains_again(outcomes):
            if again_count is not None:
                if again_depth is not None:
                    raise ValueError(
                        'At most one of again_count and again_depth may be used.'
                    )
                if again_end is not None:
                    raise ValueError(
                        'again_end cannot be used with again_count.')
                return icepool.population.again.evaluate_agains_using_count(
                    outcomes, times, again_count)
            else:
                if again_depth is None:
                    again_depth = 1
                return icepool.population.again.evaluate_agains_using_depth(
                    outcomes, times, again_depth, again_end)

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

        ```python
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

    def _select_outcomes(self, which: Callable[..., bool] | Collection[T_co],
                         star: bool | None) -> Set[T_co]:
        """Returns a set of outcomes of self that fit the given condition."""
        if callable(which):
            if star is None:
                star = guess_star(which)
            if star:
                # Need TypeVarTuple to check this.
                return {
                    outcome
                    for outcome in self.outcomes()
                    if which(*outcome)  # type: ignore
                }
            else:
                return {
                    outcome
                    for outcome in self.outcomes() if which(outcome)
                }
        else:
            # Collection.
            return set(outcome for outcome in self.outcomes()
                       if outcome in which)

    def reroll(self,
               which: Callable[..., bool] | Collection[T_co] | None = None,
               /,
               *,
               star: bool | None = None,
               depth: int | None) -> 'Die[T_co]':
        """Rerolls the given outcomes.

        Args:
            which: Selects which outcomes to reroll. Options:
                * A collection of outcomes to reroll.
                * A callable that takes an outcome and returns `True` if it
                    should be rerolled.
                * If not provided, the min outcome will be rerolled.
            star: Whether outcomes should be unpacked into separate arguments
                before sending them to a callable `which`.
                If not provided, this will be guessed based on the function
                signature.
            depth: The maximum number of times to reroll.
                If `None`, rerolls an unlimited number of times.

        Returns:
            A `Die` representing the reroll.
            If the reroll would never terminate, the result has no outcomes.
        """

        if which is None:
            outcome_set = {self.min_outcome()}
        else:
            outcome_set = self._select_outcomes(which, star)

        if depth is None:
            data = {
                outcome: quantity
                for outcome, quantity in self.items()
                if outcome not in outcome_set
            }
        elif depth < 0:
            raise ValueError('reroll depth cannot be negative.')
        else:
            total_reroll_quantity = sum(quantity
                                        for outcome, quantity in self.items()
                                        if outcome in outcome_set)
            total_stop_quantity = self.denominator() - total_reroll_quantity
            rerollable_factor = total_reroll_quantity**depth
            stop_factor = (self.denominator()**(depth + 1) - rerollable_factor
                           * total_reroll_quantity) // total_stop_quantity
            data = {
                outcome: (rerollable_factor *
                          quantity if outcome in outcome_set else stop_factor *
                          quantity)
                for outcome, quantity in self.items()
            }
        return icepool.Die(data)

    def filter(self,
               which: Callable[..., bool] | Collection[T_co],
               /,
               *,
               star: bool | None = None,
               depth: int | None) -> 'Die[T_co]':
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
                If `None`, rerolls an unlimited number of times.

        Returns:
            A `Die` representing the reroll.
            If the reroll would never terminate, the result has no outcomes.
        """

        if callable(which):
            if star is None:
                star = guess_star(which)
            if star:

                not_outcomes = {
                    outcome
                    for outcome in self.outcomes()
                    if not which(*outcome)  # type: ignore
                }
            else:
                not_outcomes = {
                    outcome
                    for outcome in self.outcomes() if not which(outcome)
                }
        else:
            not_outcomes = {
                not_outcome
                for not_outcome in self.outcomes() if not_outcome not in which
            }
        return self.reroll(not_outcomes, depth=depth)

    def split(self,
              which: Callable[..., bool] | Collection[T_co] | None = None,
              /,
              *,
              star: bool | None = None):
        """Splits this die into one containing selected items and another containing the rest.

        The total denominator is preserved.
        
        Equivalent to `self.filter(), self.reroll()`.

        Args:
            which: Selects which outcomes to reroll until. Options:
                * A callable that takes an outcome and returns `True` if it
                    should be accepted.
                * A collection of outcomes to reroll until.
            star: Whether outcomes should be unpacked into separate arguments
                before sending them to a callable `which`.
                If not provided, this will be guessed based on the function
                signature.
        """
        if which is None:
            outcome_set = {self.min_outcome()}
        else:
            outcome_set = self._select_outcomes(which, star)

        selected = {}
        not_selected = {}
        for outcome, count in self.items():
            if outcome in outcome_set:
                selected[outcome] = count
            else:
                not_selected[outcome] = count

        return Die(selected), Die(not_selected)

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
        This will typically cause some quantity to bunch up at the endpoint(s).
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

    # Processes.

    def map(
        self,
        repl:
        'Callable[..., U | Die[U] | icepool.RerollType | icepool.AgainExpression] | Mapping[T_co, U | Die[U] | icepool.RerollType | icepool.AgainExpression]',
        /,
        *extra_args,
        star: bool | None = None,
        repeat: int | Literal['inf'] = 1,
        time_limit: int | Literal['inf'] | None = None,
        again_count: int | None = None,
        again_depth: int | None = None,
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
                           time_limit=time_limit,
                           again_count=again_count,
                           again_depth=again_depth,
                           again_end=again_end)

    def map_and_time(
            self,
            repl:
        'Callable[..., T_co | Die[T_co] | icepool.RerollType] | Mapping[T_co, T_co | Die[T_co] | icepool.RerollType]',
            /,
            *extra_args,
            star: bool | None = None,
            time_limit: int) -> 'Die[tuple[T_co, int]]':
        """Repeatedly map outcomes of the state to other outcomes, while also
        counting timesteps.

        This is useful for representing processes.

        As `map_and_time(repl, self, ...)`.
        """
        return icepool.map_and_time(repl,
                                    self,
                                    *extra_args,
                                    star=star,
                                    time_limit=time_limit)

    def time_to_sum(self: 'Die[int]',
                    target: int,
                    /,
                    max_time: int,
                    dnf: 'int|icepool.RerollType|None' = None) -> 'Die[int]':
        """The number of rolls until the cumulative sum is greater or equal to the target.
        
        Args:
            target: The number to stop at once reached.
            max_time: The maximum number of rolls to run.
                If the sum is not reached, the outcome is determined by `dnf`.
            dnf: What time to assign in cases where the target was not reached
                in `max_time`. If not provided, this is set to `max_time`.
                `dnf=icepool.Reroll` will remove this case from the result,
                effectively rerolling it.
        """
        if target <= 0:
            return Die([0])

        if dnf is None:
            dnf = max_time

        def step(total, roll):
            return min(total + roll, target)

        result: 'Die[tuple[int, int]]' = Die([0]).map_and_time(
            step, self, time_limit=max_time)

        def get_time(total, time):
            if total < target:
                return dnf
            else:
                return time

        return result.map(get_time)

    @cached_property
    def _mean_time_to_sum_cache(self) -> list[Fraction]:
        return [Fraction(0)]

    def mean_time_to_sum(self: 'Die[int]', target: int, /) -> Fraction:
        """The mean number of rolls until the cumulative sum is greater or equal to the target.

        Args:
            target: The target sum.

        Raises:
            ValueError: If `self` has negative outcomes.
            ZeroDivisionError: If `self.mean() == 0`.
        """
        target = max(target, 0)

        if target < len(self._mean_time_to_sum_cache):
            return self._mean_time_to_sum_cache[target]

        if self.min_outcome() < 0:
            raise ValueError(
                'mean_time_to_sum does not handle negative outcomes.')
        time_per_effect = Fraction(self.denominator(),
                                   self.denominator() - self.quantity(0))

        for i in range(len(self._mean_time_to_sum_cache), target + 1):
            result = time_per_effect + self.reroll(
                [0],
                depth=None).map(lambda x: self.mean_time_to_sum(i - x)).mean()
            self._mean_time_to_sum_cache.append(result)

        return result

    def explode(self,
                which: Collection[T_co] | Callable[..., bool] | None = None,
                /,
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
            depth: The maximum number of additional dice to roll, not counting
                the initial roll.
                If not supplied, a default value will be used.
            end: Once `depth` is reached, further explosions will be treated
                as this value. By default, a zero value will be used.
                `icepool.Reroll` will make one extra final roll, rerolling until
                a non-exploding outcome is reached.
        """

        if which is None:
            outcome_set = {self.max_outcome()}
        else:
            outcome_set = self._select_outcomes(which, star)

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
        again_count: int | None = None,
        again_depth: int | None = None,
        again_end: 'U | Die[U] | icepool.RerollType | None' = None
    ) -> 'Die[U]':
        """Ternary conditional operator.

        This replaces truthy outcomes with the first argument and falsy outcomes
        with the second argument.

        Args:
            again_count, again_depth, again_end: Forwarded to the final die constructor.
        """
        return self.map(lambda x: bool(x)).map(
            {
                True: outcome_if_true,
                False: outcome_if_false
            },
            again_count=again_count,
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

        The sum is computed one at a time, with each additional item on the 
        right, similar to `functools.reduce()`.

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
            # In addition to working similar to reduce(), this seems to perform
            # better than binary split.
            result = self._sum_all(rolls - 1) + self

        self._sum_cache[rolls] = result
        return result

    def __matmul__(self: 'Die[int]', other) -> 'Die':
        """Roll the left `Die`, then roll the right `Die` that many times and sum the outcomes.
        
        The sum is computed one at a time, with each additional item on the 
        right, similar to `functools.reduce()`.
        """
        if isinstance(other, icepool.AgainExpression):
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

    def __rmatmul__(self, other: 'int | Die[int]') -> 'Die':
        """Roll the left `Die`, then roll the right `Die` that many times and sum the outcomes.
        
        The sum is computed one at a time, with each additional item on the 
        right, similar to `functools.reduce()`.
        """
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return other.__matmul__(self)

    def sequence(self, rolls: int) -> 'icepool.Die[tuple[T_co, ...]]':
        """Possible sequences produced by rolling this die a number of times.
        
        This is extremely expensive computationally. If possible, use `reduce()`
        instead; if you don't care about order, `Die.pool()` is better.
        """
        return icepool.cartesian_product(*(self for _ in range(rolls)),
                                         outcome_type=tuple)  # type: ignore

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
            # Haven't dealt with narrowing return type.
            return icepool.Pool({self: pool_size})[rolls]  # type: ignore

    @overload
    def keep(self, rolls: Sequence[int], /) -> 'Die':
        """Selects elements after drawing and sorting and sums them.

        Args:
            rolls: A sequence of `int` specifying how many times to count each
                element in ascending order.
        """

    @overload
    def keep(self, rolls: int,
             index: slice | Sequence[int | EllipsisType] | int, /):
        """Selects elements after drawing and sorting and sums them.

        Args:
            rolls: The number of dice to roll.
            index: One of the following:
            * An `int`. This will count only the roll at the specified index.
                In this case, the result is a `Die` rather than a generator.
            * A `slice`. The selected dice are counted once each.
            * A sequence of one `int` for each `Die`.
                Each roll is counted that many times, which could be multiple or
                negative times.

                Up to one `...` (`Ellipsis`) may be used.
                `...` will be replaced with a number of zero
                counts depending on the `rolls`.
                This number may be "negative" if more `int`s are provided than
                `rolls`. Specifically:

                * If `index` is shorter than `rolls`, `...`
                    acts as enough zero counts to make up the difference.
                    E.g. `(1, ..., 1)` on five dice would act as
                    `(1, 0, 0, 0, 1)`.
                * If `index` has length equal to `rolls`, `...` has no effect.
                    E.g. `(1, ..., 1)` on two dice would act as `(1, 1)`.
                * If `index` is longer than `rolls` and `...` is on one side,
                    elements will be dropped from `index` on the side with `...`.
                    E.g. `(..., 1, 2, 3)` on two dice would act as `(2, 3)`.
                * If `index` is longer than `rolls` and `...`
                    is in the middle, the counts will be as the sum of two
                    one-sided `...`.
                    E.g. `(-1, ..., 1)` acts like `(-1, ...)` plus `(..., 1)`.
                    If `rolls` was 1 this would have the -1 and 1 cancel each other out.
        """

    def keep(self,
             rolls: int | Sequence[int],
             index: slice | Sequence[int | EllipsisType] | int | None = None,
             /) -> 'Die':
        """Selects elements after drawing and sorting and sums them.

        Args:
            rolls: The number of dice to roll.
            index: One of the following:
            * An `int`. This will count only the roll at the specified index.
            In this case, the result is a `Die` rather than a generator.
            * A `slice`. The selected dice are counted once each.
            * A sequence of `int`s with length equal to `rolls`.
                Each roll is counted that many times, which could be multiple or
                negative times.

                Up to one `...` (`Ellipsis`) may be used. If no `...` is used,
                the `rolls` argument may be omitted.

                `...` will be replaced with a number of zero counts in order
                to make up any missing elements compared to `rolls`.
                This number may be "negative" if more `int`s are provided than
                `rolls`. Specifically:

                * If `index` is shorter than `rolls`, `...`
                    acts as enough zero counts to make up the difference.
                    E.g. `(1, ..., 1)` on five dice would act as
                    `(1, 0, 0, 0, 1)`.
                * If `index` has length equal to `rolls`, `...` has no effect.
                    E.g. `(1, ..., 1)` on two dice would act as `(1, 1)`.
                * If `index` is longer than `rolls` and `...` is on one side,
                    elements will be dropped from `index` on the side with `...`.
                    E.g. `(..., 1, 2, 3)` on two dice would act as `(2, 3)`.
                * If `index` is longer than `rolls` and `...`
                    is in the middle, the counts will be as the sum of two
                    one-sided `...`.
                    E.g. `(-1, ..., 1)` acts like `(-1, ...)` plus `(..., 1)`.
                    If `rolls` was 1 this would have the -1 and 1 cancel each other out.
        """
        if isinstance(rolls, int):
            if index is None:
                raise ValueError(
                    'If the number of rolls is an integer, an index argument must be provided.'
                )
            if isinstance(index, int):
                return self.pool(rolls).keep(index)
            else:
                return self.pool(rolls).keep(index).sum()  # type: ignore
        else:
            if index is not None:
                raise ValueError('Only one index sequence can be given.')
            return self.pool(len(rolls)).keep(rolls).sum()  # type: ignore

    def lowest(self,
               rolls: int,
               /,
               keep: int | None = None,
               drop: int | None = None) -> 'Die':
        """Roll several of this `Die` and return the lowest result, or the sum of some of the lowest.

        The outcomes should support addition and multiplication if `keep != 1`.

        Args:
            rolls: The number of dice to roll. All dice will have the same
                outcomes as `self`.
            keep, drop: These arguments work together:
                * If neither are provided, the single lowest die will be taken.
                * If only `keep` is provided, the `keep` lowest dice will be summed.
                * If only `drop` is provided, the `drop` lowest dice will be dropped
                    and the rest will be summed.
                * If both are provided, `drop` lowest dice will be dropped, then
                    the next `keep` lowest dice will be summed.

        Returns:
            A `Die` representing the probability distribution of the sum.
        """
        index = lowest_slice(keep, drop)
        canonical = canonical_slice(index, rolls)
        if canonical.start == 0 and canonical.stop == 1:
            return self._lowest_single(rolls)
        # Expression evaluators are difficult to type.
        return self.pool(rolls)[index].sum()  # type: ignore

    def _lowest_single(self, rolls: int, /) -> 'Die':
        """Roll this die several times and keep the lowest."""
        if rolls == 0:
            return self.zero().simplify()
        return icepool.from_cumulative(
            self.outcomes(), [x**rolls for x in self.quantities('>=')],
            reverse=True)

    def highest(self,
                rolls: int,
                /,
                keep: int | None = None,
                drop: int | None = None) -> 'Die[T_co]':
        """Roll several of this `Die` and return the highest result, or the sum of some of the highest.

        The outcomes should support addition and multiplication if `keep != 1`.

        Args:
            rolls: The number of dice to roll.
            keep, drop: These arguments work together:
                * If neither are provided, the single highest die will be taken.
                * If only `keep` is provided, the `keep` highest dice will be summed.
                * If only `drop` is provided, the `drop` highest dice will be dropped
                    and the rest will be summed.
                * If both are provided, `drop` highest dice will be dropped, then
                    the next `keep` highest dice will be summed.

        Returns:
            A `Die` representing the probability distribution of the sum.
        """
        index = highest_slice(keep, drop)
        canonical = canonical_slice(index, rolls)
        if canonical.start == rolls - 1 and canonical.stop == rolls:
            return self._highest_single(rolls)
        # Expression evaluators are difficult to type.
        return self.pool(rolls)[index].sum()  # type: ignore

    def _highest_single(self, rolls: int, /) -> 'Die[T_co]':
        """Roll this die several times and keep the highest."""
        if rolls == 0:
            return self.zero().simplify()
        return icepool.from_cumulative(
            self.outcomes(), [x**rolls for x in self.quantities('<=')])

    def middle(
            self,
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

    def map_to_pool(
        self,
        repl:
        'Callable[..., Sequence[icepool.Die[U] | U] | Mapping[icepool.Die[U], int] | Mapping[U, int] | icepool.RerollType] | None' = None,
        /,
        *extra_args: 'Outcome | icepool.Die | icepool.MultisetExpression',
        star: bool | None = None,
        denominator: int | None = None
    ) -> 'icepool.MultisetGenerator[U, tuple[int]]':
        """EXPERIMENTAL: Maps outcomes of this `Die` to `Pools`, creating a `MultisetGenerator`.

        As `icepool.map_to_pool(repl, self, ...)`.

        If no argument is provided, the outcomes will be used to construct a
        mixture of pools directly, similar to the inverse of `pool.expand()`.
        Note that this is not particularly efficient since it does not make much
        use of dynamic programming.

        Args:
            repl: One of the following:
                * A callable that takes in one outcome per element of args and
                    produces a `Pool` (or something convertible to such).
                * A mapping from old outcomes to `Pool` 
                    (or something convertible to such).
                    In this case args must have exactly one element.
                The new outcomes may be dice rather than just single outcomes.
                The special value `icepool.Reroll` will reroll that old outcome.
            star: If `True`, the first of the args will be unpacked before 
                giving them to `repl`.
                If not provided, it will be guessed based on the signature of 
                `repl` and the number of arguments.
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
        if repl is None:
            repl = lambda x: x
        return icepool.map_to_pool(repl,
                                   self,
                                   *extra_args,
                                   star=star,
                                   denominator=denominator)

    def explode_to_pool(
            self,
            rolls: int,
            which: Collection[T_co] | Callable[..., bool] | None = None,
            /,
            *,
            star: bool | None = None,
            depth: int = 9) -> 'icepool.MultisetGenerator[T_co, tuple[int]]':
        """EXPERIMENTAL: Causes outcomes to be rolled again, keeping that outcome as an individual die in a pool.
        
        Args:
            rolls: The number of initial dice.
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
            depth: The maximum depth of explosions for an individual dice.

        Returns:
            A `MultisetGenerator` representing the mixture of `Pool`s. Note  
            that this is not technically a `Pool`, though it supports most of 
            the same operations.
        """
        if depth == 0:
            return self.pool(rolls)
        if which is None:
            explode_set = {self.max_outcome()}
        else:
            explode_set = self._select_outcomes(which, star)
        if not explode_set:
            return self.pool(rolls)
        explode, not_explode = self.split(explode_set)

        single_data: 'MutableMapping[icepool.Vector[int], int]' = defaultdict(
            int)
        for i in range(depth + 1):
            weight = explode.denominator()**i * self.denominator()**(
                depth - i) * not_explode.denominator()
            single_data[icepool.Vector((i, 1))] += weight
        single_data[icepool.Vector(
            (depth + 1, 0))] += explode.denominator()**(depth + 1)

        single_count_die: 'Die[icepool.Vector[int]]' = Die(single_data)
        count_die = rolls @ single_count_die

        return count_die.map_to_pool(
            lambda x, nx: [explode] * x + [not_explode] * nx)

    def reroll_to_pool(
        self,
        rolls: int,
        which: Callable[..., bool] | Collection[T_co],
        /,
        max_rerolls: int,
        *,
        star: bool | None = None,
        mode: Literal['random', 'lowest', 'highest', 'drop'] = 'random'
    ) -> 'icepool.MultisetGenerator[T_co, tuple[int]]':
        """EXPERIMENTAL: Applies a limited number of rerolls shared across a pool.

        Each die can only be rerolled once (effectively `depth=1`), and no more
        than `max_rerolls` dice may be rerolled.
        
        Args:
            rolls: How many dice in the pool.
            which: Selects which outcomes are eligible to be rerolled. Options:
                * A collection of outcomes to reroll.
                * A callable that takes an outcome and returns `True` if it
                    could be rerolled.
            max_rerolls: The maximum number of dice to reroll. 
                Note that each die can only be rerolled once, so if the number 
                of eligible dice is less than this, the excess rerolls have no
                effect.
            star: Whether outcomes should be unpacked into separate arguments
                before sending them to a callable `which`.
                If not provided, this will be guessed based on the function
                signature.
            mode: How dice are selected for rerolling if there are more eligible
                dice than `max_rerolls`. Options:
                * `'random'` (default): Eligible dice will be chosen uniformly
                    at random.
                * `'lowest'`: The lowest eligible dice will be rerolled.
                * `'highest'`: The highest eligible dice will be rerolled.
                * `'drop'`: All dice that ended up on an outcome selected by 
                    `which` will be dropped. This includes both dice that rolled
                    into `which` initially and were not rerolled, and dice that
                    were rerolled but rolled into `which` again. This can be
                    considerably more efficient than the other modes.

        Returns:
            A `MultisetGenerator` representing the mixture of `Pool`s. Note  
            that this is not technically a `Pool`, though it supports most of 
            the same operations.
        """
        rerollable_set = self._select_outcomes(which, star)
        if not rerollable_set:
            return self.pool(rolls)

        rerollable_die, not_rerollable_die = self.split(rerollable_set)
        single_is_rerollable = icepool.coin(rerollable_die.denominator(),
                                            self.denominator())
        rerollable = rolls @ single_is_rerollable

        def split(initial_rerollable: int) -> Die[tuple[int, int, int]]:
            """Computes the composition of the pool.

            Returns:
                initial_rerollable: The number of dice that initially fell into
                    the rerollable set.
                rerolled_to_rerollable: The number of dice that were rerolled,
                    but fell into the rerollable set again.
                not_rerollable: The number of dice that ended up outside the
                    rerollable set, including both initial and rerolled dice.
                not_rerolled: The number of dice that were eligible for
                    rerolling but were not rerolled.
            """
            initial_not_rerollable = rolls - initial_rerollable
            rerolled = min(initial_rerollable, max_rerolls)
            not_rerolled = initial_rerollable - rerolled

            def second_split(rerolled_to_rerollable):
                """Splits the rerolled dice into those that fell into the rerollable and not-rerollable sets."""
                rerolled_to_not_rerollable = rerolled - rerolled_to_rerollable
                return icepool.tupleize(
                    initial_rerollable, rerolled_to_rerollable,
                    initial_not_rerollable + rerolled_to_not_rerollable,
                    not_rerolled)

            return icepool.map(second_split,
                               rerolled @ single_is_rerollable,
                               star=False)

        pool_composition = rerollable.map(split, star=False)

        def make_pool(initial_rerollable, rerolled_to_rerollable,
                      not_rerollable, not_rerolled):
            common = rerollable_die.pool(
                rerolled_to_rerollable) + not_rerollable_die.pool(
                    not_rerollable)
            match mode:
                case 'random':
                    return common + rerollable_die.pool(not_rerolled)
                case 'lowest':
                    return common + rerollable_die.pool(
                        initial_rerollable).highest(not_rerolled)
                case 'highest':
                    return common + rerollable_die.pool(
                        initial_rerollable).lowest(not_rerolled)
                case 'drop':
                    return not_rerollable_die.pool(not_rerollable)
                case _:
                    raise ValueError(
                        f"Invalid reroll_priority '{mode}'. Allowed values are 'random', 'lowest', 'highest', 'drop'."
                    )

        denominator = self.denominator()**(rolls + min(rolls, max_rerolls))

        return pool_composition.map_to_pool(make_pool,
                                            star=True,
                                            denominator=denominator)

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

    def stochastic_round(self,
                         *,
                         max_denominator: int | None = None) -> 'Die[int]':
        """Randomly rounds outcomes up or down to the nearest integer according to the two distances.
        
        Specificially, rounds `x` up with probability `x - floor(x)` and down
        otherwise.

        Args:
            max_denominator: If provided, each rounding will be performed
                using `fractions.Fraction.limit_denominator(max_denominator)`.
                Otherwise, the rounding will be performed without
                `limit_denominator`.
        """
        return self.map(lambda x: icepool.stochastic_round(
            x, max_denominator=max_denominator))

    def trunc(self) -> 'Die':
        return self.unary_operator(math.trunc)

    __trunc__ = trunc

    def floor(self) -> 'Die':
        return self.unary_operator(math.floor)

    __floor__ = floor

    def ceil(self) -> 'Die':
        return self.unary_operator(math.ceil)

    __ceil__ = ceil

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
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.lt)

    def __le__(self, other) -> 'Die[bool]':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.le)

    def __ge__(self, other) -> 'Die[bool]':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.ge)

    def __gt__(self, other) -> 'Die[bool]':
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other = implicit_convert_to_die(other)
        return self.binary_operator(other, operator.gt)

    # Equality operators. These produce a `DieWithTruth`.

    # The result has a truth value, but is not a bool.
    def __eq__(self, other) -> 'icepool.DieWithTruth[bool]':  # type: ignore
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
        other_die: Die = implicit_convert_to_die(other)

        def data_callback() -> Counts[bool]:
            return self.binary_operator(other_die, operator.eq)._data

        def truth_value_callback() -> bool:
            return self.equals(other)

        return icepool.DieWithTruth(data_callback, truth_value_callback)

    # The result has a truth value, but is not a bool.
    def __ne__(self, other) -> 'icepool.DieWithTruth[bool]':  # type: ignore
        if isinstance(other, icepool.AgainExpression):
            return NotImplemented
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
            'A `Die` only has a truth value if it is the result of == or !=.\n'
            'This could result from trying to use a die in an if-statement,\n'
            'in which case you should use `die.if_else()` instead.\n'
            'Or it could result from trying to use a `Die` inside a tuple or vector outcome,\n'
            'in which case you should use `tupleize()` or `vectorize().')

    @cached_property
    def _hash_key(self) -> tuple:
        """A tuple that uniquely (as `equals()`) identifies this die.

        Apart from being hashable and totally orderable, this is not guaranteed
        to be in any particular format or have any other properties.
        """
        return tuple(self.items())

    @cached_property
    def _hash(self) -> int:
        return hash(self._hash_key)

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
            return self.simplify()._hash_key == other.simplify()._hash_key
        else:
            return self._hash_key == other._hash_key

    # Strings.

    def __repr__(self) -> str:
        inner = ', '.join(f'{repr(outcome)}: {weight}'
                          for outcome, weight in self.items())
        return type(self).__qualname__ + '({' + inner + '})'
