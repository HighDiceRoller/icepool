import _context

from hdroller import Die, Pool, SinglePoolScorer

class V5PoolSuccesses(SinglePoolScorer):
    def __init__(self, extra_crit=0):
        self.extra_crit = extra_crit

    def initial_state(self, initial_pool):
        return 0
    
    def next_state(self, outcome, count, prev_state):
        if outcome == 2:
            count += self.extra_crit
            total = count + 2 * (count // 2)
            return prev_state + total
        elif outcome == 1:
            return prev_state + count
        else:
            return prev_state

    def score(self, initial_pool, initial_state, state):
        return state

scorer = V5PoolSuccesses()
scorer_plus = V5PoolSuccesses(1)

standard_die = Die([5, 4, 1], 0)
nine_die = Die([5, 3, 2], 0)

#import cProfile
#cProfile.run('scorer.evaluate(Pool(standard_die, 100))')

print(scorer.evaluate(Pool(standard_die, [2, 1, 2])))

for num_dice in range(1, 11):
    d1 = scorer.evaluate(Pool(standard_die, num_dice))
    d2 = scorer.evaluate(Pool(nine_die, num_dice))
    d3a = scorer.evaluate(Pool(standard_die, num_dice - 1))
    d3b = scorer_plus.evaluate(Pool(standard_die, num_dice - 1))
    d3 = Die.mix(d3a, d3b)

    a = (d2.mean() - d1.mean()) / d1.mean()
    b = (d3.mean() - d1.mean()) / d1.mean()
    #print(d1)
    print(num_dice, d1.mean(), d2.mean(), d3.mean())
    #print(num_dice, a, b)

"""

class V5PoolCrits(PoolScorer):
    def __init__(self, extra_crit=0):
        self.extra_crit = extra_crit

    def initial_state(self, die, max_outcomes):
        return False
    
    def next_state(self, state, outcome, count):
        if outcome == 2:
            count += self.extra_crit
            return count >= 2
        else:
            return state

    def score(self, state, num_dice):
        return int(state)

scorer = V5PoolCrits()
scorer_plus = V5PoolCrits(1)

for num_dice in range(1, 11):
    d1 = scorer.evaluate(standard_die, num_dice)
    d2 = scorer.evaluate(nine_die, num_dice)
    d3a = scorer.evaluate(standard_die, num_dice - 1)
    d3b = scorer_plus.evaluate(standard_die, num_dice - 1)
    d3 = Die.mix(d3a, d3b)
    print(num_dice, d1.mean(), d2.mean(), d3.mean())

"""


