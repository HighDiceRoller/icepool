__docformat__ = 'google'

from icepool.population.base import Population

import csv as csv_lib
import html as html_lib
import io
import math
import re

from typing import Sequence

OUTCOME_PATTERN = r'(?:\*o|o)'

COMPARATOR_OPTIONS = '|'.join(['==', '<=', '>='])
COMPARATOR_PATTERN = f'(?:[%ipq](?:{COMPARATOR_OPTIONS}))'

TOTAL_PATTERN = re.compile(f'(?:{OUTCOME_PATTERN}|{COMPARATOR_PATTERN})')


def format_probability_inverse(probability, /, int_start: int = 20):
    """EXPERIMENTAL: Formats the inverse of a value as "1 in N".
    
    Args:
        probability: The value to be formatted.
        int_start: If N = 1 / probability is between this value and 1 million
            times this value it will be formatted as an integer. Otherwise it 
            be formatted asa float with precision at least 1 part in int_start.
    """
    max_precision = math.ceil(math.log10(int_start))
    if probability <= 0 or probability > 1:
        return 'n/a'
    product = probability * int_start
    if product <= 1:
        if probability * int_start * 10**6 <= 1:
            return f'1 in {1.0 / probability:<.{max_precision}e}'
        else:
            return f'1 in {round(1 / probability)}'

    precision = 0
    precision_factor = 1
    while product > precision_factor and precision < max_precision:
        precision += 1
        precision_factor *= 10
    return f'1 in {1.0 / probability:<.{precision}f}'


def split_format_spec(col_spec: str) -> Sequence[str]:
    """Splits the col_spec into its components."""
    result = re.findall(TOTAL_PATTERN, col_spec)
    if sum(len(t) for t in result) != len(col_spec):
        raise ValueError(f"Invalid col_spec '{col_spec}'")
    return result


def make_headers(mapping: Population,
                 format_tokens: Sequence[str]) -> Sequence[str]:
    """Generates a list of strings for the header."""
    result: list[str] = []
    for token in format_tokens:
        if token == 'o':
            result.append('Outcome')
        elif token == '*o':
            r = mapping.common_outcome_length()
            if r is None:
                result.append('Outcome')
            else:
                for i in range(r):
                    result.append(f'Outcome[{i}]')
        else:
            heading = ''

            if token[0] == 'q':
                heading += 'Quantity'
            elif token[0] in ['p', '%', 'i']:
                heading += 'Probability'

            comparator = token[1:]
            if comparator != '==':
                heading += ' ' + comparator

            result.append(heading)
    return result


def gather_cols(mapping: Population,
                format_tokens: Sequence[str]) -> Sequence[Sequence]:
    result: list[list[str]] = []
    for token in format_tokens:
        if token == 'o':
            result.append([str(x) for x in mapping.outcomes()])
        elif token == '*o':
            r = mapping.common_outcome_length()
            if r is None:
                result.append([str(x) for x in mapping.outcomes()])
            else:
                for i in range(r):
                    result.append([str(x[i]) for x in mapping.outcomes()])
        else:
            comparator = token[1:]
            denom_type = token[0]
            col: Sequence
            if denom_type == 'q':
                if comparator == '==':
                    col = list(mapping.values())
                elif comparator == '<=':
                    col = mapping.quantities('<=')
                elif comparator == '>=':
                    col = mapping.quantities('>=')
                result.append([str(x) for x in col])
            elif denom_type in ['p', '%', 'i']:
                if mapping.denominator() == 0:
                    result.append(['n/a' for x in mapping.outcomes()])
                else:
                    if comparator == '==':
                        col = mapping.probabilities()
                    elif comparator == '<=':
                        col = mapping.probabilities('<=')
                    elif comparator == '>=':
                        col = mapping.probabilities('>=')

                    if denom_type == 'p':
                        result.append([f'{float(x):0.6f}' for x in col])
                    elif denom_type == '%':
                        result.append([f'{float(x):0.6%}' for x in col])
                    elif denom_type == 'i':
                        result.append(
                            [format_probability_inverse(x) for x in col])
    return result


