__docformat__ = 'google'

import icepool

def round_robin_score(*dice, tiebreaker='coin'):
    """
    Returns a score for each die equal to the chance of winning against an opponent chosen uniformly at random.
    This includes itself, which is a 50% chance if ties are broken by coin flip.
    """
    result = []
    for die in dice:
        wins = 0.0
        for opponent in dice:
            difference = die - opponent
            if tiebreaker == 'coin':
                difference = difference - icepool.coin(1, 2)
            elif tiebreaker == 'win':
                pass
            elif tiebreaker == 'lose':
                difference = difference - 1
            wins += (difference >= 0).mean()
        result.append(wins / len(dice))
    return result
