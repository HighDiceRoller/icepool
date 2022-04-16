import numpy
from math import comb

def neon_city_overdrive(action, danger):
    """
    action: the number of action dice
    danger: the number of danger dice
    normalize: whether to normalize the result
    
    Returns:
    A vector of outcome -> ways to roll that outcome.
    Outcomes above 6 represent crits.
    """
    
    # number of consumed action, danger dice, outcome -> 
    # number of ways to roll this outcome with all consumed dice >= the last processed face
    # outcomes above 6 represent crits
    state = numpy.zeros((action+1, danger+1, 6+action))
    # initial state: 1 way to have rolled no dice yet
    state[0, 0, 0] = 1.0
    for face in [6, 5, 4, 3, 2, 1]:
        next_state = numpy.zeros_like(state)
        for (consumed_action, consumed_danger, outcome), count in numpy.ndenumerate(state):
            remaining_action = action - consumed_action
            remaining_danger = danger - consumed_danger
            # how many action and danger dice rolled the current face?
            for add_action in range(remaining_action+1):
                for add_danger in range(remaining_danger+1):
                    # how many ways are there for this to happen?
                    factor = comb(remaining_action, add_action) * comb(remaining_danger, add_danger)
                    next_count = factor * count
                    if add_action > add_danger:
                        if face == 6:
                            # add crits
                            next_outcome = 5 + add_action - add_danger
                        else:
                            next_outcome = max(face, outcome)
                    else:
                        next_outcome = outcome
                    next_state[consumed_action+add_action, consumed_danger+add_danger, next_outcome] += next_count
        state = next_state

    result = state[action, danger, :]
    return result

import cProfile
cProfile.run('neon_city_overdrive(6, 6)')

y = neon_city_overdrive(6, 6)

import _context
import icepool
from icepool import die, pool, PoolEval

class NeonCityOverdriveEval(PoolEval):
    def initial_state(self, action, danger):
        return 0
        
    def next_state(self, prev_state, outcome, action, danger):
        if action > danger:
            if outcome == 6:
                return action - danger + 5
            else:
                return outcome
        else:
            return prev_state

cProfile.run('NeonCityOverdriveEval().eval(pool(icepool.d6, 11), pool(icepool.d6, 11))')

y2 = NeonCityOverdriveEval().eval(pool(icepool.d6, 6), pool(icepool.d6, 6))

print(y2)

import matplotlib as mpl
import matplotlib.pyplot as plt

figsize = (8, 4.5)
dpi = 150

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid(True, axis='y')

x = numpy.arange(0, len(y))
plt.bar(x, y / numpy.sum(y))

ax.set_xticks(x)
ax.set_xticklabels('%d' % i if i <= 6 else '6+%d' % (i - 6) for i in x)
ax.set_xlim(-0.5, len(y)-0.5)

plt.savefig('output/neon_city_overdrive.png', dpi = dpi, bbox_inches = "tight")


