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
right = 10

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
    

def nv1_fde_keep_highest_pdf(x, n, decay_constant=db):
    """
    Fixed-die equivalent for multiple step dice vs. 1.
    """
    kappa = numpy.sqrt(1.0 / n)
    scale = kappa / decay_constant
    return scipy.stats.laplace_asymmetric.pdf(x, kappa=kappa, scale=scale)

def nv1_fde_keep_highest_sf(x, n, decay_constant=db):
    """
    Fixed-die equivalent for multiple step dice vs. 1.
    """
    kappa = numpy.sqrt(1.0 / n)
    scale = kappa / decay_constant
    return scipy.stats.laplace_asymmetric.sf(x, kappa=kappa, scale=scale)

ns = [1, 2, 4, 10]

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

for n in ns:
    ax.plot(x, 100.0 * nv1_fde_keep_highest_pdf(x, n))

ax.legend(['%dv1' % n for n in ns])
set_ax_pdf(ax)

plt.savefig('output/step_dice_nv1_keep_highest_pdf.png', dpi = dpi, bbox_inches = "tight")

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

for n in ns:
    ax.plot(x, 100.0 * nv1_fde_keep_highest_sf(x, n))

ax.legend(['%dv1' % n for n in ns])
set_ax_sf(ax)

plt.savefig('output/step_dice_nv1_keep_highest_sf.png', dpi = dpi, bbox_inches = "tight")

def nv1_fde_keep_lowest_sf(x, n, decay_constant=db):
    """
    Fixed-die equivalent for multiple step dice vs. 1.
    """
    sf = numpy.zeros_like(x)
    sf[x >= 0.0] = 1 / (n+1) * numpy.exp(-x[x >= 0.0] * decay_constant)
    ratio = numpy.exp(x[x < 0.0] * decay_constant)
    sf[x < 0.0] = 1 / (n+1) / ratio * (1.0 - numpy.power(1 - ratio, n + 1))
    return sf

def nv1_fde_keep_lowest_pdf(x, n, decay_constant=db):
    sf = nv1_fde_keep_lowest_sf(x, n, decay_constant)
    pdf = -numpy.diff(sf) / numpy.diff(x)
    return pdf

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

for n in ns:
    ax.plot(x[1:], 100.0 * nv1_fde_keep_lowest_pdf(x, n))

ax.plot(x, 100.0 * scipy.stats.hypsecant.pdf(x, scale=1.0 / db), linestyle='--')
ax.plot(x, 100.0 * scipy.stats.logistic.pdf(x, scale=1.0 / db), linestyle='--')


ax.legend(['%dv1' % n for n in ns] + ['Hyperbolic secant', 'Logistic'])
set_ax_pdf(ax)

plt.savefig('output/step_dice_nv1_keep_lowest_pdf.png', dpi = dpi, bbox_inches = "tight")

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

for n in ns:
    ax.plot(x, 100.0 * nv1_fde_keep_lowest_sf(x, n))

ax.plot(x, 100.0 * scipy.stats.hypsecant.sf(x, scale=1.0 / db), linestyle='--')
ax.plot(x, 100.0 * scipy.stats.logistic.sf(x, scale=1.0 / db), linestyle='--')

ax.legend(['%dv1' % n for n in ns] + ['Hyperbolic secant', 'Logistic'])
set_ax_sf(ax)

plt.savefig('output/step_dice_nv1_keep_lowest_sf.png', dpi = dpi, bbox_inches = "tight")

# converge to logistic?

xt = numpy.arange(-50, 0, 0.001)

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ns = [100, 1000, 10000]

for n in ns:
    ax.plot(xt[1:], 100.0 * nv1_fde_keep_lowest_pdf(xt, n))

ax.plot(xt, 100.0 * scipy.stats.hypsecant.pdf(xt, scale=1.0 / db), linestyle='--')

plt.savefig('output/step_dice_nv1_keep_lowest_pdf_test.png', dpi = dpi, bbox_inches = "tight")

# 2v1

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

hi = 100.0 * nv1_fde_keep_highest_sf(x, 2)
lo = 100.0 * nv1_fde_keep_lowest_sf(x, 2)

ax.fill_between(x, hi, 100.0)
ax.fill_between(x, lo, hi)
ax.fill_between(x, 0.0, lo)

ax.legend(['Miss', 'Weak hit', 'Strong hit'])
set_ax_sf(ax)

plt.savefig('output/step_dice_2v1.png', dpi = dpi, bbox_inches = "tight")

# 3v1

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

hi = 100.0 * nv1_fde_keep_highest_sf(x, 3)
lo = 100.0 * nv1_fde_keep_lowest_sf(x, 3)

ax.fill_between(x, hi, 100.0)
ax.fill_between(x, lo, hi)
ax.fill_between(x, 0.0, lo)

ax.legend(['Miss', 'Weak hit', 'Strong hit'])
set_ax_sf(ax)

plt.savefig('output/step_dice_3v1.png', dpi = dpi, bbox_inches = "tight")

# 3v1 reverse

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

hi = 100.0 * (1.0 - nv1_fde_keep_lowest_sf(-x, 3))
lo = 100.0 * (1.0 - nv1_fde_keep_highest_sf(-x, 3))

