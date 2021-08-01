import numpy
import scipy.stats
import matplotlib.pyplot as plt

figsize = (8, 4.5)
dpi = 150

x = numpy.arange(1, 1000+1, 1)

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

wounds = [1, 2, 3, 4, 5, 10, 20]
wound_chance = 0.4

for w in wounds:
    ax.plot(100 * x / w * wound_chance, 100 / wound_chance * w * scipy.stats.nbinom.pmf(x, w, wound_chance, loc=w))


ax.legend(['%d wounds' % w if w != 1 else '1 wound' for w in wounds])
ax.set_title('Survivability (%d%% wound chance)' % (wound_chance * 100))

ax.set_xlim(0, 200)
ax.set_ylim(bottom=0)
ax.set_xlabel('Number of attacks to destroy (% of mean)')
ax.set_ylabel('Probability density (%)')
plt.savefig('output/nbinom_fixed_chance.png', dpi = dpi, bbox_inches = "tight")



fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

w = 4
wound_chances = [0.2, 0.4, 0.6, 0.8]

x_continuous = numpy.arange(0, 200+1e-6, 0.001)
ax.plot(100 * x_continuous, 100 * scipy.stats.erlang.pdf(x_continuous, w, scale=1/w))

for c in wound_chances:
    ax.plot(100 * x / w * c, 100 / c * w * scipy.stats.nbinom.pmf(x, w, c, loc=w))

ax.legend(['0% wound chance'] + ['%d%% wound chance' % (c * 100) for c in wound_chances])
ax.set_title('Survivability (%d wounds)' % w)

ax.set_xlim(0, 200)
ax.set_ylim(bottom=0)
ax.set_xlabel('Number of attacks to destroy (% of mean)')
ax.set_ylabel('Probability density (%)')
plt.savefig('output/nbinom_fixed_wounds.png', dpi = dpi, bbox_inches = "tight")

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()

a = 10
wounds = [2, 4, 6, 8]
wound_chances = [0.2, 0.4, 0.6, 0.8]

for w, c in zip(wounds, wound_chances):
    ax.plot(100 * x / w * c, 100 / c * w * scipy.stats.nbinom.pmf(x, w, c, loc=w))

ax.legend(['%d wounds, %d%% wound chance' % (w, c * 100) for w, c in zip(wounds, wound_chances)])
ax.set_title('Survivability (%d mean attacks to destroy)' % a)

ax.set_xlim(0, 200)
ax.set_ylim(bottom=0)
ax.set_xlabel('Number of attacks to destroy (% of mean)')
ax.set_ylabel('Probability density (%)')
plt.savefig('output/nbinom_fixed_attacks.png', dpi = dpi, bbox_inches = "tight")
