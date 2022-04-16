import _context

from icepool import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

figsize = (8, 4.5)
dpi = 150

x = numpy.arange(1, 16, 1)
dmg = numpy.array([1, 1.5, 2, 2, 2,
                   2, 2.5, 2.5, 2.5, 2.5,
                   3, 3, 3, 3, 4])

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

ax.plot(x, dmg)
ax.plot(x, numpy.power(x, 0.5))
ax.plot(x, numpy.power(x, 0.4))

ax.set_xticks([1, 2, 3, 7, 11, 15])
ax.set_xlim(1.0, 15.0)
ax.set_ylim(1.0, 4.0)
ax.set_xlabel('Number of monsters')
ax.set_ylabel('Multiplier')

ax.legend([
    'DMG Encounter Multiplier',
    'Lanchester 1.5',
    'Lanchester 1.4'])

plt.savefig('output/lanchester_dmg.png', dpi = dpi, bbox_inches = "tight")
