import _context

import icepool

class AllSetsEval(icepool.PoolEval):
    def initial_state(self, pool):
        return ()

    def next_state(self, prev_state, outcome, count):
        if count >= 2:
            return tuple(sorted(prev_state + (count,), reverse=True))
        else:
            return prev_state

    def ndim(self, pool):
        return 1

die = icepool.d10

for num_dice in range(2, 13):
    result = AllSetsEval().eval(icepool.Pool(die, num_dice))
    print(result)

