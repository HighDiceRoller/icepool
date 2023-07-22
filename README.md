# <img width="32" height="32" src="https://highdiceroller.github.io/icepool/favicon.png" /> Icepool

Python dice probability package.

[GitHub repository.](https://github.com/HighDiceRoller/icepool)

[PyPi page.](https://pypi.org/project/icepool/)

Try coding in your browser using [Icecup](https://highdiceroller.github.io/icepool/apps/icecup.html), a simple frontend for scripting and graphing similar to AnyDice, SnakeEyes, and Troll. You can find a series of tutorials [here](https://highdiceroller.github.io/icepool/notebooks/lab?path=tutorial%2Fc00_introduction.ipynb).

## Features

* Pure Python implementation using only the Standard Library. Run it almost anywhere Python runs: program locally, share Jupyter notebooks, or build your own client-side web apps using Pyodide.
* Dice support all standard operators (+, -, <, >, etc.) as well as an extensive library of functions (rerolling, exploding, etc.)
* Efficient dice pool algorithm can solve keep-highest, finding sets and/or straights, *RISK*-like mechanics, and more in milliseconds, even for large pools.
* Exact fractional probabilities using Python `int`s.
* Some support for decks (aka sampling without replacement).

## Installing

```
pip install icepool
```

The source is pure Python, so including a direct copy in your project can work as well.

## Contact

Feel free to open a [discussion](https://github.com/HighDiceRoller/icepool/discussions) or [issue](https://github.com/HighDiceRoller/icepool/issues) on GitHub. You can also find me on [Reddit](https://www.reddit.com/user/HighDiceRoller) or [Twitter](https://twitter.com/highdiceroller).

## API documentation

[pdoc on GitHub.](https://highdiceroller.github.io/icepool/apidoc/latest/icepool.html)

## JupyterLite notebooks

See this [JupyterLite distribution](https://highdiceroller.github.io/icepool/notebooks/lab/index.html) for a collection of interactive, editable examples. These include mechanics from published games, StackExchange, Reddit, and academic papers. 

[JupyterLite REPL.](https://highdiceroller.github.io/icepool/notebooks/repl/index.html?kernel=python&toolbar=1&code=import%20piplite%0Aawait%20piplite.install(%22icepool%22)%0Aimport%20icepool)

### Tutorial notebooks

In particular, here is a series of [tutorial notebooks.](https://highdiceroller.github.io/icepool/notebooks/lab?path=tutorial%2Fc00_introduction.ipynb)

## Web applications

These are all client-side, powered by [Pyodide](https://pyodide.org/). Perhaps you will find inspiration for your own application.

* [Icecup](https://highdiceroller.github.io/icepool/apps/icecup.html), a simple frontend for scripting and graphing.
* Alex Recarey's [Face 2 Face Calculator](https://infinitythecalculator.com/) for *Infinity the Game N4* -- including the ability to be installed on Android and iOS and run without an internet connection.
* [Ability score rolling method calculator.](https://highdiceroller.github.io/icepool/apps/ability_scores.html)
* [Cortex Prime calculator.](https://highdiceroller.github.io/icepool/apps/cortex_prime.html)
* [*Legends of the Wulin* calculator.](https://highdiceroller.github.io/icepool/apps/legends_of_the_wulin.html)
* [Year Zero Engine calculator.](https://highdiceroller.github.io/icepool/apps/year_zero_engine.html)

## Paper on algorithm

Presented at [Artificial Intelligence and Interactive Digital Entertainment (AIIDE) 2022](https://sites.google.com/view/aiide-2022/).

[In the official proceedings.](https://ojs.aaai.org/index.php/AIIDE/article/view/21971)

[Preprint in this repository.](https://github.com/HighDiceRoller/icepool/blob/main/papers/icepool_preprint.pdf)

BibTeX:

```bibtex
@inproceedings{liu2022icepool,
    title={Icepool: Efficient Computation of Dice Pool Probabilities},
    author={Albert Julius Liu},
    booktitle={Eighteenth AAAI Conference on Artificial Intelligence and Interactive Digital Entertainment},
    volume={18},
    number={1},
    pages={258-265},
    year={2022},
    month={Oct.},
    eventdate={2022-10-24/2022-10-28},
    venue={Pomona, California},
    url={https://ojs.aaai.org/index.php/AIIDE/article/view/21971},
    doi={10.1609/aiide.v18i1.21971}
}
```

## Versioning

Frankly, backwards compatability is not a high priority. If you need specific behavior, I recommend version pinning. I believe the `Die` interface to be reasonably stable, but there's a good chance that `Multiset*` will see more changes in the future. Typing is especially unstable.

## Inline examples

### Summing ability scores

What's the chance that the sum of player A's six ability scores is greater than or equal to the sum of player B's six ability scores?
(Using 4d6 keep highest 3 for each ability score.)

```python
import icepool

single_ability = icepool.d6.highest(4, 3)

# The @ operator means: compute the left side, and then roll the right side that many times and sum.
print(6 @ single_ability >= 6 @ single_ability)
```

Die with denominator 22452257707354557240087211123792674816

| Outcome | Probability |
|:--------|------------:|
| False   |  47.984490% |
| True    |  52.015510% |

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

class AllMatchingSets(icepool.MultisetEvaluator):
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

## Similar projects

In roughly chronological order:

### Troll by Torben Ægidius Mogensen

http://hjemmesider.diku.dk/~torbenm/Troll/

The oldest general-purpose dice probability calculator I know of. It has an accompanying peer-reviewed paper.

### AnyDice by Jasper Flick

https://anydice.com/

Probably the most popular dice probability calculator in existence, and with good reason---its accessibility and shareability remains unparalleled. I still use it often for prototyping and as a second opinion.

### SnakeEyes by Noé Falzon

https://snake-eyes.io/

SnakeEyes demonstrated the viability of browser-based, client-side dice calculation, as well as introducing me to [Chart.js](https://www.chartjs.org/).

### dice_roll.py by Ilmari Karonen

https://gist.github.com/vyznev/8f5e62c91ce4d8ca7841974c87271e2f

This demonstrated the trick of iterating "vertically" over the outcomes of dice in a dice pool, rather than "horizontally" through the dice---one of the insights into creating a much faster dice pool algorithm.

### `dyce` by Matt Bogosian

https://github.com/posita/dyce

Another Python dice probability package. I've benefited greatly from exchanging our experiences.
