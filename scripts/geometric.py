import numpy

class ExplodingDie():
    """
    data should be a list of (face, explode) pairs
    """
    def __init__(self, data):
        self.data = data
        self.faces = [x[0] for x in data]
        self.explodes = [x[1] for x in data]

    def explode_count(self):
        return sum(1 for explode in self.explodes if explode)

    def explode_chance(self):
        return self.explode_count() / len(self.faces)

    def mean(self):
        mean_single_roll = sum(self.faces) / len(self.faces)
        return mean_single_roll / (1 - self.explode_chance())

    def mean_explode_add(self):
        return sum(face for face, explode in self.data if explode) / self.explode_count()

    # Finds k such that the tail decays according to exp(-kx).
    def decay_rate(self):
        return -numpy.log(self.explode_chance()) / self.mean_explode_add()

    # Finds b such that the tail decays according to b^x.
    def decay_base(self):
        return numpy.power(self.explode_chance(), 1.0 / self.mean_explode_add())

    def pdf(self, max_rolls):
        pdf = numpy.zeros((max_rolls * max(self.faces) + 1,), dtype=float)
        distribution = numpy.zeros_like(pdf)
        distribution[0] = 1.0
        
        for i in range(max_rolls):
            new_distribution = numpy.zeros_like(pdf)
            for face, explode in self.data:
                if explode:
                    new_distribution += numpy.roll(distribution, face) / len(self.faces)
                else:
                    pdf += numpy.roll(distribution, face) / len(self.faces)
            distribution = new_distribution
        return pdf

    def square_abs_error(self, max_rolls):
        min_face = min(self.faces)
        pdf = self.pdf(max_rolls)
        decay_base = self.decay_base()
        
        result = 0.0
        for roll, chance in enumerate(pdf):
            above_min = roll - min_face
            if above_min < 0: continue
            expected_chance = (decay_base ** above_min) * (1 - decay_base)
            result += (expected_chance - chance) ** 2
        return result / (1 - decay_base) ** 2

    def cdf_error(self, max_rolls):
        min_face = min(self.faces)
        pdf = self.pdf(max_rolls)
        decay_base = self.decay_base()
        decay_rate = self.decay_rate()

        result = 0.0
        for roll, chance in enumerate(pdf):
            above_min = roll - min_face
            if above_min < 0: continue
            expected_chance = (decay_base ** above_min) * (1 - decay_base)
            result += numpy.abs(expected_chance - chance)
        return result * decay_rate

    def sequence_string(self):
        return ', '.join(str(face) + ('!' if explode else '') for face, explode in self.data)

"""
We assume only the last face can explode.
"""
def generate_data(num_faces, partial=[]):
    if partial:
        last_data = partial[-1]
    else:
        yield from generate_data(num_faces, [(0, False)])
        return

    last_face, last_explode = last_data

    # Base case.
    if len(partial) == num_faces:
        if last_data[0] > 0: yield partial
        return

    # Duplicate the last face unless it would outnumber the previous number.
    # Always allow duplicating the last face.
    if last_explode or last_face == 0 or partial.count(last_data) < partial.count((last_face-1, False)):
        yield from generate_data(num_faces, partial + [last_data])
    
    if not last_explode:
        # Duplicate the last face, but explode.
        yield from generate_data(num_faces, partial + [(last_face, True)])
        # Duplicate the last face and add 1.
        yield from generate_data(num_faces, partial + [(last_face + 1, False)])
        # Duplicate the last face and add 1 and explode.
        yield from generate_data(num_faces, partial + [(last_face + 1, True)])

doubling_length_target = 6.0
doubling_length_tol = 0.1

results = []

for num_faces in [8, 10, 12, 20]:
    for data in generate_data(num_faces):
        die = ExplodingDie(data)
        if die.explode_count() == 0: continue
        #if die.explode_chance() > 0.3: continue
        if die.mean_explode_add() == 0.0: continue
        doubling_length = numpy.log(2) / die.decay_rate()
        if doubling_length < doubling_length_target - doubling_length_tol: continue
        if doubling_length > doubling_length_target + doubling_length_tol: continue
        cdf_error = die.cdf_error(10)
        if cdf_error > 0.022: continue
        print(die.sequence_string())
        print('doubling length:', doubling_length, 'cdf_error', cdf_error)
        results.append(die)
    
