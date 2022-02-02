import _context

import hdroller

class AllSetsEval(hdroller.PoolEval):
    def initial_state(self, pool):
        return ()

    def next_state(self, prev_state, outcome, count):
        if count >= 2:
            return tuple(sorted(prev_state + (count,), reverse=True))
        else:
            return prev_state

    def ndim(self, pool):
        return 1

die = hdroller.d10

for num_dice in range(2, 13):
    result = AllSetsEval().eval(hdroller.pool(die, num_dice))
    print(result)

