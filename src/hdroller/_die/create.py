import hdroller
import hdroller._die.base
import hdroller._die.single
import hdroller._die.multi
from hdroller.containers import DieDataDict

def die(data, min_outcome=None, *, force_single=False):
    """
    Args:
        data: This can be one of the following:
            A die, which will be returned itself.
            An iterable of weights, with min_outcome set to an integer.
                The outcomes will be integers starting at min_outcome.
            A mapping from outcomes to weights.
            An iterable of pairs of outcomes and weights.
            A single hashable and comparable value.
                There will be a single outcome equal to the argument, with weight 1.
        force_single: If True, the die is treated as univariate even if its outcomes are iterable.
    """
    if isinstance(data, hdroller._die.base.BaseDie):
        return data
    elif min_outcome is not None:
        data = DieDataDict(((min_outcome + i, weight) for i, weight in enumerate(data) if weight > 0))
    else:
        try:
            # TODO: Filter zeros.
            data = DieDataDict(data)
        except TypeError:
            data = DieDataDict({data : 1})
    
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

def from_cweights(data, min_outcome=None, *, force_single=False):
    raise NotImplementedError()
    
def from_sweights(data, min_outcome=None, *, force_single=False):
    raise NotImplementedError()

def from_rv(rv, outcomes, d):
    raise NotImplementedError()
# from_cweights
# from_sweights
# from_rv
