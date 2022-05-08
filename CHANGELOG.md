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
