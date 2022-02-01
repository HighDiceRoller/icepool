A Python library for computing dice probabilities.

## Installing

```
pip install hdroller
```

## API documentation

[GitLab.](https://highdiceroller.gitlab.io/hdroller/apidoc/hdroller.html)

## Principles

* Handles both univariate and multivariate distributions.
* Weights are Python `int`s, providing exact results.
* Combinatorics and caching allow for asymptotically efficient solutions to common problems.
* Constant-factor optimizations are not a priority.

## Examples

### *Legend of the Five Rings* (1st-4th edition) dice

[Try this in your browser using a Starboard notebook.](https://starboard.gg/nb/nfmQTSp)

```python
import hdroller

# A standard d10.
die = hdroller.d10

# A d10, exploding on highest face at most twice, similar to Legend of the Five Rings.
die = hdroller.d10.explode(2)

# Roll ten L5R dice and keep the five highest.
die = hdroller.d10.explode(2).keep_highest(10, 5)

import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot(die.outcomes(), die.pmf())
plt.show()
```

### *Advanced Dungeons & Dragons* 1st edition ability score methods

[Try this in your browser using a Starboard notebook.](https://starboard.gg/nb/nSMJ7hH)

Source for ability score rolling methods: [https://www.reddit.com/r/dndnext/comments/6gv1qn/gary_gygaxs_ability_score_creation_methods_from](https://www.reddit.com/r/dndnext/comments/6gv1qn/gary_gygaxs_ability_score_creation_methods_from):

> **Method I:**
>
> All scores are recorded and arranged in the order the player desires. 4d6 are rolled, and the lowest die (or one of the lower) is discarded.
>
> **Method II:**
>
> All scores are recorded and arranged as in Method I. 3d6 are rolled 12 times and the highest 6 scores are retained.
>
> **Method III:**
>
> Scores rolled are according to each ability category, in order, STRENGTH, INTELLIGENCE, WISDOM, DEXTERITY, CONSTITUTION, CHARISMA. 3d6 are rolled 6 times for each ability, and the highest score in each category is retained for that category.
>
> **Method IV:**
>
> 3d6 are rolled sufficient times to generate the 6 ability scores, in order, for 12 characters. The player then selects the single set of scores which he or she finds most desirable and these scores are noted on the character record sheet.

```python

import hdroller

"""
The @ operator means "roll the left die, then roll that many of the right die and sum".
Integers are treated as a die that always rolls that number.
Therefore:
* 3 @ hdroller.d6 means 3d6.
* hdroller.d6 @ 3 means roll a d6 and multiply the result by 3.
"""

method1 = 6 @ hdroller.d6.keep_highest(num_dice=4, num_keep=3)
method2 = (3 @ hdroller.d6).keep_highest(12, 6)
# num_keep defaults to 1.
method3 = 6 @ (3 @ hdroller.d6).keep_highest(6)
method4 = (6 @ (3 @ hdroller.d6)).keep_highest(12)

import numpy
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot(method1.outcomes(), numpy.array(method1.pmf()) * 100.0)
ax.plot(method2.outcomes(), numpy.array(method2.pmf()) * 100.0)
ax.plot(method3.outcomes(), numpy.array(method3.pmf()) * 100.0)
ax.plot(method4.outcomes(), numpy.array(method4.pmf()) * 100.0)
ax.set_title('AD&D 1e ability score methods')
ax.legend(['Method I', 'Method II', 'Method III', 'Method IV'])
ax.set_xlabel('Total of ability scores')
ax.set_xlim(50, 100)
ax.set_ylim(0)
ax.grid(True)
plt.show()
```
