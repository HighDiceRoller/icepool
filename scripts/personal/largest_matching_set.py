import _context
import numpy

from icepool import Die
import icepool.matching_sets
import icepool.tournament

dice = []
for i in range(1, 10):
    dice.append(Die.from_sf(icepool.matching_sets.largest_matching_set(i, 10), 1))

print(icepool.tournament.round_robin_score(*dice))

