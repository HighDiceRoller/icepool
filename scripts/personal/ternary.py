import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.misc
import scipy.stats
import scipy.special

db = 0.1 * numpy.log(10)

figsize = (8, 4.5)
dpi = 150

def set_ax_sf(ax):
    ax.grid(True, which='major')
    ax.grid(True, which='minor', alpha=0.25)
    ax.set_ylabel('Chance (%)')
    ax.set_xticks(numpy.arange(numpy.ceil(left / 5.0) * 5.0, right + 1e-6, 5.0))
    ax.set_xticks(numpy.arange(numpy.ceil(left), right + 1e-6, 1.0), minor=True)
    ax.set_xlim(left=left, right=right)
    ax.set_yticks(numpy.arange(0.0, 100.1, 10.0))
    ax.set_ylim(bottom=0, top=100)

def triang(x, scale):
    return scipy.stats.triang.sf(x, c=0.5, loc=-scale, scale=2.0 * scale)

def beta(x, a, b, scale):
    return scipy.stats.beta.sf(x, a, b, loc=-scale, scale=2.0 * scale)

def nv1_fde_keep_highest_sf(x, n, decay_constant=db):
    """
    Fixed-die equivalent for multiple step dice vs. 1.
    """
    kappa = numpy.sqrt(1.0 / n)
    scale = kappa / decay_constant
    return scipy.stats.laplace_asymmetric.sf(x, kappa=kappa, scale=scale)


def nv1_fde_keep_lowest_sf(x, n, decay_constant=db):
    """
    Fixed-die equivalent for multiple step dice vs. 1.
    """
    sf = numpy.zeros_like(x)
    sf[x >= 0.0] = 1 / (n+1) * numpy.exp(-x[x >= 0.0] * decay_constant)
    ratio = numpy.exp(x[x < 0.0] * decay_constant)
    sf[x < 0.0] = 1 / (n+1) / ratio * (1.0 - numpy.power(1 - ratio, n + 1))
    return sf

# pbta (triang + modifier)

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

left = -8
right = 8
x = numpy.arange(left, right + 1e-6, 1e-3)

hi = 100.0 * triang(x-1.5, scale=6.0)
lo = 100.0 * triang(x+1.5, scale=6.0)

ax.fill_between(x, hi, 100.0)
ax.fill_between(x, lo, hi)
ax.fill_between(x, 0.0, lo)

ax.legend(['Miss', 'Weak hit', 'Strong hit'])
set_ax_sf(ax)
ax.set_xlabel('Relative modifier')
ax.set_xticks(numpy.arange(left, right + 1e-6, 4.0))

plt.savefig('output/ternary_triang.png', dpi = dpi, bbox_inches = "tight")

# modiphius (beta)

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

left = -9
right = 29
x = numpy.arange(left, right + 1e-6, 1e-3)

hi = 100.0 * beta(x-10, 2, 1, scale=10.0)
lo = 100.0 * beta(x-10, 1, 2, scale=10.0)

ax.fill_between(x, hi, 100.0)
ax.fill_between(x, lo, hi)
ax.fill_between(x, 0.0, lo)

ax.legend(['Miss', 'Weak hit', 'Strong hit'])
set_ax_sf(ax)
ax.set_xlabel('Target number (roll-over)')

plt.savefig('output/ternary_beta.png', dpi = dpi, bbox_inches = "tight")

# step dice, 3v1

left = -10
right = 10
x = numpy.arange(left, right + 1e-6, 1e-3)

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

hi = 100.0 * nv1_fde_keep_highest_sf(x, 3)
lo = 100.0 * nv1_fde_keep_lowest_sf(x, 3)

ax.fill_between(x, hi, 100.0)
ax.fill_between(x, lo, hi)
ax.fill_between(x, 0.0, lo)

ax.legend(['Miss', 'Weak hit', 'Strong hit'])
set_ax_sf(ax)
ax.set_xlabel('Difference in steps')

plt.savefig('output/ternary_step_dice_3v1.png', dpi = dpi, bbox_inches = "tight")

# keep-single
left = -5
right = 5

x = numpy.arange(left, right + 1e-6, 1e-3)

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

def keep_single_sf(x, chance_per_die):
    sf = numpy.zeros_like(x)
    sf[x < 0] = 1.0 - numpy.power(chance_per_die, 1.0 - x[x < 0])
    sf[x >= 0] = numpy.power(1.0 - chance_per_die, 1.0 + x[x >= 0])
    return sf

hi = 100.0 * keep_single_sf(x, 1/2)
lo = 100.0 * keep_single_sf(x, 5/6)

ax.fill_between(x, hi, 100.0)
ax.fill_between(x, lo, hi)
ax.fill_between(x, 0.0, lo)

ax.legend(['Miss', 'Weak hit', 'Strong hit'])

ax.plot(x, 100.0 * keep_single_sf(x, 1/6), color='white')
ax.plot(x, 100.0 * keep_single_sf(x, 2/6), color='white')
ax.plot(x, 100.0 * keep_single_sf(x, 3/6), color='white')
ax.plot(x, 100.0 * keep_single_sf(x, 4/6), color='white')
ax.plot(x, 100.0 * keep_single_sf(x, 5/6), color='white')

set_ax_sf(ax)
ax.set_xlabel('Number of dice')
ax.set_xticks([-5, 0, 5])
ax.set_xticklabels(['6, keep highest', '1', '6, keep lowest'])

plt.savefig('output/ternary_keep_single.png', dpi = dpi, bbox_inches = "tight")

left = 0
right = 8

x = numpy.arange(left, right + 1e-6, 1e-3)


fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

hi = 100.0 * numpy.power(5/6, x)
lo = 100.0 * numpy.power(1/2, x)

ax.fill_between(x, hi, 100.0)
ax.fill_between(x, lo, hi)
ax.fill_between(x, 0.0, lo)

ax.legend(['Miss', 'Weak hit', 'Strong hit'])
set_ax_sf(ax)
ax.set_xlabel('Number of dice')
ax.set_xticks(numpy.arange(left, right + 1e-6, 4.0))

plt.savefig('output/ternary_keep_single_reverse.png', dpi = dpi, bbox_inches = "tight")
