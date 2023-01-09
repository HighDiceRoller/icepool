## 0.24.0

Reworked built-in generators and evaluators.

* Generators now support multiset operations. These include:
  * Multiset comparisons (`<, <=, >, >=, ==, !=, isdisjoint`), which produce `Die[bool]`.
  * Multiset operators (`+`, `-`, `|`, `&`, `^`) which produce wrapped generators.
  * A suite of chainable count adjustments, including `multiply_counts`, `divide_counts`, `filter_counts`, and `unique`.
* Rename `median_left` to `median_low` etc.
* Generators and evaluators are now paramterized by count type as well.
* Move concrete evaluators to a submodule.

## 0.23.3

* Fixed weighting bug in `__matmul__` when the left die has an outcome of 0.
* Retired the names `standard` and `bernoulli`. These will be just `d` and `coin` respectively.
* `apply` now accepts `Pool` arguments, which will have `expand()` called on them.
* Reinstate automatic Cartesian product in `Population` construction.
* `if_else` now runs in two stages.

## 0.23.2

* Incremental sorting for `all_matching_sets` to reduce state space.
* `lowest()` and `highest()` now actually visible.
* Improved checking for tuple outcome sortability and types.

## 0.23.1

Prepend `sum_` to OutcomeCountGenerator versions of `highest` and `lowest`.

## 0.23.0

Expanded typing, particularly in terms of parameterizing types.

* `Die` and `Deck` constructors now expect exactly one nesting level, e.g. a Sequence of outcomes.
* Removed `Die.bool()`.
* `**kwargs` replaced with explcit `again_depth`, `again_end`. Removed `OutcomeCountEvaluator.final_kwargs()`.
* Split `include_steps` version of `Die.map()` into a `map_and_time` method.
* Split `include_outcome` version of `best_matching_set` and `best_straight` into separate methods.
* Rename `keep_highest` and `highest` to `sum_highest`; add just `highest` for taking the single highest.
* Same for `lowest`.
* Added `cartesian_product()`, took this functionality out of the `Die` constructor for now.
* Added `OutcomeCountGenerator.all_matching_sets()`.

## 0.22.0

* `Die.sub()` renamed to `Die.map()`.
* `Die.map()` can now include the number of steps taken until absorption.
* `Die.reroll_until()` renamed to `Die.filter()`.
* `wilds` arguments marked experimental, pending decision on how ordering should affect them.
* Only tuples get separate columns in tables and not `str` or `bytes`.
* Non-recursive algorithm for `Again()` handling.

## 0.21.0

* Nested lists are now allowed in the `Die()` constructor.
* Single outcomes can be sent to the `Die()` constructor without wrapping them in a list.
* Same for sending a die to the `Pool()` constructor.
* Add `Die.probabilities_lt()`, `Die.probabilities_gt()` methods.
* Add `wilds` argument to `contains_subset()` and `intersection_size()` methods.
* Removed `extra_dice` argument from `Die.sub()`.
* Added `sub()` method to `Deck`, though with less features than the `Die` version.
* `sum()` method of generators now has a `sub` option that maps outcomes before summing.
* `expand()` method of generators now has a `unique` option that counts duplicates only once.
* Forwarding of `kwargs` to `Die()` replaced with explicit arguments.
* Add comparators to `Again`.
* Experimental absorbing Markov chain analysis for `Die.sub(depth=None)`.

## 0.20.1

* Added `one_hot` function.
* Added experimental suit generator that wraps a generator and produces counts for all suits for each value.

## 0.20.0

* Retired `denominator_method`.
* Renamed `max_depth` parameters to just `depth`.
* Binary operators delegate to `Again`'s behavior.
* Only single outcomes implicity convert to `Die`.
* `marginals` is now a Sequence, and can be iterated over, unpacked, etc.
* `Die.sub()` now expands extra die arguments into their outcomes.

## 0.19.1

Fix `contains_again` checking of sequences.

## 0.19.0

New feature: `Again()`, a placeholder that allows to roll again with some modification.

