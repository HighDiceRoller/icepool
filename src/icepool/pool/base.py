__docformat__ = 'google'

import icepool

from abc import ABC, abstractmethod

class BasePool(ABC):
    @abstractmethod
    def max_outcomes(self):
        """ """
        
    @abstractmethod
    def min_outcomes(self):
        """ """
    
    @abstractmethod
    def num_outcomes(self):
        """ """
        
    @abstractmethod
    def _max_outcome(self):
        """ """
        
    @abstractmethod
    def _min_outcome(self):
        """ """
    
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
