import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.stats
import scipy.special

figsize = (8, 4.5)
dpi = 150
left = -20
right = 20

x = numpy.arange(left, right + 1e-6, 1e-3)

kappa = numpy.sqrt(0.5)
scale = 3.0 * kappa / numpy.log(2.0)

pdf = scipy.stats.laplace_asymmetric.pdf(x, kappa=kappa, scale=scale)
cdf = scipy.stats.laplace_asymmetric.cdf(x, kappa=kappa, scale=scale)

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

ax.plot(x, 100.0 * pdf)

ax.set_xlabel('Difference in rolls')
ax.set_ylabel('Chance (%)')
ax.set_xlim(left=left, right=right)
ax.set_ylim(bottom=0)

plt.savefig('output/asymmetric_laplace_pdf.png', dpi = dpi, bbox_inches = "tight")

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

ax.plot(x, 100.0 * (1.0 - cdf))

ax.set_xlabel('Difference in modifiers')
ax.set_ylabel('Chance to hit (%)')
ax.set_xlim(left=left, right=right)
ax.set_yticks(100.0 * numpy.arange(0.0, 6.1, 1.0) / 6.0)
ax.set_ylim(bottom=0, top=100)

plt.savefig('output/asymmetric_laplace_cdf.png', dpi = dpi, bbox_inches = "tight")

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

hi = numpy.zeros_like(x)
hi[x >= 0.0] = numpy.log(2) / 3.0 * 2 * numpy.power(2.0, -x[x >= 0.0] / 3.0) / 3 
hi[x <= 0.0] = numpy.log(2) / 3.0 * 2 * numpy.power(2.0, 2 * x[x <= 0.0] / 3.0) / 3

rev = numpy.zeros_like(x)
rev[x >= 0.0] = numpy.log(2) / 3.0 * 2 * numpy.power(2.0, -2 * x[x >= 0.0] / 3.0) / 3
rev[x <= 0.0] = numpy.log(2) / 3.0 * 2 * numpy.power(2.0, x[x <= 0.0] / 3.0) / 3

lo = numpy.zeros_like(x)
lo[x >= 0.0] = numpy.log(2) / 3.0 * (numpy.power(2.0, -x[x >= 0.0] / 3.0) - numpy.power(2.0, -2 * x[x >= 0.0] / 3.0) * 2 / 3)
lo[x <= 0.0] = numpy.log(2) / 3.0 * numpy.power(2.0, x[x <= 0.0] / 3.0) / 3

ax.plot(x, hi * 100.0)
#ax.plot(x, rev * 100.0)
ax.plot(x, lo * 100.0)

ax.set_xlabel('Difference in rolls')
ax.set_ylabel('Chance to hit (%)')
ax.set_xlim(left=left, right=right)
ax.set_ylim(bottom=0)

plt.savefig('output/asymmetric_laplace_compare_pdf.png', dpi = dpi, bbox_inches = "tight")

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

hi = numpy.zeros_like(x)
hi[x >= 0.0] = 2 * numpy.power(2.0, -x[x >= 0.0] / 3.0) / 3 
hi[x <= 0.0] = 1 - numpy.power(2.0, 2 * x[x <= 0.0] / 3.0) / 3

rev = numpy.zeros_like(x)
rev[x >= 0.0] = numpy.power(2.0, -2 * x[x >= 0.0] / 3.0) / 3
rev[x <= 0.0] = 1 - 2 * numpy.power(2.0, x[x <= 0.0] / 3.0) / 3

lo = numpy.zeros_like(x)
lo[x >= 0.0] = numpy.power(2.0, -x[x >= 0.0] / 3.0) - numpy.power(2.0, -2 * x[x >= 0.0] / 3.0) * 1 / 3 
lo[x <= 0.0] = 1 - numpy.power(2.0, x[x <= 0.0] / 3.0) / 3

ax.plot(x, hi * 100.0)
#ax.plot(x, rev * 100.0)
ax.plot(x, lo * 100.0)

ax.set_xlabel('Difference in modifiers')
ax.set_ylabel('Chance to hit (%)')
ax.set_xlim(left=left, right=right)
ax.set_yticks(100.0 * numpy.arange(0.0, 6.1, 1.0) / 6.0)
ax.set_ylim(bottom=0, top=100)

plt.savefig('output/asymmetric_laplace_compare_cdf.png', dpi = dpi, bbox_inches = "tight")
