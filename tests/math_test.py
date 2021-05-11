import _context

import hdroller.math
import numpy
import pytest

def test_convolve_along_last_axis_1d():
    a = numpy.array([2, 1])
    v = numpy.array([2, 1])
    result = hdroller.math.convolve_along_last_axis(a, v)
    expected = numpy.array([4, 4, 1])
    assert result == pytest.approx(expected)

def test_convolve_along_last_axis_2d():
    a = numpy.array([[2, 1], [1, 3], [1, 1]])
    v = numpy.array([[2, 1], [1, 3], [1, 1]])
    result = hdroller.math.convolve_along_last_axis(a, v)
    expected = numpy.array([[4, 4, 1], [1, 6, 9], [1, 2, 1]])
    assert result == pytest.approx(expected)
