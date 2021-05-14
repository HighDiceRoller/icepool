import pmf
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

def calc_ehp(dist):
    return 1.0 / dist.normalize().ccdf()

three_d6 = pmf.xdy(3, 6)

d8 = pmf.xdy(1, 8) + 6
d20 = pmf.xdy(1, 20)
five_d12 = pmf.xdy(5, 12) - 22
explode_d8 = pmf.xdy(1, 8).normalize().explode(3) + 6
explode_d10 = pmf.xdy(1, 10).normalize().explode(3) + 5
explode_d20 = pmf.xdy(1, 20).normalize().explode(3)
geo12 = pmf.PMF([1/12, 11/12], 0).normalize().explode(30) + 3

hl3_d20 = pmf.PMF.from_faces([0, 0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 6, 7, 8, 9, 10, 10]).normalize().explode(3) + 8
hl3 = pmf.geometric(3) + 8

three_d10 = pmf.xdy(3, 10)-12
hl5_d20 = pmf.PMF.from_faces([0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 10]).normalize().explode(3)
hl5 = pmf.geometric(5)

hl_d8 = pmf.PMF.from_faces([0, 0, 0, 0, 1, 1, 2, 3]).normalize().explode(3)
hl5_2dice = hl_d8 * 5 + pmf.xdy(1, 5) - 1
hl5_d8_d12 = hl_d8 * 5 + pmf.PMF.from_faces([1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 5, 5]) - 1

hl8_2dice = hl_d8 * 8 + pmf.xdy(1, 8) + 2
hl8 = pmf.geometric(8) + 3

hl10_2dice = hl_d8 * 10 + pmf.xdy(1, 10) - 1
hl10 = pmf.geometric(10)

figsize = (8, 4.5)
dpi = 120

# d20

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid()

legend = []

ax.plot(d20.faces(), calc_ehp(d20))
legend.append('d20')
ax.set_xticks(d20.faces())

ax.set_xlim(left = 0, right = 21)
ax.set_xticks(numpy.arange(1, 21))
ax.set_ylim(bottom = 0, top = 20)
ax.set_yticks(numpy.arange(0, 21, 2))

ax.legend(legend, loc = 'upper left')
plt.savefig('output/ehp_d20.png', dpi = dpi, bbox_inches = "tight")

# 5d12

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid()

legend = []

ax.plot(d20.faces(), calc_ehp(d20))
legend.append('d20')
#ax.set_xticks(d20.faces())

ax.plot(five_d12.faces(), calc_ehp(five_d12))
legend.append('5d12-22')

left = -10
right = 30
ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1, 2))
ax.set_ylim(bottom = 0, top = 20)
ax.set_yticks(numpy.arange(0, 21, 2))

ax.legend(legend, loc = 'upper left')
plt.savefig('output/ehp_5d12.png', dpi = dpi, bbox_inches = "tight")

# 3d6

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid()

legend = []

ax.plot(d8.faces(), calc_ehp(d8))
legend.append('1d8+6')

ax.plot(three_d6.faces(), calc_ehp(three_d6))
legend.append('3d6')
ax.set_xticks(three_d6.faces())

ax.set_ylim(bottom = 0, top = 20)
ax.set_yticks(numpy.arange(0, 21, 2))

ax.legend(legend, loc = 'upper left')
plt.savefig('output/ehp_3d6.png', dpi = dpi, bbox_inches = "tight")

# explode d8

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid()

legend = []

ax.plot(explode_d8.faces(), calc_ehp(explode_d8))
legend.append('d8! + 6')

ax.plot(three_d6.faces(), calc_ehp(three_d6))
legend.append('3d6')

left = 3
right = 20
ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1))
ax.set_ylim(bottom = 0, top = 20)
ax.set_yticks(numpy.arange(0, 21, 2))

ax.legend(legend, loc = 'upper left')
plt.savefig('output/explode_1d8.png', dpi = dpi, bbox_inches = "tight")

# explode 1d20

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid()

legend = []

ax.plot(explode_d20.faces(), calc_ehp(explode_d20))
legend.append('d20!')
#ax.set_xticks(d20.faces())

ax.plot(five_d12.faces(), calc_ehp(five_d12))
legend.append('5d12-22')

