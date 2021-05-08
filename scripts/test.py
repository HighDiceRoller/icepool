from hdroller import Die
import hdroller.pure_dice_pool
import hdroller.mixed_dice_pool
import numpy
import numpy.linalg

import time

for i in range(6, 15):
    print(i, Die.from_faces([0]*i + [1]*(19-i) + [2]).variance())

start_time = time.time()
pool = hdroller.pure_dice_pool.PureDicePool(100, Die.d6)
result = pool.keep_highest(50)
end_time = time.time()
print(result)
print('Computation time:', end_time-start_time)

start_time = time.time()
pool = hdroller.pure_dice_pool.PureDicePool(5, Die.d10.explode(5))
result = pool.keep_highest(3)
end_time = time.time()
print(result)
print('Computation time:', end_time-start_time)

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
