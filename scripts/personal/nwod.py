import _context

from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

nwod = Die.mix([0]*7 + [1]*3).explode(6, chance=0.1)
