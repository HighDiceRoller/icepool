import _context

import hdroller.countdown
from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

def match_func(size, outcome):
    return size * outcome

def straight_func(size, outcome):
    return size * outcome + (size * (size - 1)) // 2 if size >= 3 else 0

import cProfile
cProfile.run('Die.d10.best_set(10, match_func, straight_func)')

figsize = (16, 9)
dpi = 150

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

pools = []

for num_dice in range(1, 11):
    pool = Die.d10.best_set(num_dice, match_func, straight_func)
    ax.plot(pool.outcomes(), pool.sf() * 100.0)
    marker_size = 64 if num_dice < 10 else 128
    ax.scatter(pool.median(), 50.0,
               marker=('$%d$' % num_dice),
               facecolor=default_colors[num_dice-1],
               s=marker_size)
    pools.append(pool)

#ax.legend(['%d-pool' % d for d in range(1, 11)])
ax.set_xlabel('Result')
ax.set_ylabel('Chance of rolling at least (%)')
ax.set_xticks(numpy.arange(0, 60.1, 5.0))
ax.set_yticks(numpy.arange(0, 100.1, 10.0))
ax.set_xlim(1, 60)
ax.set_ylim(0, 100)

plt.savefig('output/framewerk_sf.png', dpi = dpi, bbox_inches = "tight")

aligned_pools = Die.align(pools)

result = 'Result,' + ','.join(str(x) + '-pool' for x in range(1, 11)) + '\n'

for i, outcome in enumerate(aligned_pools[0].outcomes()):
    result += '%d' % outcome
    for j, pool in enumerate(aligned_pools):
        if outcome <= (j+1) * 10:
            width = max(0, j-1)
            result += ',%.*f%%' % (width, pool.pmf()[i] * 100.0)
        else:
            result += ','
    result += '\n'

with open('output/framewerk_pmf.csv', mode='w') as outfile:
    outfile.write(result)
    
result = 'Result,' + ','.join(str(x) + '-pool' for x in range(1, 11)) + '\n'
aligned_pools = Die.align(pools)
for i, outcome in enumerate(aligned_pools[0].outcomes()):
    result += '%d' % outcome
    for j, pool in enumerate(aligned_pools):
        if outcome <= (j+1) * 10:
            width = max(0, j-1)
            result += ',%.*f%%' % (width, pool.sf()[i] * 100.0)
        else:
            result += ','
    result += '\n'

with open('output/framewerk_sf.csv', mode='w') as outfile:
    outfile.write(result)
