A Python library for computing dice probabilities.

## Installing

```
pip install hdroller
```

## Basic objectives

* Dice are assumed to have integer faces and finite range.
* **Not** Monte-Carlo-based, though this does provide a sample() function.

## Examples

### *Legend of the Five Rings* (1st-4th edition) dice

[Try this in your browser using a Starboard notebook.](https://starboard.gg/nb/nfmQTSp)

```python
from hdroller import Die

# A standard d10.
die = Die.d10

# A d10, exploding on highest face at most twice, similar to Legend of the Five Rings.
die = Die.d10.explode(2)

# Roll ten L5R dice and keep the five highest.
die = Die.d10.explode(2).keep_highest(10, 5)

# Plot it.
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot(die.outcomes(), die.pmf())
plt.show()
```

### *Advanced Dungeons & Dragons* 1st edition ability score methods

[Try this in your browser using a Starboard notebook.](https://starboard.gg/nb/nSMJ7hH)

```python
from hdroller import Die

# Note that the * operator is not commutative:
# it means "roll the left die, then roll that many of the right die and sum".
# Integers are treated as a die that always rolls that number.
# Therefore:
# 3 * Die.d6 means 3d6.
# Die.d6 * 3 means roll a d6 and multiply the result by 3.
method1 = 6 * Die.d6.keep_highest(4, 3) 
method2 = (3 * Die.d6).keep_highest(12, 6)
method3 = 6 * (3 * Die.d6).keep_highest(6)
method4 = (6 * (3 * Die.d6)).keep_highest(12)

import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot(method1.outcomes(), method1.pmf() * 100.0)
ax.plot(method2.outcomes(), method2.pmf() * 100.0)
ax.plot(method3.outcomes(), method3.pmf() * 100.0)
ax.plot(method4.outcomes(), method4.pmf() * 100.0)
ax.set_title('AD&D 1e ability score methods')
ax.legend(['Method I', 'Method II', 'Method III', 'Method IV'])
ax.set_xlabel('Total of ability scores')
ax.set_xlim(50, 100)
ax.set_ylim(0)
ax.grid(True)
plt.show()
```
