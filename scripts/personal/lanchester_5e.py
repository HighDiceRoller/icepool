import _context

import numpy

import matplotlib as mpl
import matplotlib.pyplot as plt

crs = numpy.arange(1, 21)

xp_by_cr = numpy.array([
    200,
    450,
    700,
    1100,
    1800,
    2300,
    2900,
    3900,
    5000,
    5900,
    7200,
    8400,
    10000,
    11500,
    13000,
    15000,
    18000,
    20000,
    22000,
    25000, # level 20
    33000,
    41000,
    50000,
    62000,
    75000,
    90000,
    105000,
    120000,
    135000,
    155000,
    100,
])

eq_by_cr = numpy.power(xp_by_cr, 2.0 / 3.0)

eq_by_cr_ideal = numpy.power(50 * numpy.square(numpy.arange(2, 22)), 2.0/3.0)

def fit_integer_to_sequence(seq, start, delta=0.001):
    # seq: the sequence to fit
    # start: the integer corresponding to the first value in seq
    # delta: the spacing of values to try
    log_seq = numpy.log(seq)
    def compute(candidate):
        # the resulting integers
        integer_seq = numpy.round(seq * candidate / seq[0])
        log_integer_seq = numpy.log(integer_seq)
        log_diff = log_seq - log_integer_seq
        log_scale = numpy.mean(log_diff)
        log_error = log_diff - log_scale
        error = numpy.sqrt(numpy.dot(log_error, log_error) / len(seq))
        #error = numpy.max(numpy.abs(log_error))
        scale = numpy.exp(log_scale)
        return error, candidate, scale, tuple(int(x) for x in integer_seq)
        
    #candidates = numpy.arange(start - 0.5, start + 0.5 - 0.5 * delta, delta)
    candidates = [start]
    return min(compute(candidate) for candidate in candidates)


for i in range(1, 11):
    error, candidate, scale, integer_seq = fit_integer_to_sequence(eq_by_cr, i)
    print(error, candidate)
    print(scale, 1.0 / scale, scale ** 1.5, scale ** -1.5)
    print(integer_seq)
    print()
