import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt

max_pluses = 2 # 0-2 bonus to attack and damage (not counting the initial +1) (40%)
max_minors = 19 # minor properties (40%)
max_twos = 5 # non-damage 2% properties: finesse, thrown, defender, flash, spell storing
max_crit = 1 # enhanced critical range (4%)
max_ones = 2 # non-damage 1% properties: shadow, vorpal

max_values = (max_pluses, max_minors, max_twos, max_crit, max_ones)
state_size = tuple(x+1 for x in max_values)

# compute tensors
# chance of going from state -> state
transition = numpy.zeros(state_size * 2)
# number of nonrepeatable runes
nonrepeatable_counts = numpy.zeros(state_size, dtype=int)
for state in numpy.ndindex(*state_size):
    plus, minors, twos, crit, ones = state

    # relative chances of rolling each result
    # accounting for nonrepeatables being eliminated from the table
    plus_weight = (plus < max_pluses) * 40
    minor_weight = (minors < max_minors) * 40
    twos_weight = (max_twos - twos) * 2
    crit_weight = (crit == 0) * 4
    ones_weight = max_ones - ones
    repeatable_weight = 4

    total_weight = plus_weight + minor_weight + twos_weight + crit_weight + ones_weight + repeatable_weight

    if plus_weight > 0:
        next_state = (plus+1, minors, twos, crit, ones)
        transition[state + next_state] += plus_weight / total_weight
    if minor_weight > 0:
        next_state = (plus, minors+1, twos, crit, ones)
        transition[state + next_state] += minor_weight / total_weight
    if twos_weight > 0:
        next_state = (plus, minors, twos+1, crit, ones)
        transition[state + next_state] += twos_weight / total_weight
    if crit_weight > 0:
        next_state = (plus, minors, twos, 1, ones)
        transition[state + next_state] += crit_weight / total_weight
    if ones_weight > 0:
        next_state = (plus, minors, twos, crit, ones+1)
        transition[state + next_state] += ones_weight / total_weight

    # default case: rolled a repeatable
    # repeatables are kept track implicitly by subtracting the number of nonrepeatable runes
    # from the total number of runes
    transition[state + state] += repeatable_weight / total_weight

    nonrepeatable_counts[state] = sum(state)
    
# initial state: 100% no properties
dist = numpy.zeros(state_size)
dist[tuple(0 for x in state_size)] = 1.0

flat_damage_by_plus = numpy.array([1.0, 2.0, 3.0])
mean_damage_per_repeatable = (3.5 + 3.5 / 14) / 2

max_runes = 50
mean_damages = numpy.zeros((max_runes+1,))

for rune_count in range(max_runes+1):
    repeatable_counts = rune_count - nonrepeatable_counts
    dice_damages = repeatable_counts * mean_damage_per_repeatable + 3.5
    dice_damages_weighted = dist * dice_damages

    # 20/19 and 21/19 are the multipliers to mean damage given by the critical range,
    # conditioned on a hit assuming hitting on a 2+.
    mean_dice_damage = (
        numpy.sum(dice_damages_weighted[:, :, :, 0, :]) * 20/19 +
        numpy.sum(dice_damages_weighted[:, :, :, 1, :]) * 21/19
        )

    # marginal distribution of plusses
    dist_plus = numpy.sum(dist, axis=tuple(range(1, len(state_size))))
    mean_flat_damage = numpy.dot(flat_damage_by_plus, dist_plus)
    
    mean_damage = mean_dice_damage + mean_flat_damage
    mean_damages[rune_count] = mean_damage

    line = '| %d | %0.3f | %0.3f | %0.3f |' % (rune_count, mean_dice_damage, mean_flat_damage, mean_damage)

    print(line)
    
    # transition to the next distribution
    dist = numpy.tensordot(dist, transition, axes=len(state_size))

figsize = (8, 4.5)
dpi = 120

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid(True)

ax.plot(numpy.arange(max_runes+1), mean_damages)
ax.set_xlim(0, max_runes)
ax.set_ylim(0)
ax.set_xlabel('Runes past first')
ax.set_ylabel('Mean damage')
plt.savefig('output/moonblade.png', dpi = dpi, bbox_inches = "tight")
