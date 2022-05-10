__docformat__ = 'google'


def tuple_len(a):
    """Returns the length of a tuple, or `None` if the argument is not a tuple."""
    if type(a) == tuple:
        return len(a)
    else:
        return None


def unary_elementwise(a, op, *args, **kwargs):
    """Applies a unary operation recursively elementwise.

    Specifically, if the argument is a tuple, the operation is performed on
    each element, and the results are placed in a tuple. This is done
    recursively.

    Args:
        op: The unary operation to perform.
        a: The argument to the operation.
        *args, **kwargs: Any additional arguments are provided to `op`.
    """
    if type(a) == tuple:
        return tuple(unary_elementwise(aa, op, *args, **kwargs) for aa in a)
    else:
        return op(a, *args, **kwargs)


def binary_elementwise(a, b, op, *args, **kwargs):
    """Applies a binary operation recursively elementwise.

    Specifically, if the argument is a tuple, the operation is performed on
    each pair of elements, and the results are placed in a tuple. This is done
    recursively.

    Args:
        op: The binary operation to perform.
        a, b: The arguments to the operation.
        *args, **kwargs: Any additional arguments are provided to `op`.

    Raises:
        ValueError: If a tuple is paired with a non-tuple or a tuple of a
            different length.
    """
    a_len = tuple_len(a)
    b_len = tuple_len(b)
    if a_len is None and b_len is None:
        return op(a, b, *args, **kwargs)
    if a_len != b_len:
        if a_len is None:
            raise ValueError(
                'Cannot apply operation elementwise between a non-tuple and a tuple.'
            )
        elif b_len is None:
            raise ValueError(
                'Cannot apply operation elementwise between a tuple and a non-tuple.'
            )
        else:
            raise ValueError(
                f'Cannot apply operation elementwise between tuples of different lengths {a_len} and {b_len}.'
            )
    return tuple(
        binary_elementwise(aa, bb, op, *args, **kwargs) for aa, bb in zip(a, b))
