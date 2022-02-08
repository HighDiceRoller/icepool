from hdroller import Die
import numpy
import time

base_die = Die.d4
num_dice = 3
kwargs = {
    'keep_highest' : 3,
}

method_old = base_die.repeat_and_keep_and_sum(num_dice, **kwargs)
print(method_old)

method_new = base_die.repeat_and_keep_and_sum2(num_dice, **kwargs)
print(method_new)
print(numpy.sum(method_new.pmf()))

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


points_3d6 = Die.d(3, 6).sub(point_buy_pathfinder).repeat_and_sum(6)
print(points_3d6.mean(), points_3d6.standard_deviation(), points_3d6.total_mass())

points_3d6_7 = Die.d(3, 6).sub(point_buy_pathfinder).repeat_and_keep_and_sum2(7, keep_highest=6)
print(points_3d6_7.mean(), points_3d6_7.standard_deviation(), points_3d6_7.total_mass())

start = time.time()
points_3d6_9 = Die.d(3, 6).sub(point_buy_pathfinder).repeat_and_keep_and_sum2(9, keep_highest=6)
print(points_3d6_9.mean(), points_3d6_9.standard_deviation(), points_3d6_9.total_mass())
end = time.time()
print('time:', end - start)

points_4d6_7 = Die.d(6).repeat_and_keep_and_sum2(4, keep_highest=3).sub(point_buy_pathfinder).repeat_and_keep_and_sum2(7, keep_highest=6)
print(points_4d6_7.mean(), points_4d6_7.standard_deviation(), points_4d6_7.total_mass())

means = []
bilinear_medians = []
for i in range(9):
    start = time.time()
    die = Die.d(3, 6).repeat_and_keep_and_sum2(9, keep_index=i)
    end = time.time()
    means.append(die.mean())
    bilinear_medians.append(die.bilinear_median())
    print(i, die.mean(), die.bilinear_median(), die.mode(), end-start)

print(', '.join('%0.3f' % x for x in reversed(means[3:])))
print(', '.join('%0.3f' % x for x in reversed(bilinear_medians[3:])))
    

