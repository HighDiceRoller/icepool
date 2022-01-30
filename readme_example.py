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
