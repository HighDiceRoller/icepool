## v2.0.0 (WIP)

Major rewrite of multiset handling. Things will be more unstable than usual for a while.

* `MultisetEvaluator.next_state()` now has an explicit parameter with the order in which outcomes are seen.
* Optional `MultisetEvaluator.initial_state()` method.
* `MultisetEvaluator.initial_state()` and `final_state()` now get the following parameters:
  * The order in which outcomes are / were seen.
  * All outcomes that will be / were seen.
  * The sizes of the input multisets, if inferrable with counts being non-negative.
  * Non-multiset keyword arguments that were passed to `evaluate()`.
* `ascending` and `descending` variants of `next_state` no longer exist.
  * Instead, `raise UnsupportedOrder()` if you don't like the current order. The other order will automatically be tried.
  * This can be done in `initial_state()` (recommended), `next_state()`, or `final_outcome()`.
* Multiset operator order is now always attached to the evaluator side rather than the generator side.
  * Unless the operator modifies the generator in-place, but in this case both orders will certainly be supported.
* `MultisetEvaluator` can optionally provide a key for persistent caching.
* Some existing expressions and evaluators now take advantage of inferred multiset sizes.
  * In particular, `keep()` and `sorted_match()`.
* `MultisetExpression.count()` renamed to `size()`.
* `@multiset_function` now implements late binding like a standard Python method. (Though I still recommend using only pure functions.)
* `@multiset_function` now accepts variadic arguments.
* `@multiset_function` now accepts non-multiset keyword arguments.
* `@multiset_function` now works with joint evaluations where some sub-evaluations don't contain parameters.
* Hopefully better `@multiset_function` performance.
* `Alignment` class is retired.
* Deprecated `depth=None` is removed from `Die.reroll()`.
* Multiset generators now always produce a single count value, with `MultiDeal` now producing tuple-valued counts rather than taking up multiple argument slots.
* Multiset computations now try to infer multiset sizes if the counts are non-negative. This improves the applicability of `keep` and `sort_match` expressions.
* Cartesian products (e.g. `tupleize`) now return `Reroll` if any argument is `Reroll`.

## v1.7.2 - 25 February 2025

* Add `Population.append()` and `.remove()` methods.
* Improve `Vector` performance.
* Adjusted typing of mixture expressions.
* Experimental `Wallenius` noncentral hypergeometric.

## v1.7.1 - 10 February 2025

* Fix joint evaluations and `@multiset_function` interaction with `next_state_ascending` and `next_state_descending`.

## v1.7.0 - 9 February 2025

* Overhauled multiset expressions. This allows expressions that are given to an evaluator to have the evaluation persistently cached. This makes the caching behavior more consistent: a single expression will be cached in the final evaluator (e.g. `(a - b).unique().sum()` would be cached in the `sum` evaluator), and `@multiset_function` creates an evaluator like any other.  Unfortunately, this did come at some performance cost for `@multiset_function`. I have some ideas on how to claw back some of the performance but I haven't decided whether it's worth the complexity.
* Instead of specifying `order()` for an evaluator, you can now implement `next_state_ascending()` and/or `next_state_descending()`.
* `Alignment` now has a denominator of 1.
* `keep()`, `isdisjoint()`, `sort_match()`, and `maximum_match()` operations now treat negative incoming counts as zero rather than raising an error.
* Add `Population.group_by()` method to split a population into a "covering" set of conditional probabilities.
  * `Population.group_by[]` can also be used to group by index or slice.
* Move `split()` from `Die` to the base `Population` class.
* Straight-related multiset operations can now choose between prioritizing low and high outcomes.
* Store original names of `@multiset_function` parameters.

## v1.6.2 - 23 December 2024

* Deprecate `depth=None` in favor of `depth='inf'`.
* Add experimental `format_inverse()` option that formats probabilities as "1 in N".

## v1.6.1 - 17 November 2024

