import pmf
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

def plot_ehp(ax, dist, offset=0, **kwargs):
    ehp = 1.0 / dist.normalize().sf()
    ax.semilogy(dist.faces()+offset, ehp, **kwargs)

explode_d10 = pmf.xdy(1, 10).normalize().explode(3)
explode_min_d12_10 = pmf.PMF.from_faces([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10]).normalize().explode(3)
explode_min_d20_19_is_20 = pmf.PMF.from_faces(list(range(1, 19)) + [20, 20]).normalize().explode(3)
explode_min_d20_16plus_is_20 = pmf.PMF.from_faces(list(range(1, 16)) + [20] * 5).normalize().explode(3)

figsize = (8, 4.5)
dpi = 120


# half-life 3

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid(which = "both")

legend = []

plot_ehp(ax, pmf.geometric(3), linestyle='--', color="green")
legend.append('Ideal half-life = 3')

plot_ehp(ax, explode_d10, offset = -3, color="red")
legend.append('d10! - 3')

plot_ehp(ax, explode_d10+pmf.xdy(1, 10), offset = -8.5, color="blue")
legend.append('d10! + d10 - 8.5')

plot_ehp(ax, explode_d10+pmf.xdy(2, 6), offset = -10, color="orange")
legend.append('d10! + 2d6 - 10')

left = -8
right = 14
top = 20

ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1, 2))
ax.set_ylim(bottom = 1, top = top)

ax.legend(legend, loc = 'upper left')
plt.savefig('output/ehp_half_life_3.png', dpi = dpi, bbox_inches = "tight")

# half-life 5

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid(which = "both")

legend = []

plot_ehp(ax, pmf.geometric(5), linestyle='--', color="green")
legend.append('Ideal half-life = 5')

plot_ehp(ax, explode_min_d12_10-2, color="red")
legend.append('min(d12, 10)! - 2')

plot_ehp(ax, explode_min_d12_10+pmf.xdy(1, 10), offset = -7.5, color="blue")
legend.append('min(d12, 10)! + 1d10 - 7.5')

plot_ehp(ax, explode_min_d12_10+pmf.xdy(2, 6), offset = -9, color="orange")
legend.append('min(d12, 10)! + 2d6 - 9')

left = -8
right = 22
top = 20

ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1, 2))
ax.set_ylim(bottom = 1, top = top)

ax.legend(legend, loc = 'upper left')
plt.savefig('output/ehp_half_life_5.png', dpi = dpi, bbox_inches = "tight")

# half-life 6

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid(which = "both")

legend = []

plot_ehp(ax, pmf.geometric(6), linestyle='--', color="green")
legend.append('Ideal half-life = 6')

plot_ehp(ax, explode_min_d20_19_is_20-4, color="red")
legend.append('(d20, 19+ -> 20)! - 4')

plot_ehp(ax, explode_min_d20_19_is_20+pmf.xdy(1, 20)-15, color = "blue")
legend.append('(d20, 19+ -> 20)! + 1d20 - 15')

plot_ehp(ax, explode_min_d20_19_is_20+pmf.xdy(3, 6)-14, color = "orange")
legend.append('(d20, 19+ -> 20)! + 3d6 - 14')

left = -2
right = 26
top = 20

ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1, 2))
ax.set_ylim(bottom = 1, top = top)

ax.legend(legend, loc = 'upper left')
plt.savefig('output/ehp_half_life_6.png', dpi = dpi, bbox_inches = "tight")

# half-life 10

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid(which = "both")

legend = []

plot_ehp(ax, pmf.geometric(10), linestyle='--', color="green")
legend.append('Ideal half-life = 10')

plot_ehp(ax, explode_min_d20_16plus_is_20, color="red")
legend.append('(d20, 16+ -> 20)!')

plot_ehp(ax, explode_min_d20_16plus_is_20+pmf.xdy(1, 20)-10, color = "blue")
legend.append('(d20, 16+ -> 20)! + 1d20 - 10')

plot_ehp(ax, explode_min_d20_16plus_is_20+pmf.xdy(3, 6)-9, color = "orange")
legend.append('(d20, 16+ -> 20)! + 3d6 - 9')

left = -5
right = 40
top = 20

ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1, 5))
ax.set_ylim(bottom = 1, top = top)

ax.legend(legend, loc = 'upper left')
plt.savefig('output/ehp_half_life_10.png', dpi = dpi, bbox_inches = "tight")
