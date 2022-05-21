__docformat__ = 'google'


def count_dice_tuple(num_dice, count_dice):
    """Expresses `count_dice` as a tuple.

    See `Pool.set_count_dice()` for details.

    Args:
        `num_dice`: An `int` specifying the number of dice.
        `count_dice`: Raw specification for how the dice are to be counted.
    Raises:
        `ValueError` if:
            * More than one `Ellipsis` is used.
            * An `Ellipsis` is used in the center with too few `num_dice`.
    """
    if count_dice is None:
        return (1,) * num_dice
    elif isinstance(count_dice, int):
        result = [0] * num_dice
        result[count_dice] = 1
        return tuple(result)
    elif isinstance(count_dice, slice):
        if count_dice.step is not None:
            # "Step" is not useful here, so we repurpose it to set the number
            # of dice.
            num_dice = count_dice.step
            count_dice = slice(count_dice.start, count_dice.stop)
        result = [0] * num_dice
        result[count_dice] = [1] * len(result[count_dice])
        return tuple(result)
    else:
        split = None
        for i, x in enumerate(count_dice):
            if x is Ellipsis:
                if split is None:
                    split = i
                else:
                    raise ValueError(
                        'Cannot use more than one Ellipsis (...) for count_dice.'
                    )

        if split is None:
            return tuple(count_dice)

        extra_dice = num_dice - len(count_dice) + 1

        if split == 0:
            # Ellipsis on left.
            count_dice = count_dice[1:]
            if extra_dice < 0:
                return tuple(count_dice[-extra_dice:])
            else:
                return (0,) * extra_dice + tuple(count_dice)
        elif split == len(count_dice) - 1:
            # Ellipsis on right.
            count_dice = count_dice[:-1]
            if extra_dice < 0:
                return tuple(count_dice[:extra_dice])
            else:
                return tuple(count_dice) + (0,) * extra_dice
        else:
            # Ellipsis in center.
            if extra_dice < 0:
                result = [0] * num_dice
                for i in range(min(split, num_dice)):
                    result[i] += count_dice[i]
                reverse_split = split - len(count_dice)
                for i in range(-1, max(reverse_split - 1, -num_dice - 1), -1):
                    result[i] += count_dice[i]
                return tuple(result)
            else:
                return tuple(count_dice[:split]) + (0,) * extra_dice + tuple(
                    count_dice[split + 1:])