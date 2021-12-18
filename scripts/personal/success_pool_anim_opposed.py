import _context

from hdroller import Die
import numpy
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy
import subprocess

figsize = (8, 4.5)
dpi = 150
left = -4
right = 4

offset_sd = 0.0

pool_sizes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 25, 30, 35, 40, 50, 100]

def make_webm(input_path_pattern, output_path):
    ffmpeg_cmd = [
        'ffmpeg', 
        '-y',
        '-r', '2',
        '-i', input_path_pattern,
        '-vframes', str(len(pool_sizes)),
        '-c:v', 'libvpx-vp9',
        '-b:v', '0',
        '-crf', '18',
        '-pix_fmt', 'yuv420p',
        output_path,
    ]
    subprocess.Popen(ffmpeg_cmd).wait()

def make_anim(die, name):
    coef = 2.0 * die.mean() / die.standard_deviation()
    offset = offset_sd * offset_sd / (coef * coef)
    for frame_index, pool_size_a in enumerate(pool_sizes):
        die_bonus_a = coef * numpy.sqrt(pool_size_a + offset)
        pool_a = die.repeat_and_sum(pool_size_a)
        x = []
        sf = []
        for pool_size_b in range(0, 201):
            die_bonus_b = coef * numpy.sqrt(pool_size_b + offset)
            opposed = pool_a - die.repeat_and_sum(pool_size_b)
            
            p = opposed >= Die.coin() # Coin flip on ties.
            # p = (opposed > 0) / ((opposed > 0) + (opposed < 0)) # Reroll ties.
            x.append(die_bonus_b - die_bonus_a)
            sf.append(p)
        x = numpy.array(x)
        sf = numpy.array(sf)
        pmf = -numpy.diff(sf, prepend=1.0)

        # compute ks
        ks_sf = 0.5 * scipy.special.erfc(x / 2.0)
        ks = numpy.max(numpy.abs(sf - ks_sf))

        # pmf plot
        fig = plt.figure(figsize=figsize)
        ax = plt.subplot(111)
        g_x = numpy.arange(left, right+0.001, 0.001)
        g_pmf = numpy.exp(-0.5 * numpy.square(g_x / numpy.sqrt(2))) / (2.0 * numpy.sqrt(numpy.pi))
        ax.plot(g_x, g_pmf, linestyle=':')
        ax.plot(x + 0.5 * numpy.diff(x, append=x[-1]), pmf * pool_a.standard_deviation() * 2.0, marker='.')
        ax.grid()
        ax.set_xlim(left, right)
        ax.set_xlabel('Difference in roll-over result')
        ax.set_ylabel('Normalized probability')
        ax.set_ylim(0, 0.3)
        ax.set_title('%d pool size for side A (KS = %0.2f%%)' % (pool_size_a, ks * 100.0))
        pmf_frame_path = 'output/frames/pmf_%03d.png'
        plt.savefig(pmf_frame_path % frame_index,
                    dpi = dpi, bbox_inches = "tight")
        plt.close()

        # sf plot
        fig = plt.figure(figsize=figsize)
        ax = plt.subplot(111)
        g_x = numpy.arange(left, right+0.001, 0.001)
        g_sf = 50.0 * scipy.special.erfc(g_x / 2.0)
        ax.plot(g_x, g_sf, linestyle=':')
        ax.plot(x, sf * 100.0, marker='.')
        ax.grid()
        ax.set_xlim(left, right)
        ax.set_xlabel('Side A roll-over disadvantage')
        ax.set_ylabel('Chance for side A to win (%)')
        ax.set_ylim(0, 100.0)
        ax.set_title('%d pool size for side A (KS = %0.2f%%)' % (pool_size_a, ks * 100.0))
        sf_frame_path = 'output/frames/sf_%03d.png'
        plt.savefig(sf_frame_path % frame_index,
                    dpi = dpi, bbox_inches = "tight")
        plt.close()
    
    make_webm(pmf_frame_path, 'output/success_pool_roe_opposed_%s_pmf.webm' % name)
    make_webm(sf_frame_path, 'output/success_pool_roe_opposed_%s_sf.webm' % name)

make_anim(Die.coin(3/6), 'd6_4plus')