* `**kwargs` are forwarded to the constructor of the yielded or returned die for `sub`, `if_else`, `reduce`, `accumulate`, `apply`, `apply_sorted`.
* Add optional `final_kwargs` method to evaluators.
* Rename `max_depth` parameter of `sub()` to `repeat`.

## 0.18.0

* Rename `Die.reduce()` to `Die.simplify()` to avoid confusion with the free function `reduce()`.
* Rename `OutcomeCountEvaluator.direction()` to `order()` and add explicitly named `Order` enums.
* Add `is_in`, `count`, and `count_in` methods to dice.
* Add built-in evaluators as convenience functions of `OutcomeCountGenerator`.

## 0.17.4

* Fixes to `max_depth=None` case of `sub()`.
* This is now marked experimental.

## 0.17.3

* Pass `star` parameter to `sub()` to recursive calls.

## 0.17.2

* `sub()` with `max_depth=None` now handles "monotonic" transitions with finite states. Full absorbing Markov chain calculation still under consideration.
* `sub()` no longer accept sequence input.
* Some minor formatting fixes.

## 0.17.1

* Standardize outcome count of `bernoulli`/`coin` and comparators.
* `standard_pool` now accepts a `dict` argument.
* `post_roll_counts` renamed again to `sorted_roll_counts`.
* `apply_sorted` can be subscripted to set the `sorted_roll_counts`.
* Pools are no longer resizable after creation.
* `Die.pool()` now has mandatory argument, now accepts a sequence argument to set `sorted_roll_counts`.

## 0.17.0

More renaming, experimental `sample()` methods.

* Both `Die` and `Deck` now have `quantities` rather than `weight`, `dups`, etc.
* Many `Die` methods moved to base class and are now available to `Deck`.
* "Eval" is now the full word "Evaluator".
* Parameter and method names are no longer prefixed with "num_".
* `reduce_weights` renamed back to `reduce`.
* `Deck`s can be formatted like `Die`.
* Allow formatting 0-1 probability.
* Experimental `sample()` methods for `OutcomeCountGenerator` and `OutcomeCountEvaluator`.

## 0.16.1

Development of deck API.

* Separate `Deal` class from `Deck`, roughly analogous to `Pool` vs. `Die`.
* `Deal` can now output multiple hands. The counts for each hand are provided in order to `eval.next_state`.
* `comb_row` now uses iterative rather than recursive memoization. This will prevent some stack overflows.
* `Pool`s are not permitted to be constructed using a raw `Die` or `Deck` argument.
* `reduce` argument of `Die.equals()` renamed to `reduce_weights`.

## 0.16.0

Significant API changes, experimental deck support.

* Experimental `Deck` class. API still very unstable.
* `Pool`s, `Deck`s, and internal Alignment now have a common base class `OutcomeCountGen`.
* `EvalPool` renamed to `OutcomeCountEval`.
* `Die` and `Deck` are now proper `Mapping`s with `keys`, `values`, and `items`.
* The above view types can also be accessed like sequences.
* A `Die` is now always considered not `equal()` to non-`Die`.
* `die[]` now works like a dict. Use `marginals[]` to marginalize dimensions.
* `Die`, `Pool`, and `Deck` now take a single sequence or mapping argument rather than a variable number of arguments.
* `Die`, `Pool`, and `Deck` now all have the same name for the second argument: `times`.
* `count_dice` renamed to `post_roll_counts`. No longer accepts `None`, use `[:]` instead.
* Linear algorithm for comparators on `Die`.
* Improvements to internal `Count` class.
* Add `clear_pool_cache` function.
* Forward `*extra_args` for `reroll, reroll_until, explode`.

## 0.15.0

Added type hints. Now requires Python 3.10 or later.

Other changes:

* Add `apply_sorted()` method.
* Add `Die.set_range()`.
* `standard()` / `d()` argument is now positional-only.

## 0.14.1

Reinstate alternate internal `EvalPool` algorithm, which provides better performance in some cases. 

## 0.14.0

