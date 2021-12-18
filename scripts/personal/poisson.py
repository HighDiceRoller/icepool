import _context

from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

figsize = (8, 4.5)
dpi = 120

right = 4

max_success = 4

x = numpy.arange(0.0, right + 1e-6, 0.1)
y = [numpy.zeros_like(x) for i in range(max_success+1)]

for i, half_life in enumerate(x):
    mean = half_life * numpy.log(2)
    die = Die.poisson(mean, max_outcome=max_success+1)
    sf = die.sf()
    for num_successes in range(max_success+1):
        y[num_successes][i] = sf[num_successes]

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

legend = []

for num_successes in range(1, max_success+1):
    ax.plot(x, 100.0 * y[num_successes])
    if num_successes == 1:
        legend.append('%d success' % num_successes)
    else:
        legend.append('%d successes' % num_successes)
ax.set_xlabel('A/T')
ax.set_ylabel('Chance (%)')
ax.set_xlim(left=0.0, right=right)
ax.set_xticks(numpy.arange(0, right+1))
ax.set_ylim(bottom=0.0, top=100.0)
ax.legend(legend)
plt.savefig('output/keep_highest_success_count.png', dpi = dpi, bbox_inches = "tight")
    
