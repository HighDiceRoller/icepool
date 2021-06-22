import numpy

symbol_x = [0, 1]
symbol_y = [-1, 0, 1]
die_size = 6

all_faces = []

for x in symbol_x:
    for y in symbol_y:
        all_faces.append([x, y])

def iter_dice(partial = []):
    if len(partial) == die_size:
        yield numpy.array([all_faces[i] for i in partial])
        return
    if len(partial) == 0:
        start = 0
    else:
        start = partial[-1]
    for i in range(start, len(all_faces)):
        yield from iter_dice(partial + [i])

result = ','.join('Face %d' % x for x in range(1, die_size+1))
result += ',Mean X,Var X,SD X,Var/Mean X,Mean Y,Var Y,SD Y,Var/Mean Y,Cov XY,Corr XY\n'

for die in iter_dice():
    total = numpy.sum(die, axis=0)
    
    mean = total / die_size
    deviation = die - mean
    variance = numpy.sum(deviation * deviation, axis=0) / die_size
    if numpy.any(variance == 0.0): continue
    sd = numpy.sqrt(variance)
    covariance = numpy.sum(deviation[:, :, None] * deviation[:, None, :], axis=0) / die_size
    correlation = covariance / (sd[:, None] * sd[None, :])
    abs_xy_correlation = numpy.abs(correlation[0, 1])
    if abs_xy_correlation <= 1e-12 or abs_xy_correlation >= 1 - 1e-12: continue
    result += ','.join('%s%s' % (['', 'X'][face[0]], ['', 'Y', '-Y'][face[1]]) for face in die)
    result += (',%0.3f' * 10) % (
        mean[0], variance[0], sd[0], variance[0] / mean[0],
        mean[1], variance[1], sd[1], variance[1] / mean[1],
        covariance[0, 1], correlation[0, 1])
    result += '\n'

with open('output/multivariate_d6.csv', mode='w') as outfile:
    outfile.write(result)
    
    

    
