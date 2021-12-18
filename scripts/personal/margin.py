from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

figsize = (8, 4.5)
dpi = 120

def plot_mean_damage(ax, die, x = None, damage=1.0, **kwargs):
    if x is None: x = die.outcomes()
    y = damage * numpy.array([die >= t for t in x])
    ax.plot(x, y, **kwargs)

def plot_mean_damage_mos(ax, die, damage_mult=1.0, x = None, **kwargs):
    if x is None: x = die.outcomes() - 1
    y = damage_mult * numpy.array([die.margin_of_success(t).mean() for t in x])
    ax.plot(x, y, **kwargs)

def geometric_transform(half_life):
    def transform(outcomes):
        result = numpy.zeros_like(outcomes, dtype=float)
        result[outcomes > 0] = numpy.power(2.0, numpy.floor((outcomes[outcomes > 0] - 1.0) / half_life))
        return result
    return transform

def plot_mean_damage_geo_mos(ax, die, x = None, half_life=5, damage_mult=1.0, **kwargs):
    if x is None: x = die.outcomes() - 1
    y = damage_mult * numpy.array([die.margin_of_success(t).mean(geometric_transform(half_life)) for t in x])
    ax.plot(x, y, **kwargs)

def pf2e_transform(outcomes):
    result = numpy.zeros_like(outcomes, dtype=float)
    result[outcomes > 0] = 1.0
    result[outcomes > 10] = 2.0
    return result

def plot_mean_damage_pf2e_mos(ax, die, x = None, damage_mult=1.0, **kwargs):
    if x is None: x = die.outcomes() - 1
    y = damage_mult * numpy.array([die.margin_of_success(t).mean(pf2e_transform) for t in x])
    ax.plot(x, y, **kwargs)

def semilogy_mean_damage(ax, die, x = None, damage=1.0, **kwargs):
    if x is None: x = die.outcomes()
    y = damage * numpy.array([die >= t for t in x])
    ax.semilogy(x, y, **kwargs)

def semilogy_mean_damage_mos(ax, die, damage_mult=1.0, x = None, **kwargs):
    if x is None: x = die.outcomes() - 1
    y = damage_mult * numpy.array([die.margin_of_success(t).mean() for t in x])
    ax.semilogy(x, y, **kwargs)

def semilogy_mean_damage_geo_mos(ax, die, half_life=5, damage_mult=1.0, x = None, **kwargs):
    if x is None: x = die.outcomes() - 1
    y = damage_mult * numpy.array([die.margin_of_success(t).mean(geometric_transform(half_life)) for t in x])
    ax.semilogy(x, y , **kwargs)

def semilogy_mean_damage_pf2e_mos(ax, die, damage_mult=1.0, x = None, **kwargs):
    if x is None: x = die.outcomes() - 1
    y = damage_mult * numpy.array([die.margin_of_success(t).mean(pf2e_transform) for t in x])
    ax.semilogy(x, y , **kwargs)

def print_die_ratio(die):
    for outcome, mass, success_chance in zip(die.outcomes(), die.pmf(), die.sf()):
        mos = die.margin_of_success(outcome-1).mean()
        ratio = success_chance * success_chance / (mass * mos)
        print(outcome, ratio)

#print_die_ratio(Die.d(12))
#print_die_ratio(Die.d(3, 6))
#print_die_ratio(Die.d(3, 10))

# pf2e

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Mean damage')
ax.grid(which = 'both')

legend = []

x = numpy.arange(-35, 20)

semilogy_mean_damage(ax, Die.d(12)+4, x = x, damage = 6.5, linestyle = '--', zorder=2.1)
legend.append('d12+4, damage = 6.5')

semilogy_mean_damage_mos(ax, Die.d(24)-1, damage_mult = 1.0, x = x)
legend.append('d24-2, damage = MoS + 1')

