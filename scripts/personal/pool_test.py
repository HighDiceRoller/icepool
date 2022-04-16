import _context

import icepool
from icepool import Die
from icepool.dice_pool import DicePool
import numpy

# = chicken dinner
point_buy_quadratic = {
    3 : -9,
    4 : -6,
    5 : -4,
    6 : -2,
    7 : -1,
    8 : 0,
    9 : 1,
    10 : 2,
    11 : 3,
    12 : 4,
    13 : 5,
    14 : 7,
    15 : 9,
    16 : 12,
    17 : 15,
    18 : 19,
}

class FreeAbilityPool(DicePool):
    def state_shape(self, outcome, prev_state_shape):
        return (3, outcome*2 + 1, 18 * 6 + 1,)

    def state(self, outcome, counts, prev_state):
        if len(prev_state) == 0:
            prev_score, prev_dice_total, prev_score = 0, 0, 0
        else:
            prev_dice, prev_dice_total, prev_score = prev_state

        total_dice = counts[0] + prev_dice
        total = outcome * counts[0] + prev_dice_total
        
        next_dice = total_dice % 3
        
        if total_dice >= 3:
            next_dice_total = next_dice * outcome
            next_score = total - next_dice_total
        else:
            next_dice = total_dice
            next_dice_total = prev_dice_total + outcome * counts[0]
            next_score = prev_score

    def score(self, final_state):
        return final_state[-1]

    def min_score(self, die, num_dice):
        return 3 * 6

    def max_score(self, die, num_dice):
        return 18 * 8
