import pmf
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

def calc_ehp(dist):
    return 50.0 / dist.normalize().ccdf()

half_life_3 = pmf.geometric(1000, half_life=3).normalize()

half_life_3_sum2 = (half_life_3 + half_life_3).normalize()

explode_d10 = (pmf.xdy(1, 10).explode(3) - 1).normalize()
laplace_3 = (half_life_3 - half_life_3).normalize()
laplace_3_d10 = (pmf.xdy(1, 10).explode(3) - pmf.xdy(1, 10).explode(3)).normalize()
laplace_3_opposed = (laplace_3 - laplace_3).normalize()

half_life_5 = pmf.geometric(1000, half_life=5).normalize()
laplace_5 = (half_life_5 - half_life_5).normalize()

big8 = pmf.PMF.from_faces([0, 0, 0, 0, 1, 1, 2, 3]).normalize().explode(3)
big8_geo3 = (big8 * 3 + pmf.xdy(1, 3) - 1).normalize()
big8_laplace3 = big8_geo3 - big8_geo3

big8_geo5 = (big8 * 5 + pmf.xdy(1, 5) - 1).normalize()
big8_laplace5 = big8_geo5 - big8_geo5
big8_laplace5s_faces = numpy.concatenate((-numpy.flip(big8_geo5.faces()) - 0.5, big8_geo5.faces() + 0.5))
big8_laplace5s_dist = numpy.concatenate((numpy.flip(big8_geo5.data), big8_geo5.data)) * 0.5
laplace5s_faces = numpy.concatenate((-numpy.flip(half_life_5.faces()) - 0.5, half_life_5.faces() + 0.5))
laplace5s_dist = numpy.concatenate((numpy.flip(half_life_5.data), half_life_5.data)) * 0.5

explode_d12_10plus = pmf.PMF.from_faces([1,2,3,4,5,6,7,8,9,10,10,10]).normalize().explode(3)
laplace_d12_10plus_random_ties = (explode_d12_10plus - explode_d12_10plus + pmf.PMF.from_faces([-1, 0])).normalize()

figsize = (8, 4.5)
dpi = 120

# geometric

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Face')
ax.set_ylabel('Probability (%)')
ax.grid()

legend = []

ax.plot(half_life_3.faces(), 100.0 * half_life_3.data)
legend.append('ideal geometric, half-life = 3')

ax.set_xlim(left = -1, right = 20)
ax.set_ylim(bottom = 0)
ax.set_xticks(numpy.arange(-1, 21))

ax.legend(legend, loc = 'upper right')
plt.savefig('geo_half_life_3.png', dpi = dpi, bbox_inches = "tight")

# opposed

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Face')
ax.set_ylabel('Probability (%)')
ax.grid()

legend = []

ax.plot(laplace_3.faces(), 100.0 * laplace_3.data)
legend.append('ideal Laplace, half-life = 3')

ax.plot(laplace_3_d10.faces(), 100.0 * laplace_3_d10.data)
legend.append('d10! - d10!')

ax.plot(big8_laplace3.faces(), 100.0 * big8_laplace3.data)
legend.append('opposed big-small, half-life = 3')

ax.plot(explode_d10.faces(), 50.0 * explode_d10.data)
legend.append('non-opposed d10!')

ax.set_xlim(left = -20, right = 20)
ax.set_ylim(bottom = 0)
ax.set_xticks(numpy.arange(-20, 21, 2))

ax.legend(legend, loc = 'upper left')
plt.savefig('laplace_half_life_3.png', dpi = dpi, bbox_inches = "tight")

# ehp

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('EHP (%)')
ax.grid()

legend = []

ax.plot(laplace_3.faces(), calc_ehp(laplace_3))
legend.append('ideal Laplace, half-life = 3')

ax.plot(laplace_3_d10.faces(), calc_ehp(laplace_3_d10))
legend.append('d10! - d10!')

ax.plot(big8_laplace3.faces(), calc_ehp(big8_laplace3))
legend.append('opposed big-small, half-life = 3')

ax.plot(explode_d10.faces() - 4, calc_ehp(explode_d10))
legend.append('non-opposed d10! - 4')

#ax.plot(half_life_3.faces() - 2.5, calc_ehp(half_life_3))
#legend.append('geometric - 2.5, half-life = 3')

ax.set_xlim(left = -5, right = 15)
ax.set_ylim(bottom = 0, top = 2000)
ax.set_yticks(numpy.arange(0, 2001, 200))
ax.set_xticks(numpy.arange(-5, 16))

ax.legend(legend, loc = 'upper left')
plt.savefig('laplace_half_life_3_ehp.png', dpi = dpi, bbox_inches = "tight")

# geometric

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Face')
ax.set_ylabel('Probability (%)')
ax.grid()

legend = []

ax.plot(half_life_3.faces(), 100.0 * half_life_3.data)
legend.append('geometric, half-life = 3')

ax.plot(half_life_3_sum2.faces(), 100.0 * half_life_3_sum2.data)
legend.append('two geometric, half-life = 3')

ax.set_xlim(left = -1, right = 20)
ax.set_ylim(bottom = 0)
ax.set_xticks(numpy.arange(-1, 21))

ax.legend(legend, loc = 'upper right')
plt.savefig('geo_half_life_3_two.png', dpi = dpi, bbox_inches = "tight")

# sign

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Face')
ax.set_ylabel('Probability (%)')
ax.grid()

legend = []

ax.plot(laplace5s_faces, 100.0 * laplace5s_dist)
legend.append('ideal Laplace, tiebreak with coin flip, half-life = 5')

#ax.plot(big8_laplace5.faces(), 100.0 * big8_laplace5.data)
#legend.append('opposed big-small, half-life = 5')

ax.plot(big8_laplace5s_faces, 100.0 * big8_laplace5s_dist)
legend.append('random sign geometric, half-life = 5')

ax.plot(laplace_d12_10plus_random_ties.faces() + 0.5, 100.0 * laplace_d12_10plus_random_ties.data)
legend.append('min(d12, 10)! - min(d12, 10)!, tiebreak with coin flip')

ax.set_xlim(left = -20, right = 20)
ax.set_ylim(bottom = 0, top = 9)
ax.set_xticks(numpy.arange(-20, 21, 2))

ax.legend(legend, loc = 'upper left')
plt.savefig('laplace_half_life_5_random_sign.png', dpi = dpi, bbox_inches = "tight")
