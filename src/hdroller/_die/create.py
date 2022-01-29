import hdroller
import hdroller._die.data
import hdroller._die.base
import hdroller._die.single
import hdroller._die.multi

def _die_from_checked_dict(d, *, force_single=False):
    data = hdroller._die.data.DieData(d)
    
    if force_single:
        return hdroller._die.single.SingleDie(data)
    
    ndim = None
    for outcome in data.keys():
        try:
            if ndim is None:
                ndim = len(outcome)
            elif ndim != len(outcome):
                return hdroller._die.single.SingleDie(data)
        except TypeError:
            return hdroller._die.single.SingleDie(data)
    
    return hdroller._die.multi.MultiDie(data)

def die(arg, min_outcome=None, *, force_single=False):
    """
    Args:
        arg: This can be one of the following:
            A die, which will be returned itself.
            An iterable of weights, with min_outcome set to an integer.
                The outcomes will be integers starting at min_outcome.
            A mapping from outcomes to weights.
            An iterable of pairs of outcomes and weights.
            A single hashable and comparable value.
                There will be a single outcome equal to the argument, with weight 1.
        force_single: If True, the die is treated as univariate even if its outcomes are iterable.
    """
    if isinstance(arg, hdroller._die.base.BaseDie):
        return arg
    
    if min_outcome is not None:
        data = {min_outcome + i : weight for i, weight in enumerate(arg) if weight > 0}
    else:
        try:
            data = { k : arg[k] for k in sorted(arg.keys()) if arg[k] > 0 }
        except (AttributeError, TypeError):
            try:
                data = { k : v for k, v in sorted(arg) if v > 0 }
            except TypeError:
                # Treat arg as the only possible value.
                data = {arg : 1}
    
    return _die_from_checked_dict(data, force_single=force_single)

def standard(num_sides):
    return die([1] * num_sides, min_outcome=1)

def __getattr__(key):
    if key[0] == 'd':
        try:
            return standard(int(key[1:]))
        except ValueError:
            pass
    raise AttributeError(key)

def bernoulli(n, d):
    return die({False : d - n, True : d})

def from_cweights(outcomes, cweights, *, force_single=False):
    prev = 0
    d = {}
    for outcome, weight in zip(outcomes, cweights):
        d[outcome] = weight - prev
        prev = weight
    return _die_from_checked_dict(d)
    
def from_sweights(outcomes, sweights, *, force_single=False):
    for i, outcome in enumerate(outcomes):
        if i < len(outcomes) - 1:
            d[outcome] = sweights[i] - sweights[i+1]
        else:
            d[outcome] = sweights[i]
    return _die_from_checked_dict(d)

def from_rv(rv, outcomes, d):
    raise NotImplementedError("TODO")
