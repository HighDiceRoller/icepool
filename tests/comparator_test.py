import _context

import hdroller
import pytest

def lt_test():
    assert (hdroller.d6 < hdroller.d6) == Die.bernoulli(15, 36)

def gt_test():
    assert (hdroller.d6 > hdroller.d6) == Die.bernoulli(15, 36)

def leq_test():
    assert (hdroller.d6 <= hdroller.d6) == Die.bernoulli(21, 36)

def geq_test():
    assert (hdroller.d6 >= hdroller.d6) == Die.bernoulli(21, 36)