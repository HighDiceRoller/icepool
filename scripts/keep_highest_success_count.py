import numpy
from scipy.special import factorial

cdf = 0.0
attack_ratio = 4.0

for k in range(6):
    print(k, (1.0 - numpy.power(0.5, attack_ratio)) / (1.0 - cdf))
    cdf += numpy.power(0.5, attack_ratio) * numpy.power(attack_ratio * numpy.log(2.0), k) / factorial(k)
