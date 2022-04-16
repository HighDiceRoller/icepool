import _context


from icepool import Die

die = Die.d6.reroll([2, 3, 4, 5], max_times=2) <= 1
print(5 * die)
print(10 * die)

die = Die.d6.reroll([2, 3, 4, 5], max_times=2) <= 3
print(5 * die)

print(Die.d6 * Die.d6)
