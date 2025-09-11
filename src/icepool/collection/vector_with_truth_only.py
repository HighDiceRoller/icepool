__docformat__ = 'google'

import icepool
from icepool.collection.vector import Vector

from icepool.typing import Outcome, S, T, T_co, U


class VectorWithTruthOnly(Vector[T_co]):

    def __init__(self, truth_value: bool):
        self._truth_value = truth_value

    @property
    def _data(self):
        raise ValueError(
            'The result of a comparison between vectors of different lengths can only be used as a truth value.'
        )

    # Strings.

    def __repr__(self) -> str:
        return type(self).__qualname__ + f'({self._truth_value})'

    def __str__(self) -> str:
        return type(self).__qualname__ + f'({self._truth_value})'
