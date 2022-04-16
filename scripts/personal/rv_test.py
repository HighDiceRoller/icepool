import _context

import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.stats
import scipy.special

from icepool import Die

die = Die.d(1000, 6)

die = Die.d(10, 6)
norm_die = Die.from_rv(scipy.stats.norm, die.min_outcome(), die.max_outcome(), loc=die.mean(), scale=die.standard_deviation())

fig = plt.figure()
ax = plt.subplot(111)

ax.plot(die.outcomes(), die.cdf())
ax.plot(norm_die.outcomes(), norm_die.cdf())

#plt.show()
