import _context

from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

import time
import cProfile
import pstats

figsize = (16, 9)
dpi = 150

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid(True)

ability = Die.d(3, 6)

means = []
legend = []

for i in range(6):
    result = ability.keep_index(12, 11 - i)
    ax.plot(result.outcomes(), result.pmf() * 100.0)
    means.append(result.mean())
    legend.append('Mean = %0.2f' % result.mean())

overall_mean = numpy.mean(means)

ax.set_xticks(numpy.arange(3, 19))
ax.set_xlim(3, 18)
ax.set_ylim(0)
ax.set_xlabel('Ability score')
ax.set_ylabel('Chance (%)')
ax.set_title('Best 6 of 12× 3d6 (mean = %0.2f)' % overall_mean)
ax.legend(legend)

plt.savefig('output/ability_scores.png', dpi = dpi, bbox_inches = "tight")
