from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

plt.rcParams['xtick.top'] = True
plt.rcParams['ytick.right'] = True
plt.rcParams['xtick.labeltop'] = True
plt.rcParams['ytick.labelright'] = True

point_buy_zero = {
    3 : 0,
    4 : 0,
    5 : 0,
    6 : 0,
    7 : 0,
    8 : 0,
    9 : 1,
    10 : 2,
    11 : 3,
    12 : 4,
    13 : 5,
    14 : 7,
    15 : 9,
    16 : 12,
    17 : 15,
    18 : 19,
}

point_buy_linear = {
    3 : -5,
    4 : -4,
    5 : -3,
    6 : -2,
    7 : -1,
    8 : 0,
    9 : 1,
    10 : 2,
    11 : 3,
    12 : 4,
    13 : 5,
    14 : 7,
    15 : 9,
    16 : 12,
    17 : 15,
    18 : 19,
}

# = chicken dinner
point_buy_quadratic = {
    3 : -9,
    4 : -6,
    5 : -4,
    6 : -2,
    7 : -1,
    8 : 0,
    9 : 1,
    10 : 2,
    11 : 3,
    12 : 4,
    13 : 5,
    14 : 7,
    15 : 9,
    16 : 12,
    17 : 15,
    18 : 19,
}

point_buy_pathfinder = {
    3 : -16,
    4 : -12,
    5 : -9,
    6 : -6,
    7 : -4,
    8 : -2,
    9 : -1,
    10 : 0,
    11 : 1,
    12 : 2,
    13 : 3,
    14 : 5,
    15 : 7,
    16 : 10,
    17 : 13,
    18 : 17,
}

point_buy_skan = {
    3 : -12,
    4 : -10,
    5 : -8,
    6 : -6,
    7 : -4,
    8 : -2,
    9 : -1,
    10 : 0,
    11 : 1,
    12 : 2,
    13 : 3,
    14 : 5,
    15 : 7,
    16 : 10,
    17 : 13,
    18 : 16,
}

point_buy_to_use = point_buy_pathfinder

figsize = (16, 9)
dpi = 120

def plot_extremeness(ax, die, **kwargs):
    extremeness = numpy.minimum(die.cdf(), die.ccdf())
    ax.plot(die.outcomes(), extremeness, **kwargs)

def semilogy_extremeness(ax, die, **kwargs):
    print('%0.3f | %0.3f' % (die.mean(), die.standard_deviation()))
    extremeness = numpy.minimum(die.cdf(), die.ccdf())
    extremeness[extremeness>0.5] = 1.0
    ax.semilogy(die.outcomes(), 1.0 / extremeness, **kwargs)

die_3d6 = Die.d(3, 6)
points_3d6 = die_3d6.relabel(point_buy_to_use).repeat_and_sum(6)

die_3d6r1 = Die.d(3, 5)+3
points_3d6r1 = die_3d6r1.relabel(point_buy_to_use).repeat_and_sum(6)

die_3d6r2 = Die.d(3, 4)+6
points_3d6r2 = die_3d6r2.relabel(point_buy_to_use).repeat_and_sum(6)

die_4d6kh3 = Die.d(6).repeat_and_keep_and_sum(4, keep_highest=3)
points_4d6kh3 = die_4d6kh3.relabel(point_buy_to_use).repeat_and_sum(6)

die_4d6r1kh3 = Die.d(5).repeat_and_keep_and_sum(4, keep_highest=3)+3
points_4d6r1kh3 = die_4d6r1kh3.relabel(point_buy_to_use).repeat_and_sum(6)

die_5d6kh3 = Die.d(6).repeat_and_keep_and_sum(5, keep_highest=3)
points_5d6kh3 = die_5d6kh3.relabel(point_buy_to_use).repeat_and_sum(6)

die_5d6r1kh3 = Die.d(5).repeat_and_keep_and_sum(5, keep_highest=3)+3
points_5d6r1kh3 = die_5d6r1kh3.relabel(point_buy_to_use).repeat_and_sum(6)

die_5d6median3 = Die.d(6).repeat_and_keep_and_sum(5, keep_middle=3)
points_5d6median3 = die_5d6median3.relabel(point_buy_to_use).repeat_and_sum(6)

# 4d6
fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
left = -30
right = 70
yticks_major = [10, 100, 1000]
yticks_minor = list(range(2, 10)) + list(range(20, 100, 10)) + list(range(200, 1000, 100))

ax.set_xlabel('Point-buy total cost')
ax.set_ylabel('Odds of getting result at least as extreme on same side of median')
ax.grid(which='major', alpha=1.0)
ax.grid(which='minor', alpha=0.25)

semilogy_extremeness(ax, points_3d6, color='limegreen')
semilogy_extremeness(ax, points_3d6r1, color='limegreen', linestyle='--')
semilogy_extremeness(ax, points_3d6r2, color='limegreen', linestyle=':')
semilogy_extremeness(ax, points_4d6kh3, color='blue')
semilogy_extremeness(ax, points_4d6r1kh3, color='blue', linestyle='--')
semilogy_extremeness(ax, points_5d6kh3, color='magenta')
#semilogy_extremeness(ax, points_5d6median3, color='magenta', linestyle='-.')
#semilogy_extremeness(ax, points_5d6r1kh3, linestyle='--')


ax.legend([
    '3d6',
    '3d6r1',
    '3d6r1r2',
    '4d6kh3',
    '4d6r1kh3',
    '5d6kh3',
    #'5d6median3',
    ])

ax.set_xticks(numpy.arange(left, right+1, 5))
ax.set_xticks(numpy.arange(left, right+1), minor=True)
ax.set_xlim(left=left, right=right)

ax.set_yticks(yticks_major)
ax.set_yticklabels(list('1 in %d' % x for x in yticks_major))
ax.set_yticks(yticks_minor, minor='true')
ax.set_yticklabels(list(str(x) for x in yticks_minor), minor=True)
ax.set_ylim(bottom=yticks_minor[0], top=yticks_major[-1])
plt.savefig('output/points_pf.png', dpi = dpi, bbox_inches = "tight")
