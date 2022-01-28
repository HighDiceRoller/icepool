import numpy
from math import comb

n = 10
step = 1

x = numpy.linspace(0, 1, 1001)
xticks = numpy.arange(0.0, 1.0001, 0.1)

def plot_beta(ax, x, xticks, n, step=1):
    for k in range(0, n+1, step):
        y = numpy.power(x, k) * numpy.power(1.0 - x, n - k) * (comb(n, k) * (n+1))
        ax.plot(x, y)
    ax.set_xlim(0, 1)
    ax.set_xticks(xticks)
    ax.set_ylim(0, 2 * numpy.sqrt(n))


import matplotlib as mpl
import matplotlib.pyplot as plt

figsize = (8, 4.5)
dpi = 150

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid(True)

plot_beta(ax, x, xticks, n, step)

plt.savefig('output/beta.png', dpi = dpi, bbox_inches = "tight")

def plot_beta_arcsine(ax, x, xticks, n, step=1):
    def rescale_x(x):
        return numpy.arcsin(numpy.sqrt(x))
    x_rescaled = rescale_x(x)
    y_scale = numpy.sqrt(x * (1.0-x))
    for k in range(0, n+1, step):
        y = numpy.power(x, k) * numpy.power(1.0 - x, n - k) * (comb(n, k) * (n+1))
        y_rescaled = y * y_scale
        ax.plot(x_rescaled, y_rescaled)
    ax.set_xlim(rescale_x(0), rescale_x(1))
    ax.set_xticks(rescale_x(xticks))
    ax.set_xticklabels(['%0.1f' % t for t in xticks])
    ax.set_ylim(0)

figsize = (8, 4.5)
dpi = 150

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid(True)

x = numpy.linspace(0, 1, 1001)
plot_beta_arcsine(ax, x, xticks, n, step)

ax.set_ylim(0)
ax.set_yticks([])

plt.savefig('output/beta_arcsine.png', dpi = dpi, bbox_inches = "tight")

x = numpy.linspace(0.01, 0.99, 1001)
xticks = numpy.arange(0.1, 0.9001, 0.1)

def plot_beta_logit(ax, x, xticks, n, step=1):
    def rescale_x(x):
        return numpy.log(x / (1.0 - x))
    x_rescaled = rescale_x(x)
    y_scale = x * (1.0-x)
    for k in range(0, n+1, step):
        y = numpy.power(x, k) * numpy.power(1.0 - x, n - k) * (comb(n, k) * (n+1))
        y_rescaled = y * y_scale
        ax.plot(x_rescaled, y_rescaled)
    ax.set_xlim(rescale_x(x[0]), rescale_x(x[-1]))
    ax.set_xticks(rescale_x(xticks))
    ax.set_xticklabels(['%0.1f' % t for t in xticks])
    ax.set_ylim(0)

figsize = (8, 4.5)
dpi = 150

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid(True)

plot_beta_logit(ax, x, xticks, n, step)

ax.set_ylim(0)
ax.set_yticks([])

plt.savefig('output/beta_logit.png', dpi = dpi, bbox_inches = "tight")
