import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.stats
import scipy.special

def balls_into_bins_lifetime(num_bins, max_load):
    # result: number of balls needed to exceed max_load
    max_balls = num_bins * max_load
    result = numpy.zeros((max_balls+2,))
    # each dimension represents the number of balls in one bin
    state = numpy.zeros((max_load+1,) * num_bins)
    state[(0,) * num_bins] = 1.0

    for i in range(1, max_balls+2):
        next_state = numpy.zeros_like(state)
        for indexes in numpy.ndindex((max_load+1,) * num_bins):
            p = state[indexes] / num_bins
            for hit_bin in range(num_bins):
                if indexes[hit_bin] == max_load:
                    result[i] += p
                else:
                    next_indices = indexes[:hit_bin] + (indexes[hit_bin] + 1,) + indexes[hit_bin+1:]
                    next_state[next_indices] += p
        state = next_state
    return numpy.arange(max_balls+2), result

figsize = (8, 4.5)
dpi = 150

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

legend = []

for max_load in range(1, 6):
    x, y = balls_into_bins_lifetime(6, max_load)
    print(y)
    mean = numpy.dot(x, y)
    ax.plot(x, y * 100.0)
    legend.append('%d hits to single bin to kill (mean = %0.2f)' % (max_load+1, mean))

ax.set_xlim(0)
ax.set_ylim(0)
ax.set_xlabel('Total number of hits to kill')
ax.set_ylabel('Chance (%)')
ax.legend(legend)
ax.set_title('6 bins')

plt.savefig('output/balls_into_bins.png', dpi = dpi, bbox_inches = "tight")
