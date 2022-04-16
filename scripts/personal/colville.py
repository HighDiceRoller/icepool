import _context

import numpy
from icepool import Die, Pool, SinglePoolScorer

ability = Die.d6.keep_highest(4, 3).reroll([3, 4, 5, 6, 7])
pool = Pool(ability, 6)

class AtLeastTwo15s(SinglePoolScorer):
    def __init__(self, index):
        self.index = index
    
    def initial_state(self, initial_pool):
        return ()

    def next_state(self, outcome, count, prev_state):
        if outcome == 15 and len(prev_state) > 4:
            return None  # reroll everything
        return prev_state + (outcome,) * count

    def score(self, initial_pool, initial_state, final_state):
        return final_state[self.index]

import cProfile
cProfile.run('for i in range(6):\n    AtLeastTwo15s(i).evaluate(pool)')

for i in range(6):
    result = AtLeastTwo15s(i).evaluate(pool)
    print(result)

