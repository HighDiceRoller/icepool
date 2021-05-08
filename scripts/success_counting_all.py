from hdroller import Die
import numpy

def iter_standard_dice():
    for die_size in [3, 4, 5, 6, 7, 8, 9, 10, 12]:
        metadata = {
            'size' : die_size,
            'threshold' : 0,
            'feature' : 'standard die',
            'faces' : [str(x) for x in range(1, die_size+1)],
            'notes' : '',
        }
        yield Die.d(die_size), metadata

def iter_exploding_dice():
    for die_size in [4, 6, 8, 10, 12]:
        for i in range(1, die_size):
            faces = [0]*i + [1]*(die_size-i)
            for num_explode in range(0, die_size-i+1):
                metadata = {
                    'size' : die_size,
                    'threshold' : i+1,
                    'feature' : 'none',
                    'faces' : [str(x) for x in faces],
                    'notes' : '',
                    }
                if num_explode == 1:
                    metadata['feature'] = 'explode on %d' % die_size
                elif num_explode == (die_size-i):
                    metadata['feature'] = 'explode on any success'
                elif num_explode > 0:
                    metadata['feature'] = 'explode on %d+' % (die_size - num_explode + 1)
                for j in range(num_explode):
                    metadata['faces'][-1-j] += '!'
                if die_size == 10 and i == 7 and num_explode == 1: metadata['notes'] = 'New World of Darkness'
                yield Die.from_faces(faces).explode(200, chance=num_explode/die_size), metadata
        

def iter_simple_dice(die_size):
    # standard die
    metadata = {
        'size' : die_size,
        'threshold' : 0,
        'feature' : 'standard die',
        'faces' : [str(x) for x in range(1, die_size+1)],
        'notes' : '',
    }
    yield Die.d(die_size), metadata
    # exploding standard die (problem: VMR too high to be useful)
    """
    metadata = {
        'size' : die_size,
        'threshold' : 0,
        'feature' : 'exploding standard die',
        'faces' : [str(x) for x in range(1, die_size+1)],
        'notes' : '',
    }
    metadata['faces'][-1] += '!'
    yield Die.d(die_size).explode(10), metadata
    """
    # odd standard dice
    if die_size % 2 == 0 and die_size >= 6 and die_size <= 10:
        metadata = {
            'size' : die_size-1,
            'threshold' : 0,
            'feature' : 'standard die',
            'faces' : [str(x) for x in range(1, die_size-1+1)],
            'notes' : '',
        }
        yield Die.d(die_size-1), metadata
    # no feature
    for i in range(1, die_size):
        faces = [0]*i + [1]*(die_size-i)
        metadata = {
            'size' : die_size,
            'threshold' : i+1,
            'feature' : 'none',
            'faces' : [str(x) for x in faces],
            'notes' : '',
            }
        if die_size == 6 and i == 3: metadata['notes'] = 'Burning Wheel'
        if die_size == 6 and i == 4: metadata['notes'] = 'Shadowrun 4e'
        yield Die.from_faces(faces), metadata
    # negative on 1
    for i in range(2, die_size):
        faces = [-1] + [0]*(i-1) + [1]*(die_size-i)
        metadata = {
            'size' : die_size,
            'threshold' : i+1,
            'feature' : '-1 success on bottom face',
            'faces' : [str(x) for x in faces],
            'notes' : '',
            }
        if die_size == 10 and i == 6: metadata['notes'] = 'Old World of Darkness'
        yield Die.from_faces(faces), metadata
    # double on max
    for i in range(1, die_size-1):
        faces = [0]*i + [1]*(die_size-i-1) + [2]
        metadata = {
            'size' : die_size,
            'threshold' : i+1,
            'feature' : '2 successes on top face',
            'faces' : [str(x) for x in faces],
            'notes' : '',
            }
        if die_size == 10 and i == 6: metadata['notes'] = 'Exalted 2e'
        yield Die.from_faces(faces), metadata
    # explode
    for i in range(1, die_size):
        faces = [0]*i + [1]*(die_size-i)
        metadata = {
            'size' : die_size,
            'threshold' : i+1,
            'feature' : 'explode on top face',
            'faces' : [str(x) for x in faces],
            'notes' : '',
            }
        metadata['faces'][-1] += '!'
        if die_size == 10 and i == 7: metadata['notes'] = 'New World of Darkness'
        yield Die.from_faces(faces).explode(100, chance=1/die_size), metadata
    """
    # all explode
    for i in range(die_size * 3 // 4, die_size-2):
        faces = [0]*i + [1]*(die_size-i)
        metadata = {
            'size' : die_size,
            'threshold' : i+1,
            'feature' : 'explode on any success',
            'faces' : ['0']*i + ['1!']*(die_size-i),
            'notes' : '',
            }
        yield Die.from_faces(faces).explode(10), metadata
        
    # mid explode
    for i in range(1, die_size):
        faces = [0]*i + [1]*(die_size-i)
        for num_explode in range(1, die_size-i-1):
            metadata = {
                'size' : die_size,
                'threshold' : i+1,
                'feature' : 'explode on top %d faces' % num_explode,
                'faces' : [str(x) for x in faces],
                'notes' : '',
                }
            for j in range(num_explode):
                metadata['faces'][-1-j] += '!'
            yield Die.from_faces(faces).explode(10, chance=num_explode/die_size), metadata
    """


output_header = 'Die,TN,Special,Mean,Var,Var/Mean,SD,SD/Mean,Faces'+','*12+'Notes\n'
def make_output_row(die, metadata):
    metadata['mean'] = die.mean()
    metadata['variance'] = die.variance()
    metadata['d'] = die.variance() / die.mean()
    metadata['standard_deviation'] = die.standard_deviation()
    metadata['cv'] = die.standard_deviation() / die.mean()
    result = 'd%(size)d,%(threshold)d+,%(feature)s,%(mean)0.3f,%(variance)0.3f,%(d)0.3f,%(standard_deviation)0.3f,%(cv)0.3f' % metadata
    result += ''.join(',%s' % face for face in metadata['faces'])
    result += ',' * (12 - die_size)
    result += ',%(notes)s' % metadata
    result += '\n'
    return result
    
output = output_header
for die_size in [3, 4, 6, 8, 10, 12]:
    for die, metadata in iter_simple_dice(die_size):
        output += make_output_row(die, metadata)

with open('output/success_counting.csv', mode='w') as f:
    f.write(output)

output = output_header
for die, metadata in list(iter_standard_dice()) + list(iter_exploding_dice()):
    output += make_output_row(die, metadata)

with open('output/success_counting_explode.csv', mode='w') as f:
    f.write(output)
