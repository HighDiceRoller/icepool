import numpy
import scipy.stats
import matplotlib.pyplot as plt

default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

ns = [2, 3, 4, 5, 6]


# count

figsize = (8, 4.5)
dpi = 150

legend = ['second highest of %d dice' % n for n in ns]

fig = plt.figure(figsize=figsize)
x = numpy.arange(0, 1+1e-6, 1e-3)
ax = plt.subplot(111)
ax.grid()

for n in ns:
    y = n * (n - 1) * numpy.power(x, n - 2) * (1 - x)
    ax.plot(100.0 * x, 100.0 * y)

ax.legend(legend)
ax.set_xticks(numpy.arange(0, 201, 25))
ax.set_yticks(numpy.arange(0, 301, 25))
ax.set_xlim(0, 100)
ax.set_ylim(0, 250)
ax.set_xlabel('Outcome (% of range)')
ax.set_ylabel('Probability density (%)')
plt.savefig('output/keep_two_success_pdf.png', dpi = dpi, bbox_inches = "tight")

# sum

figsize = (8, 4.5)
dpi = 150

legend = ['Highest 2 of %d dice' % n for n in ns]

fig = plt.figure(figsize=figsize)
x = numpy.arange(0, 2+1e-6, 1e-3)
ax = plt.subplot(111)
ax.grid()

for n in ns:
    y = numpy.zeros_like(x)
    y[x <= 1.0] = n * numpy.power(0.5 * x[x <= 1.0], n - 1)
    y[x > 1.0] = n * (numpy.power(0.5 * x[x > 1.0], n - 1) - numpy.power(x[x > 1.0] - 1, n - 1))
    ax.plot(100.0 * x, 100.0 * y)

ax.legend(legend)
ax.set_xticks(numpy.arange(0, 201, 25))
ax.set_yticks(numpy.arange(0, 176, 25))
ax.set_xlim(0, 200)
ax.set_ylim(0)
ax.set_xlabel('Outcome (% of single die range)')
ax.set_ylabel('Probability density (%)')
plt.savefig('output/keep_two_pdf.png', dpi = dpi, bbox_inches = "tight")

# sf

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

x = numpy.arange(0, 1+1e-6, 1e-3)
t = 2.0 - x

for n in ns:
    sf = 1.0 + numpy.power(t-1, n) - 2 * numpy.power(0.5*t, n)
    ax.plot(100 * x, 100 * numpy.sqrt(sf))

ax.legend(legend)
ax.set_xticks(100.0 * numpy.arange(0, 1 + 1e-6, 0.1))
ax.set_yticks(100.0 * numpy.sqrt(numpy.arange(0, 1 + 1e-6, 0.1)))
ax.set_yticklabels(['%d' % x for x in numpy.arange(0, 101, 10)])
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.set_xlabel('Distance from maximum outcome (% of single die range)')
ax.set_ylabel('Chance of hitting (%)')
plt.savefig('output/keep_two_sf.png', dpi = dpi, bbox_inches = "tight")

# keep many expected

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

n = numpy.arange(1, 11)

rs = [1, 2, 3, 4, 5]
legend = ['Keep %d highest' % r for r in rs]

for r in rs:
    ev = r / (n + 1) * (n - (r - 1) / 2)
    ev /= r
    ax.plot(n[r-1:], 100.0 * ev[r-1:])

ax.set_xticks(n)
ax.set_xlim(1, 10)
ax.set_ylim(0, 100)
ax.legend(legend)
ax.set_xlabel('Number of dice')
ax.set_ylabel('Mean sum of kept dice (% of maximum sum)')
plt.savefig('output/keep_many_ev.png', dpi = dpi, bbox_inches = "tight")

# Number of dice vs. target number (lower)

def compute_q(q0):
    target = numpy.linspace(1e-3, 2 - 1e-3, 1999)
    n = numpy.log(q0 / 2.0) / numpy.log(target / 2.0)
    q = numpy.zeros_like(target)
    q[target <= 1.0] = q0
    q[target > 1.0] = q0 - numpy.power(target[target > 1.0] - 1, n[target > 1.0])
    return target, 1.0 - q

def compute_n(q0):
    n = numpy.arange(2, 10)
    target = 2.0 * numpy.power(q0 / 2.0, 1.0 / n)
    q = numpy.zeros_like(target)
    q[target <= 1.0] = q0
    q[target > 1.0] = q0 - numpy.power(target[target > 1.0] - 1, n[target > 1.0])
    return target, 1.0 - q

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

