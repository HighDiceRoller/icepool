__docformat__ = 'google'

import hdroller
from hdroller.collections import Weights

from collections import defaultdict
import math

def Die(*args, weights=None, min_outcome=None, ndim=None, total_weight_method='lcm'):
    """ Factory for constructing a die.
    
    This is capitalized because it is the preferred way of getting a new instance,
    and so that you can use `from hdroller import Die` while leaving the name `die` free.
    The actual class of the result will be one of the subclasses of `BaseDie`.
    
    Don't confuse this with `hdroller.d()`:
    
    * `hdroller.Die(6)`: A die that always rolls the `int` 6.
    * `hdroller.d(6)`: A d6.
    
    Args:
        *args: Each of these arguments can be one of the following:
            * A single outcome, which must be hashable and comparable.
                The same outcome can appear multiple times,
                in which case it will be weighted proportionally higher.
            
                Note: An argument that is a sequence will be treated as a single outcome.
                If you want each element in the sequence to be a separate outcome,
                you need to unpack it into separate arguments.
            * A die. The `ndim` of the die must be preserved, or this is a `ValueError`.
            * A dict-like that maps outcomes to weights.
                This option will be taken in preference to treating the dict-like itself as an outcome
                even if the dict-like itself is hashable and comparable.
                If you want to use the dict-like itself as an outcome (not recommended), wrap it in another dict.
            * `hdroller.Reroll`, which will drop itself
                and the corresponding element of `weights` from consideration.
        weights: Controls the relative weight of the arguments.
            If not provided, each argument will have the same total weight.
            For example, `Die(d6, 7)` is the same as `Die(1, 2, 3, 4, 5, 6, 7, 7, 7, 7, 7, 7)`.
        min_outcome: If used, there must be zero `*args` and `weights` must be provided.
            The outcomes of the result will be integers starting at `min_outcome`,
            one per weight in `weights` with that weight.
        ndim: If set to `'scalar'`, the die will be forced to be scalar.
            If set to an `int`, the die will be forced to be vector with that number of dimensions.
            If not provided, this will be automatically detected.
            E.g. for `str` outcomes you may want to set `ndim='scalar'`, which will
            treat e.g. `'abc' as a single string rather than `('a', 'b', 'c')`.
        total_weight_method: How to determine the total weight of the result if the arguments themselves contain weights.
            From greatest to least:
            * 'prod': Product of the individual argument weights, times the total of `weights`.
                This is like rolling all of the possible dice, and then selecting a result.
            * 'lcm' (default): LCM of the individual argument weights, times the total of `weights`.
                This is like rolling `weights` first, then selecting an argument to roll.
            * 'lcm_weighted': LCM of the individual (argument weights times corresponding element of `weights`).
                This is like rolling the above, but the specific weight rolled
                is used to help determine the result of the selected argument.
    Raises:
        `ValueError` if `ndim` is set but is not consistent with `*args`,
            or there is a mismatch between the `ndim` of die arguments.
            Furthermore, `None` is not a valid outcome for a die.
    """
    
    if min_outcome is not None:
        if weights is None:
            raise ValueError('If min_outcome is provided, weights must also be provided.')
        if len(args) > 0:
            raise ValueError('If min_outcome is provided, no *args may be used.')
        if ndim not in [None, 'scalar']:
            raise ValueError('If min_outcome is provided, the result may only be a scalar die.')
        data = Weights({i + min_outcome : weight for i, weight in enumerate(weights)})
        return hdroller.ScalarDie(data)
    
    if weights is not None:
        if len(weights) != len(args):
            raise ValueError('If weights are provided, there must be exactly one weight per argument.')
    else:
        weights = (1,) * len(args)
    
    # Remove rerolls.
    args, weights = zip(*((arg, weight) for arg, weight in zip(args, weights) if arg is not hdroller.Reroll))
    for arg in args:
        if _is_dict(arg):
            arg.pop(hdroller.Reroll, None)
    
    # Total weights.
    arg_total_weights = [_arg_total_weight(arg) for arg in args]
    
    if total_weight_method == 'prod':
        weight_product = math.prod(arg_total_weights)
    elif total_weight_method == 'lcm':
        weight_product = math.lcm(*arg_total_weights)
    elif total_weight_method == 'lcm_weighted':
        weight_product = math.lcm(*[atw * w for atw, w in zip(arg_total_weights, weights)])
    else:
        raise ValueError(f'Invalid total_weight_method {total_weight_method}.')    
    
    # Compute ndim.
    ndim = _calc_ndim(*args)
    
    # Make data.
    data = defaultdict(int)
    for arg, atw, w in zip(args, arg_total_weights, weights):
        factor = weight_product * w // atw if atw else 0
        if _is_die(arg) or _is_dict(arg):
            for outcome, weight in arg.items():
                data[outcome] += weight * factor
        else:
            data[arg] += factor
    
    for arg in args:
        ndim = _arg_ndim(arg, ndim)
    
    if ndim is None:
        ndim = 'scalar'
    
    if ndim == 'scalar':
        data = Weights(data)
        return hdroller.ScalarDie(data)
    else:
        data = Weights({ tuple(k) : v for k, v in data.items() })
        return hdroller.VectorDie(data, ndim)

def _is_die(arg):
    return isinstance(arg, hdroller.BaseDie)

def _is_dict(arg):
    return hasattr(arg, 'keys') and hasattr(arg, 'items') and hasattr(arg, '__getitem__') and hasattr(arg, 'pop')

def _is_seq(arg):
    return hasattr(arg, '__len__')

def _arg_total_weight(arg):
    if _is_die(arg):
        return arg.total_weight()
    elif _is_dict(arg):
        return sum(arg.values())
    else:
        return 1

def _calc_ndim(*args, ndim=None):
    """ Computes the common `ndim` of the arguments. 
    
    Args:
        *args: Args to find the common `ndim` of.
        ndim: The required ndim of the results.
    
    Returns:
        The common `ndim` of the arguments.  
        May return `None` if no `ndim` is found.
    
    Raises:
        `ValueError` if the arguments include conflicting `ndim`s.
    """
    for arg in args:
        ndim = _arg_ndim(arg, ndim)
    return ndim 

def _arg_ndim(arg, ndim):
    """ Checks the ndim of a single argument. """
    if _is_die(arg):
        if arg.is_empty():
            return ndim
        elif ndim is None:
            return arg.ndim()
        elif arg.ndim() != ndim:
            raise ValueError(f'Argument die has ndim={arg.ndim()} inconsistent with other ndim={ndim}.')
        return ndim
    elif ndim == 'scalar':
        return 'scalar'
    elif _is_dict(arg):
        for outcome in arg.keys():
            if hasattr(outcome, '__len__'):
                if ndim is None:
                    ndim = len(outcome)
                elif len(outcome) != ndim:
                    return 'scalar'
        return ndim
    elif _is_seq(arg):
        # Arg is a sequence.
        if ndim is None:
            return len(arg)
        elif len(arg) != ndim:
            return 'scalar'
        else:
            return ndim
    else:
        # Arg is a scalar.
        return 'scalar'

def dice_with_common_ndim(*args, ndim=None):
    """ Converts the arguments to dice with a common `ndim`.
    
    Args:
        *args: Args to be converted to dice.
        ndim: The required `ndim` of the results.
    
    Returns:
        dice, ndim: A tuple containing one die per arg, and the common `ndim`,
    
    Raises:
        `ValueError` if the arguments include conflicting `ndim`s.
    """
    ndim = _calc_ndim(*args, ndim)
    return tuple(Die(arg, ndim=ndim) for arg in args), ndim
