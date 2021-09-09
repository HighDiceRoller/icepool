import numpy
import scipy.stats
import matplotlib as mpl
import matplotlib.pyplot as plt

sds = numpy.linspace(-4, 4, 8001)
x = numpy.linspace(-40, 40, 80001)

include_miss = True

def plot_cv(ax, pdf):
    print(numpy.sum(pdf))

    y = numpy.zeros_like(sds)
    for i, threshold in enumerate(sds):
        mask = x >= threshold
        total_mass = numpy.sum(pdf[mask])
        if total_mass < 1e-3: continue
        if include_miss:
            miss_x = x - threshold
            miss_x[miss_x <= 0] = 0.0
            mean = numpy.sum(miss_x * pdf) / numpy.sum(pdf)
            sq_mean = numpy.sum(miss_x * miss_x * pdf) / numpy.sum(pdf)
        else:
            truncated_pdf = pdf[mask]
            truncated_x = x[mask] - threshold
            mean = numpy.sum(truncated_x * truncated_pdf) / numpy.sum(truncated_pdf)
            sq_mean = numpy.sum(truncated_x * truncated_x * truncated_pdf) / numpy.sum(truncated_pdf)
        var = sq_mean - mean * mean
        sd = numpy.sqrt(var)
        y[i] = sd / mean
    ax.plot(sds, y)
        

norm_pdf = scipy.stats.norm.pdf(x)
laplace_pdf = scipy.stats.laplace.pdf(x, scale=1.0 / scipy.stats.laplace.std())
logistic_pdf = scipy.stats.logistic.pdf(x, scale=1.0 / scipy.stats.logistic.std())

uniform_scale = 1.0 / scipy.stats.uniform.std()
uniform_pdf = scipy.stats.uniform.pdf(x, loc=-0.5 * uniform_scale, scale=uniform_scale)

figsize = (8, 4.5)
dpi = 150

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

plot_cv(ax, uniform_pdf)
plot_cv(ax, norm_pdf)
plot_cv(ax, logistic_pdf)
plot_cv(ax, laplace_pdf)

ax.legend(['Uniform', 'Normal', 'Logistic', 'Laplace'])

ax.set_xlabel('Threshold (SDs from mean)')
ax.set_ylabel('Coefficient of variation')
ax.set_ylim(0, 10)

plt.savefig('output/truncated_cv.png', dpi=dpi, bbox_inches = "tight")
