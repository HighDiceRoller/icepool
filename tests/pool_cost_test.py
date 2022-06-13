import _context

import icepool
import pytest

from icepool import d4, d6, d8, d10, d12
import icepool.pool_cost

def test_pool_single_type():
    pool = icepool.Pool(d6, d6, d6)
    pop_min_cost, pop_max_cost = icepool.pool_cost.estimate_costs(pool)
    assert pop_min_cost == pop_max_cost

def test_pool_standard():
    pool = icepool.Pool(d8, d12, d6)
    pop_min_cost, pop_max_cost = icepool.pool_cost.estimate_costs(pool)
    assert pop_min_cost > pop_max_cost

def test_pool_standard_negative():
    pool = icepool.Pool(-d8, -d12, -d6)
    pop_min_cost, pop_max_cost = icepool.pool_cost.estimate_costs(pool)
    assert pop_min_cost < pop_max_cost
    
def test_pool_non_truncate():
    pool = icepool.Pool(-d8, d12, -d6)
    pop_min_cost, pop_max_cost = icepool.pool_cost.estimate_costs(pool)
    assert pop_min_cost == pop_max_cost

def test_pool_skip_min():
    pool = icepool.Pool(d6, d6, d6)[0,1,1]
    pop_min_cost, pop_max_cost = icepool.pool_cost.estimate_costs(pool)
    assert pop_min_cost > pop_max_cost

def test_pool_skip_max():
    pool = icepool.Pool(d6, d6, d6)[1,1,0]
    pop_min_cost, pop_max_cost = icepool.pool_cost.estimate_costs(pool)
    assert pop_min_cost < pop_max_cost

def test_pool_skip_min_but_truncate():
    pool = icepool.Pool(-d6, -d6, -d8)[0,1,1]
    pop_min_cost, pop_max_cost = icepool.pool_cost.estimate_costs(pool)
    assert pop_min_cost < pop_max_cost

def test_pool_skip_max_but_truncate():
    pool = icepool.Pool(d6, d6, d8)[1,1,0]
    pop_min_cost, pop_max_cost = icepool.pool_cost.estimate_costs(pool)
    assert pop_min_cost > pop_max_cost