* Add `pointwise_max`, `pointwise_min` arguments to take pointwise maximum or minimum of CDFs.
* Add `Die.time_to_sum()` method.
* Fix identification of absorbing states in the presence of `extra_args` in `map_and_time()`.
* Add `time_limit` parameter to `map()`.
* `repeat` parameter now uses `'inf'` to request the absorbing distribution rather than `None`.

## v1.6.0 - 20 September 2024

* Breaking change: outcomes with zero quantities are removed when constructing `Die` and `Deck`.
  * Functions and methods relating to zero-quantities are removed: `align()`, `align_range()`, `Population.has_zero_quantities()`, `Die.trim()`, `Die.set_range()`, `Die.set_outcomes()`.
  * You can use `consecutive()` or `sorted_union()` to get an appropriate superset of sets of outcomes.
* Breaking change: `MultisetEvaluator.alignment()` is renamed to `MultisetEvaluator.extra_outcomes()`.
  * `MultisetEvaluator.range_alignment()` is renamed to `MultisetEvaluator.consecutive()`.
  * The `Alignment` class is no longer public.
* Breaking change: `Deck.multiply_counts()` and `Population.scale_quantities()` are replaced/renamed to `Population.multiply_quantities()` etc.
* Add `Deck.sequence()` and `Die.sequence()` method.
* Add `Population.pad_to_denominator()` method.
* Move `zero()` and `zero_outcome()` from `Die` to `Population`.
* `@` operator now sums left-to-right.
* Remove old `compair` evaluation.
* `min_outcome()` and `max_outcome()` free functions can now be called using a single iterable argument.
* Forward algorithm now has a persistent cache.
* Add skip optimization for single deals with keep tuples.
* Pools now only skip dice, not outcomes. This is a bit slower in some cases but provides more consistent iteration order.
* Add shared evaluator instances for some built-in evaluator for caching.
* Simplify determination of outcome order for multiset evaluations.
* Simplify implementation of generator unbinding.
* Fix `extra_args` expansion for `map_and_time`.

## v1.5.0 - 23 August 2024

* Providing only a `drop` argument to `lowest()` or `highest()` will now keep all other elements rather than just the first non-dropped element.
* `depth` argument to `Die.reroll()` is now mandatory.
* `tuple` outcomes are now auto-`tupleize`d again during `Die` construction.
* Add `Die.stochastic_round()` method.
* Add `Die.reroll_to_pool()` method.
* Add `Die.keep()` method. This works as `MultisetGenerator.keep()` with an implicit sum.
* Add `percent` option to `Population.probability`.
* Add new `again_count` mode for handling `Again`, which limits the total number of dice.
* Improved ability to `keep` from both ends for certain types of multiset expressions.
* Rename `func` parameters to `function`.
* `MultisetExpression.order()` is now public. 
* Improved sorting for `Symbols`; now compares counts in alphabetical order.
* Experimental `sort_match`, `maximum_match_highest`, `maximum_match_lowest` expressions. `sort_match` replaces the `compair` evaluations.
* Experimental `all_straights_reduce_counts` and `argsort` multiset evaluations.
* Breaking change: `nearest`, `quantity`, `quantities`, `probability`, `probabilities`, `keep_counts` no longer have separate variants for each comparison; instead, they now take a comparison argument. `quantities` and  `probabilities` now accept a comparison argument but no longer accept a list of outcomes.

## v1.4.0 - 1 February 2024

* Rename `keep_counts` to `keep_counts_ge`. Add `le`, `lt`, `gt`, `eq`, and `ne` variants.
* Add `count_subset` evaluation that counts how many times the right side is contained in the left.
* Add `ImplicitConversionError` as subclass of `TypeError`.
* Add binary multiset operators to `Deck`.
* Add `modulo_counts` / `%` operation on multisets.
* Rebind generators and evaluate when fully bound non-generator expressions are given to an evaluator.
* Fix `Symbols` intersection.
* Fix argument order in `__rfloordiv__`.

## v1.3.0 - 30 December 2023