semilogy_mean_damage_pf2e_mos(ax, Die.d(20)+1, damage_mult = 6.5, x = x)
legend.append('d20, damage = 6.5 if hit, double if MoS >= 10')

ax.set_xlim(left=-20, right=20)
ax.set_ylim(bottom=1,top=50)
ax.legend(legend, loc = 'upper right')
plt.savefig('output/mean_damage_mos_pf2e.png', dpi = dpi, bbox_inches = "tight")

# pf2e

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Mean damage')
ax.grid(which = 'both')

legend = []

x = numpy.arange(-35, 20)

semilogy_mean_damage(ax, Die.d(12)+4, x = x, damage = 6.5)
legend.append('d12+4, damage = 6.5')

semilogy_mean_damage_mos(ax, Die.d(24)-1, damage_mult = 1.0, x = x)
legend.append('d24-2, damage = MoS + 1')

semilogy_mean_damage_pf2e_mos(ax, Die.d(20)+1, damage_mult = 6.5, x = x)
legend.append('d20, damage = 6.5 if hit, double if MoS >= 10')

ax.set_xlim(left=-20, right=20)
ax.set_ylim(bottom=1,top=50)
ax.legend(legend, loc = 'upper right')
plt.savefig('output/mean_damage_mos_pf2e.png', dpi = dpi, bbox_inches = "tight")

# pf2e shift

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Mean damage')
ax.grid(which = 'both')

legend = []

x = numpy.arange(-35, 20)

semilogy_mean_damage_mos(ax, Die.d(20)+5, damage_mult = 1.0, x = x)
legend.append('d20+4, damage = MoS + 1')

semilogy_mean_damage_pf2e_mos(ax, Die.d(20)+1, damage_mult = 10, x = x)
legend.append('d20, damage = 10 if hit, double if MoS >= 10')

semilogy_mean_damage(ax, Die.d(20)-3, x = x, damage = 15)
legend.append('d20-3, damage = 15')

ax.set_xlim(left=-20, right=20)
ax.set_ylim(bottom=1,top=40)
ax.legend(legend, loc = 'lower left')
plt.savefig('output/mean_damage_mos_pf2e_shift.png', dpi = dpi, bbox_inches = "tight")

# d12 direct

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Mean damage')
ax.grid(which = 'both')

legend = []

x = numpy.arange(-15, 20)

plot_mean_damage_mos(ax, Die.d(12), x = x)
legend.append('d12, damage = MoS + 1')

plot_mean_damage(ax, Die.d(12), x = x, damage = 2.5)
legend.append('d12, damage = 2.5')


ax.set_xlim(left=-4, right=11)
ax.set_ylim(bottom=0,top=10)
ax.legend(legend, loc = 'upper right')
plt.savefig('output/mean_damage_mos_d12_direct_linear.png', dpi = dpi, bbox_inches = "tight")

# d12 direct

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Mean damage')
ax.grid(which = 'both')

legend = []

x = numpy.arange(-15, 20)

semilogy_mean_damage_mos(ax, Die.d(12), x = x)
legend.append('d12, damage = MoS + 1')

semilogy_mean_damage(ax, Die.d(12), x = x, damage = 2.5)
legend.append('d12, damage = 2.5')

ax.set_xlim(left=-4, right=11)
ax.set_ylim(bottom=0.2,top=10)
ax.legend(legend, loc = 'upper right')
plt.savefig('output/mean_damage_mos_d12_direct.png', dpi = dpi, bbox_inches = "tight")

# d12

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Mean damage')
ax.grid(which = 'both')

legend = []

x = numpy.arange(-15, 20)

semilogy_mean_damage_mos(ax, Die.d(20)-3, x=x)
legend.append('d20 - 4, damage = MoS + 1')

semilogy_mean_damage(ax, Die.d(12), x=x, damage = 5.5)
legend.append('d12, damage = 5.5')

