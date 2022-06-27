# <img width="32" height="32" src="https://highdiceroller.github.io/icepool/favicon.png" /> Icepool

A Python package for computing dice probabilities.

[GitHub repository.](https://github.com/HighDiceRoller/icepool)

[PyPi page.](https://pypi.org/project/icepool/)

## Features

* Pure Python implementation.
* Exact fractional probabilities using Python `int`s.
* Dice support all standard operators (+, -, <, >, etc.) as well as an extensive library of functions (rerolling, exploding, etc.)
* Can outperform sequence/multiset-based algorithms on many dice pool problems.
    In some cases it may be thousands or millions of times faster.
* Experimental support for decks (sampling without replacement).

## Installing

```
pip install icepool
```

The source is pure Python, so making a direct copy can work as well.

## Contact

Feel free to open a [discussion](https://github.com/HighDiceRoller/icepool/discussions) or [issue](https://github.com/HighDiceRoller/icepool/issues) on GitHub. You can also find me on [Twitter](https://twitter.com/highdiceroller) or [Reddit](https://www.reddit.com/user/HighDiceRoller).

## API documentation

[pdoc on GitHub.](https://highdiceroller.github.io/icepool/apidoc/icepool.html)

## JupyterLite notebooks

See this [JupyterLite distribution](https://highdiceroller.github.io/icepool/notebooks/lab/index.html) for a collection of interactive, editable examples. These include mechanics from published games, StackExchange, Reddit, and academic papers. 

[JupyterLite REPL.](https://highdiceroller.github.io/icepool/notebooks/repl/index.html?kernel=python&toolbar=1&code=import%20piplite%0Aawait%20piplite.install(%22icepool%22)%0Aimport%20icepool)

## Web applications

* [Icecup](https://highdiceroller.github.io/icepool/apps/icecup.html), a simple frontend for scripting and graphing.
* [Ability score rolling method calculator.](https://highdiceroller.github.io/icepool/apps/ability_scores.html)
* [*Cortex Prime* calculator.](https://highdiceroller.github.io/icepool/apps/cortex_prime.html)
* [*Legends of the Wulin* calculator.](https://highdiceroller.github.io/icepool/apps/legends_of_the_wulin.html)

## Inline examples

### Summing ability scores

What's the chance that the sum of player A's six ability scores is greater than or equal to the sum of player B's six ability scores?
(Using 4d6 keep highest 3 for each ability score.)

```python
import icepool

single_ability = icepool.d6.keep_highest(4, 3)

# The @ operator means: compute the left side, and then roll the right side that many times and sum.
print(6 @ single_ability >= 6 @ single_ability)
```

Denominator: 22452257707354557240087211123792674816
| Outcome |                                 Weight | Probability |
|--------:|---------------------------------------:|------------:|
|   False | 10773601417436608285167797336637018642 |  47.984490% |
|    True | 11678656289917948954919413787155656174 |  52.015510% |

### All matching sets

[Blog post.](https://asteroid.divnull.com/2008/01/chance-of-reign/)

[Question on Reddit.](https://www.reddit.com/r/askmath/comments/rqtqkq/probability_value_has_chance_in_a_way_i_dont/)

[Another question on Reddit.](https://www.reddit.com/r/RPGdesign/comments/u8yuhg/odds_of_multiples_doubles_triples_quads_quints/)

[Question on StackExchange.](https://math.stackexchange.com/questions/4436121/probability-of-rolling-repeated-numbers)

Roll a bunch of dice, and find **all** matching sets (pairs, triples, etc.)

We *could* manually enumerate every case as per the blog post. However, this is prone to error.
Fortunately, Icepool can do this simply and reasonably efficiently with no explicit combinatorics on the user's part.

```python
import icepool

class AllMatchingSets(icepool.OutcomeCountEvaluator):
    def next_state(self, state, outcome, count):
        """next_state computes a "running total"
        given one outcome at a time and how many dice rolled that outcome.
        """
        if state is None:
            state = ()
        # If at least a pair, append the size of the matching set.
        if count >= 2:
            state += (count,)
        # Prioritize larger sets.
        return tuple(sorted(state, reverse=True))

all_matching_sets = AllMatchingSets()

# Evaluate on 10d10.
print(all_matching_sets(icepool.d10.pool(10)))
```

Die with denominator 10000000000

| Outcome         |   Quantity | Probability |
|:----------------|-----------:|------------:|
| ()              |    3628800 |   0.036288% |
| (2,)            |  163296000 |   1.632960% |
| (2, 2)          | 1143072000 |  11.430720% |
| (2, 2, 2)       | 1905120000 |  19.051200% |
| (2, 2, 2, 2)    |  714420000 |   7.144200% |
| (2, 2, 2, 2, 2) |   28576800 |   0.285768% |
| (3,)            |  217728000 |   2.177280% |
| (3, 2)          | 1524096000 |  15.240960% |
| (3, 2, 2)       | 1905120000 |  19.051200% |
| (3, 2, 2, 2)    |  381024000 |   3.810240% |
| (3, 3)          |  317520000 |   3.175200% |
| (3, 3, 2)       |  381024000 |   3.810240% |
| (3, 3, 2, 2)    |   31752000 |   0.317520% |
| (3, 3, 3)       |   14112000 |   0.141120% |
| (4,)            |  127008000 |   1.270080% |
| (4, 2)          |  476280000 |   4.762800% |
| (4, 2, 2)       |  285768000 |   2.857680% |
| (4, 2, 2, 2)    |   15876000 |   0.158760% |
| (4, 3)          |  127008000 |   1.270080% |
| (4, 3, 2)       |   63504000 |   0.635040% |
| (4, 3, 3)       |    1512000 |   0.015120% |
| (4, 4)          |    7938000 |   0.079380% |
| (4, 4, 2)       |    1134000 |   0.011340% |
| (5,)            |   38102400 |   0.381024% |
| (5, 2)          |   76204800 |   0.762048% |
| (5, 2, 2)       |   19051200 |   0.190512% |
| (5, 3)          |   12700800 |   0.127008% |
| (5, 3, 2)       |    1814400 |   0.018144% |
| (5, 4)          |     907200 |   0.009072% |
| (5, 5)          |      11340 |   0.000113% |
| (6,)            |    6350400 |   0.063504% |
| (6, 2)          |    6350400 |   0.063504% |
| (6, 2, 2)       |     453600 |   0.004536% |
| (6, 3)          |     604800 |   0.006048% |
| (6, 4)          |      18900 |   0.000189% |
| (7,)            |     604800 |   0.006048% |
| (7, 2)          |     259200 |   0.002592% |
| (7, 3)          |      10800 |   0.000108% |
| (8,)            |      32400 |   0.000324% |
| (8, 2)          |       4050 |   0.000041% |
| (9,)            |        900 |   0.000009% |
| (10,)           |         10 |   0.000000% |
