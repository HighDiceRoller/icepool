import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.stats
import scipy.special

figsize = (8, 4.5)
dpi = 120

half_width = 4

# standard deviation

x = numpy.arange(-half_width, half_width + 1e-6, 1e-3)
gaussian = numpy.exp(-0.5*x*x) / numpy.sqrt(2 * numpy.pi)
gaussian_param = 1.0

uniform = (numpy.abs(x) < numpy.sqrt(3)) / numpy.sqrt(12)

logistic_param = numpy.sqrt(3) / numpy.pi
logistic_numerator = numpy.exp(-x / logistic_param) 
logistic = logistic_numerator / (logistic_param * numpy.square(1 + logistic_numerator))

laplace_param = numpy.sqrt(0.5)
laplace = numpy.exp(-numpy.abs(x) / laplace_param) / (2.0 * laplace_param)

print('SD max laplace', numpy.max(laplace))
print('SD max gaussian', numpy.max(gaussian))

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

ax.plot(x, 100.0 * uniform)
ax.plot(x, 100.0 * gaussian)
ax.plot(x, 100.0 * logistic)
ax.plot(x, 100.0 * laplace)

ax.set_xlabel('Result (standard deviations)')
ax.set_ylabel('Chance (%)')
ax.set_xlim(left=-half_width, right=half_width)
ax.set_ylim(bottom=0, top=60)

legend = ['Uniform', 'Gaussian', 'Logistic', 'Laplace']
ax.legend(legend)

plt.savefig('output/symmetric_sd_pmf.png', dpi = dpi, bbox_inches = "tight")

# sd ccdf

gaussian = 1.0 - 0.5 * (1.0 + scipy.special.erf(x * gaussian_param / numpy.sqrt(2)))
uniform = numpy.clip(0.5 - x / numpy.sqrt(12), 0.0, 1.0)
laplace = 0.5 - numpy.sign(x) * (0.5 - 0.5 * numpy.exp(-numpy.abs(x / laplace_param)))
logistic = 1 / (1 + numpy.exp(x / logistic_param))

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

ax.plot(x, 100.0 * uniform)
ax.plot(x, 100.0 * gaussian)
ax.plot(x, 100.0 * logistic)
ax.plot(x, 100.0 * laplace)

ax.set_xlabel('Result (median absolute deviations)')
ax.set_ylabel('Chance (%)')
ax.set_xlim(left=-half_width, right=half_width)
ax.set_xticks(numpy.arange(-half_width, half_width+1))
ax.set_ylim(bottom=0, top=100)

legend = ['Uniform', 'Gaussian', 'Logistic', 'Laplace']
ax.legend(legend)

plt.savefig('output/symmetric_sd_ccdf.png', dpi = dpi, bbox_inches = "tight")

# median absolute deviation

half_width = 6

x = numpy.arange(-half_width, half_width + 1e-6, 1e-3)
gaussian_param = scipy.stats.norm.ppf(0.75)
print('gaussian_param:', gaussian_param)
gaussian = numpy.exp(-0.5*numpy.square(x * gaussian_param)) * gaussian_param / numpy.sqrt(2 * numpy.pi)

uniform = (numpy.abs(x) < 2) / 4

logistic_param = 1.0 / numpy.log(3)
logistic_numerator = numpy.exp(-x / logistic_param) 
logistic = logistic_numerator / (logistic_param * numpy.square(1 + logistic_numerator))

laplace_param = 1.0 / numpy.log(2)
laplace = numpy.exp(-numpy.abs(x) / laplace_param) / (2.0 * laplace_param)

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

ax.plot(x, 100.0 * uniform)
ax.plot(x, 100.0 * gaussian)
ax.plot(x, 100.0 * logistic)
ax.plot(x, 100.0 * laplace)

ax.set_xlabel('Result (median absolute deviations)')
ax.set_ylabel('Chance (%)')
ax.set_xlim(left=-half_width, right=half_width)
ax.set_xticks(numpy.arange(-half_width, half_width+1))
ax.set_ylim(bottom=0, top=40)

legend = ['Uniform', 'Gaussian', 'Logistic', 'Laplace']
ax.legend(legend)

plt.savefig('output/symmetric_mad_pmf.png', dpi = dpi, bbox_inches = "tight")

# median absolute deviation ccdf

gaussian = 1.0 - 0.5 * (1.0 + scipy.special.erf(x * gaussian_param / numpy.sqrt(2)))
uniform = numpy.clip(0.5 - 0.25 * x, 0.0, 1.0)
laplace = 0.5 - numpy.sign(x) * (0.5 - 0.5 * numpy.exp(-numpy.abs(x / laplace_param)))
logistic = 1 / (1 + numpy.exp(x / logistic_param))

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

