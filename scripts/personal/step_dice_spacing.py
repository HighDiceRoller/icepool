import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

ideal = 3.0 * numpy.power(10, 0.1 * numpy.arange(0, 11))
actual = numpy.array([3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 16.0, 20.0, 24.0, 30.0])
ratio = actual / ideal
offset = numpy.mean(numpy.log(ratio))

figsize = (8, 1)
dpi = 150

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)

ax.grid(True, axis='x')

for x in actual:
    ax.scatter(numpy.log(x) - offset, 1.0, s=144, marker='d')
    ax.annotate('d%d' % x, (numpy.log(x) - offset, 2.0), ha='center')

ax.set_ylim(0, 3)
ax.set_xlabel('Step dice vs. decibels')
ax.set_xticks(numpy.log(ideal))
ax.set_xticklabels([])
ax.set_yticks([])
ax.set_yticklabels([])

plt.savefig('output/step_dice_decibels.png', dpi = dpi, bbox_inches = "tight")
