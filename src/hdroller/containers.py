from sortedcontainers import SortedDictionary

class WeightDict(SortedDictionary):
    def __getitem__(self, outcome):
        return self.get(outcome, 0)