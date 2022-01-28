import _context

import hdroller.countdown
from hdroller import Die
import numpy

def match_func(size, outcome):
    return size * 10 + outcome

die = (Die.d10 - 1).best_set(7, match_func)
print(die)
