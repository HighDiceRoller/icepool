__docformat__ = 'google'

import hdroller
from hdroller.collections import Weights

from collections import defaultdict
import math

def Die(*args, weights=None, min_outcome=None, ndim=None, denominator_method='lcm'):
    """ Factory for constructing a die.
    
    This is capitalized because it is the preferred way of getting a new instance,
    and so that you can use `from hdroller import Die` while leaving the name `die` free.
    The actual class of the result will be one of the subclasses of `BaseDie`.
    
    Don't confuse this with `hdroller.d()`:
    
    * `hdroller.Die(6)`: A die that always rolls the `int` 6.
    * `hdroller.d(6)`: A d6.
    
    Here are some different ways of constructing a d6:
    
    * Just import it: `from hdroller import d6`
    * Use the `d()` function: `hdroller.d(6)`
    * Use a d6 that you already have: `Die(d6)`
    * Mix a d3 and a d3+3: `Die(d3, d3+3)`
    * Use a dict: `Die({1:1, 2:1, 3:1, 4:1, 5:1, 6:1})`
    * Give the faces as args: `Die(1, 2, 3, 4, 5, 6)`
    
    Args:
        *args: Each of these arguments can be one of the following:
            * A single outcome, which must be hashable and comparable.
                The same outcome can appear multiple times,
                in which case it will be weighted proportionally higher.
            
                Note: An argument that is a sequence will be treated as a single outcome.
                If you want each element in the sequence to be a separate outcome,
                you need to unpack it into separate arguments.
            * A die. The `ndim` of the die must be preserved, or this is a `ValueError`.
                The outcomes of the die will be "flattened" in the result die.
            * A dict-like that maps outcomes to weights.
                This option will be taken in preference to treating the dict-like itself as an outcome
                even if the dict-like itself is hashable and comparable.
                
                Not recommended options:
                
                * If you want to use the dict-like itself as an outcome, wrap it in another dict.
                * The dict itself can contain `hdroller.Reroll`.
                    This will only reroll within the dict, not the entire construction.
            * `hdroller.Reroll`, which will drop itself
                and the corresponding element of `weights` from consideration.
        weights: Controls the relative weight of the arguments.
            If not provided, each argument will end up with the same total weight,
            unless they have zero weight to begin with.
            For example, `Die(d6, 7)` is the same as `Die(1, 2, 3, 4, 5, 6, 7, 7, 7, 7, 7, 7)`.
        min_outcome: If used, there must be zero `*args` and `weights` must be provided.
            The outcomes of the result will be integers starting at `min_outcome`,
            one per weight in `weights` with that weight.
        ndim: If set to `'scalar'`, the die will be forced to be scalar.
            If set to an `int`, the die will be forced to be vector with that number of dimensions.
            If not provided, this will be automatically detected.
            E.g. for `str` outcomes you may want to set `ndim='scalar'`, which will
            treat e.g. `'abc' as a single string rather than `('a', 'b', 'c')`.
        denominator_method: How to determine the denominator of the result
            if the arguments themselves contain weights.
            From greatest to least:
            * 'prod': Product of the individual argument denominators, times the total of `weights`.
                This is like rolling all of the possible dice, and then selecting a result.
            * 'lcm' (default): LCM of the individual argument denominators, times the total of `weights`.
                This is like rolling `weights` first, then selecting an argument to roll.
            * 'lcm_weighted': LCM of the individual (argument denominators times corresponding element of `weights`).
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
    args_weights = tuple(zip(*((arg, weight) for arg, weight in zip(args, weights) if arg is not hdroller.Reroll)))
    if len(args_weights) == 0:
        args, weights = (), ()
    else:
        args, weights = args_weights
    for arg in args:
        if _is_dict(arg) and hdroller.Reroll in arg:
            del arg[hdroller.Reroll]
    
    # Special cases.
    if len(args) == 0:
        return hdroller.EmptyDie()
    elif len(args) == 1 and _is_die(args[0]) and weights[0] == 1:
        # Single unmodified die: just return the existing instance.
        return args[0]
    
    # Total weights.
    arg_denominators = [_arg_denominator(arg) for arg in args]
    
    if denominator_method == 'prod':
        denominator_prod = math.prod(d for d in arg_denominators if d > 0)
    elif denominator_method == 'lcm':
        denominator_prod = math.lcm(*(d for d in arg_denominators if d > 0))
    elif denominator_method == 'lcm_weighted':
        denominator_prod = math.lcm(*(d * w for d, w in zip(arg_denominators, weights) if d > 0))
    else:
        raise ValueError(f'Invalid denominator_method {denominator_method}.')    
    
    # Compute ndim.
    ndim = _calc_ndim(*args)
    
    # Make data.
    data = defaultdict(int)
    for arg, arg_denominator, w in zip(args, arg_denominators, weights):
        factor = denominator_prod * w // arg_denominator if arg_denominator else 0
        if _is_die(arg) or _is_dict(arg):
            for outcome, weight in arg.items():
                data[outcome] += weight * factor
        else:
            data[arg] += factor
    
    for arg in args:
        ndim = _arg_ndim(arg, ndim)
    
    if ndim == 'scalar':
        data = Weights(data)
        return hdroller.ScalarDie(data)
    elif ndim is None:
        # Implicitly ndim = 'empty'.
        return hdroller.EmptyDie()
    else:
        data = Weights({ tuple(k) : v for k, v in data.items() })
        return hdroller.VectorDie(data, ndim)

def _is_die(arg):
    return isinstance(arg, hdroller.BaseDie)

def _is_dict(arg):
    return hasattr(arg, 'keys') and hasattr(arg, 'items') and hasattr(arg, '__getitem__')

def _is_seq(arg):
    return hasattr(arg, '__len__')

def _arg_denominator(arg):
    if _is_die(arg):
        return arg.denominator()
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
            # No recursion to nested dicts.
            if _is_seq(outcome):
                if ndim is None:
                    ndim = len(outcome)
                elif len(outcome) != ndim:
                    return 'scalar'
            else:
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
