import pmf
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

def plot_pmf(ax, dist, offset=0, yscale=1.0, **kwargs):
    ax.plot(dist.faces()+offset, 100.0 * yscale * dist.data, **kwargs)

def plot_ehp(ax, dist, offset=0, yscale=1.0, **kwargs):
    ehp = 1.0 / dist.normalize().sf()
    ax.plot(dist.faces()+offset, yscale * ehp, **kwargs)

def semilogy_ehp(ax, dist, offset=0, yscale=1.0, **kwargs):
    ehp = 1.0 / dist.normalize().sf()
    ax.semilogy(dist.faces()+offset, yscale * ehp, **kwargs)

explode_d10 = pmf.xdy(1, 10).normalize().explode(3)
explode_min_d12_10 = pmf.PMF.from_faces([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10]).normalize().explode(3)
explode_min_d20_19_is_20 = pmf.PMF.from_faces(list(range(1, 19)) + [20, 20]).normalize().explode(3)
explode_min_d20_16plus_is_20 = pmf.PMF.from_faces(list(range(1, 16)) + [20] * 5).normalize().explode(3)

figsize = (8, 4.5)
dpi = 120


# d100

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid()

legend = []

plot_ehp(ax, pmf.xdy(1, 100))
legend.append('d100')

left = 0
right = 100
top = 10

ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1, 10))
ax.set_ylim(bottom = 0.5, top = top)
ax.set_yticks(numpy.arange(0, top+1))

#ax.legend(legend, loc = 'upper left')
plt.savefig('output/ehp_d100.png', dpi = dpi, bbox_inches = "tight")

# geo 12

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid()

legend = []

plot_ehp(ax, pmf.xdy(1, 20).normalize().explode(3))
legend.append('d20!')
#ax.set_xticks(d20.faces())

plot_ehp(ax, pmf.xdy(5, 12).normalize() - 22)
legend.append('5d12-22')

#plot_ehp(ax, pmf.PMF.from_faces([0] + 9 * [1]).normalize().explode(100) + 4)
#legend.append('[explode d10>1] + 4')

plot_ehp(ax, pmf.PMF.from_faces([0] + 11 * [1]).normalize().explode(100) + 3)
legend.append('[explode d12>1] + 3')

left = -10
right = 35
ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1, 2))
ax.set_ylim(bottom = 0, top = 40)
ax.set_yticks(numpy.arange(0, 41, 5))

ax.legend(legend, loc = 'upper left')
plt.savefig('output/geo.png', dpi = dpi, bbox_inches = "tight")

# geo 12 zoom

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid()

legend = []

plot_ehp(ax, pmf.xdy(1, 20).normalize().explode(3))
legend.append('d20!')
#ax.set_xticks(d20.faces())

plot_ehp(ax, pmf.xdy(5, 12).normalize() - 22)
legend.append('5d12-22')

#plot_ehp(ax, pmf.PMF.from_faces([0] + 9 * [1]).normalize().explode(100) + 4)
#legend.append('[explode d10>1] + 4')

plot_ehp(ax, pmf.PMF.from_faces([0] + 11 * [1]).normalize().explode(100) + 3)
legend.append('[explode d12>1] + 3')

left = 10
right = 30
ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1, 1))
ax.set_ylim(bottom = 0, top = 10)
ax.set_yticks(numpy.arange(0, 11, 1))

ax.legend(legend, loc = 'lower right')
plt.savefig('output/geo_zoom.png', dpi = dpi, bbox_inches = "tight")

# geo 12 semilogy

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid(which = "both")

legend = []

semilogy_ehp(ax, pmf.xdy(1, 20).normalize().explode(3))
legend.append('d20!')
#ax.set_xticks(d20.faces())

semilogy_ehp(ax, pmf.xdy(5, 12).normalize() - 22)
legend.append('5d12-22')

#semilogy_ehp(ax, pmf.PMF.from_faces([0] + 9 * [1]).normalize().explode(100) + 4)
#legend.append('[explode d10>1] + 4')

semilogy_ehp(ax, pmf.PMF.from_faces([0] + 11 * [1]).normalize().explode(100) + 3)
legend.append('[explode d12>1] + 3')

left = -10
right = 35
ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1, 2))
ax.set_ylim(bottom = 1, top = 100)
#ax.set_yticks(numpy.arange(0, 21, 2))

ax.legend(legend, loc = 'upper left')
plt.savefig('output/geo_semilogy.png', dpi = dpi, bbox_inches = "tight")

# laplace pmf

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Face')
ax.set_ylabel('Probability (%)')
ax.grid()

legend = []

plot_pmf(ax, pmf.geometric(3) - pmf.geometric(3), linestyle='--', color = "green")
legend.append('ideal Laplace, half-life = 3')

plot_pmf(ax, explode_d10 - explode_d10, color = "blue")
legend.append('d10! - d10!')

plot_pmf(ax, (explode_d10 + pmf.xdy(2, 6) - explode_d10 - pmf.xdy(2, 6)).normalize(), color = "orange")
legend.append('d10! + 2d6 - (d10! + 2d6)')

plot_pmf(ax, explode_d10, yscale = 0.5, color = "red")
legend.append('non-opposed d10!')

ax.set_xlim(left = -20, right = 20)
ax.set_ylim(bottom = 0)
ax.set_xticks(numpy.arange(-20, 21, 2))

ax.legend(legend, loc = 'upper left')
plt.savefig('output/laplace_half_life_3.png', dpi = dpi, bbox_inches = "tight")

# ehp

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid(which = "both")

legend = []

semilogy_ehp(ax, pmf.geometric(3) - pmf.geometric(3), linestyle='--', color = "green")
legend.append('ideal Laplace, half-life = 3')

semilogy_ehp(ax, explode_d10 - explode_d10, color = "blue")
legend.append('d10! - d10!')

semilogy_ehp(ax, explode_d10 + pmf.xdy(2, 6) - explode_d10 - pmf.xdy(2, 6), color = "orange")
legend.append('d10! + 2d6 - (d10! + 2d6)')

semilogy_ehp(ax, explode_d10, yscale = 2.0, color = "red")
legend.append('non-opposed d10!')

ax.set_xlim(left = -5, right = 15)
ax.set_ylim(bottom = 1, top = 40)
ax.set_xticks(numpy.arange(-5, 16))

ax.legend(legend, loc = 'upper left')
plt.savefig('output/laplace_half_life_3_ehp.png', dpi = dpi, bbox_inches = "tight")

# d20 vs d6 x d6

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid(which = "both")

legend = []

semilogy_ehp(ax, pmf.xdy(1, 20))
legend.append('1d20')

semilogy_ehp(ax, pmf.xdy(1, 6) * pmf.xdy(1, 6))
legend.append('1d6 × 1d6')

ax.set_xlim(left = 0, right = 36)
ax.set_ylim(bottom = 1, top = 40)
ax.set_xticks(numpy.arange(0, 37, 5))

ax.legend(legend, loc = 'upper left')
plt.savefig('output/d6_x_d6.png', dpi = dpi, bbox_inches = "tight")

