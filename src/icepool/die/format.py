__docformat__ = 'google'

import icepool

import csv as csv_lib
import io
import re

from collections.abc import Sequence

OUTCOME_PATTERN = r'(?:\*o|o)'

COMPARATOR_OPTIONS = '|'.join(['==', '<=', '>='])
COMPARATOR_PATTERN = f'(?:[w%](?:{COMPARATOR_OPTIONS}))'
"""A comparator followed by w for weight or % for probability percent."""

TOTAL_PATTERN = re.compile(f'(?:{OUTCOME_PATTERN}|{COMPARATOR_PATTERN})')

DENOM_TYPE_HEADERS = {
    'w': 'Weight',
    '%': 'Chance (%)',
}


def split_format_spec(format_spec: str) -> Sequence[str]:
    """Splits the format_spec into its components."""
    result = re.findall(TOTAL_PATTERN, format_spec)
    if sum(len(t) for t in result) != len(format_spec):
        raise ValueError(f"Invalid format spec '{format_spec}")
    return result


def make_headers(die: 'icepool.Die',
                 format_tokens: Sequence[str]) -> Sequence[str]:
    """Generates a list of strings for the header."""
    result: list[str] = []
    for token in format_tokens:
        if token == 'o':
            result.append('Outcome')
        elif token == '*o':
            r = die.outcome_len()
            if r is None:
                result.append('Outcome')
            else:
                for i in range(r):
                    result.append(f'Outcome[{i}]')
        else:
            comparator = token[1:]
            denom_type = DENOM_TYPE_HEADERS[token[0]]
            if comparator == '==':
                result.append(denom_type)
            else:
                result.append(f'{denom_type} {comparator}')
    return result


def gather_cols(die: 'icepool.Die',
                format_tokens: Sequence[str]) -> Sequence[Sequence]:
    result: list[list[str]] = []
    for token in format_tokens:
        if token == 'o':
            result.append([str(x) for x in die.outcomes()])
        elif token == '*o':
            r = die.outcome_len()
            if r is None:
                result.append([str(x) for x in die.outcomes()])
            else:
                for i in range(r):
                    result.append([str(x[i]) for x in die.outcomes()])
        else:
            comparator = token[1:]
            denom_type = token[0]
            if denom_type == 'w':
                if comparator == '==':
                    col = die.weights()
                elif comparator == '<=':
                    col = die.cweights()
                elif comparator == '>=':
                    col = die.sweights()
                result.append([str(x) for x in col])
            elif denom_type == '%':
                if die.denominator() == 0:
                    result.append(['n/a' for x in die.outcomes()])
                else:
                    if comparator == '==':
                        col = die.pmf(percent=True)
                    elif comparator == '<=':
                        col = die.cdf(percent=True)
                    elif comparator == '>=':
                        col = die.sf(percent=True)
                    result.append([f'{x:0.6f}' for x in col])
    return result


def make_rows(die: 'icepool.Die',
              format_tokens: Sequence[str]) -> Sequence[Sequence[str]]:
    cols = gather_cols(die, format_tokens)
    return [[c for c in row_data] for row_data in zip(*cols)]


def compute_col_widths(headers: Sequence[str],
                       rows: Sequence[Sequence[str]]) -> Sequence[int]:
    result = [len(s) for s in headers]
    for row in rows:
        result = [max(x, len(s)) for x, s in zip(result, row)]
    return result


def compute_alignments(rows: Sequence[Sequence[str]]) -> Sequence[str]:
    """Returns a list of '<' or '>' for each column specifying alignment.

    Columns are aligned right iff all values are numeric.
    """
    result: list[str] = ['>'] * len(rows[0])
    for row in rows:
        for i, cell in enumerate(row):
            if not re.match(r'\d+(\.\d*)?', cell):
                result[i] = '<'
    return result


def markdown(die: 'icepool.Die', format_spec: str) -> str:
    """Formats the die as a Markdown table."""
    if die.is_empty():
        return 'Empty die\n'

    format_tokens = split_format_spec(format_spec)

    headers = make_headers(die, format_tokens)
    rows = make_rows(die, format_tokens)
    col_widths = compute_col_widths(headers, rows)
    alignments = compute_alignments(rows)

    result = f'Denominator: {die.denominator()}\n\n'
    result += '|'
    for header, col_width in zip(headers, col_widths):
        result += f' {header:<{col_width}} |'
    result += '\n'

    result += '|'
    for alignment, col_width in zip(alignments, col_widths):
        if alignment == '<':
            result += ':' + '-' * col_width + '-|'
        else:
            result += '-' + '-' * col_width + ':|'
    result += '\n'

    for row in rows:
        result += '|'
        for s, alignment, col_width in zip(row, alignments, col_widths):
            result += f' {s:{alignment}{col_width}} |'
        result += '\n'

    return result


def csv(die, format_spec: str, *, dialect: str = 'excel', **fmtparams) -> str:
    """Formats the die as a comma-separated-values string."""

    format_tokens = split_format_spec(format_spec)

    headers = make_headers(die, format_tokens)
    rows = make_rows(die, format_tokens)

    with io.StringIO() as out:
        writer = csv_lib.writer(out, dialect=dialect, **fmtparams)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)

        return out.getvalue()
