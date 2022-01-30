import _context

import numpy
import hdroller
from hdroller import die, pool, PoolEval

class AllSetsScorer(PoolEval):
    def initial_state(self, pool):
        return ()

    def next_state(self, prev_state, outcome, count):
        if count >= 2:
            return tuple(reversed(sorted(prev_state + (count,))))
        else:
            return prev_state

die = hdroller.d12

import cProfile
cProfile.run('AllSetsScorer().eval(pool(die, 10))')

for num_dice in range(2, 13):
    result = AllSetsScorer().eval(pool(die, num_dice))
    print(result)
