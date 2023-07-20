from PIL import Image, ImageDraw, ImageFont

final_size = 512
upscale = 16
image_size = final_size * upscale
cell_count = 64
cell_size = image_size // cell_count

github_size = (1280, 640)

red = (189, 35, 42, 255)
white = (252, 252, 252, 255)
font_color = (15, 15, 31, 255)

def draw_i():
    img = Image.new('RGBA', (image_size, image_size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    ice = (7 * 9, 7 * 27, 7 * 35, 255)
    ice = red

    # Background.

    round_cells = 7

    draw.rounded_rectangle([0, 0, image_size, image_size,],
                           radius=cell_size*round_cells, fill=ice)

    # Dots.

    dot_cells = 14
    space_cells = 4
    dot_size = cell_size * dot_cells

    first = 7
    mid = first + dot_cells + space_cells
    last = mid + dot_cells + space_cells

    for cx, cy in [(first, first),
                   (mid, first),
                   (first, last),
                   (mid, mid),
                   (last, first),
                   (mid, last),
                   (last, last),
                   ]:
        xy = [cx * cell_size,
              cy * cell_size,
              cx * cell_size + dot_size,
              cy * cell_size + dot_size,]
        draw.ellipse(xy, fill=white)

    ico = img.resize((256, 256), resample=Image.Resampling.BICUBIC)
    ico.save('favicon.ico')
    img = img.resize((final_size, final_size), resample=Image.Resampling.BICUBIC)
    img.save('favicon.png')


    circle_size = final_size * 3 // 2
    circle_border = (circle_size - final_size) // 2
    circle_img = Image.new('RGBA', (circle_size, circle_size), color=(0, 0, 0, 0))
    circle_img.paste(img, box=(circle_border,
                               circle_border,
                               circle_size - circle_border,
                               circle_size - circle_border))
    circle_img.save('favicon_circle.png')

    github_icon = img.resize((192, 192), resample=Image.Resampling.BICUBIC)
    github_card = Image.new('RGBA', github_size, color=(245, 245, 252, 255))
    github_card.paste(github_icon, (github_size[0] // 2 - 96, 128), mask=github_icon)
    github_draw = ImageDraw.Draw(github_card)
    title_font = ImageFont.truetype('RobotoMono-Regular.ttf', size=64)
    github_draw.text((github_size[0] // 2, 384), 'Icepool',
                     font=title_font, fill=font_color, anchor='ms')
    subtitle_font = ImageFont.truetype('RobotoMono-Regular.ttf', size=32)
    github_draw.text((github_size[0] // 2, 448), 'Python dice probability package',
                     font=subtitle_font, fill=font_color, anchor='ms')
    github_card.save('github_card.png')

draw_i()
