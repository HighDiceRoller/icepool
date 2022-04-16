import _context

from icepool import Die

import time

start_time = time.perf_counter()

max_explode = 20

dice = []

for explode_faces in [0, 1, 2]:
    for emphasis in [False, True]:
        die = Die.d10
        if explode_faces > 0:
            die = die.explode(max_explode, faces=explode_faces)
        if emphasis:
            die = die.reroll(outcomes=1, max_rerolls=1)
        dice.append(((explode_faces, emphasis), die))

rk_dice = []

for e, die in dice:
    for r in range(1, 11):
        for k in range(1, r + 1):
            rk_die = die.keep_highest(r, k)
            rk_dice.append(((r, k), e, rk_die))

end_time = time.perf_counter()
print('Computation time:', end_time-start_time)

result = 'Roll,Keep,Explode,Empahsis,Mean,SD'
for i in range(1, 111): result += ',%d' % i
result += '\n'

explode_strings = [
    'none',
    '10',
    '9-10',
]

for (r, k), (explode_faces, emphasis), rk_die in rk_dice:
    result += '%d,%d' % (r, k)
    result += ',' + explode_strings[explode_faces]
    result += ',%d' % emphasis
    result += ',%.10f' % rk_die.mean()
    result += ',%.10f' % rk_die.standard_deviation()
    for i in range(0, min(110, len(rk_die))):
        result += ',%.10f%%' % (rk_die.pmf()[i] * 100.0)
    result += '\n'

with open('output/lynks_se.csv', mode='w') as outfile:
    outfile.write(result)
