import pmf
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

x = [4, 5, 6, 8, 10, 12, 16, 20, 24]
factor = 2

y_low = []
y_high = []

y_low_explode = []
y_high_explode = []

for die_size in x:
    die = pmf.xdy(1, die_size).normalize()
    double_die = pmf.xdy(1, int(die_size * factor)).normalize()
    y_low.append(die > double_die)
    y_high.append(die >= double_die)

    die_explode = die.explode(3)
    double_die_explode = double_die.explode(3)
    y_low_explode.append(die_explode > double_die_explode)
    y_high_explode.append(die_explode >= double_die_explode)

print(y_low)
print(y_high)
print(y_low_explode)
print(y_high_explode)

figsize = (8, 4.5)
dpi = 120

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

legend = ['Ties go to underdog',
          'Ties broken by coin flip',
          'Ties go to overdog',]

ax.semilogx(x, y_high_explode, marker='v', color='blue')
ax.semilogx(x, 0.5 * (numpy.array(y_high_explode) + numpy.array(y_low_explode)), color='green')
ax.semilogx(x, y_low_explode, marker='^', color='red')


ax.legend(legend, loc = 'lower right')

ax.set_ylim(bottom=0)
ax.set_xticks(x)
ax.set_xticklabels('d%d\nvs.\nd%d' % (die_size, die_size * factor) for die_size in x)
ax.set_yticks(numpy.arange(0, 0.41, 0.05))
ax.set_xlabel('Die size')
ax.set_ylabel('Chance underdog wins')
ax.grid()

plt.savefig('output/step_dice_vs_double.png', dpi = dpi, bbox_inches = "tight")
