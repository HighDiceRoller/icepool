import icepool
import pytest


def test_vampire():

    # One method is to express the possible outcomes using a tuple
    # that has exactly one element set according to the symbol rolled.
    # This is called a "one-hot" representation.
    # In this case we have four types of symbols.

    normal_die = icepool.Die({
        (0, 0, 0, 0): 5,  # failure
        (0, 1, 0, 0): 4,  # success
        (0, 0, 1, 0): 1,  # crit
    })
    hunger_die = icepool.Die({
        (1, 0, 0, 0): 1,  # bestial failure
        (0, 0, 0, 0): 4,  # failure
        (0, 1, 0, 0): 4,  # success
        (0, 0, 0, 1): 1,  # messy crit
    })

    # Summing the dice produces the total number of each symbol rolled.
    # The @ operator means roll the left die, then roll that many of the right die and sum.
    # For outcomes that are tuples, sums are performed element-wise.
    total = 3 @ normal_die + 2 @ hunger_die

    # Then we can use a function to compute the final result.
    def eval_one_hot(hunger_botch, success, crit, hunger_crit):
        total_crit = crit + hunger_crit
        success += total_crit + 2 * (total_crit // 2)
        if total_crit >= 2:
            if hunger_crit > 0:
                win_type = 'messy'
            else:
                win_type = 'crit'
        else:
            win_type = ''
        loss_type = 'bestial' if hunger_botch > 0 else ''
        return success, win_type, loss_type

    # star=True unpacks the tuples before giving them to eval_one_hot.
    result = total.map(eval_one_hot)
    assert result.quantity((0, '', '')) == 2000
