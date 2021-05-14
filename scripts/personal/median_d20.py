from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

for i in range(3, 22, 2):
    median = Die.d(20).repeat_and_keep_and_sum(i, keep_middle=1)
    adv = Die.d(20).advantage(i)
    print('%dd20' % i)
    print(median.standard_deviation())
    print(adv.standard_deviation())

multi_median = Die.d(20)
for i in range(3):
    multi_median = multi_median.repeat_and_keep_and_sum(3, keep_middle=1)
    print('multimedian steps:', i+1)
    print(multi_median, multi_median.standard_deviation())

print(Die.d(20).repeat_and_keep_and_sum(3, keep_middle=1).repeat_and_keep_and_sum(7, keep_middle=1).standard_deviation())
