import _context

from hdroller import Die
import numpy
import numpy.linalg

import time
import cProfile
import pstats

def legend_of_five_rings_test():
    for i in range(100):
        result = Die.d10.explode(5).keep_highest(10, 5)

cProfile.run('legend_of_five_rings_test()')

start_time = time.perf_counter()
result = Die.d6.keep_highest(5, 3).keep_highest(7, 6)
end_time = time.perf_counter()
print('7x 5d6kh3 chargen computation time:', end_time-start_time)

start_time = time.perf_counter()
result = Die.d10.explode(2).keep_highest(10, 5)
end_time = time.perf_counter()
print(result)
print('L5R 10k5 explode 2 computation time:', end_time-start_time)

start_time = time.perf_counter()
result = Die.d10.explode(3).keep_highest(10, 5)
end_time = time.perf_counter()
print(result)
print('L5R 10k5 explode 3 computation time:', end_time-start_time)


start_time = time.perf_counter()
result = Die.d10.keep_highest(16, 8)
end_time = time.perf_counter()
print(result)
print('highest 8 of 16d10 computation time:', end_time-start_time)

start_time = time.perf_counter()
result = Die.d10.keep_highest(20, 2)
end_time = time.perf_counter()
print(result)
print('highest 2 of 20d10 computation time:', end_time-start_time)

start_time = time.perf_counter()
result = Die.d10.explode(5).keep_highest(5, 3)
end_time = time.perf_counter()
print(result)
print('L5R 5k3 explode 5 computation time:', end_time-start_time)

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

start_time = time.perf_counter()
repeated_result = points_3d6.keep_highest(9, 6)
end_time = time.perf_counter()

print('Repeated dice pool, 3d6x9 keep 6 highest')
print(repeated_result)
print('Computation time:', end_time-start_time)


