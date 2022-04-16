import _context

from icepool import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.optimize

plt.rcParams['xtick.top'] = True
plt.rcParams['ytick.right'] = True
plt.rcParams['xtick.labeltop'] = True
plt.rcParams['ytick.labelright'] = True

figsize = (12, 9)
dpi = 100

use_log = False

bottom = 1/3
top = 25

def plot_die(ax, x, die):
    y = []
    for outcome, hit_chance, mass in zip(die.outcomes(), die.sf(), die.pmf()):
        y_coord = -1.0 / numpy.log2(1.0 - hit_chance)
        if mass == 0.0: continue
        if outcome == 1: continue
        #if y_coord < bottom: continue
        if y_coord > top: continue
        y.append(y_coord)
        coord = (x, y_coord)
        ax.annotate(str(outcome) + ' ', coord, ha='right', va='center')
    x = numpy.ones_like(y) * x
    ax.scatter(x, y, marker='<')
    

def find_num_dice(die, tn_die, base_tn, target_miss_chance):
    def f(num_dice):
        if num_dice <= 0.0: return 1.0 - target_miss_chance
        net_tn = tn_die.outcomes() + base_tn
        net_tn_indices = net_tn - die.min_outcome()
        net_tn_indices = numpy.maximum(net_tn_indices, 0)
        single_hit_chances = die.sf()[net_tn_indices]
        miss_chances = numpy.power(1.0 - single_hit_chances, num_dice)
        miss_chance = numpy.dot(tn_die.pmf(), miss_chances)
        return miss_chance - target_miss_chance
    root_results = scipy.optimize.root_scalar(f, x0=1.0, x1=2.0)
    return root_results.root

def plot_die_random_tn(ax, x, die, tn_die):
    y = []
    base_tns = numpy.arange(die.max_outcome() - tn_die.max_outcome() + 1)
        
    for base_tn in base_tns:
        num_dice = find_num_dice(die, tn_die, base_tn, 0.5)
        if num_dice > top: continue
        y.append(num_dice)
        coord = (x, num_dice)
        ax.annotate(' %d+%s' % (base_tn, tn_die.name()), coord, ha='left', va='center')
    x = numpy.ones_like(y) * x
    ax.scatter(x, y, marker='>')

def plot_random_tn_curve(ax, die, tn_die, base_tn, miss_chances):
    x = miss_chances
    y = numpy.array([find_num_dice(die, tn_die, base_tn, miss_chance) for miss_chance in miss_chances])
    y /= -numpy.log2(miss_chances)
    y = numpy.maximum(y, 1.0)
    ax.loglog(1.0 / x, y)

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Dice type')
ax.set_ylabel('T = number of dice needed to halve miss chance')
ax2 = ax.twinx()
ax2.set_ylabel('Number of dice for 50% miss chance')
ax.grid(which='major', alpha=1.0)
ax.grid(which='minor', alpha=0.25)

legend = []

plot_die(ax, len(legend), Die.d6)
legend.append('d6')

plot_die(ax, len(legend), Die.d10)
legend.append('d10')

plot_die(ax, len(legend), Die.d20)
legend.append('d20')

plot_die(ax, len(legend), Die.d6.explode(3))
legend.append('d6!')

plot_die(ax, len(legend), Die.d10.explode(3))
legend.append('d10!')

plot_die(ax, len(legend), Die.d6.min(5).explode(3))
legend.append('min(d6,5)!')

plot_die(ax, len(legend), Die.d12.min(10).explode(3))
legend.append('min(d12,10)!')

#plot_die(ax, len(legend), (Die.d8-1).min(5).explode(3))
#legend.append('min(d8-1,5)!')

plot_die_random_tn(ax, len(legend), Die.d6.explode(3), Die.d6)
legend.append('d6!\nvs.\nTN+d6')

plot_die_random_tn(ax, len(legend), Die.d10.explode(3), Die.d10)
legend.append('d10!\nvs.\nTN+d10')

ax.set_xlim(left=-0.5, right=len(legend))
ax.set_xticks(range(len(legend)))
ax.set_xticklabels(legend)

if use_log:
    ax.set_yscale('log')
    yticks_major = [1, 10]
    yticks_minor = numpy.concatenate(([1/3, 1/2], numpy.arange(1, top+1)))
    yticklabels_minor = []
    for ytick in yticks_minor:
        if ytick < 1.0: yticklabels_minor.append('1/%d' % numpy.round(1.0 / ytick))
        elif ytick < 10 or ytick % 2 == 0: yticklabels_minor.append('%d' % ytick)
        else: yticklabels_minor.append('')
    ax.set_yticks(yticks_major)
    ax.set_yticks(yticks_minor, minor=True)
    ax.set_yticklabels('%d' % t if t >= 1.0 else '%0.1f' % t for t in yticks_major)
    ax.set_yticklabels(yticklabels_minor, minor=True)
    ax.set_ylim(bottom=bottom, top=top)

    ax2.set_yticks(yticks_major)
    ax2.set_yticks(yticks_minor, minor=True)
    ax2.set_yticklabels('%d' % t if t >= 1.0 else '%0.1f' % t for t in yticks_major)
    ax2.set_yticklabels(yticklabels_minor, minor=True)
    ax2.set_ylim(bottom=bottom, top=top)

    plt.savefig('output/keep_highest_comparison.png', dpi = dpi, bbox_inches = "tight")
else:
    yticks_major = numpy.arange(0, top+1, 5)
    yticks_minor = numpy.arange(top+1)
    yticklabels_minor = []
    for ytick in yticks_minor:
        yticklabels_minor.append('%d' % ytick)
    ax.set_yticks(yticks_major)
    ax.set_yticks(yticks_minor, minor=True)
    ax.set_yticklabels('%d' % t for t in yticks_major)
    ax.set_yticklabels(yticklabels_minor, minor=True)
    ax.set_ylim(bottom=0, top=top)

    ax2.set_yticks(yticks_major)
    ax2.set_yticks(yticks_minor, minor=True)
    ax2.set_yticklabels('%d' % t for t in yticks_major)
    ax2.set_yticklabels(yticklabels_minor, minor=True)
    ax2.set_ylim(bottom=0, top=top)

    plt.savefig('output/keep_highest_comparison_linear.png', dpi = dpi, bbox_inches = "tight")

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('1 / miss chance')
ax.set_ylabel('Number of dice / -log2(miss chance)')
ax.grid(which='major', alpha=1.0)
ax.grid(which='minor', alpha=0.25)

miss_chances = numpy.logspace(-20, 0, base=2.0)

for base_tn in range(20):
    plot_random_tn_curve(ax, Die.d6.explode(5), Die.d(2, 6), base_tn, miss_chances)

plt.savefig('output/keep_highest_random_tn.png', dpi = dpi, bbox_inches = "tight")


