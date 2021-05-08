from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.optimize
import scipy.special
import subprocess

# Minimize distance on d20 curve.

def objective(sd):
    gaussian = Die.gaussian(10.5, sd)
    return Die.d20.ks_stat(gaussian)

print(scipy.optimize.minimize_scalar(objective, bounds=(5.0, 8.0), method='bounded'))

d20 = Die.d20

opposed_d20 = d20 - d20 - Die.coin()

figsize = (8, 4.5)
dpi = 150

def make_pmf_plot(die, offset=0, sd=None):
    if sd is None:
        gaussian = Die.gaussian(die)
    else:
        gaussian = Die.gaussian(die.mean(), sd)

    print('Var:', die.variance())
    print('MAD median:', die.mad_median())

    fig = plt.figure(figsize=figsize)
    ax = plt.subplot(111)
    ax.grid()

    print('Gaussian mode:', gaussian.mode())

    ax.plot(die.outcomes() + offset, die.pmf() * 100.0, marker='.')
    ax.plot(gaussian.outcomes() + offset, gaussian.pmf() * 100.0, marker='.')
    
    ax.set_ylim(bottom = 0)
    ax.set_ylabel('Chance (%) of rolling exactly')

    return ax

def make_mos_plot(die, offset=0, sd=None):
    if sd is None:
        gaussian = Die.gaussian(die)
    else:
        gaussian = Die.gaussian(die.mean(), sd)

    fig = plt.figure(figsize=figsize)
    ax = plt.subplot(111)
    ax.grid()

    x = numpy.arange(min(0, die.min_outcome()), die.max_outcome() + 1)
    y_die = [die.margin_of_success(t).mean() for t in x]
    y_gaussian = [gaussian.margin_of_success(t).mean() for t in x]

    ax.plot(x + offset, y_die, marker='.')
    ax.plot(x + offset, y_gaussian, marker='.')

    ax.set_xlim(left=x[0], right=x[-1])
    
    ax.set_ylim(bottom = 0)
    ax.set_ylabel('Mean margin of success')

    return ax

def make_ccdf_plot(die, offset=0, sd=None):
    if sd is None:
        gaussian = Die.gaussian(die)
    else:
        gaussian = Die.gaussian(die.mean(), sd)

    print('KS: %0.2f%%' % (die.ks_stat(gaussian) * 100.0))
    print('Above end: %0.2f%%' % ((gaussian > die.max_outcome()) * 100.0))
    gaussian_clipped = gaussian.clip(die)
    for outcome, die_chance, gaussian_chance in zip(die.outcomes(), die.ccdf(), gaussian_clipped.ccdf()):
        print('%d: %0.2f%%, %0.2f%%, %0.3f, %0.3f, %+0.2f%%' % (
            outcome,
            100.0 * die_chance,
            100.0 * gaussian_chance,
            die_chance / gaussian_chance,
            gaussian_chance / die_chance,
            100.0 * (gaussian_chance - die_chance)))

    
    
    fig = plt.figure(figsize=figsize)
    ax = plt.subplot(111)
    ax.grid()

    ax.plot(die.outcomes() + offset, die.ccdf() * 100.0, marker='.')
    ax.plot(gaussian.outcomes() + offset, gaussian.ccdf() * 100.0, marker='.')
    ax.set_ylim(bottom = 0, top = 100)
    ax.set_ylabel('Chance (%) of rolling at least')

    return ax

print('\nSame SD')

ax = make_pmf_plot(d20)
ax.set_xlabel('Number')
ax.legend(['d20', 'Gaussian with same SD'])
ax.set_aspect(4)
ax.set_xlim(-10, 30)
plt.savefig('output/gaussian_vs_uniform_pmf.png', dpi = dpi, bbox_inches = "tight")

ax = make_mos_plot(d20)
ax.set_xlabel('Number needed to hit')
ax.legend(['d20', 'Gaussian with same SD'])
plt.savefig('output/gaussian_vs_uniform_mos.png', dpi = dpi, bbox_inches = "tight")

ax = make_ccdf_plot(d20)
ax.set_xlabel('Number needed to hit')
ax.legend(['d20', 'Gaussian with same SD'])
ax.set_aspect(0.2)
ax.set_xlim(-10, 30)
plt.savefig('output/gaussian_vs_uniform_ccdf.png', dpi = dpi, bbox_inches = "tight")

print('\nSD 8')

sd = 8

ax = make_pmf_plot(d20, sd=sd)
ax.set_xlabel('Number')
ax.legend(['d20', 'Gaussian with same median PMF'])
ax.set_aspect(4)
ax.set_xlim(-10, 30)
plt.savefig('output/gaussian_vs_mm_uniform_pmf.png', dpi = dpi, bbox_inches = "tight")

ax = make_mos_plot(d20, sd=sd)
ax.set_xlabel('Number needed to hit')
ax.legend(['d20', 'Gaussian with same median PMF'])
plt.savefig('output/gaussian_vs_mm_uniform_mos.png', dpi = dpi, bbox_inches = "tight")

ax = make_ccdf_plot(d20, sd=sd)
ax.set_xlabel('Number needed to hit')
ax.legend(['d20', 'Gaussian with same median PMF'])
ax.set_aspect(0.2)
ax.set_xlim(-10, 30)
plt.savefig('output/gaussian_vs_mm_uniform_ccdf.png', dpi = dpi, bbox_inches = "tight")

print('\nSD 6')

sd = 6

