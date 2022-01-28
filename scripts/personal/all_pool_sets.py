import _context

import numpy
from hdroller import Die, Pool, SinglePoolScorer

class AllSetsScorer(SinglePoolScorer):
    def initial_state(self, initial_pool):
        return ()

    def next_state(self, outcome, count, prev_state):
        if count >= 2:
            return tuple(sorted(prev_state + (count,)))
        else:
            return prev_state

    def score(self, initial_pool, initial_state, final_state):
        return tuple(reversed(final_state))

die = Die.d10

import cProfile
cProfile.run('AllSetsScorer().evaluate_dict(Pool(die, 10))')

for num_dice in range(2, 13):
    result = AllSetsScorer().evaluate_dict(Pool(die, num_dice))
    total_weight = sum(result.values())
    print(f'## {num_dice} dice')
    print()
    print('| Sets | Weight | Probability |')
    print('|------|-------:|------------:|')
    for sets in sorted(result.keys()):
        print(f'|{sets}|{int(result[sets])}|{result[sets]/total_weight:0.3%}|')
    print()
