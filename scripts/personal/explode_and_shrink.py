import _context

from icepool import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

die_sizes = [4, 6, 8, 10, 12]
colors = ['red', 'darkorange', 'green', 'blue', 'purple']

xticks = numpy.arange(0, 26, 5)

figsize = (16, 9)
dpi = 120

def explode_and_shrink(die_size):
    result = Die.d(die_size)
    if die_size <= 4: return result
    else:
        return result.relabel_outcomes({die_size : explode_and_shrink(die_size - 2) + die_size})

def compare(exploding_kwargs={}, shrinking_kwargs={}):
    fig = plt.figure(figsize=figsize)
    ax = plt.subplot(111)

    ax.set_xlabel('Target number')
    ax.set_ylabel('Chance of hitting')
    ax.grid(which = 'both')
    plt.minorticks_on()

    legend = []

    for die_size, color in zip(die_sizes, colors):
        exploding = Die.d(die_size).explode(100)
        shrinking = explode_and_shrink(die_size)
        print(shrinking)
        ax.semilogy(exploding.outcomes(), exploding.sf(), color=color, **exploding_kwargs)
        ax.semilogy(shrinking.outcomes(append=True), shrinking.sf(inclusive='both'), color=color, **shrinking_kwargs)
        legend.append('d%d exploding' % die_size)
        legend.append('d%d cascading' % die_size)

    ax.set_xticks(xticks)
    ax.set_xlim(left=0, right=25)
    ax.set_ylim(top=1, bottom=1e-3)

    ax.legend(legend, loc = 'lower left')

compare(exploding_kwargs = {'linestyle' : '--', 'alpha' : 0.25})
plt.savefig('output/shrink_vs_explode.png', dpi = dpi, bbox_inches = "tight")

compare(shrinking_kwargs = {'linestyle' : '--', 'alpha' : 0.25})
plt.savefig('output/explode_vs_shrink.png', dpi = dpi, bbox_inches = "tight")
