import _context

import numpy
import hdroller
from hdroller import die, pool, PoolEval

class AllSetsEval(PoolEval):
    def initial_state(self, pool):
        return ()

    def next_state(self, prev_state, outcome, count):
        if count >= 2:
            return tuple(sorted(prev_state + (count,), reverse=True))
        else:
            return prev_state

die = hdroller.d12

import cProfile
cProfile.run('AllSetsEval().eval(pool(die, 10))')

for num_dice in range(2, 13):
    result = AllSetsEval().eval(pool(die, num_dice))
    print(result)

import hdroller


# Note that the * operator is not commutative:
# it means "roll the left die, then roll that many of the right die and sum".
# Integers are treated as a die that always rolls that number.
# Therefore:
# 3 * hdroller.d6 means 3d6.
# hdroller.d6 * 3 means roll a d6 and multiply the result by 3.
method1 = 6 * hdroller.d6.keep_highest(num_dice=4, num_keep=3)
method2 = (3 * hdroller.d6).keep_highest(12, 6)
# num_keep defaults to 1.
method3 = 6 * (3 * hdroller.d6).keep_highest(6)
method4 = (6 * (3 * hdroller.d6)).keep_highest(12)

import numpy
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot(method1.outcomes(), numpy.array(method1.pmf()) * 100.0)
ax.plot(method2.outcomes(), numpy.array(method2.pmf()) * 100.0)
ax.plot(method3.outcomes(), numpy.array(method3.pmf()) * 100.0)
ax.plot(method4.outcomes(), numpy.array(method4.pmf()) * 100.0)
ax.set_title('AD&D 1e ability score methods')
ax.legend(['Method I', 'Method II', 'Method III', 'Method IV'])
ax.set_xlabel('Total of ability scores')
ax.set_xlim(50, 100)
ax.set_ylim(0)
ax.grid(True)
plt.show()
