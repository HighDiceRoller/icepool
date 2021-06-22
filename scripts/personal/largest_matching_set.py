import _context
import numpy

from hdroller import Die
import hdroller.matching_sets
import hdroller.tournament

dice = []
for i in range(1, 10):
    dice.append(Die.from_ccdf(hdroller.matching_sets.largest_matching_set(i, 10), 1))

print(hdroller.tournament.round_robin_score(*dice))

