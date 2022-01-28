import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.misc
import scipy.stats
import scipy.special

import _context
from hdroller import Die

db = 0.1 * numpy.log(10)

figsize = (8, 4.5)
dpi = 150
left = -10
right = 0

x = numpy.arange(left, right + 1e-6, 1e-3)

def set_ax_pdf(ax):
    ax.grid(True, which='major')
    ax.grid(True, which='minor', alpha=0.25)
    ax.set_xlabel('Difference in steps')
    ax.set_ylabel('Chance (%)')
    ax.set_xticks(numpy.arange(left, right + 1e-6, 5.0))
    ax.set_xticks(numpy.arange(left, right + 1e-6, 1.0), minor=True)
    ax.set_xlim(left=left, right=right)
    ax.set_ylim(bottom=0)

def set_ax_sf(ax):
    ax.grid(True, which='major')
    ax.grid(True, which='minor', alpha=0.25)
    ax.set_xlabel('Difference in steps')
    ax.set_ylabel('Chance to hit (%)')
    ax.set_xticks(numpy.arange(left, right + 1e-6, 5.0))
    ax.set_xticks(numpy.arange(left, right + 1e-6, 1.0), minor=True)
    ax.set_xlim(left=left, right=right)
    ax.set_yticks(numpy.arange(0.0, 100.1, 10.0))
    ax.set_ylim(bottom=0, top=100)

def nv0_fde_keep_highest_sf(x, n, decay_constant=db):
    """
    Fixed-die equivalent for multiple step dice vs. 1.
    """
    return 1.0 - numpy.exp(n * x * db)

def nv0_fde_keep_lowest_sf(x, n, decay_constant=db):
    r = numpy.exp(x * db)
    return numpy.power(1.0 - r, n)

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

hi = 100.0 * nv0_fde_keep_highest_sf(x, 2)
lo = 100.0 * nv0_fde_keep_lowest_sf(x, 2)

ax.fill_between(x, hi, 100.0)
ax.fill_between(x, lo, hi)
ax.fill_between(x, 0.0, lo)

ax.legend(['Miss', 'Weak hit', 'Strong hit'])
set_ax_sf(ax)

plt.savefig('output/step_dice_2v0.png', dpi = dpi, bbox_inches = "tight")

left = 0
right = 10
x = numpy.arange(left, right + 1e-6, 1e-3)

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

hi = 100.0 * (1.0 - nv0_fde_keep_lowest_sf(-x, 2))
lo = 100.0 * (1.0 - nv0_fde_keep_highest_sf(-x, 2)) 

ax.fill_between(x, hi, 100.0)
ax.fill_between(x, lo, hi)
ax.fill_between(x, 0.0, lo)

ax.legend(['Miss', 'Weak hit', 'Strong hit'])
set_ax_sf(ax)

plt.savefig('output/step_dice_2v0_reverse.png', dpi = dpi, bbox_inches = "tight")
