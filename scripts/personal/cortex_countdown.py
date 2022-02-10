import _context

import numpy
import hdroller
import hdroller.tournament

from functools import cached_property

import time

start_time = time.perf_counter()

max_pool_size = 10
num_drops_and_keeps = [
    [0, 2],
    [1, 3],
    [0, 3],
]
max_keep = max(k for d, k in num_drops_and_keeps)

reference_die = hdroller.d12.sub({1: 0})
base_dice = [12, 10, 8, 6, 4]

gm_pools = [hdroller.d6.sub({1: 0}),
            2 @ hdroller.d6.sub({1: 0}),
            2 @ hdroller.d8.sub({1: 0}),
            2 @ hdroller.d10.sub({1: 0}),
            2 @ hdroller.d12.sub({1: 0})]

class Pool():
    def __init__(self, pool_comp, num_drop, num_keep):
        self.pool_comp = pool_comp
        self.num_drop = num_drop
        self.num_keep = num_keep

    @cached_property
    def size(self):
        return sum(self.pool_comp)

    @cached_property
    def dice(self):
        return sum(([die] * count for die, count in zip(base_dice, self.pool_comp)), [])

    @cached_property
    def sum_die(self):
        result = reference_die.keep_highest(max_outcomes=self.dice, num_keep=self.num_keep, num_drop=self.num_drop)
        return result

    @cached_property
    def hitch_chance(self):
        return reference_die.keep_lowest(max_outcomes=self.dice, num_keep=1).probability(0)

    @cached_property
    def multi_hitch_chance(self):
        return reference_die.keep_lowest(max_outcomes=self.dice, num_keep=2).probability(0)

def iter_pool_comps(max_pool_size, partial=()):
    if len(partial) == 5:
        if sum(partial) >= 1:
            yield partial
        return
    
    for i in range(max_pool_size - sum(partial) + 1):
        yield from iter_pool_comps(max_pool_size, partial + (i,))

def iter_pools(max_pool_size, num_drops_and_keeps):
    for pool_comp in iter_pool_comps(max_pool_size):
        pool_size = sum(pool_comp)
        for num_drop, num_keep in num_drops_and_keeps:
            if pool_size < num_keep + num_drop: continue
            yield Pool(pool_comp, num_drop, num_keep)

pools = [x for x in iter_pools(max_pool_size, num_drops_and_keeps)]

vs_gms = [[pool.sum_die > gm_pool for gm_pool in gm_pools] for pool in pools]

end_time = time.perf_counter()
print('Computation time:', end_time-start_time)

result = 'Total dice,Drop,Keep,d12,d10,d8,d6,d4,Mean,SD,>0 Hitch,>1 Hitch,>1d6,>2d6,>2d8,>2d10,>2d12'
for x in range(12 * max_keep - 1): result += ',>%d' % (x+1)
result += '\n'
for pool, vs_gm in zip(pools, vs_gms):
    result += '%d' % pool.size
    result += (',%d' % pool.num_drop).replace(',', ',')
    result += ',%d' % pool.num_keep
    result += (',%d,%d,%d,%d,%d' % pool.pool_comp).replace(',0', ',')

    result += ',%0.2f' % pool.sum_die.mean()
    result += ',%0.2f' % pool.sum_die.standard_deviation()
    
    result += ',%0.2f%%' % (pool.hitch_chance * 100.0)
    result += ',%0.2f%%' % (pool.multi_hitch_chance * 100.0)
    
    for x in vs_gm: result += ',%0.2f%%' % (x.mean() * 100.0)
    
    for p in pool.sum_die.sf()[1:]: result += ',%0.2f%%' % (p * 100.0)
    result += ',' * (12 * max_keep - pool.sum_die.num_outcomes())
    result += '\n'

with open('output/cortex.csv', mode='w') as outfile:
    outfile.write(result)
