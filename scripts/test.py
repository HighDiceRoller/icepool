import _context

from hdroller import Die
import hdroller.pure_dice_pool
import hdroller.mixed_dice_pool
import numpy
import numpy.linalg

import time
import cProfile

def legend_of_five_rings_test():
    for i in range(1000):
        pool = hdroller.pure_dice_pool.PureDicePool(10, Die.d10.explode(3))
        result = pool.keep_highest(5)

#cProfile.run('legend_of_five_rings_test()')

result = Die.d6.keep_highest(1, 0)
print(result)



start_time = time.time()
result = Die.d10.explode(3).keep_highest(10, 5)
end_time = time.time()
print(result)
print('L5R 10k5 explode 3 computation time:', end_time-start_time)

"""

start_time = time.time()
pool = hdroller.pure_dice_pool.PureDicePool(16, Die.d10)
result = pool.keep_highest(8)
end_time = time.time()
print(result)
print('highest 8 of 16d10 computation time:', end_time-start_time)

start_time = time.time()
pool = hdroller.pure_dice_pool.PureDicePool(20, Die.d10)
result = pool.keep_highest(2)
end_time = time.time()
print(result)
print('highest 2 of 20d10 computation time:', end_time-start_time)

start_time = time.time()
pool = hdroller.pure_dice_pool.PureDicePool(5, Die.d10.explode(5))
result = pool.keep_highest(3)
end_time = time.time()
print(result)
print('L5R 5k3 explode 5 computation time:', end_time-start_time)

"""

"""

start_time = time.time()
pool = hdroller.pure_dice_pool.PureDicePool(19, Die.d20)
result = pool.keep_index(9)
end_time = time.time()
print(result)
print('Computation time:', end_time-start_time)

start_time = time.time()
pool = hdroller.mixed_dice_pool.MixedDicePool(*([Die.d12] * 20))
result = pool.keep_highest(4)
end_time = time.time()
print(result)
print('Computation time:', end_time-start_time)


start_time = time.time()
pool = hdroller.mixed_dice_pool.MixedDicePool(Die.d4, Die.d6, Die.d8, Die.d10, Die.d12)

result = pool.keep_highest(2)

end_time = time.time()

print(result)
print('Computation time:', end_time-start_time)

point_buy_pathfinder = {
    3 : -16,
    4 : -12,
    5 : -9,
    6 : -6,
    7 : -4,
    8 : -2,
    9 : -1,
    10 : 0,
    11 : 1,
    12 : 2,
    13 : 3,
    14 : 5,
    15 : 7,
    16 : 10,
    17 : 13,
    18 : 17,
}

die_3d6 = Die.d(3, 6)
points_3d6 = die_3d6.relabel(point_buy_pathfinder).repeat_and_sum(6)

start_time = time.time()
pool = hdroller.pure_dice_pool.PureDicePool(9, points_3d6)
repeated_result = pool.keep_highest(6)
end_time = time.time()

print('Repeated dice pool, 3d6x9 keep 6 highest')
print(result)
print('Computation time:', end_time-start_time)

start_time = time.time()
pool = hdroller.mixed_dice_pool.MixedDicePool(*([points_3d6] * 9))
mixed_result = pool.keep_highest(6)
end_time = time.time()

print('Mixed dice pool, 3d6x9 keep 6 highest')
print(mixed_result)
print('Computation time:', end_time-start_time)

print(numpy.linalg.norm(repeated_result.pmf() - mixed_result.pmf(), ord=1))


"""
