import _context

from hdroller import Die
import numpy

class BruteForceCounter():
    def __init__(self):
        self.data = {}
        
    def insert(self, outcome, mass):
        if outcome not in self.data: self.data[outcome] = mass
        else: self.data[outcome] += mass
        
    def die(self):
        min_outcome = min(self.data.keys())
        max_outcome = max(self.data.keys())
        pmf = numpy.zeros((max_outcome - min_outcome + 1,))
        for outcome, mass in self.data.items():
            pmf[outcome - min_outcome] += mass
        die = Die(pmf, min_outcome)
        return die
        