def make_rows(mapping: Population,
              format_tokens: Sequence[str]) -> Sequence[Sequence[str]]:
    cols = gather_cols(mapping, format_tokens)
    return [[c for c in row_data] for row_data in zip(*cols)]


def compute_col_widths(headers: Sequence[str],
                       rows: Sequence[Sequence[str]]) -> Sequence[int]:
    result = [len(s) for s in headers]
    for row in rows:
        result = [max(x, len(s)) for x, s in zip(result, row)]
    return result


def compute_alignments(rows: Sequence[Sequence[str]]) -> Sequence[str]:
    """A list of '<' or '>' for each column specifying alignment.

    Columns are aligned right iff all values are numeric.
    """
    result: list[str] = ['>'] * len(rows[0])
    for row in rows:
        for i, cell in enumerate(row):
            if not re.match(r'-?\d+(\.\d*)?%?$', cell):
                result[i] = '<'
    return result


def markdown(population: Population, col_spec: str) -> str:
    """Formats the Population as a Markdown table."""
    if population.is_empty():
        return f'Empty {type(population).__name__}\n'

    format_tokens = split_format_spec(col_spec)

    headers = make_headers(population, format_tokens)
    rows = make_rows(population, format_tokens)
    col_widths = compute_col_widths(headers, rows)
    alignments = compute_alignments(rows)

    result = f'{type(population).__name__} with denominator {population.denominator()}\n\n'
    result += '|'
    for header, alignment, col_width in zip(headers, alignments, col_widths):
        result += f' {header:{alignment}{col_width}} |'
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

    result += '\n'

    return result


def csv(population: Population,
        col_spec: str,
        *,
        dialect: str = 'excel',
        **fmtparams) -> str:
    """Formats the `Population` as a comma-separated-values table."""

    format_tokens = split_format_spec(col_spec)

    headers = make_headers(population, format_tokens)
    rows = make_rows(population, format_tokens)

    with io.StringIO() as out:
        writer = csv_lib.writer(out, dialect=dialect, **fmtparams)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)

        return out.getvalue()


def bbcode(population: Population, col_spec: str) -> str:
    """Formats the `Population` as a BBCode table."""
    if population.is_empty():
        return f'Empty {type(population).__name__}\n'

    format_tokens = split_format_spec(col_spec)

    headers = make_headers(population, format_tokens)
    rows = make_rows(population, format_tokens)
    alignments = compute_alignments(rows)

    result = f'{type(population).__name__} with denominator {population.denominator()}\n\n'
    result += '[table]\n'
    result += '[tr]'
    for header, alignment in zip(headers, alignments):
        if alignment == '<':
            result += f'[th]{header}[/th]'
        else:
            result += f'[th][right]{header}[/right][/th]'
    result += '[/tr]\n'

    for row in rows:
        result += '[tr]'
        for s, alignment in zip(row, alignments):
            if alignment == '<':
                result += f'[td]{s}[/td]'
            else:
                result += f'[td][right]{s}[/right][/td]'
        result += '[/tr]\n'

    result += '[/table]\n'

    return result


def html(population: Population, col_spec: str) -> str:
    """Formats the `Population` as a HTML table."""
    if population.is_empty():
        return f'Empty {type(population).__name__}\n'

    format_tokens = split_format_spec(col_spec)

    headers = make_headers(population, format_tokens)
    rows = make_rows(population, format_tokens)
    alignments = compute_alignments(rows)

    result = '<table>\n'
    result += f'<caption>{type(population).__name__} with denominator {population.denominator()}</caption>\n'
    result += '<tr>'
    for header, alignment in zip(headers, alignments):
        header = html_lib.escape(header)
        if alignment == '<':
            result += f'<th>{header}</th>'
        else:
            result += f'<th style="text-align:right;">{header}</th>'
    result += '</tr>\n'

    for row in rows:
        result += '<tr>'
        for s, alignment in zip(row, alignments):
            s = html_lib.escape(s)
            if alignment == '<':
                result += f'<td>{s}</td>'
            else:
                result += f'<td style="text-align:right;">{s}</td>'
        result += '</tr>\n'

    result += '</table>\n'

    return result
