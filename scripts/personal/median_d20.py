import _context

from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

threed6 = Die.d6.repeat_and_sum(3)
print(threed6.standard_deviation())

mob_median = Die.d20.keep_index(20, 10)
print(mob_median)
print(mob_median.standard_deviation())

mob_median = Die.d20.keep_index(10, 5)
print(mob_median)
print(mob_median.standard_deviation())
