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

## Web applications

* [Ability score rolling method calculator](https://highdiceroller.github.io/icepool/apps/ability_scores.html)
* [*Cortex Prime* calculator](https://highdiceroller.github.io/icepool/apps/cortex_prime.html)
* [*Legends of the Wulin* calculator](https://highdiceroller.github.io/icepool/apps/legends_of_the_wulin.html)

## Inline example: *Vampire* 5th edition

[Official site.](https://www.worldofdarkness.com/vampire-the-masquerade)

This edition works as follows:

1. Roll a pool of d10s. Some of these will be normal dice, and some will be Hunger dice.
2. Count each 6+ as a success.
3. For each pair of 10s, add two additional successes (for a total of four successes from those two dice).
4. If the total number of successes meets or exceeds the difficulty, it's a win. Otherwise it's a loss.

In addition to the binary win/loss aspect of the outcome, there are the following special rules:

* A win with at least one pair of 10s is a **critical win**.
* However, a critical win with at least one Hunger die showing a 10 becomes a **messy critical** instead.
* A loss with at least one Hunger die showing a 1 is a **bestial failure**.

### Method 1: One-hot representation

```python
import icepool

# One method is to express the possible outcomes using a tuple 
# that has exactly one element set according to the symbol rolled.
# This is called a "one-hot" representation.
# In this case we have four types of symbols.

normal_die = icepool.Die({(0, 0, 0, 0): 5, # failure
                          (0, 1, 0, 0): 4, # success
                          (0, 0, 1, 0): 1, # crit
                         })
hunger_die = icepool.Die({(1, 0, 0, 0): 1, # bestial failure
                          (0, 0, 0, 0): 4, # failure
                          (0, 1, 0, 0): 4, # success
                          (0, 0, 0, 1): 1, # messy crit
                         })



# Summing the dice produces the total number of each symbol rolled.
# The @ operator means roll the left die, then roll that many of the right die and sum.
# For outcomes that are tuples, sums are performed element-wise.
total = 3 @ normal_die + 2 @ hunger_die

# Then we can use a function to compute the final result.
def eval_one_hot(hunger_botch, success, crit, hunger_crit):
    total_crit = crit + hunger_crit
    success += total_crit + 2 * (total_crit // 2)
    if total_crit >= 2:
        if hunger_crit > 0:
            win_type = 'messy'
        else:
            win_type = 'crit'
    else:
        win_type = ''
    loss_type = 'bestial' if hunger_botch > 0 else ''
    return success, win_type, loss_type

# star=1 unpacks the tuples before giving them to eval_one_hot.
result = total.sub(eval_one_hot, star=1)
print(result)
```

### Method 2: EvalPool

```python
# Another method is to use `EvalPool` with a normal pool and a hunger pool.
# This is a more complex solution, but may be a helpful example.
# In many cases, `EvalPool` is more computationally efficient.

# The die to use.
v5_die = icepool.Die({'botch' : 1, 'failure' : 4, 'success' : 4, 'crit' : 1})

# This evaluates the results of the two pools.
class EvalVampire5(icepool.EvalPool):
    # next_state() computes a "running total". In this case, this is:
    # * The number of successes.
    # * The type of win, if the result is a win.
    # * The type of loss, if the result is a loss.
    def next_state(self, state, outcome, normal, hunger):
        success, win_type, loss_type = state or (0, '', '')
        if outcome == 'crit':
            total_crit = normal + hunger
            # Crits count as successes, and every pair adds 2 more.
            success += total_crit + 2 * (total_crit // 2)
            if total_crit >= 2:
                if hunger > 0:
                    win_type = 'messy'
                else:
                    win_type = 'crit'
        elif outcome == 'success':
            success += normal + hunger
        elif outcome == 'botch':
            if hunger > 0:
                loss_type = 'bestial'
        else:  # normal loss
            pass

        return success, win_type, loss_type

v5_eval = EvalVampire5()

# Now we can construct the normal and Hunger pools and evaluate:
result = v5_eval(v5_die.pool(3), v5_die.pool(2))
print(result)
```

Denominator: 100000

| Outcome[0] | Outcome[1] | Outcome[2] | Weight | Probability |
|-----------:|-----------:|-----------:|-------:|------------:|
|          0 |            |            |   2000 |   2.000000% |
|          0 |            |    bestial |   1125 |   1.125000% |
|          1 |            |            |  11000 |  11.000000% |
|          1 |            |    bestial |   4625 |   4.625000% |
|          2 |            |            |  23160 |  23.160000% |
|          2 |            |    bestial |   6840 |   6.840000% |
|          3 |            |            |  23632 |  23.632000% |
|          3 |            |    bestial |   4368 |   4.368000% |
|          4 |            |            |  11776 |  11.776000% |
|          4 |            |    bestial |   1024 |   1.024000% |
|          4 |       crit |            |    240 |   0.240000% |
|          4 |       crit |    bestial |    135 |   0.135000% |
|          4 |      messy |            |    725 |   0.725000% |
|          4 |      messy |    bestial |    150 |   0.150000% |
|          5 |            |            |   2304 |   2.304000% |
|          5 |       crit |            |    688 |   0.688000% |
|          5 |       crit |    bestial |    237 |   0.237000% |
|          5 |      messy |            |   2055 |   2.055000% |
|          5 |      messy |    bestial |    270 |   0.270000% |
|          6 |       crit |            |    656 |   0.656000% |
|          6 |       crit |    bestial |    104 |   0.104000% |
|          6 |      messy |            |   1920 |   1.920000% |
|          6 |      messy |    bestial |    120 |   0.120000% |
|          7 |       crit |            |    208 |   0.208000% |
|          7 |      messy |            |    592 |   0.592000% |
|          8 |      messy |            |     23 |   0.023000% |
|          8 |      messy |    bestial |      2 |   0.002000% |
|          9 |      messy |            |     21 |   0.021000% |
