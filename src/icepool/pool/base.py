__docformat__ = 'google'

import icepool

from abc import ABC, abstractmethod

class BasePool(ABC):
    """ Abstract base class for dice pools.
    
    This provides the methods needed to run the dice pool algorithm.
    
    There are two subclasses:
    
    * `DicePool`, which represents a pool of dice with random results.
    * `PoolRoll`, which represents a single, fixed roll of a pool.
    """
    
    @abstractmethod
    def _is_single_roll(self):
        """ Returns `True` iff this is a single, fixed roll of a pool. """
    
    @abstractmethod
    def _has_max_outcomes(self):
        """ Returns `True` iff the pool has right-truncation. """
        
    @abstractmethod
    def _has_min_outcomes(self):
        """ Returns `True` iff the pool has left-truncation. """
    
    @abstractmethod
    def outcomes(self):
        """ The outcomes of the fundamental die (including those with zero weight). """
        
    @abstractmethod
    def _max_outcome(self):
        """ The maximum outcome of the fundamental die. """
        
    @abstractmethod
    def _min_outcome(self):
        """ The minimum outcome of the fundamental die. """
    
    @abstractmethod
    def _pop_max(self):
        """ Returns a sequence of pool, count, weight corresponding to removing the max outcome,
        with count and weight corresponding to various numbers of dice rolling that outcome.
        """
    
    @abstractmethod
    def _pop_min(self):
        """ Returns a sequence of pool, count, weight corresponding to removing the min outcome,
        with count and weight corresponding to various numbers of dice rolling that outcome.
        """