ax.set_xlim(left=-4, right=11)
ax.set_ylim(bottom=0.4,top=20)
ax.legend(legend, loc = 'upper right')
plt.savefig('output/mean_damage_mos_d12.png', dpi = dpi, bbox_inches = "tight")

# 3d6

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Mean damage')
ax.grid(which = 'both')

legend = []

x = numpy.arange(-10, 30)

semilogy_mean_damage_mos(ax, Die.d(3, 10)-5, x=x)
legend.append('3d10 - 6, damage = MoS + 1')

semilogy_mean_damage(ax, Die.d(3, 6), x=x, damage=4.5)
legend.append('3d6, damage = 4.5')

ax.set_xlim(left=0, right=15)
ax.set_ylim(bottom=0.4,top=20)

ax.legend(legend, loc = 'upper right')
plt.savefig('output/mean_damage_mos_3d6.png', dpi = dpi, bbox_inches = "tight")

# 3d6 geometric mos

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Mean damage')
ax.grid(which = 'both')

legend = []

x = numpy.arange(-10, 30)

semilogy_mean_damage_geo_mos(ax, Die.d(3, 10)-5, x=x, damage_mult = 3.25, half_life=5)
legend.append('3d10 - 6, damage = 3.25 × 2^floor(MoS/5)')

semilogy_mean_damage_mos(ax, Die.d(3, 10)-5, x=x)
legend.append('3d10 - 6, damage = MoS + 1')

semilogy_mean_damage(ax, Die.d(3, 6), x=x, damage=4.5)
legend.append('3d6, damage = 4.5')


ax.set_xlim(left=-10, right=15)
ax.set_ylim(bottom=1,top=100)

ax.legend(legend, loc = 'upper right')
plt.savefig('output/mean_damage_mos_3d6_geo_damage.png', dpi = dpi, bbox_inches = "tight")

# 3d6 shift

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Mean damage')
ax.grid(which = 'both')

legend = []

x = numpy.arange(-10, 30)

semilogy_mean_damage_mos(ax, Die.d(3, 6)+4, x=x)
legend.append('3d6 + 3, damage = MoS + 1')

semilogy_mean_damage(ax, Die.d(3, 6), x=x, damage=7.5)
legend.append('3d6, damage = 7.5')

ax.set_xlim(left=0, right=15)
ax.set_ylim(bottom=0.6,top=30)

ax.legend(legend, loc = 'upper right')
plt.savefig('output/mean_damage_mos_3d6_shift.png', dpi = dpi, bbox_inches = "tight")

# 3d6 shift linear

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Mean damage')
ax.grid(which = 'both')

legend = []

x = numpy.arange(-10, 30)

plot_mean_damage_mos(ax, Die.d(3, 10)-5, damage_mult=1.6, x=x)
legend.append('3d10 - 6, damage = 1.6×(MoS + 1)')

plot_mean_damage_mos(ax, Die.d(3, 6)+4, x=x)
legend.append('3d6 + 3, damage = MoS + 1')

plot_mean_damage(ax, Die.d(3, 6), x=x, damage=7.5)
legend.append('3d6, damage = 7.5')

ax.set_xlim(left=0, right=15)
ax.set_ylim(bottom=0,top=15)

ax.legend(legend, loc = 'upper right')
plt.savefig('output/mean_damage_mos_3d6_shift_linear.png', dpi = dpi, bbox_inches = "tight")

# 3d6 shift geometric mos

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Mean damage')
ax.grid(which = 'both')

legend = []

x = numpy.arange(-10, 30)

semilogy_mean_damage_geo_mos(ax, Die.d(3, 6)+4, x=x, damage_mult = 3.5, half_life=5)
legend.append('3d6 + 3, damage = 3.5 × 2^floor(MoS/5)')

semilogy_mean_damage_mos(ax, Die.d(3, 6)+4, x=x)
legend.append('3d6 + 3, damage = MoS + 1')

semilogy_mean_damage(ax, Die.d(3, 6), x=x, damage=7.5)
legend.append('3d6, damage = 7.5')

