__docformat__ = 'google'


def _header_strings(die, include_weights, unpack_outcomes):
    """Generates a list of strings for the header."""
    header = []
    if unpack_outcomes:
        for i in range(die.outcome_len()):
            header.append(f'Outcome[{i}]')
    else:
        header.append('Outcome')
    if include_weights:
        header.append('Weight')
    header.append('Probability')
    return header, [len(s) for s in header]


def _row_string(outcome, weight, p, include_weights, unpack_outcomes):
    row = []
    if unpack_outcomes:
        for x in outcome:
            row.append(str(x))
    else:
        row.append(str(outcome))
    if include_weights:
        row.append(str(weight))
    row.append(f'{p:11.6%}')

    return row


def _row_strings(die, include_weights, unpack_outcomes):
    result = [
        _row_string(outcome, weight, p, include_weights, unpack_outcomes)
        for outcome, weight, p in zip(die.outcomes(), die.weights(), die.pmf())
    ]
    col_widths = [max(len(s) for s in col) for col in zip(*result)]
    return result, col_widths


def markdown(die, *, include_weights=True, unpack_outcomes=True):
    """Formats the die as a Markdown table.

    Args:
        include_weights: If `True`, a column will be emitted for the weights.
            Otherwise, only probabilities will be emitted.
        unpack_outcomes: If `True` and all outcomes have a common length,
            outcomes will be unpacked, producing one column per element.
    """
    if die.is_empty():
        return 'Empty die\n'

    unpack_outcomes = unpack_outcomes and die.outcome_len() is not None
    header_strings, header_widths = _header_strings(die, include_weights,
                                                    unpack_outcomes)
    row_strings, col_widths = _row_strings(die, include_weights,
                                           unpack_outcomes)
    col_widths = [max(h, c) for h, c in zip(header_widths, col_widths)]

    result = f'Denominator: {die.denominator()}\n\n'
    result += '| '
    result += ' | '.join(
        f'{s:>{width}}' for s, width in zip(header_strings, col_widths))
    result += ' |\n'

    result += '|-'
    result += ':|-'.join('-' * width for width in col_widths)
    result += ':|\n'

    for row in row_strings:
        result += '| '
        result += ' | '.join(
            f'{s:>{width}}' for s, width in zip(row, col_widths))
        result += ' |\n'

    return result
