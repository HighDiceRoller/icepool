import _context

import hdroller.countdown
import hdroller.die_repeater
from hdroller import Die
import numpy

master_die = Die.d12.relabel({1:0})

die_sizes = [6, 6, 4]
keep_mask = [False] * (len(die_sizes) - 2) + [True, True]

die = master_die.keep(len(die_sizes), keep_mask, die_sizes)
print(die)

#expected = Die.combine([Die.d(x) for x in die_sizes], func=lambda *outcomes: sum(sorted(outcomes)[-2:]))
#print(expected)

print(die.sf())

import cProfile

#cProfile.run('Die.d10.explode(2).keep_highest(10, 5)')
#cProfile.run('Die.d10.keep_highest(16, 8)')
#cProfile.run('Die.d10.keep_highest(40, 2)')
#cProfile.run('Die.d100.keep_highest(4, 2)')

repeater = hdroller.die_repeater.DieRepeater(Die.d100)

cProfile.run('Die.d100.keep_highest(10, 2)')
cProfile.run('repeater.keep_highest(10, 2)')
cProfile.run('repeater.keep_highest(10, 2)')

