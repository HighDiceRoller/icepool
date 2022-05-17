__docformat__ = 'google'

import icepool

from abc import ABC, abstractmethod


class PoolBase(ABC):
    """Abstract base class for dice pools.

    This provides the methods needed to run the dice pool algorithm.

    There are two subclasses:

    * `Pool`, which represents a pool of dice with random results.
    * `PoolRoll`, which represents a single, fixed roll of a pool.
        `PoolRoll` is only needed internally, as external dicts and sequences
        will be implicitly converted to `PoolRoll` in `EvalPool.eval()`.
    """

    @abstractmethod
    def _is_single_roll(self):
        """Returns `True` iff this is a single, fixed roll of a pool. """

    @abstractmethod
    def _has_truncate_min(self):
        """Returns `True` iff the pool has truncated min outcomes. """

    @abstractmethod
    def _has_truncate_max(self):
        """Returns `True` iff the pool has truncated max outcomes. """

    @abstractmethod
    def outcomes(self):
        """The outcomes of the fundamental die (including those with zero weight). """

    @abstractmethod
    def _min_outcome(self):
        """The minimum outcome of the fundamental die. """

    @abstractmethod
    def _max_outcome(self):
        """The maximum outcome of the fundamental die. """

    @abstractmethod
    def _direction_score_ascending(self):
        """Returns a number indicating how preferred iterating in the ascending direction is.

        This is only called when there is no truncation.

        If the pool does not care at all about direction, the result is 0.

        The collective score is summed.
        """

    @abstractmethod
    def _direction_score_descending(self):
        """Returns a number indicating how preferred iterating in the descending direction is.

        This is only called when there is no truncation.

        If the pool does not care at all about direction, the result is 0.

        The collective score is summed.
        """

    @abstractmethod
    def _pop_min(self):
        """Returns a sequence of pool, count, weight corresponding to removing
        the min outcome, with count and weight corresponding to various numbers
        of dice rolling that outcome.
        """

    @abstractmethod
    def _pop_max(self):
        """Returns a sequence of pool, count, weight corresponding to removing
        the max outcome, with count and weight corresponding to various numbers
        of dice rolling that outcome.
        """

    def eval(self, eval_or_func, /):
        """Evaluates this pool using the given `EvalPool` or function.

        Note that each `EvalPool` instance carries its own cache;
        if you plan to use an evaluation multiple times,
        you may want to explicitly create an `EvalPool` instance
        rather than passing a function to this method directly.

        Args:
            func: This can be an `EvalPool`, in which case it evaluates the pool
                directly. Or it can be a `EvalPool.next_state()`-like function,
                taking in `state, outcome, *counts` and returning the next state.
                In this case a temporary `WrapFuncEval` is constructed and used
                to evaluate this pool.
        """
        if not isinstance(eval_or_func, icepool.EvalPool):
            eval_or_func = icepool.WrapFuncEval(eval_or_func)
        return eval_or_func.eval(self)

    def sum(self):
        """Convenience method to simply sum the dice in this pool.

        This uses `icepool.sum_pool`.

        Returns:
            A die representing the sum.
        """
        return icepool.sum_pool(self)
