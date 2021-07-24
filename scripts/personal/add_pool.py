import _context

from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

figsize = (8, 4.5)
dpi = 150
left = -4
right = 4

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

def plot_pmf(ax, single_die, die_counts, die_name):
    print('Single', die_name,
          'Mean:', single_die.mean(),
          'SD:', single_die.standard_deviation(),
          'CV:', single_die.standard_deviation() / single_die.mean(),
          'Var:', single_die.variance())
    coef = 4.0 * single_die.mean() * single_die.mean() / single_die.variance()
    legend = []

    for die_count in die_counts:
        die = single_die.repeat_and_sum(die_count)
        die_bonus = numpy.sqrt(numpy.maximum(die_count * coef - variance_b, 0.0))
        x = []
        y = []
        for outcome, mass in zip(die.outcomes(), die.pmf()):
            if outcome < 0: continue
            outcome_bonus = numpy.sqrt(numpy.maximum(outcome / single_die.mean() * coef - variance_b, 0.0))
            x.append(outcome_bonus - die_bonus)
            y.append(mass * 100.0)
            #if x[-1] >= left: ax.annotate('%d' % outcome, (x[-1], y[-1]), ha='center', va='center', fontsize='small')

        marker = marker_map[die_count] if die_count in marker_map else 'o'
        ax.plot(x, y, marker=marker)
        legend.append('%d%s' % (die_count, die_name))
    ax.legend(legend, loc = 'upper right')
    ax.set_xlabel('Roll-over number needed to hit')
    ax.set_ylabel('Chance (%)')
    ax.grid(which = "both")

def plot_pmf_weg(ax, pip_counts):
    coef = 4.0 * Die.d6.mean() * Die.d6.mean() / Die.d6.variance()
    legend = []

    for pip_count in pip_counts:
        die_count = pip_count // 3
        modifier = pip_count % 3
        die = Die.d6.repeat_and_sum(die_count) + modifier
        die_bonus = numpy.sqrt(numpy.maximum(pip_count / 3.0 * coef - variance_b, 0.0))
        x = []
        y = []
        for outcome, mass in zip(die.outcomes(), die.pmf()):
            if outcome < 0: continue
            outcome_bonus = numpy.sqrt(numpy.maximum(outcome / Die.d6.mean() * coef - variance_b, 0.0))
            x.append(outcome_bonus - die_bonus)
            y.append(mass * 100.0)
            #if x[-1] >= left: ax.annotate('%d' % outcome, (x[-1], y[-1]), ha='center', va='center', fontsize='small')

        marker = marker_map[die_count] if die_count in marker_map else 'o'
        ax.plot(x, y, marker=marker)
        legend.append('%d pips' % (pip_count,))
    ax.legend(legend, loc = 'upper right')
    ax.set_xlabel('Roll-over number needed to hit')
    ax.set_ylabel('Chance (%)')
    ax.grid(which = "both")


die_counts_simple = [1, 2, 3, 4, 5, 6, 8, 10, 15, 20]
die_counts_standard = die_counts_simple

# coin

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

plot_pmf(ax, Die.coin(), die_counts_simple, '(d6>=4)')

ax.set_xlim(left = left, right = right)
ax.set_ylim(bottom = 0)
plt.savefig('output/success_pool_4plus.png', dpi = dpi, bbox_inches = "tight")

# 2 plus on d6

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

plot_pmf(ax, Die.coin(5/6), die_counts_simple, '(d6>=2)')

ax.set_xlim(left = left, right = right)
ax.set_ylim(bottom = 0)
plt.savefig('output/success_pool_2plus.png', dpi = dpi, bbox_inches = "tight")

# 3 plus on d6

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

plot_pmf(ax, Die.coin(2/3), die_counts_simple, '(d6>=3)')

ax.set_xlim(left = left, right = right)
ax.set_ylim(bottom = 0)
plt.savefig('output/success_pool_3plus.png', dpi = dpi, bbox_inches = "tight")

# 5 plus on d6

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

plot_pmf(ax, Die.coin(1/3), die_counts_simple, '(d6>=5)')

ax.set_xlim(left = left, right = right)
ax.set_ylim(bottom = 0)
plt.savefig('output/success_pool_5plus.png', dpi = dpi, bbox_inches = "tight")

# 6 plus on d6

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

plot_pmf(ax, Die.coin(1/6), die_counts_simple, '(d6>=6)')

ax.set_xlim(left = left, right = right)
ax.set_ylim(bottom = 0)
plt.savefig('output/success_pool_6plus.png', dpi = dpi, bbox_inches = "tight")

# exalted 2e

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

plot_pmf(ax, Die.mix(*([0]*6 + [1]*3 + [2])), die_counts_simple, 'dExalted2e')

ax.set_xlim(left = left, right = right)
ax.set_ylim(bottom = 0)
plt.savefig('output/success_pool_exalted2e.png', dpi = dpi, bbox_inches = "tight")

# owod

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

plot_pmf(ax, Die.mix(*([-1] + [0]*5 + [1]*4)), die_counts_simple, 'dOWoD')

ax.set_xlim(left = left, right = right)
ax.set_ylim(bottom = 0)
plt.savefig('output/success_pool_owod.png', dpi = dpi, bbox_inches = "tight")

# nwod

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

plot_pmf(ax, Die.mix(*([0]*7 + [1]*3)).explode(100, chance=0.1), die_counts_simple, 'dNWoD')

ax.set_xlim(left = left, right = right)
ax.set_ylim(bottom = 0)
plt.savefig('output/success_pool_nwod.png', dpi = dpi, bbox_inches = "tight")

# d6

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

plot_pmf(ax, Die.d(6), die_counts_standard, 'd6')

ax.set_xlim(left = left, right = right)
ax.set_ylim(bottom = 0)
plt.savefig('output/success_pool_d6.png', dpi = dpi, bbox_inches = "tight")

# half-life

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

plot_pmf(ax, Die.d(3,2)-3, die_counts_standard, '(3d2-3)')

ax.set_xlim(left = left, right = right)
ax.set_ylim(bottom = 0)
plt.savefig('output/success_pool_3c.png', dpi = dpi, bbox_inches = "tight")

# weg

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

plot_pmf_weg(ax, [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])

ax.set_xlim(left = left, right = right)
ax.set_ylim(bottom = 0)
plt.savefig('output/success_pool_weg.png', dpi = dpi, bbox_inches = "tight")
