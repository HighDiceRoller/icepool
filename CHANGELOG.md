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
