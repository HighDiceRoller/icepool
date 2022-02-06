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

class SumPoolDescending(hdroller.SumPool):
    def direction(self, pool):
        return -1

def test_sum_descending():
    result = SumPoolDescending().eval(hdroller.d6.pool(5))
    expected = 5 @ hdroller.d6
    assert result.equals(expected)

def test_sum_descending_limit_outcomes():
    result = -SumPoolDescending().eval((-hdroller.d12).pool(min_outcomes=[-8, -6]))
    expected = hdroller.d6 + hdroller.d8
    assert result.equals(expected)

def test_sum_descending_keep_highest():
    result = SumPoolDescending().eval(hdroller.d6.pool()[0, 1, 1, 1])
    expected = hdroller.d6.keep_highest(4, 3)
    assert result.equals(expected)
