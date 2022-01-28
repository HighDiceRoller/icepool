import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.stats
import scipy.special

figsize = (8, 4.5)
dpi = 150

x = numpy.arange(0.0, 1.0 + 1e-9, 1e-5)

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

unmodified = scipy.stats.powerlaw.sf(x, 1.0)
advantage = scipy.stats.powerlaw.sf(x, 2.0)
interpolated = (unmodified + advantage) * 0.5
powerlaw_15 = scipy.stats.powerlaw.sf(x, 1.5)
powerlaw_sqrt2 = scipy.stats.powerlaw.sf(x, numpy.sqrt(2.0))

ax.plot(100.0 * x, 100.0 * unmodified)
ax.plot(100.0 * x, 100.0 * advantage)
ax.plot(100.0 * x, 100.0 * interpolated)
ax.plot(100.0 * x, 100.0 * powerlaw_15)
ax.plot(100.0 * x, 100.0 * powerlaw_sqrt2)

ax.legend([
    'Unmodified',
    'Advantage',
    'Interpolated',
    'Power-law 1.5',
    'Power-law sqrt(2)',
    ])

ax.set_xlabel('Result (%)')
ax.set_ylabel('Chance (%) to roll at least')
ax.set_xlim(left=0, right=100)
ax.set_ylim(bottom=0, top=100)
plt.savefig('output/powerlaw_sf.png', dpi = dpi, bbox_inches = "tight")


ax.set_xlim(left=0, right=10)
ax.set_ylim(bottom=90, top=100)
plt.savefig('output/powerlaw_sf_zoom.png', dpi = dpi, bbox_inches = "tight")