left = -10
right = 35
ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1, 2))
ax.set_ylim(bottom = 0, top = 40)
ax.set_yticks(numpy.arange(0, 41, 5))

ax.legend(legend, loc = 'upper left')
plt.savefig('output/explode_d20.png', dpi = dpi, bbox_inches = "tight")

# half life 3 via d20

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid()

legend = []

ax.plot(explode_d8.faces(), calc_ehp(explode_d8), color="red")
legend.append('d8! + 6')

ax.plot(explode_d10.faces(), calc_ehp(explode_d10), color="orangered")
legend.append('d10! + 5')

ax.plot(three_d6.faces(), calc_ehp(three_d6), color="green")
legend.append('3d6')

ax.plot(hl3_d20.faces(), calc_ehp(hl3_d20), color="blue")
legend.append('[explode d{0, 0, 0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 6, 7, 8, 9, 10, 10}] + 8')

ax.plot(hl3.faces(), calc_ehp(hl3), color="indigo")
legend.append('ideal half-life = 3')

left = 3
right = 20
ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1))
ax.set_ylim(bottom = 0, top = 10)
ax.set_yticks(numpy.arange(0, 11, 1))

ax.legend(legend, loc = 'upper left')
plt.savefig('output/hl3_d20.png', dpi = dpi, bbox_inches = "tight")

# half life 5 via d20

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid()

legend = []

ax.plot(three_d10.faces(), calc_ehp(three_d10))
legend.append('3d10-12')

ax.plot(hl5_d20.faces(), calc_ehp(hl5_d20))
legend.append('explode d{0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 10}')

ax.plot(hl5.faces(), calc_ehp(hl5))
legend.append('ideal half-life = 5')

left = 0
right = 20
ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1))
ax.set_ylim(bottom = 0, top = 10)
ax.set_yticks(numpy.arange(0, 11, 1))

ax.legend(legend, loc = 'upper left')
plt.savefig('output/hl5_d20.png', dpi = dpi, bbox_inches = "tight")

# half life 5 with 2 dice

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid()

legend = []

ax.plot(three_d10.faces(), calc_ehp(three_d10))
legend.append('3d10-12')

ax.plot(hl5_d8_d12.faces(), calc_ehp(hl5_d8_d12))
legend.append('half-life = 5 using big-small d12')

ax.plot(hl5.faces(), calc_ehp(hl5))
legend.append('ideal half-life = 5')

left = 0
right = 20
ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1))
ax.set_ylim(bottom = 0, top = 10)
ax.set_yticks(numpy.arange(0, 11, 1))

ax.legend(legend, loc = 'upper left')
plt.savefig('output/hl5_2dice.png', dpi = dpi, bbox_inches = "tight")

# half life 10 with 2 dice

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid()

legend = []

ax.plot(hl10_2dice.faces(), calc_ehp(hl10_2dice))
legend.append('half-life = 10 using big-small scheme')

ax.plot(hl10.faces(), calc_ehp(hl10))
legend.append('ideal half-life = 10')

left = 0
right = 40
ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1, 2))
ax.set_ylim(bottom = 0, top = 10)
ax.set_yticks(numpy.arange(0, 11, 1))

ax.legend(legend, loc = 'upper left')
plt.savefig('output/hl10_2dice.png', dpi = dpi, bbox_inches = "tight")

# explode 1d20

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP multiplier')
ax.grid()

legend = []

ax.plot(explode_d20.faces(), calc_ehp(explode_d20))
legend.append('d20!')
#ax.set_xticks(d20.faces())

ax.plot(five_d12.faces(), calc_ehp(five_d12))
legend.append('5d12-22')

ax.plot(hl8_2dice.faces(), calc_ehp(hl8_2dice))
legend.append('half-life = 8 using big-small scheme')

ax.plot(hl8.faces(), calc_ehp(hl8))
legend.append('ideal half-life = 8')

left = -10
right = 35
ax.set_xlim(left = left, right = right)
ax.set_xticks(numpy.arange(left, right+1, 2))
ax.set_ylim(bottom = 0, top = 20)
ax.set_yticks(numpy.arange(0, 21, 2))

ax.legend(legend, loc = 'upper left')
plt.savefig('output/hl8_2dice.png', dpi = dpi, bbox_inches = "tight")
