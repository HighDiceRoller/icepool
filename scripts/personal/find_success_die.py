from icepool import Die
import numpy

def iter_faces(die_size):
    for i in range(1, die_size):
        yield [0] * i + [1] * (die_size - i)
    for i in range(1, die_size-1):
        yield [-1] + [0] * i + [1] * (die_size - 1 - i)
        yield [0] * i + [1] * (die_size - 1 - i) + [2]
    for i in range(1, die_size-2):
        pass
        #yield [-1] + [0] * i + [1] * (die_size - 2 - i) + [2]

def iter_double_success(die_size):
    for i in range(1, die_size-1):
        for j in range(i+1, die_size-1):
            name = 'success on %d+, double success on %d+' % (i+1, j+1)
            yield Die.from_faces([0]*i + [1]*(j-i) + [2]*(die_size-i-j)).rename(name)

def iter_negative_success(die_size):
    for i in range(1, die_size-1):
        for j in range(i+1, die_size-1):
            name = 'success on %d+, negative success on %d or lower' % (j+1, i)
            yield Die.from_faces([-1]*i + [0]*(j-i) + [1]*(die_size-i-j)).rename(name)

def iter_explode(die_size):
    for i in range(1, die_size-1):
        for j in range(i+1, die_size-1):
            name = 'success on %d+, explode on %d+' % (i+1, j+1)
            explode_chance = (die_size-j)/die_size
            yield Die.from_faces([0]*i + [1]*(die_size-i)).explode(10, chance=explode_chance).rename(name)

def iter_dice(die_size, explode):
    for faces in iter_faces(die_size):
        base_die = Die.from_faces(faces)
        if not explode:
            yield base_die.rename('d' + str(die_size) + str(faces))
        else:
            if faces[0] == -1: return
            max_explode = min(faces.count(1) // 2, faces.count(0), die_size // 4)
            for explode_faces in range(1, max_explode+1):
                if faces[-explode_faces] != 1: break
                explode_chance = explode_faces / die_size
                yield base_die.explode(10, chance=explode_chance).rename(
                    'd%d%s!%s' % (die_size, faces, explode_faces))

mean_tol_factor = 0.15 + 1e-6
variance_tol_factor = 0.3 + 1e-6

exchange_dice = [
    Die.d4,
    Die.d6,
    Die.d8,
    Die.d10,
    Die.d12,
    ]

explode = False

exchange_dice += [die.explode(10) for die in exchange_dice]

for exchange_die in exchange_dice:
    for exchange_count in numpy.arange(1, 11.1, 1):
        target_mean = exchange_die.mean() / exchange_count
        #if target_mean != 0.5: continue
        #if target_mean < 1.0 or target_mean > 1.11: continue
        target_variance = exchange_die.variance() / exchange_count
        tol_mean = target_mean * mean_tol_factor
        tol_variance = target_variance * variance_tol_factor

        found_any = False

        for die_size in [4, 6, 8, 10, 12]:
            for die in iter_dice(die_size, explode):
                if die.mean() <= 0.0: continue
                if (die.mean() <= target_mean + 1e-6 and die.mean() > target_mean - tol_mean and
                    abs(die.variance() - target_variance) <= tol_variance):
                    if not found_any:
                        print('%s vs. %0.1f (mean %0.3f, variance %0.3f)' % (exchange_die.name(), exchange_count, target_mean, target_variance))
                        found_any = True
                    print('  %0.3f' % die.mean(), '%0.3f' % die.variance(), die.name())