ax.fill_between(x, hi, 100.0)
ax.fill_between(x, lo, hi)
ax.fill_between(x, 0.0, lo)

ax.legend(['Miss', 'Weak hit', 'Strong hit'])
set_ax_sf(ax)

plt.savefig('output/step_dice_3v1_reverse.png', dpi = dpi, bbox_inches = "tight")

# 3v1 verification

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

xd = numpy.arange(left, right+1)

def nv1_fde_keep_highest_sf(x, n, decay_constant=db):
    result = []
    player = Die.d100.keep_highest(n)
    for step in x:
        opposition = int(numpy.exp(step * decay_constant) * 100)
        result.append((player > Die.d(opposition)).mean())
    return numpy.array(result)

def nv1_fde_keep_lowest_sf(x, n, decay_constant=db):
    result = []
    player = Die.d100.keep_lowest(n)
    for step in x:
        opposition = int(numpy.exp(step * decay_constant) * 100)
        result.append((player > Die.d(opposition)).mean())
    return numpy.array(result)

hi = 100.0 * nv1_fde_keep_highest_sf(xd, 3)
lo = 100.0 * nv1_fde_keep_lowest_sf(xd, 3)

ax.fill_between(xd, hi, 100.0)
ax.fill_between(xd, lo, hi)
ax.fill_between(xd, 0.0, lo)

ax.legend(['Miss', 'Weak hit', 'Strong hit'])
set_ax_sf(ax)

plt.savefig('output/step_dice_3v1_verify.png', dpi = dpi, bbox_inches = "tight")

# 2v1 mixed approx
fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

xd = numpy.arange(left, right+1)
    

def mixed_keep_highest_sf(x, ratio, decay_constant=db):
    result = []
    oppo = Die.d100
    for step in x:
        p1 = Die.d(int(round(numpy.exp(-step * decay_constant) * numpy.sqrt(ratio) * 100)))
        p2 = Die.d(int(round(numpy.exp(-step * decay_constant) / numpy.sqrt(ratio) * 100)))
        p = Die.max(p1, p2)
        result.append((p > oppo).mean())
    return numpy.array(result)

def mixed_keep_lowest_sf(x, ratio, decay_constant=db):
    result = []
    oppo = Die.d100
    for step in x:
        p1 = Die.d(int(numpy.exp(-step * decay_constant) * numpy.sqrt(ratio) * 100))
        p2 = Die.d(int(numpy.exp(-step * decay_constant) / numpy.sqrt(ratio) * 100))
        p = Die.min(p1, p2)
        result.append((p > oppo).mean())
    return numpy.array(result)

hi = 100.0 * mixed_keep_highest_sf(xd, 2)
lo = 100.0 * mixed_keep_lowest_sf(xd, 2)

ax.fill_between(xd, hi, 100.0)
ax.fill_between(xd, lo, hi)
ax.fill_between(xd, 0.0, lo)

ax.legend(['Miss', 'Weak hit', 'Strong hit'])
set_ax_sf(ax)

plt.savefig('output/step_dice_2v1_mixed_approx.png', dpi = dpi, bbox_inches = "tight")

# mixed exact?

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

def mixed2_keep_highest(x, ratio, decay_constant=db):
    a = numpy.exp(-x * decay_constant) * numpy.sqrt(ratio)
    b = numpy.exp(-x * decay_constant) / numpy.sqrt(ratio)
    cdf = numpy.zeros_like(x, dtype=float)

    mask = 1.0 >= a
    cdf[mask] = (1/3 * b * b * b + (1-b) * b * b + 1/2 * (a-b) * (a-b) * b + (1-a) * b * (a-b))[mask]

    mask = (1.0 < a) & (1.0 > b)
    cdf[mask] = (1/3 * b * b * b + (1-b) * b * b + 1/2 * (1-b) * (1-b) * b)[mask]

    mask = 1.0 <= b
    cdf[mask] = 1/3

    return 1.0 - (cdf / (a * b))

def mixed2_keep_lowest(x, ratio, decay_constant=db):
    a = numpy.exp(-x * decay_constant) * numpy.sqrt(ratio)
    b = numpy.exp(-x * decay_constant) / numpy.sqrt(ratio)
    sf = numpy.zeros_like(x, dtype=float)

    mask = 1.0 >= a
    sf[mask] = (1/3 * b * b * b + 1/2 * b * b * (a - b))[mask]

    mask = (1.0 < a) & (1.0 > b)
    sf[mask] = (1/3 * b * b * b + 1/2 * (a-b) * b * b)[mask]

    mask = 1.0 <= b
    sf[mask] = (1/3 + 1/2 * (b-1) + 1/2 * (a-1) + (b-1) * (a-1) )[mask]

    return sf / (a * b)

hi = 100.0 * mixed2_keep_highest(x, 2)
lo = 100.0 * mixed2_keep_lowest(x, 2)

ax.fill_between(x, hi, 100.0)
ax.fill_between(x, lo, hi)
ax.fill_between(x, 0.0, lo)

ax.legend(['Miss', 'Weak hit', 'Strong hit'])
set_ax_sf(ax)

plt.savefig('output/step_dice_2v1_mixed_2to1.png', dpi = dpi, bbox_inches = "tight")
