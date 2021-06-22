import _context

from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

figsize = (8, 4.5)
dpi = 120

left = -20
right = 20
x = numpy.arange(left * 2, right * 2+1)
logistic = Die.logistic(-0.5, half_life=3)

plus_d10 = Die.d10.explode(10) + Die.d10
opposed_d10 = plus_d10 - plus_d10 - Die.coin()

plus_d10_exploding = 2 * Die.d10.explode(10)
opposed_d10_exploding = plus_d10_exploding - plus_d10_exploding - Die.coin()

plus_d12 = Die.d10.explode(10) + Die.d12
opposed_d12 = plus_d12 - plus_d12 - Die.coin()

print(logistic.standard_deviation())

legend = [
    'Logistic',
    'Opposed d10! + d10',
    'Opposed d10! + d12',
    'Opposed 2d(d10!)',
]

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Difference in rolls or (difference in Elo) / 40')
ax.set_ylabel('Chance (%)')
ax.grid()

ax.plot(logistic.outcomes() + 0.5, 100.0 * logistic.pmf(), linestyle='--')
ax.plot(opposed_d10.outcomes() + 0.5, 100.0 * opposed_d10.pmf())
ax.plot(opposed_d12.outcomes() + 0.5, 100.0 * opposed_d12.pmf())
ax.plot(opposed_d10_exploding.outcomes() + 0.5, 100.0 * opposed_d10_exploding.pmf())

ax.set_xlim(left=left, right=right)
ax.set_ylim(bottom=0.0)
ax.legend(legend, loc = 'upper right')
plt.savefig('output/elo_pmf.png', dpi = dpi, bbox_inches = "tight")


logistic6 = Die.logistic(-0.5, half_life=6 / numpy.log2(6))

print(logistic6.standard_deviation())

plus_d6 = Die.d6.explode(10) + 2 * Die.d6
opposed_d6 = plus_d6 - plus_d6 - Die.coin()

plus_d6_explode = 2 * Die.d6.explode(10)
opposed_d6_explode = plus_d6_explode - plus_d6_explode - Die.coin()

legend = [
    'Logistic',
    'Opposed d6! + 2d6',
    'Opposed 2d(d6!)',
]

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Difference in rolls or (difference in Elo) / 51.9')
ax.set_ylabel('Chance (%)')
ax.grid()

ax.plot(logistic6.outcomes() + 0.5, 100.0 * logistic6.pmf(), linestyle='--')
ax.plot(opposed_d6.outcomes() + 0.5, 100.0 * opposed_d6.pmf())
ax.plot(opposed_d6_explode.outcomes() + 0.5, 100.0 * opposed_d6_explode.pmf())

ax.set_xlim(left=left, right=right)
ax.set_ylim(bottom=0.0)
ax.legend(legend, loc = 'upper right')
plt.savefig('output/elo_pmf6.png', dpi = dpi, bbox_inches = "tight")


logistic05 = Die.logistic(-0.5, half_life=5 / numpy.log2(6))

print(logistic05.standard_deviation())

plus_d05_explode = 2 * (Die.d6-1).explode(10)
opposed_d05_explode = plus_d05_explode - plus_d05_explode - Die.coin()

legend = [
    'Logistic',
    'Opposed 2d((d6-1)!)',
]

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Difference in rolls or (difference in Elo) / 62.25')
ax.set_ylabel('Chance (%)')
ax.grid()

ax.plot(logistic05.outcomes() + 0.5, 100.0 * logistic05.pmf(), linestyle='--')
ax.plot(opposed_d05_explode.outcomes() + 0.5, 100.0 * opposed_d05_explode.pmf())

ax.set_xlim(left=left, right=right)
ax.set_ylim(bottom=0.0)
ax.legend(legend, loc = 'upper right')
plt.savefig('output/elo_pmf05.png', dpi = dpi, bbox_inches = "tight")

logistic10_5 = Die.logistic(-0.5, half_life=5 / numpy.log2(10))

plus_d10_5_explode = Die.d10.explode(10, outcomes=[5])
opposed_d10_5_explode = plus_d10_5_explode - plus_d10_5_explode - Die.coin()

legend = [
    'Logistic',
    'Opposed d10!5',
]

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Difference in rolls or (difference in Elo) / 80')
ax.set_ylabel('Chance (%)')
ax.grid()

ax.plot(logistic10_5.outcomes() + 0.5, 100.0 * logistic10_5.pmf(), linestyle='--')
ax.plot(opposed_d10_5_explode.outcomes() + 0.5, 100.0 * opposed_d10_5_explode.pmf())

ax.set_xlim(left=left, right=right)
ax.set_ylim(bottom=0.0)
ax.legend(legend, loc = 'upper right')
plt.savefig('output/elo_pmf_d10_5.png', dpi = dpi, bbox_inches = "tight")
