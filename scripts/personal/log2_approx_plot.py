import _context
from icepool import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

right = 8

figsize = (8, 4.5)
dpi = 150

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax2 = ax.twinx()
ax2.set_ylabel('Miss chance (%)')

yticks = [0.0, 0.25, 0.5, 0.75, 1.0]

ax.set_yticks(yticks)
ax.set_yticklabels('%d' % (y * 100.0) for y in yticks)
ax2.set_yticks(yticks)
ax2.set_yticklabels('%d' % ((1.0 - y) * 100.0) for y in yticks)

x = numpy.arange(0.0, right+1e-3, 0.01)
y = 1.0 - numpy.power(2.0, -x)

ax.plot(x, y)
ax.annotate('    Approximately linear hit chance',
            xy=(0.0, 0.0),
            xytext=(0.5, 0.5 * numpy.log(2.0)),
            arrowprops={'facecolor':'black', 'headwidth':5.0, 'shrink':0.01, 'width':1.0},
            ha='left', va='bottom')

ax.annotate('Exponential falloff\nin miss chance',
            xy=(8.0, 15/16),
            xytext=(5.0, 7/8),
            arrowprops={'facecolor':'black', 'headwidth':5.0, 'shrink':0.01, 'width':1.0},
            ha='right', va='top')

ax.set_xlabel('A/T')
ax.set_ylabel('Hit chance (%)')
ax.set_xlim(left=0.0, right=right)
ax.set_ylim(bottom=0.0, top=1.0)
plt.savefig('output/log2_approx_plot.png', dpi = dpi, bbox_inches = "tight")
