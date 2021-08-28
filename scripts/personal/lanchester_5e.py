import _context

import numpy
import scipy.optimize
import hdroller.optimize

import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

crs = numpy.arange(1, 21)

xp_by_cr = [
    200,
    450,
    700,
    1100,
    1800,
    2300,
    2900,
    3900,
    5000,
    5900,
    7200,
    8400,
    10000,
    11500,
    13000,
    15000,
    18000,
    20000,
    22000,
    25000,
]

figsize = (8, 4.5)
dpi = 150

def power_offset(x, scale, power, offset):
    return scale * numpy.power(x + offset, power)

def log_power_offset(x, scale, power, offset):
    return numpy.log(power_offset(x, scale, power, offset))

[pscale, ppower, poffset], pcov = scipy.optimize.curve_fit(
    log_power_offset,
    crs,
    numpy.log(xp_by_cr),
    p0 = [1.0, 1.0, 0.0],
    bounds = (
        [0.0, 0.0, -numpy.inf],
        [numpy.inf, numpy.inf, numpy.inf],
        )
    )

print(pscale, ppower, poffset)

pscale, ppower, poffset = 50, 2.0, 1.0

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

ax.semilogy(crs, xp_by_cr)
ax.semilogy(crs, power_offset(crs, pscale, ppower, poffset))

ax.set_xlabel('CR')
ax.set_ylabel('XP')
ax.set_xticks([1, 5, 10, 15, 20])
ax.set_xticks(numpy.arange(1, 21), minor=True)
ax.set_xlim(1, 20)

ax.legend(['XP', '%0.1f * (CR + %0.1f)^%0.1f' % (pscale, poffset, ppower)])

plt.savefig('output/dnd5e_xp_power_fit.png', dpi = dpi, bbox_inches = "tight")

