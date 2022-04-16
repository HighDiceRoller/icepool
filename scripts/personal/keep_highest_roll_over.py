import _context

from icepool import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

figsize = (8, 4.5)
dpi = 120

die = 2 * Die.d10.explode(3)
offset = 11.5

legend = [
    'Gumbel',
    'd10! + d10! - 11.5',
    ]

left = -10
right = 20

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Chance (%)')
ax.grid(which = 'both')

x = numpy.arange(left, right + 0.01, 0.01)
x_hl = x / 3.0
y = numpy.power(2.0, -x_hl-numpy.power(2.0, -x_hl)) * numpy.log(2.0) * numpy.log(2.0) / 3.0
ax.plot(x, 100.0 * y)
ax.plot(die.outcomes()  - offset, 100.0 * die.pmf())
ax.legend(legend)

ax.set_xlim(left=left, right=right)
ax.set_ylim(bottom=0.0)
plt.savefig('output/gumbel_pmf.png', dpi = dpi, bbox_inches = "tight")

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Chance to hit (%)')
ax.grid(which = 'both')

x = numpy.arange(left, right + 0.01, 0.01)
x_hl = x / 3.0
y = 1.0 - numpy.power(2.0, -numpy.power(2.0, -x_hl))
ax.plot(x, 100.0 * y)
ax.plot(die.outcomes() - offset, 100.0 * die.sf())
ax.legend(legend)

ax.set_xlim(left=left, right=right)
ax.set_ylim(bottom=0.0, top=100.0)
plt.savefig('output/gumbel_cdf.png', dpi = dpi, bbox_inches = "tight")