* Fix `Symbols` operator priority with `Population`, `AgainExpression`.
* Added experimental `map_to_pool` and `explode_to_pool` methods.
* Split `compair` into `compare_lt` etc.
* Constructing a mixture of dice now effectively uses the old `lcm_joint` method, which reduces the denominator more aggressively.

## v1.2.0 - 23 December 2023

* Experimental `Symbols` class representing a multiset of characters.
* `marginals` now forwards `__getattr__` to outcomes, as long as the attribute name doesn't begin with an underscore.
* Operators on expressions now keep negative counts by default. The `keep_negative_counts` argument is retired.
* Add unary `-` for `MultisetExpression`.
* `MultisetExpression.isdisjoint()` now raises an error for negative counts.
* Small performance optimization for `Vector`.
* `Population.marginals` is no longer a `Sequence`, since the mixins don't make sense.
* `Mapping`s are now properly excluded from `Population.common_outcome_length`.
* Fixed quoting in `repr` for populations.

## v1.1.2 - 10 December 2023

* Add `z(n)`, which produces a die that runs from 0 to `n - 1` inclusive.
* Add `Population.to_one_hot()`, which converts the die or deck to a one-hot representation.
* Add `Die.mean_time_to_sum()`, which computes the mean number of rolls until the cumulative sum is greater or equal to the target.

## v1.1.1 - 16 November 2023

* Fix non-fully-bound case of `MultisetEvaluator.evaluate()`.
* Add `default` argument to `lowest(), highest(), middle()`.
* Add `Population.entropy()`.

## v1.1.0 - 15 October 2023

* `mean()`, `variance()`, etc. now return an exact `fractions.Fraction` when possible. (Note that `Fraction`s only support float-style formatting from Python 3.12.)
* Rename `disjoint_union` to `additive_union`.
* Add `keep_negative_counts` keyword argument to `+, -, &, |` binary operators for multiset expressions (default `False`).
* Symmetric difference (`^`) for multiset expressions is now a straight absolute difference of counts.
* Add unary `+` operator for multiset expressions, which is the same as `keep_counts(0)`.

## v1.0.0 - 22 July 2023

Improve some error messages.

## v0.29.3 - 13 July 2023

Fix a bug in `MultisetExpression.keep_outcomes()` and `drop_outcomes()` regarding unbinding variables.

## v0.29.2 - 12 July 2023

* `MultisetExpression.map_counts()` now accepts multiple arguments.
* `MultisetExpression.keep_outcomes()` and `drop_outcomes()` now accept an expression as an argument.
* `MultisetExpression.highest_outcome_and_count()` now returns the min outcome if no outcomes have positive count.

## v0.29.1 - 2 July 2023

* `highest`, `lowest`, and `middle` can now take a single iterable argument.
* Add `all_straights` evaluation.
* `all_counts` and `all_straights` now output sizes in descending order.
* Harmonize method and free function versions of `map`. Both now allow extra arguments and repeat.
* Rename `filter_counts` to `keep_counts`.
* `expand` evaluator now allows order to be set.
* Experimental `compair` evaluation.

## v0.29.0 - 30 April 2023

* Add HTML and BBCode options for population formatting.
* Renamed `apply` to `map` and the decorator version to `map_function`.
* The above now uses `guess_star`.
* Add default of 1 die for `Die.pool()`.

## v0.28.1 - 23 April 2023

Fix mathematical bug in `Die.reroll` for limited depth.

## v0.28.0 - 16 April 2023

Retired implicit elementwise operations on tuples. This is now handled by a new explicit `Vector` container.
`cartesian_product()` is replaced by two new functions: `tupleize()` and `vectorize()`.
These compute the Cartesian product and produce a `tuple` or `Vector` respectively (or a die/deck thereof).

The `Again` symbol is now used without parentheses. The name of the underlying type is now `AgainExpression`.

`die.zero()` now multiplies all outcomes by `0` to determine the zero-outcome rather than using the default constructor.
This allows it to work with `Vector`'s elementwise operations while still producing the expected result for
tuples, strings, etc.

