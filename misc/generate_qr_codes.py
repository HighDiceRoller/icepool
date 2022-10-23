import qrcode

targets = [
    ('github', 'https://github.com/HighDiceRoller/icepool'),
    ('ability_scores',
     'https://highdiceroller.github.io/icepool/apps/ability_scores.html'),
    ('cortex_prime',
     'https://highdiceroller.github.io/icepool/apps/cortex_prime.html'),
    ('legends_of_the_wulin',
     'https://highdiceroller.github.io/icepool/apps/legends_of_the_wulin.html'),
    ('icecup', 'https://highdiceroller.github.io/icepool/apps/icecup.html'),
    ('notebooks',
     'https://highdiceroller.github.io/icepool/notebooks/lab/index.html'),
]

error_correction = qrcode.ERROR_CORRECT_L
box_size = 1

max_version = 1

# First pass to compute version size.
for _, url in targets:
    qr = qrcode.QRCode(version=None,
                       error_correction=error_correction,
                       box_size=box_size)
    qr.add_data(url)
    qr.make(fit=True)
    max_version = max(max_version, qr.version)

print(f'max_version = {max_version}')

for name, url in targets:
    qr = qrcode.QRCode(version=max_version,
                       error_correction=error_correction,
                       box_size=box_size)
    qr.add_data(url)
    qr.make()
    img = qr.make_image(fill_color="black", back_color="white")
    img.save('./misc/qr_' + name + '.png')
