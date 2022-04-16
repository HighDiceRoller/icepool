import _context
from icepool import Die

base_die = Die.d12

for i in range(6, 15):
    die = Die.mix(0, base_die, 2 * base_die, weights=[19 - i, i, 1])
    print(i, die.variance() / base_die.mean() / base_die.mean())
    