ax.plot(x, 100.0 * uniform)
ax.plot(x, 100.0 * gaussian)
ax.plot(x, 100.0 * logistic)
ax.plot(x, 100.0 * laplace)

ax.set_xlabel('Result (median absolute deviations)')
ax.set_ylabel('Chance (%)')
ax.set_xlim(left=-half_width, right=half_width)
ax.set_xticks(numpy.arange(-half_width, half_width+1))
ax.set_ylim(bottom=0, top=100)

legend = ['Uniform', 'Gaussian', 'Logistic', 'Laplace']
ax.legend(legend)

plt.savefig('output/symmetric_mad_ccdf.png', dpi = dpi, bbox_inches = "tight")

# modal density

half_width = 2.0

x = numpy.arange(-half_width, half_width + 1e-6, 1e-3)
gaussian_param = numpy.sqrt(2 * numpy.pi)
print('modal gaussian_param:', gaussian_param)
gaussian = numpy.exp(-0.5*numpy.square(x * gaussian_param)) * gaussian_param / numpy.sqrt(2 * numpy.pi)

uniform = (numpy.abs(x) < 0.5)

logistic_param = 1.0 / 4.0
logistic_numerator = numpy.exp(-x / logistic_param) 
logistic = logistic_numerator / (logistic_param * numpy.square(1 + logistic_numerator))

laplace_param = 1.0 / 2.0
laplace = numpy.exp(-numpy.abs(x) / laplace_param) / (2.0 * laplace_param)

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

ax.plot(x, 100.0 * uniform)
ax.plot(x, 100.0 * gaussian)
ax.plot(x, 100.0 * logistic)
ax.plot(x, 100.0 * laplace)

ax.set_xlabel('Result (inverse median densities)')
ax.set_ylabel('Chance (%)')
ax.set_xlim(left=-half_width, right=half_width)
ax.set_xticks(numpy.arange(-half_width, half_width+1e-6, 0.5))
ax.set_ylim(bottom=0, top=120)

legend = ['Uniform', 'Gaussian', 'Logistic', 'Laplace']
ax.legend(legend)

plt.savefig('output/symmetric_median_density_pmf.png', dpi = dpi, bbox_inches = "tight")

# median density ccdf

gaussian = 1.0 - 0.5 * (1.0 + scipy.special.erf(x * gaussian_param / numpy.sqrt(2)))
uniform = numpy.clip(0.5 - x, 0.0, 1.0)
laplace = 0.5 - numpy.sign(x) * (0.5 - 0.5 * numpy.exp(-numpy.abs(x / laplace_param)))
logistic = 1 / (1 + numpy.exp(x / logistic_param))

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

ax.plot(x, 100.0 * uniform)
ax.plot(x, 100.0 * gaussian)
ax.plot(x, 100.0 * logistic)
ax.plot(x, 100.0 * laplace)

ax.set_xlabel('Result (median absolute deviations)')
ax.set_ylabel('Chance (%)')
ax.set_xlim(left=-half_width, right=half_width)
ax.set_xticks(numpy.arange(-half_width, half_width+1))
ax.set_ylim(bottom=0, top=100)

legend = ['Uniform', 'Gaussian', 'Logistic', 'Laplace']
ax.legend(legend)

plt.savefig('output/symmetric_median_density_ccdf.png', dpi = dpi, bbox_inches = "tight")

# asymmetric

left = -10.0
right = 20.0
x = numpy.arange(left, right + 1e-6, 1e-3)

geometric_param = 10.0 / numpy.log(10.0)
p = 1.0 - numpy.exp(-1.0 / geometric_param)
geometric = numpy.exp(-x / geometric_param) * p * (x >= 0)

gumbel_param = 10.0 / numpy.log(10.0)
gumbel_offset = 0.0
z = (x - gumbel_offset) / gumbel_param
gumbel = (1.0 / gumbel_param) * numpy.exp(-(z + numpy.exp(-z)))

print('var geometric', (1 - p) / numpy.square(p))
print('var gumbel', numpy.square(numpy.pi * gumbel_param) / 6.0)

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

ax.plot(x, 100.0 * geometric)
ax.plot(x, 100.0 * gumbel)

ax.set_xlabel('Result')
ax.set_ylabel('Chance (%)')
ax.set_xlim(left=left, right=right)
ax.set_ylim(bottom=0)

legend = ['Geometric', 'Gumbel']
ax.legend(legend)

plt.savefig('output/geometric_gumbel.png', dpi = dpi, bbox_inches = "tight")
