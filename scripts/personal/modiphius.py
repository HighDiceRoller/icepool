import _context

from icepool import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

figsize = (8, 4.5)
dpi = 150

pbta_upper = 2 * Die.d6
pbta_lower = 2 * Die.d6 - 4
modi_upper = Die.d9.keep_highest(2)
modi_lower = Die.d9.keep_lowest(2)

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Stat')
ax.set_ylabel('Chance (%)')
ax.grid()
ax.grid(which='minor', axis='x')

legend = ['2d6 + bonus >= 7',
          '2d6 + bonus >= 11',
          'One of two d9 <= stat',
          'Both of two d9 <= stat',
          ]

ax.plot(pbta_lower.outcomes(), 100.0 * pbta_lower.cdf())
ax.plot(pbta_upper.outcomes(), 100.0 * pbta_upper.cdf())
ax.plot(modi_lower.outcomes(), 100.0 * modi_lower.cdf(), linestyle='--')
ax.plot(modi_upper.outcomes(), 100.0 * modi_upper.cdf(), linestyle='--')


ax.set_xticks(numpy.arange(-2, 13), minor=True)
ax.set_xlim(-2, 12)
ax.set_yticks(numpy.arange(0.0, 100.1, 25.0))
ax.set_ylim(bottom=0.0, top=100.0)

pbta_offset = -3
ax2 = ax.secondary_xaxis('top', functions=(lambda x: x + pbta_offset, lambda x: x - pbta_offset))
ax2.set_xlabel('Bonus')

ax.legend(legend)
plt.savefig('output/pbta_vs_two_pool.png', dpi = dpi, bbox_inches = "tight")
