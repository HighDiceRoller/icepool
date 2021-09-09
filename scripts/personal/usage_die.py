import _context

from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

figsize = (8, 4.5)
dpi = 150

die_sizes = [4, 6, 8, 10, 12]

def usage_die(sides, tn=2, end_sides=4):
    if sides < end_sides:
        return Die(0)
    return Die.coin(1 - tn / sides).explode(100) + 1 + usage_die(sides - 2, tn, end_sides)

def mean_uses(sides):
    return sum(range(2, sides//2+1))

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

for die_size, color in zip(die_sizes, default_colors):
    die = usage_die(die_size)
    print(die.standard_deviation() / die.mean())
    ax.plot(die.outcomes() / mean_uses(die_size) * 100.0,
            die.pmf() * mean_uses(die_size) * 100.0, color=color)

for die_size, color in zip(die_sizes, default_colors):
    die_count = (die_size//2 - 1)
    constant_chance = mean_uses(die_size) / die_count
    constant_die = Die.coin(1 - 1 / constant_chance).explode(100) + 1
    constant_die = die_count * constant_die
    ax.plot(constant_die.outcomes()/ mean_uses(die_size) * 100.0,
            constant_die.pmf() * mean_uses(die_size) * 100.0,
            color=color, linestyle=':', linewidth=1)
            

ax.legend(['d%d (mean = %d)' % (x, mean_uses(x)) for x in die_sizes])
ax.set_title('Usage die (normalized by mean)')
ax.set_xlim(0, 200)
ax.set_ylim(0)
ax.set_xlabel('Uses (% of mean)')
ax.set_ylabel('Probability density (%)')
plt.savefig('output/usage_die.png', dpi = dpi, bbox_inches = "tight")
