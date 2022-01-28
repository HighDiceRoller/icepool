import _context

import hdroller.countdown
from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

def match_func(size, outcome):
    return size

import cProfile
cProfile.run('Die.d6.best_set(20, match_func)')

figsize = (16, 9)
dpi = 150

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid(which='major', alpha=1.0)
ax.grid(which='minor', alpha=0.25)

pool_sizes = numpy.arange(1, 21)
max_matching = 10
pools = []

for num_dice in pool_sizes:
    pool = Die.d6.best_set(num_dice, match_func)
    pools.append(pool)

prev_y = 100.0

for match_size in numpy.arange(2, max_matching+1):
    y = 100.0 * numpy.array([float(pool >= match_size) for pool in pools])
    if match_size == 3: print(y)
    ax.fill_between(pool_sizes, prev_y, y)
    prev_y = y

ax.fill_between(pool_sizes, prev_y, 0.0)
    
ax.legend(['No matching dice'] +
          ['%d matching dice' % d for d in numpy.arange(2, max_matching)] +
          ['%d+ matching dice' % max_matching], loc='upper left')
ax.set_xlabel('Number of dice')
ax.set_ylabel('Chance (%)')
ax.set_xticks(numpy.arange(0, 21, 5))
ax.set_xticks(numpy.arange(0, 21), minor=True)
ax.set_yticks(numpy.arange(0, 100.1, 10.0))
ax.set_xlim(1, 20)
ax.set_ylim(0, 100)

plt.savefig('output/d6_matches_sf.png', dpi = dpi, bbox_inches = "tight")

# Compare: count 5s

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid(which='major', alpha=1.0)
ax.grid(which='minor', alpha=0.25)

pool_sizes = numpy.arange(1, 21)
max_matching = 10
pools = []

for num_dice in pool_sizes:
    pool = num_dice * (Die.d6 >= 4)
    pools.append(pool)

prev_y = 100.0

for match_size in numpy.arange(2, max_matching+1):
    y = 100.0 * numpy.array([float(pool >= match_size) for pool in pools])
    if match_size == 3: print(y)
    ax.fill_between(pool_sizes, prev_y, y)
    prev_y = y

ax.fill_between(pool_sizes, prev_y, 0.0)
    
ax.legend(['No matching dice'] +
          ['%d matching dice' % d for d in numpy.arange(2, max_matching)] +
          ['%d+ matching dice' % max_matching], loc='upper left')
ax.set_xlabel('Number of dice')
ax.set_ylabel('Chance (%)')
ax.set_xticks(numpy.arange(0, 21, 5))
ax.set_xticks(numpy.arange(0, 21), minor=True)
ax.set_yticks(numpy.arange(0, 100.1, 10.0))
ax.set_xlim(1, 20)
ax.set_ylim(0, 100)

plt.savefig('output/d6_count_sf.png', dpi = dpi, bbox_inches = "tight")
