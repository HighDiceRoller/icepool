import sortedcontainers
from sortedcontainers import SortedDict

class DieDataDict(SortedDict):
    def __getitem__(self, outcome):
        return self.get(outcome, 0)