Retired the linear algorithm for comparators for `Die`. While the quadratic algorithm is slower, it allows for non-bool outputs.

`die.tuple_len()` renamed to `common_outcome_length`. Now applies to all sized outcome types.

## v0.27.1 - 9 April 2023

* Counts type `Qs` is now invariant with more detailed typing in `Deal`.

## v0.27.0 - 29 March 2023

Incremented two versions because I messed up the last version number.

* `commonize_denominator` visible at top level.

## v0.25.6 - 28 March 2023

* Rename `from_cumulative_quantities` to `from_cumulative` and allow die inputs.
* Mark `multiset_function` experimental again and note more caveats in the docstring.

## v0.25.5 - 11 March 2023

* Add missing variants of `nearest` and `quantities` methods.
* Add optional `outcomes` argument to `quantities` and `probabilities` methods.

## v0.25.4 - 17 February 2023

* `map` and similar functions will attempt to guess `star`.
* Changed `positive_only` parameter to `expression.all_counts` to `filter`.
* Changed implementation of bound generators to unbind expressions rather than dynamically splitting.
* Retired `apply_sorted` and variants.
* Add `outcome_function` decorator similar to `apply`.
* Add `map_counts` expression.
* `Reroll` in tuple outcomes and joint evaluations causes the whole thing to be rerolled.

## v0.25.3 - 28 January 2023

* Tuple outcomes can now be compared with single outcomes.
* Add `.keep, .highest, lowest, .middle` variants of `apply_sorted`.
* Recommend `multiset_function` be used as a decorator, add `update_wrapper`.
* Add `keep_outcomes, drop_outcomes` methods to expressions.
* Add `any` evaluation to expresions.

## v0.25.2 - 23 January 2023

Comparisons on dice with tuple outcomes are now performed elementwise.

## v0.25.1 - 23 January 2023

Testing GitHub workflows.

## 0.25.0 - 22 January 2023

Expanded multiset processing with multiset expressions.

* `OutcomeCountGenerator`, `OutcomeCountEvaluator` renamed to `MultisetGenerator`, `MultisetEvaluator`.
* `multiset_function` is an easy way to create joint evaluators.
* `Pool` indexing is now relative rather than absolute.
* Renamed `pool.sorted_roll_counts` to `pool.keep` and `pool.keep_tuple`.
* `Die` versions of `sum_highest` etc. renamed to just `highest`; these always return dice.
* `MultisetExpression` (including generators like `Pool`) have `highest()` returning an expression.
* `Die` operators now does mixed vector-scalar binary operations by broadcasting the scalar.
* Add `middle()` methods.
* Remove `*generators` argument from `evaluator.order()`, `evaluator.final_outcome()`.
* `*generators` argument of `evaluator.alignment` replaced with the union of all generator outcomes.
* Removed suits.
* Stop using `__class_getitem__`, which is intended for typing only.

## 0.24.0 - 8 January 2023

Reworked built-in generators and evaluators.

* Generators now support multiset operations. These include:
  * Multiset comparisons (`<, <=, >, >=, ==, !=, isdisjoint`), which produce `Die[bool]`.
  * Multiset operators (`+`, `-`, `|`, `&`, `^`) which produce wrapped generators.
  * A suite of chainable count adjustments, including `multiply_counts`, `divide_counts`, `filter_counts`, and `unique`.
* Rename `median_left` to `median_low` etc.
* Generators and evaluators are now paramterized by count type as well.
* Move concrete evaluators to a submodule.

## 0.23.3 - 31 December 2022

* Fixed weighting bug in `__matmul__` when the left die has an outcome of 0.
* Retired the names `standard` and `bernoulli`. These will be just `d` and `coin` respectively.
* `apply` now accepts `Pool` arguments, which will have `expand()` called on them.
* Reinstate automatic Cartesian product in `Population` construction.
* `if_else` now runs in two stages.