ax.set_xlim(left=-10, right=15)
ax.set_ylim(bottom=1,top=100)

ax.legend(legend, loc = 'upper right')
plt.savefig('output/mean_damage_mos_3d6_shift_geo_damage.png', dpi = dpi, bbox_inches = "tight")

# 3d6 shift geometric mos linear

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Mean damage')
ax.grid(which = 'both')

legend = []

x = numpy.arange(-10, 30)

plot_mean_damage_geo_mos(ax, Die.d(3, 6)+4, x=x, damage_mult = 3.5, half_life=5)
legend.append('3d6 + 3, damage = 3.5 × 2^floor(MoS/5)')

plot_mean_damage_mos(ax, Die.d(3, 6)+4, x=x)
legend.append('3d6 + 3, damage = MoS + 1')

plot_mean_damage(ax, Die.d(3, 6), x=x, damage=7.5)
legend.append('3d6, damage = 7.5')

ax.set_xlim(left=-10, right=15)
ax.set_ylim(bottom=0,top=80)

ax.legend(legend, loc = 'upper right')
plt.savefig('output/mean_damage_mos_3d6_shift_geo_damage_linear.png', dpi = dpi, bbox_inches = "tight")

# geometric

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Mean damage')
ax.grid(which = 'both')

legend = []

x = numpy.arange(-10, 20)

semilogy_mean_damage_mos(ax, Die.geometric(half_life=3)+1, x=x)
legend.append('half-life = 3, damage = MoS + 1')

semilogy_mean_damage(ax, Die.geometric(half_life=3), x=x, damage=5)
legend.append('half-life = 3, damage = 5')

ax.set_xlim(left=-10, right=20)

ax.legend(legend, loc = 'upper right')
plt.savefig('output/mean_damage_mos_geo.png', dpi = dpi, bbox_inches = "tight")

# exploding

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Mean damage')
ax.grid(which = 'both')

legend = []

x = numpy.arange(0, 31)

semilogy_mean_damage_mos(ax, Die.d(10).explode(3) + 7, damage_mult=4.0, x = x)
legend.append('d10! + 6, damage = 4×(MoS + 1)')

semilogy_mean_damage(ax, Die.d(10).explode(3) + 7, damage=20, x = x, linestyle='--', zorder=2.1)
legend.append('d10! + 6, damage = 20')

semilogy_mean_damage_mos(ax, (Die.d(10).explode(3) + Die.d(10))+1, damage_mult=1.0, x = x)
legend.append('d10! + d10, damage = MoS + 1')

semilogy_mean_damage(ax, Die.d(10).explode(3) + Die.d(10), damage=5, x = x, linestyle='--', zorder=2.1)
legend.append('d10! + d10, damage = 5')

ax.set_xlim(left=0, right=30)
ax.set_ylim(bottom=0.05, top=50)

ax.legend(legend, loc = 'upper right')
plt.savefig('output/mean_damage_mos_explode_d10.png', dpi = dpi, bbox_inches = "tight")

# exploding opposed

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Mean damage')
ax.grid(which = 'both')

legend = []

left = -10
right = 20

x = numpy.arange(left, right+1)

semilogy_mean_damage_mos(ax, (Die.d(10).explode(3) - Die.d(10).explode(3))+1, damage_mult=1.0, x = x)
legend.append('d10! - d10!, damage = MoS + 1')

semilogy_mean_damage(ax, Die.d(10).explode(3) - Die.d(10).explode(3), damage=5, x = x, linestyle='--', zorder=2.1)
legend.append('d10! - d10!, damage = 5')

ax.set_xlim(left=left, right=right)
ax.set_ylim(bottom=0.05, top=50)

ax.legend(legend, loc = 'upper right')
plt.savefig('output/mean_damage_mos_explode_opposed.png', dpi = dpi, bbox_inches = "tight")
