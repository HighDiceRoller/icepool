import _context

from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

die_sizes = [4, 6, 8, 10, 12]
x = numpy.arange(1, 21)
xticks = numpy.arange(0, 21, 4)

figsize = (8, 4.5)
dpi = 120

# ideal plot

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Target number')
ax.set_ylabel('Chance of hitting')
ax.grid(which = "both")
ax.set_title('Ideal')

legend = []

for die_size in die_sizes:
    y = numpy.power(die_size, -(x-1) / die_size)
    ax.semilogy(x, y)
    legend.append('d%d!' % die_size)

ax.set_xticks(xticks)
ax.set_xlim(left=0, right=20)
ax.set_ylim(top=1, bottom=1e-2)
ax.legend(legend, loc = 'upper right')
plt.savefig('output/explode_non_opposed_ideal.png', dpi = dpi, bbox_inches = "tight")

# actual

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Target number')
ax.set_ylabel('Chance of hitting')
ax.grid(which = "both")
ax.set_title('Actual')

legend = []

for die_size in die_sizes:
    die = Die.d(die_size).explode(10)
    y = [die >= t for t in x]
    ax.semilogy(x, y)
    legend.append('d%d!' % die_size)

ax.set_xticks(xticks)
ax.set_xlim(left=0, right=20)
ax.set_ylim(top=1, bottom=1e-2)
ax.legend(legend, loc = 'lower left')
plt.savefig('output/explode_non_opposed_actual.png', dpi = dpi, bbox_inches = "tight")

# wild

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Target number')
ax.set_ylabel('Chance of hitting')
ax.grid(which = "both")
ax.set_title('With wild die')

legend = []

for die_size in die_sizes:
    die = Die.d(die_size).explode(10)
    wild = Die.d6.explode(10)
    die = die.max(wild)
    y = [die >= t for t in x]
    ax.semilogy(x, y)
    legend.append('max(d%d!, d6!)' % die_size)

ax.set_xticks(xticks)
ax.set_xlim(left=0, right=20)
ax.set_ylim(top=1, bottom=1e-2)
ax.legend(legend, loc = 'lower left')
plt.savefig('output/explode_non_opposed_wild.png', dpi = dpi, bbox_inches = "tight")

# big-small

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Target number')
ax.set_ylabel('Chance of hitting')
ax.grid(which = "both")
ax.set_title('Big-small')

legend = []

for die_size in die_sizes:
    die = Die.coin(0.5).explode(100) * die_size + Die.d(die_size)
    y = [die >= t for t in numpy.arange(1, 41)]
    ax.semilogy(numpy.arange(1, 41), y)
    legend.append('d{0,1}!*%d+d%d' % (die_size, die_size))

ax.set_xticks(numpy.arange(0,41,5))
ax.set_xlim(left=0, right=40)
ax.set_ylim(top=1, bottom=1e-2)
ax.legend(legend, loc = 'lower left')
plt.savefig('output/explode_non_opposed_big_small.png', dpi = dpi, bbox_inches = "tight")

# ratio

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Target number')
ax.set_ylabel('Actual chance / ideal chance')
ax.grid()

legend = []

for die_size in die_sizes:
    die = Die.d(die_size).explode(10)
    y1 = numpy.power(die_size, -(x-1) / die_size)
    y2 = numpy.array([die >= t for t in x])
    ax.plot(x, y2 / y1)
    legend.append('d%d!' % die_size)

ax.set_xticks(xticks)
ax.set_xlim(left=0, right=20)
ax.set_ylim(bottom=0)
#ax.set_yticks(numpy.arange(0.6, 1.9, 0.2))
ax.legend(legend, loc = 'upper left')
plt.savefig('output/explode_non_opposed_ratio.png', dpi = dpi, bbox_inches = "tight")

# smoothed

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Target number')
ax.set_ylabel('Chance of hitting')
ax.grid(which = "both")

legend = []

for die_size in [3, 4, 5, 6, 8, 10, 12]:
    die = Die.d(die_size).explode(10) + Die.d(die_size)
    y = [die >= t for t in x]
    ax.semilogy(x, y)
    legend.append('d%d! + d%d' % (die_size, die_size))

ax.set_xticks(xticks)
ax.set_ylim(top=1, bottom=1e-2)
ax.legend(legend, loc = 'lower left')
plt.savefig('output/explode_non_opposed_smoothed.png', dpi = dpi, bbox_inches = "tight")

# double

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Target number')
ax.set_ylabel('Chance of hitting')
ax.grid(which = "both")

legend = []

for die_size in [3, 4, 5, 6, 8, 10, 12]:
    die = 2 * Die.d(die_size).explode(10)
    y = [die >= t for t in x]
    ax.semilogy(x, y)
    legend.append('2d%d!' % (die_size,))

ax.set_xticks(xticks)
ax.set_ylim(top=1, bottom=1e-2)
ax.legend(legend, loc = 'lower left')
plt.savefig('output/explode_non_opposed_double.png', dpi = dpi, bbox_inches = "tight")

# advantage

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Target number')
ax.set_ylabel('Chance of hitting')
ax.grid(which = "both")

legend = []

for die_size in [3, 4, 5, 6, 8, 10, 12]:
    die = Die.d(die_size).explode(10).keep_highest(2, 1)
    y = [die >= t for t in x]
    ax.semilogy(x, y)
    legend.append('2d%dkh' % (die_size,))

ax.set_xticks(xticks)
ax.set_ylim(top=1, bottom=1e-2)
ax.legend(legend, loc = 'lower left')
plt.savefig('output/explode_non_opposed_adv.png', dpi = dpi, bbox_inches = "tight")

# plus d6

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Target number')
ax.set_ylabel('Chance of hitting')
ax.grid(which = "both")

legend = []

for die_size in [4, 6, 8, 10, 12]:
    die = Die.d(die_size).explode(10) + Die.d6
    y = [die >= t for t in x]
    ax.semilogy(x, y)
    legend.append('d%d + d6' % (die_size,))

ax.set_xticks(xticks)
ax.set_ylim(top=1, bottom=1e-2)
ax.legend(legend, loc = 'lower left')
plt.savefig('output/explode_non_opposed_plus_d6.png', dpi = dpi, bbox_inches = "tight")
