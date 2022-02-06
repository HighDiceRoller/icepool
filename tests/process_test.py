import _context

import hdroller
import pytest

def test_hitting_time():
    full_result = hdroller.d6.hitting_time(lambda x: x >= 10, max_depth=None)
    for n in range(11):
        result = (full_result <= n).reduce().trim()
        expected = (n @ hdroller.d6 >= 10).reduce().trim()
        assert result.equals(expected)
