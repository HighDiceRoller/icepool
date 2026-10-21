import icepool
import pytest

test_dice = [icepool.Die([]), icepool.d6, icepool.d6.map(lambda x: (x, x + 1))]

# Test against errors only.


@pytest.mark.parametrize('die', test_dice)
def test_repr(die):
    repr(die)


@pytest.mark.parametrize('die', test_dice)
def test_str(die):
    str(die)


format_specs = [
    '',
    'md:q==|q<=|q>=',
    'md:p==|p<=|p>=',
    'md:%==|%>=|%>=',
    'csv:q==|q<=|q>=',
    'csv:p==|p<=|p>=',
    'csv:%==|%>=|%>=',
    'bbcode:q==|q<=|q>=',
    'bbcode:p==|p<=|p>=',
    'bbcode:%==|%>=|%>=',
    'html:q==|q<=|q>=',
    'html:p==|p<=|p>=',
    'html:%==|%>=|%>=',
]


@pytest.mark.parametrize('die', test_dice)
@pytest.mark.parametrize('format_spec', format_specs)
def test_format_spec(die, format_spec):
    f'{die:{format_spec}}'


def test_format_no_columns():
    assert f'{icepool.d6:md:}' == 'Die with denominator 6\n\n|\n|\n' + '|\n' * 6 + '\n'
    assert icepool.Die([()]).format('md:*o') == 'Die with denominator 1\n\n|\n|\n|\n\n'
    assert f'{icepool.d6:csv:}' == '\r\n' * 7
    assert f'{icepool.d6:html:}'
    assert f'{icepool.d6:bbcode:}'
