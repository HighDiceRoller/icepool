A Python library for computing dice probabilities.

## Installing

```
pip install hdroller
```

## Basic objectives

* Dice are assumed to have integer faces and finite range.
* **Not** Monte-Carlo-based, though this does provide a sample() function.

## Example

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
