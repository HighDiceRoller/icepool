import _context
from hdroller import Die
import numpy
import math
import fractions

die = Die.d10.explode(10) + Die.d10

print(die.excess_kurtosis())

print(2**63)
print(2**64)
print(2**65)
print(numpy.lcm(2**64, 2**64+1))
print(math.lcm(2**64, 2**64+1))
print(numpy.lcm(numpy.array([2**128]), numpy.array([2**128+1])))

x = {fractions.Fraction(1, 2) : 'foo'}
