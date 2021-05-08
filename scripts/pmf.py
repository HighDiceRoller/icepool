import numpy

class PMF():
    """
    data is an array containing the probabiity mass function.
    min_face is the minimum face.
    data[face-min_face] is the chance of each face.

    PMFs can have integer or float probabilities.
    integer probabilites can be normalized to floats but not the other way around.
    
    This class is immutable; all operations return a new instance.
    """
    def __init__(self, data, min_face):
        self.data = numpy.array(data)
        self.min_face = min_face
    
    @staticmethod
    def from_faces(faces):
        min_face = numpy.min(faces)
        max_face = numpy.max(faces)
        data = numpy.zeros((max_face - min_face + 1,), dtype=int)
        for face in faces:
            data[face-min_face] += 1
        return PMF(data, min_face)

    @staticmethod
    def from_cdf(cdf, min_face):
        data = numpy.diff(numpy.concatenate(([0], cdf)))
        return PMF(data, min_face)

    @staticmethod
    def from_ccdf(ccdf, min_face):
        data = numpy.flip(numpy.diff(numpy.concatenate(([0], numpy.flip(ccdf)))))
        return PMF(data, min_face)

    def copy(self):
        return PMF(self.data, self.min_face)

    def outcomes(self):
        return range(self.min_face, self.min_face + len(self.data))

    def max_face(self):
        return self.min_face + len(self.data) - 1

    def total_mass(self):
        return numpy.sum(self.data)

    def normalize(self):
        return PMF(self.data / self.total_mass(), self.min_face)

    def scale_mass(self, factor):
        return PMF(factor * self.data, self.min_face)

    def faces(self):
        return numpy.arange(self.min_face, self.min_face + len(self.data))

    def __neg__(self):
        return PMF(numpy.flip(self.data), -self.max_face())

    def __add__(self, other):
        if isinstance(other, PMF):
            result_data = numpy.convolve(self.data, other.data)
            result_min_face = self.min_face + other.min_face
            return PMF(result_data, result_min_face)
        else:
            return PMF(self.data, self.min_face + other)

    def __sub__(self, other):
        return self + (-other)
    
    def __mul__(self, other):
        if isinstance(other, PMF):
            if self.min_face < 0 or other.min_face < 0:
                raise NotImplementedError('Multiplication not implemented for non-positive faces')
            result_min_face = self.min_face * other.min_face
            result_max_face = self.max_face() * other.max_face()
            result_data = numpy.zeros((result_max_face - result_min_face + 1)) # todo: dtype
            for face, mass in zip(other.faces(), other.data):
                start_index = face * self.min_face - result_min_face
                result_data[start_index:start_index+face*len(self.data):face] += self.data * mass
            return PMF(result_data, result_min_face)
        else:
            kernel = numpy.zeros((other,), dtype=int)
            kernel[0] = 1
            result_data = numpy.kron(self.data, kernel)[:-(other-1)]
            result_min_face = self.min_face * other
            return PMF(result_data, result_min_face)

    def advantage(self, n=2):
        return PMF.from_cdf(numpy.power(self.cdf(), n), self.min_face)

    def disadvantage(self, n=2):
        return PMF.from_ccdf(numpy.power(self.ccdf(), n), self.min_face)

    def repeat_and_sum(self, n):
        result = PMF([1], 0)
        for i in range(n):
            result += self
        return result

    def add_mass(self, other):
        if self.min_face > other.min_face: return other.sum_distributions(self)
        other_start_index = other.min_face - self.min_face
        length = max(len(self.data), len(other.data) + other_start_index)
        self_padded = numpy.pad(self.data, (0, length - len(self.data)))
        other_padded = numpy.pad(other.data, (other_start_index, 0))
        return PMF(self_padded + other_padded, self.min_face)

    def __lt__(self, other):
        if isinstance(other, PMF):
            return (self - other) < 0
        else:
            result = 0
            for i in range(0, other - self.min_face):
                result += self.data[i]
            return result

    def __le__(self, other):
        return self < other + 1

    def __ge__(self, other):
        return self.total_mass() - (self < other)

    def __gt__(self, other):
        return self.total_mass() - (self <= other)

    def csv_string(self):
        result = ''
        for i, x in enumerate(self.data):
            result += '%d,%s\n' % (self.min_face + i, x)
        return result
    
    def explode(self, n):
        result = self.copy()
        for i in range(n):
            without_last = PMF(self.total_mass() * result.data[:-1], result.min_face)
            exploded = self.scale_mass(result.data[-1]) + result.max_face()
            result = without_last.add_mass(exploded)
        return result

    def cdf(self):
        return numpy.cumsum(self.data)

    def ccdf(self):
        return numpy.flip(numpy.cumsum(numpy.flip(self.data)))
        
    def median(self):
        median_cdf = self.total_mass() * 0.5
        return numpy.nonzero(self.cdf() > median_cdf)[0][0] + self.min_face

def xdy(x, y):
    one_d_y = PMF(numpy.ones((y,), dtype=int), 1)
    return one_d_y.repeat_and_sum(x)

def geometric(half_life, n=100):
    factor = 0.5 ** (1.0 / half_life)
    data = numpy.power(factor, numpy.arange(n)) * (1.0 - factor)
    data[-1] = 1.0 - numpy.sum(data[:-1])
    return PMF(data, 0)