for q0, color in zip([0.1, 0.25, 0.5, 0.75, 0.9, 0.99], default_colors):
    x, y = compute_q(q0)
    ax.plot(x * 100.0, y * 100.0, color=color)
    x, y = compute_n(q0)
    for i, (a, b) in enumerate(zip(x, y)):
        ax.scatter(a * 100.0, b * 100.0, marker = '$%d$' % (i+2), facecolor=color)

ax.set_xticks(numpy.arange(0, 201, 25))
ax.set_yticks(numpy.arange(0, 101, 25))
ax.set_yticks(numpy.arange(0, 101, 5), minor=True)
ax.set_xlim(0, 200)
ax.set_ylim(0, 100)
ax.set_xlabel('Outcome (% of single die range)')
ax.set_ylabel('Hit chance (%)')
plt.savefig('output/keep_two_lower.png', dpi = dpi, bbox_inches = "tight")

# Exponential approximation

figsize = (8, 4.5)
dpi = 150

fig = plt.figure(figsize=figsize)
x = numpy.arange(0, 2+1e-6, 1e-3)
ax = plt.subplot(111)
ax.grid()

ns = [2, 3, 4, 5, 10, 20]
legend = ['Highest 2 of %d dice' % n for n in ns]

for n, color in zip(ns, default_colors):
    y = numpy.zeros_like(x)
    y[x <= 1.0] = 2 * numpy.power(0.5*x[x <= 1.0], n)
    y[x > 1.0] = 2 * numpy.power(0.5*x[x > 1.0], n) - numpy.power(x[x > 1.0]-1, n)
    ax.plot(100.0 * (2 - x), 100.0 * (1 - y), color=color)

for n, color in zip(ns, default_colors):
    y = numpy.zeros_like(x)
    # approximation
    y = 2 * numpy.exp(-0.5 * n * (2.0 - x)) - numpy.exp(-n * (2.0 - x))
    ax.plot(100.0 * (2 - x), 100.0 * (1 - y), linestyle='--', color=color)

ax.legend(legend, loc='lower right')
ax.set_xticks(numpy.arange(0, 201, 25))
ax.set_yticks(numpy.arange(0, 176, 25))
ax.set_xlim(left=0, right=100)
ax.set_ylim(bottom=0, top=100)
ax.set_xlabel('Distance from maximum result (% of single die range)')
ax.set_ylabel('Hit chance (%)')
plt.savefig('output/keep_two_sf_approx.png', dpi = dpi, bbox_inches = "tight")

# Exponential approximation (log)

figsize = (8, 4.5)
dpi = 150

fig = plt.figure(figsize=figsize)
s = numpy.logspace(-2, 0, num=2000)
ax = plt.subplot(111)
ax.grid()

ns = [2, 3, 4, 5, 10, 20]
legend = ['Highest 2 of %d dice' % n for n in ns]

for n, color in zip(ns, default_colors):
    y = 2 * numpy.power(0.5*(2 - s), n) - numpy.power((2 - s)-1, n)
    ax.loglog(s, (1 - y), color=color)

for n, color in zip(ns, default_colors):
    y = numpy.zeros_like(x)
    # approximation
    y = 2 * numpy.exp(-0.5 * n * s) - numpy.exp(-n * s)
    ax.loglog(s, (1 - y), linestyle='--', color=color)

ax.legend(legend, loc='lower right')
#ax.set_xticks(numpy.arange(0, 201, 25))
#ax.set_yticks(numpy.arange(0, 176, 25))
#ax.set_xlim(left=0, right=100)
#ax.set_ylim(bottom=0, top=100)
ax.set_xlabel('Distance from maximum result')
ax.set_ylabel('Hit chance')
plt.savefig('output/keep_two_sf_approx_log.png', dpi = dpi, bbox_inches = "tight")

# Exponential roll over equivalent

figsize = (8, 4.5)
dpi = 150

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

x = numpy.arange(-5, 10+1e-6, 1e-3)
y = numpy.exp(-x - numpy.exp(-x)) * (numpy.exp(0.5 * numpy.exp(-x)) - 1.0)

ax.semilogy(x, y)
plt.savefig('output/keep_two_roe_pdf.png', dpi = dpi, bbox_inches = "tight")

# Mean sum

figsize = (8, 4.5)
dpi = 150

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

x = numpy.arange(1.0, 4.00001, 0.001)
y = 1 - 0.5 / x

ax.plot(x, 100.0 * y)

ax.set_xlim(1.0, 4.0)
ax.set_yticks(numpy.arange(0, 101, 10))
ax.set_ylim(0, 100)
ax.set_xlabel('(number of dice + 1) / (number of kept dice + 1)')
ax.set_ylabel('Expected sum (% of maximum possible result)')


plt.savefig('output/keep_expected_sum.png', dpi = dpi, bbox_inches = "tight")
