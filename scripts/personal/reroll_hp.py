import _context

import functools

from hdroller import Die
import numpy

def opt_hp_at_max_level(die, max_level):
    @functools.lru_cache(maxsize=None)
    def inner(current_level, current_hp):
        if current_level == max_level:
            return current_hp
        hp_if_no_reroll = 0.0
        for outcome, p in zip(die.outcomes(), die.pmf()):
            hp_if_no_reroll += inner(current_level + 1, current_hp + outcome) * p
        hp_if_reroll = 0.0
        reroll_die = (current_level + 1) * die
        for outcome, p in zip(reroll_die.outcomes(), reroll_die.pmf()):
            hp_if_reroll += inner(current_level + 1, outcome) * p

        return max(hp_if_no_reroll, hp_if_reroll)

    return inner(0, 0)

dice = [Die.d4, Die.d6, Die.d8, Die.d10, Die.d12]
for die in dice:
    # First level always rolls max hp, so we add it afterwards.
    print(opt_hp_at_max_level(die, 19) + die.max_outcome())