## 0.23.2 - 30 December 2022

* Incremental sorting for `all_matching_sets` to reduce state space.
* `lowest()` and `highest()` now actually visible.
* Improved checking for tuple outcome sortability and types.

## 0.23.1 - 29 December 2022

Prepend `sum_` to OutcomeCountGenerator versions of `highest` and `lowest`.

## 0.23.0 - 29 December 2022

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

## 0.22.0 - 19 December 2022

* `Die.sub()` renamed to `Die.map()`.
* `Die.map()` can now include the number of steps taken until absorption.
* `Die.reroll_until()` renamed to `Die.filter()`.
* `wilds` arguments marked experimental, pending decision on how ordering should affect them.
* Only tuples get separate columns in tables and not `str` or `bytes`.
* Non-recursive algorithm for `Again()` handling.

## 0.21.0 - 3 December 2022

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

## 0.20.1 - 10 September 2022

* Added `one_hot` function.
* Added experimental suit generator that wraps a generator and produces counts for all suits for each value.

## 0.20.0 - 6 September 2022

* Retired `denominator_method`.
* Renamed `max_depth` parameters to just `depth`.
* Binary operators delegate to `Again`'s behavior.
* Only single outcomes implicity convert to `Die`.
* `marginals` is now a Sequence, and can be iterated over, unpacked, etc.
* `Die.sub()` now expands extra die arguments into their outcomes.

## 0.19.1 - 21 August 2022

Fix `contains_again` checking of sequences.

## 0.19.0 - 21 August 2022

New feature: `Again()`, a placeholder that allows to roll again with some modification.

* `**kwargs` are forwarded to the constructor of the yielded or returned die for `sub`, `if_else`, `reduce`, `accumulate`, `apply`, `apply_sorted`.
* Add optional `final_kwargs` method to evaluators.
* Rename `max_depth` parameter of `sub()` to `repeat`.

## 0.18.0 - 19 August 2022

* Rename `Die.reduce()` to `Die.simplify()` to avoid confusion with the free function `reduce()`.
* Rename `OutcomeCountEvaluator.direction()` to `order()` and add explicitly named `Order` enums.
* Add `is_in`, `count`, and `count_in` methods to dice.
* Add built-in evaluators as convenience functions of `OutcomeCountGenerator`.

## 0.17.4 - 1 August 2022

* Fixes to `max_depth=None` case of `sub()`.
* This is now marked experimental.

## 0.17.3 - 1 August 2022

* Pass `star` parameter to `sub()` to recursive calls.

## 0.17.2 - 1 August 2022

* `sub()` with `max_depth=None` now handles "monotonic" transitions with finite states. Full absorbing Markov chain calculation still under consideration.
* `sub()` no longer accept sequence input.
* Some minor formatting fixes.

## 0.17.1 - 25 June 2022

* Standardize outcome count of `bernoulli`/`coin` and comparators.
* `standard_pool` now accepts a `dict` argument.
* `post_roll_counts` renamed again to `sorted_roll_counts`.
* `apply_sorted` can be subscripted to set the `sorted_roll_counts`.
* Pools are no longer resizable after creation.
* `Die.pool()` now has mandatory argument, now accepts a sequence argument to set `sorted_roll_counts`.

## 0.17.0 - 19 June 2022

More renaming, experimental `sample()` methods.

* Both `Die` and `Deck` now have `quantities` rather than `weight`, `dups`, etc.
* Many `Die` methods moved to base class and are now available to `Deck`.
* "Eval" is now the full word "Evaluator".
* Parameter and method names are no longer prefixed with "num_".
* `reduce_weights` renamed back to `reduce`.
* `Deck`s can be formatted like `Die`.
* Allow formatting 0-1 probability.
* Experimental `sample()` methods for `OutcomeCountGenerator` and `OutcomeCountEvaluator`.

## 0.16.1 - 18 June 2022

Development of deck API.

