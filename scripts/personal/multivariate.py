import _context

from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.stats

default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

def ellipse_from_covariance(center, cov, **kwargs):
    w, v = numpy.linalg.eigh(cov)
    print(v)
    return mpl.patches.Ellipse(
        center,
        width=2*numpy.sqrt(w[0]),
        height=2*numpy.sqrt(w[1]),
        angle=numpy.degrees(numpy.arctan2(v[1,0], v[0,0])),
        fill=False,
        **kwargs)

def plot_covariance(ax, center, cov, **kwargs):
    for scale, alpha in [(1.0, 1.0),
                         #(2.0, 0.25),
                         #(3.0, 0.4),
                         ]:
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
