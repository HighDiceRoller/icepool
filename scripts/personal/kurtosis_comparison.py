import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.stats

figsize = (8, 4.5)
dpi = 120

half_width = 4

# standard deviation

x = numpy.arange(-half_width, half_width + 1e-6, 1e-3)
gaussian = numpy.exp(-0.5*x*x) / numpy.sqrt(2 * numpy.pi)

uniform = (numpy.abs(x) < numpy.sqrt(3)) / numpy.sqrt(12)

logistic_param = numpy.sqrt(3) / numpy.pi
logistic_numerator = numpy.exp(-x / logistic_param) 
logistic = logistic_numerator / (logistic_param * numpy.square(1 + logistic_numerator))

laplace_param = numpy.sqrt(0.5)
laplace = numpy.exp(-numpy.abs(x) / laplace_param) / (2.0 * laplace_param)

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

plt.savefig('output/kurtosis_sd_pmf.png', dpi = dpi, bbox_inches = "tight")

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

plt.savefig('output/kurtosis_mad_pmf.png', dpi = dpi, bbox_inches = "tight")

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

ax.set_xlabel('Result (inverse of density at mode)')
ax.set_ylabel('Chance (%)')
ax.set_xlim(left=-half_width, right=half_width)
ax.set_xticks(numpy.arange(-half_width, half_width+1e-6, 0.5))
ax.set_ylim(bottom=0, top=120)

legend = ['Uniform', 'Gaussian', 'Logistic', 'Laplace']
ax.legend(legend)

plt.savefig('output/kurtosis_mode_pmf.png', dpi = dpi, bbox_inches = "tight")
