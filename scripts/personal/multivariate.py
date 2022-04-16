import _context

from icepool import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.stats

default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

def ellipse_from_covariance(center, cov, **kwargs):
    w, v = numpy.linalg.eigh(cov)
    #print(v)
    return mpl.patches.Ellipse(
        center,
        width=2*numpy.sqrt(w[0]),
        height=2*numpy.sqrt(w[1]),
        angle=numpy.degrees(numpy.arctan2(v[1,0], v[0,0])),
        fill=False,
        **kwargs)

def plot_covariance(ax, center, cov, max_n=1, alpha_factor=0.5, **kwargs):
    for scale in range(1, max_n+1):
        alpha = numpy.power(alpha_factor, scale-1)
        e = ellipse_from_covariance(center, cov * scale * scale,
                                    alpha=alpha, **kwargs)
        ax.add_artist(e)


for z in [1, 2, 3]:
    print(z, scipy.stats.chi.cdf(z, 1), scipy.stats.chi.cdf(z, 2))

figsize = (8, 4.5)
dpi = 150

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

spiral_mean = numpy.array([2/3, 0])
spiral_cov = numpy.array([[5/9, -1/4],
                        [-1/4, 1.0]])
spiral_one_x = [
                0, 1, 
                1, 2, 2, 0]
spiral_one_y = [
                2, 1,
                0, -1, 0, 0]

spiral_dup_x = [0, 0, 1]
spiral_dup_y = [-1, 1, -1]

ax.set_xlabel('Successes')
ax.set_ylabel('Spares - Spirals')
ax.set_xticks(numpy.arange(0, 7))
ax.set_xlim(0, 6)
ax.set_yticks(numpy.arange(-3, 4))
ax.set_ylim(-2.5, 2.5)
ax.set_aspect('equal')
ax.scatter(spiral_one_x, spiral_one_y, marker='x', c=default_colors[0])
ax.scatter(spiral_dup_x, spiral_dup_y, marker='X', c=default_colors[0])
for count, color in zip(range(1, 7), default_colors):
    plot_covariance(ax,
                    spiral_mean * count,
                    spiral_cov * count,
                    edgecolor=color)

plt.savefig('output/spiral_distribution.png', dpi = dpi, bbox_inches = "tight")

def scatter_spiral(num_dice, rolls_mult):
    x1 = numpy.array([0, 0, 0, 0,
                      0, 1, 1, 1,
                      1, 2, 2, 0])
    y1 = numpy.array([-1, -1, 1, 1,
                      2, 1, -1, -1,
                      0, -1, 0, 0])

    result = (numpy.random.rand(rolls_mult * (len(x1) ** num_dice), 2) - 0.5) * 0.5
    print(result.shape)
    for i in range(num_dice):
        indices = (numpy.arange(result.shape[0]) // (len(x1) ** i)) % 12
        result[:, 0] += x1[indices]
        result[:, 1] += y1[indices]

    return result

fig = plt.figure(figsize=(16, 9))
ax = plt.subplot(111)
ax.grid()

count = 3
rolls_mult = 1
rolls = scatter_spiral(count, rolls_mult)

ax.set_title('%d Spiral Dice (%d outcomes)' % (count, 12 ** count))
ax.set_xlabel('Successes')
ax.set_ylabel('Spares - Spirals')
ax.set_xticks(numpy.arange(0, 2*count+1))
ax.set_yticks(numpy.arange(-count, 2*count+1))

print(numpy.mean(rolls, axis=0))
color = default_colors[count-1]
ax.scatter(rolls[:, 0], rolls[:, 1], marker = '.', s=1)
plot_covariance(ax, spiral_mean * count, spiral_cov * count, max_n=2, edgecolor=color)

ax.set_aspect('equal')

plt.savefig('output/spiral_scatter.png', dpi=dpi, bbox_inches = "tight")
                
