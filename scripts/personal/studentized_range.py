import _context

from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

opposed_d6 = Die.d6 - Die.d6

figsize = (8, 4.5)
dpi = 150

half_width = 10
x = numpy.arange(-half_width, half_width + 1e-6, 1e-3)

gaussian_param = 1.0 / opposed_d6.standard_deviation()
print('gaussian_param:', gaussian_param)
gaussian = numpy.exp(-0.5*numpy.square(x * gaussian_param)) * gaussian_param / numpy.sqrt(2 * numpy.pi)

gaussian_tail = numpy.copy(gaussian)
gaussian_tail[numpy.abs(x) < 5.0] = 0.0

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

ax.plot(opposed_d6.outcomes(), 100.0 * opposed_d6.pmf(), marker = '.')
ax.plot(x, gaussian * 100.0)
ax.fill_between(x, 0, gaussian_tail * 100.0, facecolor='red')

ax.legend(['d6 - d6', 'Gaussian', 'Probability outside range'])

ax.set_xlabel('Result')
ax.set_ylabel('Chance (%)')
ax.set_xlim(left=-half_width, right=half_width)
ax.set_ylim(bottom=0)

plt.savefig('output/studentized_range.png', dpi = dpi, bbox_inches = "tight")
