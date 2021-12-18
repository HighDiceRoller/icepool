import _context

from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

figsize = (8, 4.5)
dpi = 120

def opposed_keep_highest(x, half_life=3):
    attack_ratio = numpy.power(0.5, x / half_life)
    sf = attack_ratio / (attack_ratio + 1.0)
    return Die.from_sf(sf, x[0])

left = -20
right = 20
x = numpy.arange(left * 2, right * 2+1)
okh = Die.logistic(-0.5, half_life=3)
opposed_simple = Die.d(10).explode(3) - Die.d(10).explode(3) - Die.coin(0.5)

sech = Die.sech(half_life=3)
half_sech_approx = Die.d10.explode(3) + Die.d6
sech_approx = half_sech_approx - half_sech_approx - Die.coin(0.5)

laplace = Die.laplace(half_life=3) - Die.coin(0.5)
exploding = Die.d(10).explode(3) + Die.d(1, 12)
opposed_exploding = exploding - exploding - Die.coin(0.5)
two_exploding = 2 * Die.d(10).explode(3)
opposed_two_exploding = two_exploding - two_exploding - Die.coin(0.5)

legend = [
   'Laplace, half-life = 3',
    'Opposed d10!',
    #'Hyperbolic secant, half-life = 3',
    #'Opposed ?',
    'Logistic, half-life = 3',
    #'Opposed d10! + d12',
    'Opposed d10! + d10!',
]

# sf

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Difference in modifiers')
ax.set_ylabel('Chance to hit (%)')
ax.grid()

ax.plot(laplace.outcomes(), 100.0 * laplace.sf(), linestyle='--')
ax.plot(opposed_simple.outcomes(), 100.0 * opposed_simple.sf())

#ax.plot(sech.outcomes(), 100.0 * sech.sf(), linestyle='--')
#ax.plot(sech_approx.outcomes(), 100.0 * sech_approx.sf())

ax.plot(okh.outcomes(), 100.0 * okh.sf(), linestyle='--')
#ax.plot(opposed_exploding.outcomes(), 100.0 * opposed_exploding.sf())
ax.plot(opposed_two_exploding.outcomes(), 100.0 * opposed_two_exploding.sf())

ax.set_xlim(left=left, right=right)
ax.set_ylim(bottom=0.0,top=100.0)
ax.legend(legend, loc = 'upper right')
plt.savefig('output/laplace_logistic_sf.png', dpi = dpi, bbox_inches = "tight")

# pdf

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Difference in rolls')
ax.set_ylabel('Chance (%)')
ax.grid()

ax.plot(laplace.outcomes() + 0.5, 100.0 * laplace.pmf(), linestyle='--')
ax.plot(opposed_simple.outcomes() + 0.5, 100.0 * opposed_simple.pmf())

#ax.plot(sech.outcomes() + 0.5, 100.0 * sech.pmf(), linestyle='--')
#ax.plot(sech_approx.outcomes() + 0.5, 100.0 * sech_approx.pmf())

ax.plot(okh.outcomes() + 0.5, 100.0 * okh.pmf(), linestyle='--')
#ax.plot(opposed_exploding.outcomes() + 0.5, 100.0 * opposed_exploding.pmf())
ax.plot(opposed_two_exploding.outcomes() + 0.5, 100.0 * opposed_two_exploding.pmf())

ax.set_xlim(left=left, right=right)
ax.set_ylim(bottom=0.0)
ax.legend(legend, loc = 'upper right')
plt.savefig('output/laplace_logistic_pmf.png', dpi = dpi, bbox_inches = "tight")
