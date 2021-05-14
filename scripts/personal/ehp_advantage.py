import pmf
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

def plot_pmf(ax, dist, offset=0, yscale=1.0, **kwargs):
    ax.plot(dist.faces()+offset, 100.0 * yscale * dist.data, **kwargs)

def plot_ehp(ax, dist, offset=0, yscale=1.0, **kwargs):
    ehp = 0.5 / dist.normalize().ccdf()
    ax.plot(dist.faces()+offset, yscale * ehp, **kwargs)

def semilogy_ehp(ax, dist, offset=0, yscale=1.0, **kwargs):
    ehp = 0.5 / dist.normalize().ccdf()
    ax.semilogy(dist.faces()+offset, yscale * ehp, **kwargs)

figsize = (8, 4.5)
dpi = 120

# d100

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid()

legend = []

semilogy_ehp(ax, pmf.xdy(1, 100))
legend.append('d100')

semilogy_ehp(ax, pmf.xdy(1, 100).advantage())
legend.append('d100 advantage')

semilogy_ehp(ax, pmf.xdy(1, 100).disadvantage())
legend.append('d100 disadvantage')

left = 0
right = 100
top = 100

ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1, 10))
ax.set_ylim(bottom = 0.5, top = top)

ax.legend(legend, loc = 'upper left')

plt.savefig('output/ehp_d100_advantage.png', dpi = dpi, bbox_inches = "tight")