* Added a new `EvalPool.alignment()` method. This allows to specify an iterable of outcomes that should always be seen by `next_state` even if they have zero count.
* The free function `d()` is now simply an alias for `standard()`.
* Removed `Die.d()`.
* The `@` operator now casts the right side to a `Die` like other operators.
* Some internal changes to `EvalPool` algorithm.

## 0.13.2

The data of a die resulting from `==` or `!=` is lazily evaluated.

This saves computation in case the caller is only interested in the truth value.

## 0.13.1

`EvalPool` favors the cached direction more.

## 0.13.0

Major reworking of pool construction.

* Public constructor is now just `Pool(*dice)`.
* In particular, no more `truncate_min` or `truncate_max` arguments.
* Pools can be of arbitrary dice, though non-truncative sets of dice will have lower performance. There is some performance penalty overall.
* `apply()` called with no arguments now calls `func` once with no arguments.

## 0.12.1

* Removed `Die.keep()`. Use `Die.pool(...).sum()`.
* `highest`/`lowest` returns empty die if any of the input dice are empty.

## 0.12.0

* Free-function form of `lowest`, `highest` now selects between algorithms for better performance and generality.
* Removed `die.lowest, `die.highest`.
* `die.min_outcome`, `die.max_outcome` no longer take arguments beyond `self`.
* No more (public) `repeat_and_sum`, as this is redundant with `@` and `die.keep()`.
* No more public `die.keep_lowest_single()`, `die.keep_highest_single()`.
* `count_dice` arguments are now keyword-only.
* `die.zero()` no longer reduces weights to 1.
* Update PyPi classifiers.

## 0.11.0

* Removed `min_outcome` parameter from die construction.
* Operations on tuple outcomes are now performed recursively, to match the fact that die expansion on construction is recursive.
* Renamed `Die.reduce()` to `Die.reduce_weights()`.
* Added `reduce()` and `accumulate()` functions analogous to the functions of the same name from functools/itertools.
* Add CSV output.
* Renamed `Die.markdown()` to `Die.format_markdown()`.
* Added `star` parameter to `sub`, `explode`, `reroll`, `reroll_until` methods. If set, this unpacks outcomes before giving them to the supplied function.
* Added experimental `JointEval` class for performing two evals on the same roll of a pool.

## 0.10.2

* Operators other than `[]` are performed element-wise on tuples.
* Rename `DicePool` to just `Pool`. Merge the old factory function into the constructor.

## 0.10.1

* Fix denominator_method='reduce' in die creation.
* Fix outcomes consisting of empty tuple `()`.
* `apply()` with no dice produces an empty die.

## 0.10.0

Retired the `EmptyDie` / `ScalarDie` / `VectorDie` distinction.

* There is now only one `Die` class; it behaves similarly to how `ScalarDie` used to.
* There is no more `ndim`.
* The `[]` operator now forwards to the outcome, acting similar to what `VectorDie.dim[]` used to do.
* Removed `PoolEval.bind_dice()`. It was cute, but I'm not convinced it was worth spending API on.

## 0.9.1

* This will probably be the last version with a `VectorDie` distinction.
* Dice cannot have negative weights.
* `VectorDie` cannot be nested inside tuple outcomes.

## 0.9.0

* Die and dict arguments to `Die()` are now expanded, including when nested.
* Add `Die.if_else()` method, which acts as a ternary conditional operator on outcomes.
* Dice are now hashable. `==` and `!=` return dice with truth values based on whether the two dice have identical outcomes and weights.
* `ndim` now uses singletons `icepool.Scalar` and `icepool.Empty`.

## 0.8.0

* `EvalPool.eval()` can now be provided with single rolls of a pool.
    This can be a dict-like mapping individual die outcomes to counts or a sequence of individual die outcomes.
* `EvalPool.next_state()` can not expect that the outcomes it sees are consecutive,
    though they are guaranteed to be seen in monotonic order.
* `FindBestRun()` no longer assumes consecutive outcomes.
* Added `DicePool.sample()`.
* Added `die.truncate()`.
* `min_outcomes`, `max_outcomes` (for pool definitions) renamed to `truncate_min`, `truncate_max`.
* Removed `die.getitem()`.
* `DicePool` is no longer iterable, since there isn't an intuitive, unambiguous way of doing so.
* `align_range()` now only operates on scalar outcomes.

## 0.7.0

* Renamed from `hdroller` to `icepool`.
* Primary repository is now https://github.com/HighDiceRoller/icepool.
* Only `tuple`s become `VectorDie`.
* Weights of 10^30 or above are not shown in tables by default.

## 0.6.7

* Add `max_depth` parameter to `sub()`. If set to `None` this seeks a fixed point.
* Add `'reduce'` option for `denominator_method` parameters.
* Cache results of `repeat_and_sum()`.

## 0.6.6

* Add `ndim` keyword argument to `d()`.
* Removed `hitting_time()` method; it seems too niche to commit to.
* Several arguments are now keyword-only.
* Fix to `reroll_until()` for vector dice.

## 0.6.5

* Add `VectorDie.all()` and `VectorDie.any()`.
* More fixes to `ndim` calculation.

## 0.6.4

* `EmptyDie` (a die with no outcomes) is now its own class.
* `mix()` along with its weights argument is folded into the `Die()` factory.
* Fixes to `ndim` calculation.
* `apply(), EvalPool.final_outcome()` can now return dice, `hdroller.Reroll`, etc.
* Center `Ellipsis` when indexing a pool can now work on undersized pools, rather than being an error.
* Fix `lcm_weighted` denominator method.
* `len(die)` is now the same as `die.num_outcomes()` again.
* Slicing a die now refers to (sorted) outcome indexes.
* Dimension slicing is now `VectorDie.dim[select]`.

## 0.6.3

* `Die()` now takes a variable number of arguments. A sequence provided as a single argument will be treated as a single outcome equal to that sequence.
    To have one outcome per item in the sequence, the sequence must be unpacked into multiple arguments.
* `min_outcome` and `ndim` args to `Die()` are now keyword-only.
* Non-integers are now allowed for `count_dice`. Use at your own risk.
* The third argument to a `count_dice` slice, if provided, changes the size of the pool.
* Up to one `Ellipsis` (`...`) may now be used in `count_dice`. This allows the tuple option to adapt to differently-sized pools.
* `VectorDie` outcomes are now unpacked when providing them to callable arguments in `reroll()`, `explode()`, `split()`.
* `if_else()` is now a method of `ScalarDie` rather than a free function.
* Fixed the invert operator.

## 0.6.2

* Rerolls in pools, `mix()`, and `sub()` are now triggered by a sentinel value `hdroller.Reroll` (rather than `None`).
* Single-`int` indexes for `count_dice` and pool `[]` operator now produce a die rather than a pool,
    in analogy to sequence indexing. However, note that this is absolute relative to the whole pool
    rather than relative to any previous indexing.
* `EvalPool` can now iterate in both directions even if one of `max_outcomes` or `min_outcomes` is given,
    though at lower efficiency in the disfavored direction.
* Default such direction changed back to ascending.
* Re-implemented `clip()`.
* The minimum outcome of `highest()` is equal to the highest minimum outcome among all input dice
    and likewise for `lowest()`. This will prevent introducing zero-weight outcomes where they did not exist before.

## 0.6.1

* Pool `max_outcomes` or `min_outcomes` outside the range of the fundamental die is now an error.
* Pools no longer automatically shrink the die to fit `max_outcomes` or `min_outcomes`. This is to guarantee a predictable iteration order.
* Improved `str(die)` formatting.
* `VectorDie` outcomes are automatically converted to tuples.
* `ScalarDie` now has `ndim='scalar'` rather than `ndim=False`.
* Add `standard_pool()` function for easy creation of standard pools.
* Removed `reroll_lt()`, etc. as they weren't enough faster than `reroll(func)` to justify spending extra space.

## 0.6.0

* Removed `initial_state()` in favor of using `None` as the initial state.
* Added simple `pool.eval()` method.
* `None` now rerolls in `EvalPool`.
* Fix `trunc`, `floor`, `ceil`.
* Various improvements to pool algorithm.
* Add some thresholding methods for dice.
* Max/min renamed to highest/lowest.
* Improve empty die handling.
* Improved `VectorDie` string formatting.
* Disabled `reverse()`.

## 0.5.2

* Faster algorithm for keeping the single highest/lowest.
* Fix `from_sweights()`.

## 0.5.1

* Fix `max()` and `min()` casting to dice.

## 0.5.0

* Capitalize `Die()` and `Pool()` factory methods.
* `PoolEval` renamed to `EvalPool`.
* Implemented `min_outcomes` for pools. Direction is now determined by `EvalPool`.
* Allow dice with zero weights or zero outcomes.
* `BaseDie` subclasses are now `ScalarDie` and `VectorDie`.
* `==` and `!=` compare outcomes again. Dice are no longer hashable by the standard `hash()`.
* Rewored `Pool()` arguments.
* Added several methods.

## 0.4.4

* Fix `weights_le()` etc.
* `set_outcomes()` is now public.

## 0.4.3

* `min_outcome()`, `max_outcome()` now accept multiple dice.
* Fix slice range going below zero.
* `num_dice` is now an optional parameter for `keep*()` and `pool()`. Exactly one out of `num_dice`, `min_outcomes`, and `max_outcomes` should be provided.
* Removed right-side cast for `@` operator, as it leads to confusion with either other operator casting or `d()` casting.
* Replaced key-value sequence option for `die()` with a sequence of weight-1 outcomes.
* Add `has_zero_weights()` method to dice.
* `align()`, `align_range()` are now public.

## 0.4.2

* Remove numpy install dependency.

## 0.4.1

* Use the `@` operator and `d()` instead of `*` for "roll the die on the left, then roll that many dice on the right and sum".
* `*` operator now multiplies.
* Add `/` operator.
* Add `median_left(), median_right(), ppf(), ppf_left(), ppf_right(), sample(), cmp(), sign()`.

## 0.4.0

No longer numpy-based. Major changes:

* API completely reworked.
* Weights are Python `int`s. This decreases performance but produces all exact results.
* New `MultiDie` class representing multivariate distributions.
* `PoolScorer` classes merged to a single `PoolEval` class.

## 0.3.3

This will most likely be the last numpy-based version.

* Pool scorers skip zero-weight outcomes.
* Removed `__bool__` since zero-weight dice are no longer allowed.

## 0.3.2

* Pool scorers can now return `None` states, which drops the state from evaluation, effectively performing a full reroll.
* Operations that result in no remaining weight (e.g. rerolling all outcomes) now return None.
* Dice can no longer be constructed with zero total weight.
* The `Die()` constructor now auto-trims.
* `Die._align()` is now private and no longer makes all the dice the same weight.
* Fixed `Die.explode()` weighting.
* Cleaned up unused functions.

## 0.3.1

* Optimize `Pool.pops()` by immediately removing all the dice if there are no left in the mask.
* `Die.reroll` now tracks weights properly.

## 0.3.0

* Implemented new keep/pool algorithms, which make heavy use of caching. The `keep*()` function signatures changed.
* `Die` is now hashable.
* Empty `Die` is now an error.
* Removed weight normalization.
* Added `%` and `//` operators to `Die`.
* Renamed `ccdf` to `sf` following `scipy`'s naming.

## 0.2.2

* `best_set` now queries the `score_func` to determine possible outcomes, which allows more flexibility.

## 0.2.1

* `Die.align()` and `Die.trim()` are now public.
* Optimize `keep()` algorithm by skipping to results after passing the last kept die.
* Add `best_set()` method for computing sets of matching dice.

## 0.2.0

The major change in this version is a new roll-and-keep algorithm. This can keep arbitrary indexes, as well as supporting dissimilar dice as long as they share a common "prefix" of weights.
