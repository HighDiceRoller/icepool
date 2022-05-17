__docformat__ = 'google'


def _common_truncation(*dice):
    """Determines if the dice can be expressed as a one-sided truncation of a single fundamental die.

    Returns:
        1 for a common truncate_max.
        -1 for a common truncate_min.
        0 if the dice are all identical.
        None if there is no common truncation.
    """
    base_die = dice[0]
    truncate_max = True
    truncate_min = True
    for die in dice[1:]:
        if die.num_outcomes() == base_die.num_outcomes():
            if die.equals(base_die):
                continue
            else:
                return None

        if die.num_outcomes() > base_die.num_outcomes():
            base_die, die = die, base_die

        if truncate_min:
            for a, b in zip(reversed(die.items()), reversed(base_die.items())):
                if a != b:
                    truncate_min = False
                    break

        if truncate_max:
            for a, b in zip(die.items(), base_die.items()):
                if a != b:
                    truncate_max = False
                    break

        if not (truncate_min or truncate_max):
            return None

    if truncate_max and truncate_min:
        return 0
    elif truncate_min:
        return -1
    elif truncate_max:
        return 1
    else:
        return None
