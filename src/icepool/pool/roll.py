__docformat__ = 'google'

import icepool
from icepool.collections import Counts

from collections import defaultdict
from functools import cached_property
import math


def _is_dict(arg):
    return hasattr(arg, 'keys') and hasattr(arg, 'items') and hasattr(
        arg, '__getitem__')


class PoolRoll(icepool.PoolBase):
    """Represents a single, fixed roll of a dice pool.

    Like `Pool`, this may be used as an argument to `EvalPool`.

    `PoolRoll` is only needed internally, as external dicts and sequences
    will be implicitly converted to `PoolRoll` in `EvalPool.eval()`.
    """

    def __init__(self, arg, /):
        """
        Args:
            arg: One of the following:
                * A dict-like, mapping outcomes to counts.
                * A sequence of outcomes, which are treated as having count 1
                    per appearance.
        """
        data = defaultdict(int)
        if _is_dict(arg):
            for outcome, count in arg.items():
                data[outcome] += count
        else:
            for outcome in arg:
                data[outcome] += 1

        self._data = Counts(sorted(data.items()))

    def _is_single_roll(self):
        return True

    def _has_truncate_min(self):
        return False

    def _has_truncate_max(self):
        return False

    def outcomes(self):
        return self._data.keys()

    def _min_outcome(self):
        return self._data.keys()[0]

    def _max_outcome(self):
        return self._data.keys()[-1]

    def _direction_score_ascending(self):
        return 0

    def _direction_score_descending(self):
        return 0

    def _pop_min(self):
        data = {outcome: count for outcome, count in self._data.items()[1:]}
        count = self._data.values()[0]
        return (PoolRoll(data), count, 1),

    def _pop_max(self):
        data = {outcome: count for outcome, count in self._data.items()[:-1]}
        count = self._data.values()[-1]
        return (PoolRoll(data), count, 1),

    # Forwarding dict-like methods.

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def __getitem__(self, key):
        return self._data[key]

    def __str__(self):
        return f'PoolRoll({str(self._data)})'

    @cached_property
    def _key_tuple(self):
        return self._data.items()

    def __eq__(self, other):
        try:
            other = icepool.PoolRoll(other)
        except TypeError:
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self):
        return hash(self._key_tuple)

    def __hash__(self):
        return self._hash
