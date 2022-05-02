def markdown(die, *, include_weights=True, unpack_outcomes=True):
    """Formats the die as a Markdown table.

    Args:
        include_weights: If `True`, a column will be emitted for the weights.
            Otherwise, only probabilities will be emitted.
        unpack_outcomes: If `True` and all outcomes have a common length,
            outcomes will be unpacked, producing one column per element.
    """
    if unpack_outcomes and die.outcome_len() is not None:
        outcome_lengths = []
        for i in range(die.outcome_len()):
            outcome_length = max(
                tuple(len(str(outcome[i])) for outcome in die.outcomes()) +
                (len(f'Outcome[{i}]'),))
            outcome_lengths.append(outcome_length)
        result = ''
        result += f'Denominator: {die.denominator()}\n\n'
        result += '|'
        for i in range(die.outcome_len()):
            result += ' ' + ' ' * (outcome_lengths[i] - len(f'Outcome[{i}]')
                                  ) + f'Outcome[{i}]' + ' |'
        if include_weights:
            weight_length = max(
                tuple(len(str(weight)) for weight in die.weights()) +
                (len('Weight'),))
            result += ' ' + ' ' * (weight_length - len('Weight')) + 'Weight |'
        if die.denominator() > 0:
            result += ' Probability |'
        result += '\n'
        result += '|'
        for i in range(die.outcome_len()):
            result += '-' + '-' * outcome_lengths[i] + ':|'
        if include_weights:
            result += '-' + '-' * weight_length + ':|'
        if die.denominator() > 0:
            result += '------------:|'
        result += '\n'
        for outcome, weight, p in zip(die.outcomes(), die.weights(), die.pmf()):
            result += '|'
            for i, x in enumerate(outcome):
                result += f' {str(x):>{outcome_lengths[i]}} |'
            if include_weights:
                result += f' {weight:>{weight_length}} |'
            if die.denominator() > 0:
                result += f' {p:11.6%} |'
            result += '\n'
        return result
    else:
        outcome_length = max(
            tuple(len(str(outcome)) for outcome in die.outcomes()) +
            (len('Outcome'),))
        result = ''
        result += f'Denominator: {die.denominator()}\n\n'
        result += '| ' + ' ' * (outcome_length - len('Outcome')) + 'Outcome |'
        if include_weights:
            weight_length = max(
                tuple(len(str(weight)) for weight in die.weights()) +
                (len('Weight'),))
            result += ' ' + ' ' * (weight_length - len('Weight')) + 'Weight |'
        if die.denominator() > 0:
            result += ' Probability |'
        result += '\n'
        result += '|-' + '-' * outcome_length + ':|'
        if include_weights:
            result += '-' + '-' * weight_length + ':|'
        if die.denominator() > 0:
            result += '------------:|'
        result += '\n'
        for outcome, weight, p in zip(die.outcomes(), die.weights(), die.pmf()):
            result += f'| {str(outcome):>{outcome_length}} |'
            if include_weights:
                result += f' {weight:>{weight_length}} |'
            if die.denominator() > 0:
                result += f' {p:11.6%} |'
            result += '\n'
        return result