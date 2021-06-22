import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy.special import comb, factorial

def poisson_chance(m):
    result = 0.0
    for k in range(100):
        result += m ** k / factorial(k) * k / (k+m)
    return result * numpy.exp(-m)


def reduction_chance(n):
    result = 0.0
    for k in range(0, n+1):
        p = comb(n, k, exact=True) * (n-1) ** (n - k) / n ** n
        contribution = p * k / (k+1)
        result += contribution
    return result

for i in range(1, 11):
    print(i, poisson_chance(i))

figsize = (16, 4)
dpi = 120

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Expected number of successes (%)')
ax.set_ylabel('Chance of at least one success (%)')
ax.grid()

x = numpy.linspace(0.0, 4.0, 1001)
legend = []
ax.plot(x * 100.0, x * 100.0)
legend.append('Single die')

for n in [2, 3, 6, 10]:
    ax.plot(x * 100.0, (1.0 - numpy.maximum(1.0 - x / n, 0.0) ** n) * 100.0)
    legend.append('%d dice at 1/%d the chance each' % (n, n))
ax.plot(x * 100.0, (1.0 - numpy.exp(-x)) * 100.0)
legend.append('n dice at 1/n the chance each, n → infinity')

ax.set_aspect(1.0)
ax.set_xlim(0.0, 400.0)
ax.set_ylim(0.0, 100.0)

ax.legend(legend)

plt.savefig('output/keep_highest_exchange', dpi = dpi, bbox_inches = "tight")
