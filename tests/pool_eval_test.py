import _context

import hdroller
import pytest

class SumRerollIfAnyOnes(hdroller.EvalPool):
    def initial_state(self, pool):
        return 0
        
    def next_state(self, prev_state, outcome, count):
        return prev_state + outcome * count
        
    def reroll_state(self, prev_state, outcome, count):
        return outcome == 1 and count > 0

def test_reroll_state():
    result = SumRerollIfAnyOnes().eval(hdroller.d6.pool(5))
    expected = 5 @ (hdroller.d5+1)
    assert result.equals(expected)