* Separate `Deal` class from `Deck`, roughly analogous to `Pool` vs. `Die`.
* `Deal` can now output multiple hands. The counts for each hand are provided in order to `eval.next_state`.
* `comb_row` now uses iterative rather than recursive memoization. This will prevent some stack overflows.
* `Pool`s are not permitted to be constructed using a raw `Die` or `Deck` argument.
* `reduce` argument of `Die.equals()` renamed to `reduce_weights`.

## 0.16.0 - 17 June 2022

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

## 0.15.0 - 10 June 2022

Added type hints. Now requires Python 3.10 or later.

Other changes:

* Add `apply_sorted()` method.
* Add `Die.set_range()`.
* `standard()` / `d()` argument is now positional-only.

## 0.14.1 - 30 May 2022

Reinstate alternate internal `EvalPool` algorithm, which provides better performance in some cases. 

## 0.14.0 - 30 May 2022

* Added a new `EvalPool.alignment()` method. This allows to specify an iterable of outcomes that should always be seen by `next_state` even if they have zero count.
* The free function `d()` is now simply an alias for `standard()`.
* Removed `Die.d()`.
* The `@` operator now casts the right side to a `Die` like other operators.
* Some internal changes to `EvalPool` algorithm.

## 0.13.2 - 23 May 2022

The data of a die resulting from `==` or `!=` is lazily evaluated.

This saves computation in case the caller is only interested in the truth value.

## 0.13.1 - 23 May 2022

`EvalPool` favors the cached direction more.

## 0.13.0 - 23 May 2022

Major reworking of pool construction.

* Public constructor is now just `Pool(*dice)`.
* In particular, no more `truncate_min` or `truncate_max` arguments.
* Pools can be of arbitrary dice, though non-truncative sets of dice will have lower performance. There is some performance penalty overall.
* `apply()` called with no arguments now calls `func` once with no arguments.

## 0.12.1 - 21 May 2022

* Removed `Die.keep()`. Use `Die.pool(...).sum()`.
* `highest`/`lowest` returns empty die if any of the input dice are empty.

## 0.12.0 - 18 May 2022

