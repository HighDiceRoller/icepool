import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.stats
import scipy.special

figsize = (8, 4.5)
dpi = 150
half_width = 20

x = numpy.arange(-half_width, half_width + 1e-6, 1e-3)

pdf = scipy.stats.laplace_asymmetric.pdf(x, kappa=numpy.sqrt(0.5), scale=3.0)
cdf = scipy.stats.laplace_asymmetric.cdf(x, kappa=numpy.sqrt(0.5), scale=3.0)

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

ax.plot(x, 100.0 * pdf)

ax.set_xlabel('Difference in rolls')
ax.set_ylabel('Chance (%)')
ax.set_xlim(left=-half_width, right=half_width)
ax.set_ylim(bottom=0)

plt.savefig('output/asymmetric_laplace_pdf.png', dpi = dpi, bbox_inches = "tight")

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

ax.plot(x, 100.0 * (1.0 - cdf))

ax.set_xlabel('Difference in modifiers')
ax.set_ylabel('Chance to hit (%)')
ax.set_xlim(left=-half_width, right=half_width)
ax.set_yticks(100.0 * numpy.arange(0.0, 6.1, 1.0) / 6.0)
ax.set_ylim(bottom=0, top=100)

plt.savefig('output/asymmetric_laplace_cdf.png', dpi = dpi, bbox_inches = "tight")
