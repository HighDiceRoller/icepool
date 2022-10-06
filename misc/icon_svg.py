import svgwrite
import svgwrite.shapes

size = 64
dot_radius = 7
dot_spacing = 4
dot_color = svgwrite.rgb(252, 252, 252)
background_radius = 7
background_color = svgwrite.rgb(63, 189, 245)

draw = svgwrite.Drawing('misc/icon.svg', size=(size, size), profile='tiny')

# Background.
draw.add(
    svgwrite.shapes.Rect((0, 0), (size, size),
                         rx=background_radius,
                         ry=background_radius,
                         fill=background_color))

# Dots.
first = 14
mid = first + dot_radius * 2 + dot_spacing
last = mid + dot_radius * 2 + dot_spacing

for cx, cy in [
    (first, first),
    (mid, first),
    (first, last),
    (mid, mid),
    (last, first),
    (mid, last),
    (last, last),
]:
    draw.add(svgwrite.shapes.Circle((cx, cy), r=dot_radius, fill=dot_color))

draw.save()
