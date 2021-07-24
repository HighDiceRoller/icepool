import _context

from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

figsize = (8, 4.5)
dpi = 150

variance_b = 0.0

marker_map = {
    1 : '.',
    2 : 'd',
    3 : '^',
    4 : 's',
    5 : 'p',
    6 : 'h',
    10 : 'X',
}

# die_counts refer to the total dice on both sides.
def plot_opposed_fixed_total(ax, single_die, die_counts, die_name):
    coef = 4.0 * single_die.mean() * single_die.mean() / single_die.variance()
    
    legend = []

    for die_count in die_counts:
        x = []
        cdf = []
        for die_count_a in range(die_count+1):
            die_count_b = die_count - die_count_a
            
            die_bonus_a = numpy.sqrt(numpy.maximum(die_count_a * coef - variance_b, 0.0))
            die_bonus_b = numpy.sqrt(numpy.maximum(die_count_b * coef - variance_b, 0.0))

            opposed = single_die.repeat_and_sum(die_count_a) - single_die.repeat_and_sum(die_count_b)
            p = opposed >= Die.coin()
            x.append(die_bonus_b - die_bonus_a)
            cdf.append(p)
        
        pmf = (numpy.diff(cdf, prepend=0.0) + numpy.diff(cdf, append=1.0)) * 50.0
        marker = marker_map[die_count] if die_count in marker_map else '.'
        ax.plot(x, pmf, marker = marker)
        legend.append('%dd%s' % (die_count, die_name))
    ax.legend(legend, loc = 'upper right')
    ax.set_xlabel('Bonus disparity after conversion to roll-over')
    ax.set_ylabel('"Chance" (%)')
    ax.grid(which = "both")

def plot_opposed_fixed_side(ax, single_die, die_counts, die_name):
    coef = 4.0 * single_die.mean() * single_die.mean() / single_die.variance()
    
    legend = []

    for die_count_a in die_counts:
        x = []
        ccdf = []
        for die_count_b in range(0, 100):
            die_bonus_a = numpy.sqrt(numpy.maximum(die_count_a * coef - variance_b, 0.0))
            die_bonus_b = numpy.sqrt(numpy.maximum(die_count_b * coef - variance_b, 0.0))

            opposed = single_die.repeat_and_sum(die_count_a) - single_die.repeat_and_sum(die_count_b)
            p = opposed >= Die.coin()
            # p = (opposed > 0) / ((opposed > 0) + (opposed < 0))
            x.append(die_bonus_b - die_bonus_a)
            ccdf.append(p)

        #pmf = (numpy.diff(cdf, prepend=0.0) + numpy.diff(cdf, append=1.0)) * 50.0
        pmf = -numpy.diff(ccdf, prepend=1.0) * 100.0
        marker = marker_map[die_count_a] if die_count_a in marker_map else '.'
        ax.plot(x + 0.5 * numpy.diff(x, append=x[-1]), pmf, marker = marker)
        legend.append('%dd%s' % (die_count_a, die_name))
    ax.legend(legend, loc = 'upper right')
    ax.set_xlabel('Bonus disparity after conversion to roll-over')
    ax.set_ylabel('"Chance" (%)')
    ax.grid(which = "both")
    ax.set_ylim(bottom = 0)

die_counts_simple = [1, 2, 3, 4, 5, 6, 8, 10, 15, 20]
die_counts_standard = [1, 2, 3, 4, 5, 6]

left = -4
right = 4

# 3+ on d6

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

plot_opposed_fixed_side(ax, Die.coin(2/3), die_counts_simple, '(d6>=3)')

ax.set_xlim(left = left, right = right)
plt.savefig('output/success_pool_opposed_3plus.png', dpi = dpi, bbox_inches = "tight")

# coin

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

plot_opposed_fixed_side(ax, Die.coin(), die_counts_simple, '(d6>=4)')

ax.set_xlim(left = left, right = right)
plt.savefig('output/success_pool_opposed_4plus.png', dpi = dpi, bbox_inches = "tight")

# 5+ on d6

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

plot_opposed_fixed_side(ax, Die.coin(1/3), die_counts_simple, '(d6>=5)')

ax.set_xlim(left = left, right = right)
plt.savefig('output/success_pool_opposed_5plus.png', dpi = dpi, bbox_inches = "tight")

# exalted 2e

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

plot_opposed_fixed_side(ax, Die.mix(*([0]*6 + [1]*3 + [2])), die_counts_simple, 'Exalted2e')

ax.set_xlim(left = left, right = right)
plt.savefig('output/success_pool_opposed_exalted2e.png', dpi = dpi, bbox_inches = "tight")

# coin

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

plot_opposed_fixed_side(ax, Die.d(6), die_counts_simple, '6')

ax.set_xlim(left = left, right = right)
plt.savefig('output/success_pool_opposed_d6.png', dpi = dpi, bbox_inches = "tight")
