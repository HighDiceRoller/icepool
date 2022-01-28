import scipy.stats

distributions = [
    (scipy.stats.uniform, {'loc':-0.5}),
    (scipy.stats.norm, {}),
    (scipy.stats.logistic, {}),
    (scipy.stats.laplace, {}),
    ]

def leapfrog(chance, steps):
    for dist, kwargs in distributions:
        mod = dist.ppf(chance, **kwargs)
        total_mod = mod * steps
        print('%0.2f' % (dist.cdf(total_mod, **kwargs) * 100.0))

leapfrog(0.25, 2)

def inv_leapfrog(single_chance, target_chance):
    for dist, kwargs in distributions:
        single_mod = dist.ppf(single_chance, **kwargs)
        target_mod = dist.ppf(target_chance, **kwargs)
        print('%0.2f' % (target_mod / single_mod))

inv_leapfrog(0.4, 0.05)