ax = make_ccdf_plot(d20, sd=sd)
ax.set_xlabel('Number needed to hit')
ax.legend(['d20', 'Gaussian with minimum vertical distance vs. d20'])
ax.set_aspect(0.2)
ax.set_xlim(-10, 30)
plt.savefig('output/gaussian_vs_min_uniform_ccdf.png', dpi = dpi, bbox_inches = "tight")

print('\nOpposed')

ax = make_pmf_plot(opposed_d20, offset=0.5)
ax.set_xlabel('Difference')
ax.legend(['opposed d20', 'Gaussian with same SD'])
ax.set_aspect(4)
ax.set_xlim(-25, 25)
plt.savefig('output/gaussian_vs_triangular_pmf.png', dpi = dpi, bbox_inches = "tight")

ax = make_mos_plot(opposed_d20)
ax.set_xlabel('Difference in modifiers')
ax.legend(['opposed d20', 'Gaussian with same SD'])
plt.savefig('output/gaussian_vs_triangular_mos.png', dpi = dpi, bbox_inches = "tight")

ax = make_ccdf_plot(opposed_d20)
ax.set_xlabel('Difference in modifiers')
ax.legend(['opposed d20', 'Gaussian with same SD'])
ax.set_aspect(0.2)
ax.set_xlim(-25, 25)
plt.savefig('output/gaussian_vs_triangular_ccdf.png', dpi = dpi, bbox_inches = "tight")

# Adding a small die.

fig = plt.figure(figsize=figsize)
ax = plt.subplot(111)
ax.grid()
ax.plot(Die.d20.outcomes(), Die.d20.ccdf() * 100.0, marker='.')
added_die = Die.d20 + Die.d6
ax.plot(added_die.outcomes() - 3.5, added_die.ccdf() * 100.0, marker='.')
added_die = Die.d20 + Die.d12
ax.plot(added_die.outcomes() - 6.5, added_die.ccdf() * 100.0, marker='.')
added_die = Die.d20 + Die.d20
ax.plot(added_die.outcomes() - 10.5, added_die.ccdf() * 100.0, marker='.')
ax.set_aspect(0.2)
ax.set_xlim(-10, 30)
ax.set_ylim(0, 100)
ax.set_xlabel('Number needed to hit')
ax.set_ylabel('Chance (%) of hitting')
ax.legend(['d20',
           'd20 + d6 - 3.5',
           'd20 + d12 - 6.5',
           'd20 + d20 - 10.5'])
plt.savefig('output/add_small_die_ccdf.png', dpi = dpi, bbox_inches = "tight")


# Coin flips.

for coin_count in range(1, 11):
    fig = plt.figure(figsize=figsize)
    ax = plt.subplot(111)
    ax.grid()

    x = numpy.linspace(-3, 3, 1001)
    y = numpy.exp(-0.5 * numpy.square(x)) / numpy.sqrt(2 * numpy.pi)
    ax.plot(x, y, linestyle=':')


    coins = Die.d(coin_count, 2)
    gaussian = Die.gaussian(coins)
    ks = coins.ks_stat(gaussian) * 100.0
    print('KS %d: %0.2f%%' % (coin_count, ks))
    ax.plot((coins.outcomes() - coins.mean()) / coins.standard_deviation(),
            coins.pmf() * coins.standard_deviation(), marker='.')

    ax.set_xlim(-3, 3)
    ax.set_xlabel('Deviation from mean in SDs')
    ax.set_ylabel('Normalized probability')
    ax.set_ylim(0, 0.4)
    ax.set_title('%d coin(s): KS = %0.2f%%' % (coin_count, ks))

    plt.savefig('output/frames/frame_%03d.png' % (coin_count - 1), dpi = dpi, bbox_inches = "tight")

ffmpeg_cmd = [
    'ffmpeg', 
    '-y',
    '-r', '2',
    '-i', 'output/frames/frame_%03d.png',
    '-vframes', str(coin_count),
    '-c:v', 'libvpx-vp9',
    '-b:v', '0',
    '-crf', '18',
    '-pix_fmt', 'yuv420p',
    'output/gaussian_vs_coins.webm',
]
subprocess.Popen(ffmpeg_cmd).wait()

for coin_count in range(1, 11):
    fig = plt.figure(figsize=figsize)
    ax = plt.subplot(111)
    ax.grid()

    x = numpy.linspace(-3, 3, 3001)
    y = 0.5 * scipy.special.erfc(x / numpy.sqrt(2))
    ax.plot(x, y * 100.0, linestyle=':')

    coins = Die.d(coin_count, 2)
    gaussian = Die.gaussian(coins)
    ks = coins.ks_stat(gaussian) * 100.0
    print('KS %d: %0.2f%%' % (coin_count, ks))
    ax.plot((coins.outcomes(include_one_past_end=True) - 0.5 - coins.mean()) / coins.standard_deviation(),
            coins.ccdf(inclusive='both') * 100.0, marker='.')

    ax.set_xlim(-3, 3)
    ax.set_xlabel('Deviation from mean in SDs')
    ax.set_ylabel('Chance (%) to hit')
    ax.set_ylim(0, 100)
    ax.set_title('%d coin(s): KS = %0.2f%%' % (coin_count, ks))

    plt.savefig('output/frames/frame_%03d.png' % (coin_count - 1), dpi = dpi, bbox_inches = "tight")

ffmpeg_cmd = [
    'ffmpeg', 
    '-y',
    '-r', '2',
    '-i', 'output/frames/frame_%03d.png',
    '-vframes', str(coin_count),
    '-c:v', 'libvpx-vp9',
    '-b:v', '0',
    '-crf', '18',
    '-pix_fmt', 'yuv420p',
    'output/gaussian_vs_coins_ccdf.webm',
]
subprocess.Popen(ffmpeg_cmd).wait()
