import _context

from hdroller import Die
import numpy
        
def repeat_and_sum(die, num_dice):
    return keep_highest(die, num_dice, num_dice)

def keep_highest(die, num_dice, num_keep):
    if num_keep == 0: return Die(0)
    pmf_length = (len(die) - 1) * num_keep + 1
    min_outcome = die.min_outcome() * num_keep
    pmf = numpy.zeros((pmf_length,))
    for rolls in numpy.ndindex((len(die),) * num_dice):
        total = sum(sorted(rolls)[-num_keep:])
        mass = numpy.product(die.pmf()[numpy.array(rolls)])
        pmf[total] += mass
    return Die(pmf, min_outcome)
    
def keep_lowest(die, num_dice, num_keep):
    if num_keep == 0: return Die(0)
    pmf_length = (len(die) - 1) * num_keep + 1
    min_outcome = die.min_outcome() * num_keep
    pmf = numpy.zeros((pmf_length,))
    for rolls in numpy.ndindex((len(die),) * num_dice):
        total = sum(sorted(rolls)[:num_keep])
        mass = numpy.product(die.pmf()[numpy.array(rolls)])
        pmf[total] += mass
    return Die(pmf, min_outcome)

def keep_index(die, num_dice, index):
    pmf = numpy.zeros_like(die.pmf())
    min_outcome = die.min_outcome()
    for rolls in numpy.ndindex((len(die),) * num_dice):
        picked = sorted(rolls)[index]
        mass = numpy.product(die.pmf()[numpy.array(rolls)])
        pmf[picked] += mass
    return Die(pmf, min_outcome)