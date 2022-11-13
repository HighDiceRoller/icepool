import random

import numpy

import svgwrite
import svgwrite.path

from math import sqrt, sin, cos, pi, ceil


def tetrahedron(base_to_tip):
    """Creates a tetrahedron as a path."""

    top = numpy.array([0, -sqrt(1 / 2)]) * base_to_tip
    left = numpy.array([-sqrt(3 / 8), sqrt(1 / 8)]) * base_to_tip
    right = numpy.array([sqrt(3 / 8), sqrt(1 / 8)]) * base_to_tip

    path = svgwrite.path.Path('M')
    # Outer triangle.
    path.push(top)
    path.push(left)
    path.push(right)
    path.push('Z')

    # Spokes.
    path.push('M', (0, 0))
    path.push(top)

    path.push('M', (0, 0))
    path.push(left)

    path.push('M', (0, 0))
    path.push(right)

    return path


def cube(pole_to_pole):
    path = svgwrite.path.Path('M')

    def vertex(i):
        angle = i * pi / 3
        x = sin(angle) * pole_to_pole / 2
        y = -cos(angle) * pole_to_pole / 2
        return numpy.array([x, y])

    # Outer hexagon.
    for i in range(6):
        path.push(vertex(i))
    path.push('Z')

    # Inner spokes.
    for i in range(1, 6, 2):
        path.push('M')
        path.push((0, 0))
        path.push(vertex(i))

    return path


def octahedron(pole_to_pole):
    path = svgwrite.path.Path('M')

    def vertex(i):
        angle = i * pi / 3
        x = sin(angle) * pole_to_pole / 2
        y = -cos(angle) * pole_to_pole / 2
        return numpy.array([x, y])

    # Outer hexagon.
    for i in range(6):
        path.push(vertex(i))
    path.push('Z')

    # Inner chords.
    for i in range(0, 6, 2):
        path.push('M')
        path.push(vertex(i))
        path.push(vertex(i + 2))

    return path


# Source: https://math.stackexchange.com/questions/2464000/pentagonal-trapezohedron-with-face-perpendicular-to-side
def pentagonal_trapezohedron(pole_to_pole):

    scale = pole_to_pole / 2
    s = sin(pi / 5)
    s2 = sin(2 * pi / 5)
    c = cos(pi / 5)
    tropic = (1 / sqrt(c) - sqrt(c)) / (1 / sqrt(c) + sqrt(c))
    tropic_r = 2.0 / (1 / sqrt(c) + sqrt(c))

    top = numpy.array([0, -1]) * scale
    bottom = numpy.array([0, 1]) * scale
    center = numpy.array([0, tropic]) * scale
    left_inner = numpy.array([-s * tropic_r, -tropic]) * scale
    right_inner = numpy.array([s * tropic_r, -tropic]) * scale
    left_bottom = numpy.array([-s2 * tropic_r, tropic]) * scale
    right_bottom = numpy.array([s2 * tropic_r, tropic]) * scale
    left_top = numpy.array([-s2 * tropic_r, -tropic]) * scale
    right_top = numpy.array([s2 * tropic_r, -tropic]) * scale

    # Outer polygon.
    path = svgwrite.path.Path('M')
    path.push(top)
    path.push(right_top)
    path.push(right_bottom)
    path.push(bottom)
    path.push(left_bottom)
    path.push(left_top)
    path.push('Z')

    # Equatorial "M".
    path.push('M')
    path.push(left_bottom)
    path.push(left_inner)
    path.push(center)
    path.push(right_inner)
    path.push(right_bottom)

    # Vertical edges.
    path.push('M')
    path.push(top)
    path.push(left_inner)
    path.push('M')
    path.push(top)
    path.push(right_inner)
    path.push('M')
    path.push(bottom)
    path.push(center)

    return path


# https://math.stackexchange.com/questions/753038/edge-length-of-a-dodecahedron
def dodecahedron(pole_to_pole):
    scale = pole_to_pole / 2

    def outer(i):
        angle = i * pi / 5
        x = sin(angle) * scale
        y = -cos(angle) * scale
        return numpy.array([x, y])

    path = svgwrite.path.Path('M')
    # Outer decagon.
    for i in range(10):
        path.push(outer(i))
    path.push('Z')

    # Inner pentagon.
    inner_ratio = (sqrt(5) - 1) / sqrt(3)
    path.push('M')
    for i in range(0, 10, 2):
        path.push(outer(i) * inner_ratio)
    path.push('Z')

    # Spokes.
    for i in range(0, 10, 2):
        path.push('M')
        path.push(outer(i) * inner_ratio)
        path.push(outer(i))

    return path


# https://math.stackexchange.com/questions/2538184/proof-of-golden-rectangle-inside-an-icosahedron
def icosahedron(pole_to_pole):
    path = svgwrite.path.Path('M')

    def outer(i):
        angle = i * pi / 3
        x = sin(angle) * pole_to_pole / 2
        y = -cos(angle) * pole_to_pole / 2
        return numpy.array([x, y])

    # Outer hexagon.
    for i in range(6):
        path.push(outer(i))
    path.push('Z')

    side_ratio = 2 / (1 + sqrt(5))

    # Foward triangle.
    path.push('M')
    for i in range(0, 6, 2):
        path.push(outer(i) * side_ratio)
    path.push('Z')

    # Outer connectors.
    for i in range(0, 6, 2):
        for offset in [-1, 0, 1]:
            path.push('M')
            path.push(outer(i) * side_ratio)
            path.push(outer(i + offset))

    return path


choices = [
    (tetrahedron, 18),  # 15-18 base-to-pole.
    (cube, 24),  # 14-16 side-to-side. This is 24.25-27.7 pole-to-pole.
    (octahedron, 22),  # 16 side-to-side, 21-23 pole-to-pole
    (pentagonal_trapezohedron, 22),  # 21-23 pole-to-pole
    (pentagonal_trapezohedron, 22),
    (dodecahedron, 22),  # 18.5-21 pole-to-pole
    (icosahedron, 23),  # 21-25 pole-to-pole
]

# Wallpaper.
bleed = 0
width = 12 + 2 * bleed
height = 4 + 2 * bleed

row_height = sqrt(3) / 2
stroke_color = svgwrite.rgb(217, 238, 252)  # svgwrite.rgb(234, 248, 255)
stroke_width = 1.0

draw = svgwrite.Drawing('misc/dice_twitter_wallpaper.svg',
                        size=(width * 25.4, height * 25.4),
                        profile='tiny')

y = bleed - row_height
r = 0
while y < height + row_height:
    for c in range(ceil(width) + 2):
        path_func, scale = random.choice(choices)
        die: svgwrite.path.Path = path_func(scale)
        die.stroke(stroke_color, width=stroke_width)
        die.fill('none')
        if r % 2 == 0:
            die.translate((c + bleed - 0.5) * 25.4, y * 25.4)
        else:
            die.translate((c + bleed - 1) * 25.4, y * 25.4)
        draw.add(die)
    y += row_height
    r += 1

draw.save()

# Single images.

stroke_color = svgwrite.rgb(217, 238, 252)

for path_func, scale in choices:
    name = path_func.__name__
    draw = svgwrite.Drawing(f'misc/{name}.svg',
                            size=(25.4, 25.4),
                            profile='tiny')
    die = path_func(scale)
    die.stroke(stroke_color, width=stroke_width)
    die.fill(svgwrite.rgb(255, 255, 255))
    die.translate((25.4 / 2, 25.4 / 2))
    if name == 'tetrahedron':
        die.translate((0.0, 25.4 / 12))
    draw.add(die)
    draw.save()