* Free-function form of `lowest`, `highest` now selects between algorithms for better performance and generality.
* Removed `die.lowest, `die.highest`.
* `die.min_outcome`, `die.max_outcome` no longer take arguments beyond `self`.
* No more (public) `repeat_and_sum`, as this is redundant with `@` and `die.keep()`.
* No more public `die.keep_lowest_single()`, `die.keep_highest_single()`.
* `count_dice` arguments are now keyword-only.
* `die.zero()` no longer reduces weights to 1.
* Update PyPi classifiers.

## 0.11.0 - 11 May 2022

* Removed `min_outcome` parameter from die construction.
* Operations on tuple outcomes are now performed recursively, to match the fact that die expansion on construction is recursive.
* Renamed `Die.reduce()` to `Die.reduce_weights()`.
* Added `reduce()` and `accumulate()` functions analogous to the functions of the same name from functools/itertools.
* Add CSV output.
* Renamed `Die.markdown()` to `Die.format_markdown()`.
* Added `star` parameter to `sub`, `explode`, `reroll`, `reroll_until` methods. If set, this unpacks outcomes before giving them to the supplied function.
* Added experimental `JointEval` class for performing two evals on the same roll of a pool.

## 0.10.2 - 8 May 2022

* Operators other than `[]` are performed element-wise on tuples.
* Rename `DicePool` to just `Pool`. Merge the old factory function into the constructor.

## 0.10.1 - 8 May 2022

* Fix denominator_method='reduce' in die creation.
* Fix outcomes consisting of empty tuple `()`.
* `apply()` with no dice produces an empty die.

## 0.10.0 - 7 May 2022

Retired the `EmptyDie` / `ScalarDie` / `VectorDie` distinction.

* There is now only one `Die` class; it behaves similarly to how `ScalarDie` used to.
* There is no more `ndim`.
* The `[]` operator now forwards to the outcome, acting similar to what `VectorDie.dim[]` used to do.
* Removed `PoolEval.bind_dice()`. It was cute, but I'm not convinced it was worth spending API on.

## 0.9.1 - 1 May 2022

* This will probably be the last version with a `VectorDie` distinction.
* Dice cannot have negative weights.
* `VectorDie` cannot be nested inside tuple outcomes.

## 0.9.0 - 28 April 2022

* Die and dict arguments to `Die()` are now expanded, including when nested.
* Add `Die.if_else()` method, which acts as a ternary conditional operator on outcomes.
* Dice are now hashable. `==` and `!=` return dice with truth values based on whether the two dice have identical outcomes and weights.
* `ndim` now uses singletons `icepool.Scalar` and `icepool.Empty`.

## 0.8.0 - 23 April 2022

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

## 0.7.0 - 16 April 2022

* Renamed from `hdroller` to `icepool`.
* Primary repository is now https://github.com/HighDiceRoller/icepool.
* Only `tuple`s become `VectorDie`.
* Weights of 10^30 or above are not shown in tables by default.

## 0.6.7 - 18 March 2022

* Add `max_depth` parameter to `sub()`. If set to `None` this seeks a fixed point.
* Add `'reduce'` option for `denominator_method` parameters.
* Cache results of `repeat_and_sum()`.

## 0.6.6 - 24 February 2022

* Add `ndim` keyword argument to `d()`.
* Removed `hitting_time()` method; it seems too niche to commit to.
* Several arguments are now keyword-only.
* Fix to `reroll_until()` for vector dice.

## 0.6.5 - 20 February 2022

* Add `VectorDie.all()` and `VectorDie.any()`.
* More fixes to `ndim` calculation.

## 0.6.4 - 20 February 2022

* `EmptyDie` (a die with no outcomes) is now its own class.
* `mix()` along with its weights argument is folded into the `Die()` factory.
* Fixes to `ndim` calculation.
* `apply(), EvalPool.final_outcome()` can now return dice, `hdroller.Reroll`, etc.
* Center `Ellipsis` when indexing a pool can now work on undersized pools, rather than being an error.
* Fix `lcm_weighted` denominator method.
* `len(die)` is now the same as `die.num_outcomes()` again.
* Slicing a die now refers to (sorted) outcome indexes.
* Dimension slicing is now `VectorDie.dim[select]`.

## 0.6.3 - 18 February 2022

* `Die()` now takes a variable number of arguments. A sequence provided as a single argument will be treated as a single outcome equal to that sequence.
    To have one outcome per item in the sequence, the sequence must be unpacked into multiple arguments.
* `min_outcome` and `ndim` args to `Die()` are now keyword-only.
* Non-integers are now allowed for `count_dice`. Use at your own risk.
* The third argument to a `count_dice` slice, if provided, changes the size of the pool.
* Up to one `Ellipsis` (`...`) may now be used in `count_dice`. This allows the tuple option to adapt to differently-sized pools.
* `VectorDie` outcomes are now unpacked when providing them to callable arguments in `reroll()`, `explode()`, `split()`.
* `if_else()` is now a method of `ScalarDie` rather than a free function.
* Fixed the invert operator.

## 0.6.2 - 16 February 2022

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

## 0.6.1 - 12 February 2022

* Pool `max_outcomes` or `min_outcomes` outside the range of the fundamental die is now an error.
* Pools no longer automatically shrink the die to fit `max_outcomes` or `min_outcomes`. This is to guarantee a predictable iteration order.
* Improved `str(die)` formatting.
* `VectorDie` outcomes are automatically converted to tuples.
* `ScalarDie` now has `ndim='scalar'` rather than `ndim=False`.
* Add `standard_pool()` function for easy creation of standard pools.
* Removed `reroll_lt()`, etc. as they weren't enough faster than `reroll(func)` to justify spending extra space.

## 0.6.0 - 9 February 2022

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

## 0.5.2 - 6 February 2022

* Faster algorithm for keeping the single highest/lowest.
* Fix `from_sweights()`.

## 0.5.1 - 6 February 2022

* Fix `max()` and `min()` casting to dice.

## 0.5.0 - 6 February 2022

* Capitalize `Die()` and `Pool()` factory methods.
* `PoolEval` renamed to `EvalPool`.
* Implemented `min_outcomes` for pools. Direction is now determined by `EvalPool`.
* Allow dice with zero weights or zero outcomes.
* `BaseDie` subclasses are now `ScalarDie` and `VectorDie`.
* `==` and `!=` compare outcomes again. Dice are no longer hashable by the standard `hash()`.
* Rewored `Pool()` arguments.
* Added several methods.

## 0.4.4 - 2 February 2022

* Fix `weights_le()` etc.
* `set_outcomes()` is now public.

## 0.4.3 - 2 February 2022

* `min_outcome()`, `max_outcome()` now accept multiple dice.
* Fix slice range going below zero.
* `num_dice` is now an optional parameter for `keep*()` and `pool()`. Exactly one out of `num_dice`, `min_outcomes`, and `max_outcomes` should be provided.
* Removed right-side cast for `@` operator, as it leads to confusion with either other operator casting or `d()` casting.
* Replaced key-value sequence option for `die()` with a sequence of weight-1 outcomes.
* Add `has_zero_weights()` method to dice.
* `align()`, `align_range()` are now public.

## 0.4.2 - 31 January 2022

* Remove numpy install dependency.

## 0.4.1 - 31 January 2022

* Use the `@` operator and `d()` instead of `*` for "roll the die on the left, then roll that many dice on the right and sum".
* `*` operator now multiplies.
* Add `/` operator.
* Add `median_left(), median_right(), ppf(), ppf_left(), ppf_right(), sample(), cmp(), sign()`.

## 0.4.0 - 30 January 2022

No longer numpy-based. Major changes:

* API completely reworked.
* Weights are Python `int`s. This decreases performance but produces all exact results.
* New `MultiDie` class representing multivariate distributions.
* `PoolScorer` classes merged to a single `PoolEval` class.

## 0.3.3 - 27 January 2022

This will most likely be the last numpy-based version.

* Pool scorers skip zero-weight outcomes.
* Removed `__bool__` since zero-weight dice are no longer allowed.

## 0.3.2 - 25 January 2022

* Pool scorers can now return `None` states, which drops the state from evaluation, effectively performing a full reroll.
* Operations that result in no remaining weight (e.g. rerolling all outcomes) now return None.
* Dice can no longer be constructed with zero total weight.
* The `Die()` constructor now auto-trims.
* `Die._align()` is now private and no longer makes all the dice the same weight.
* Fixed `Die.explode()` weighting.
* Cleaned up unused functions.

## 0.3.1 - 24 January 2022

* Optimize `Pool.pops()` by immediately removing all the dice if there are no left in the mask.
* `Die.reroll` now tracks weights properly.

## 0.3.0 - 23 January 2022

* Implemented new keep/pool algorithms, which make heavy use of caching. The `keep*()` function signatures changed.
* `Die` is now hashable.
* Empty `Die` is now an error.
* Removed weight normalization.
* Added `%` and `//` operators to `Die`.
* Renamed `ccdf` to `sf` following `scipy`'s naming.

## 0.2.2 - 30 October 2021

* `best_set` now queries the `score_func` to determine possible outcomes, which allows more flexibility.

## 0.2.1 - 30 October 2021

* `Die.align()` and `Die.trim()` are now public.
* Optimize `keep()` algorithm by skipping to results after passing the last kept die.
* Add `best_set()` method for computing sets of matching dice.

## 0.2.0 - 22 October 2021

The major change in this version is a new roll-and-keep algorithm. This can keep arbitrary indexes, as well as supporting dissimilar dice as long as they share a common "prefix" of weights.

## 0.1.1 - 21 September 2021

## 0.1.0 - 21 September 2021

Initial version.
