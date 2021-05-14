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
    print(name)
    coef = 2.0 * die.mean() / die.standard_deviation()
    offset = offset_sd * offset_sd / (coef * coef)
    for frame_index, pool_size in enumerate(pool_sizes):
        # dice
        pool = die.repeat_and_sum(pool_size)
        sqrt_arg = pool_size + offset
        die_modifier = coef * numpy.sqrt(numpy.abs(sqrt_arg)) * numpy.sign(sqrt_arg)
        x_pmf = []
        x_ccdf = []
        ccdf = []
        for outcome, p in zip(pool.outcomes(include_one_past_end=True), pool.ccdf(inclusive='both')):
            sqrt_arg = outcome / die.mean() + offset
            outcome_modifier = coef * numpy.sqrt(numpy.abs(sqrt_arg)) * numpy.sign(sqrt_arg)
            x_pmf.append(outcome_modifier - die_modifier)
            
            sqrt_arg = (outcome - 0.5) / die.mean() + offset
            outcome_modifier = coef * numpy.sqrt(numpy.abs(sqrt_arg)) * numpy.sign(sqrt_arg)
            x_ccdf.append(outcome_modifier - die_modifier)
            
            ccdf.append(p)
        x_pmf = numpy.array(x_pmf[:-1])
        x_ccdf = numpy.array(x_ccdf)
        ccdf = numpy.array(ccdf)
        pmf = -numpy.diff(ccdf)

        g_x = numpy.arange(left, right+0.001, 0.001)
        g_pmf = numpy.exp(-0.5 * numpy.square(g_x)) / numpy.sqrt(2 * numpy.pi)
        g_ccdf = 0.5 * scipy.special.erfc(g_x / numpy.sqrt(2.0))

        # compute ks
        ks_ccdf = 0.5 * scipy.special.erfc(x_ccdf / numpy.sqrt(2.0))
        ks = numpy.max(numpy.abs(ccdf - ks_ccdf))
        
        # pmf plot
        fig = plt.figure(figsize=figsize)
        ax = plt.subplot(111)

        ax.plot(g_x, g_pmf, linestyle=':')
        ax.plot(x_pmf, pmf * pool.standard_deviation(), marker='.')

        ax.grid()
        ax.set_xlim(left, right)
        ax.set_xlabel('Deviation from mean (SDs)')
        ax.set_ylabel('Normalized probability')
        ax.set_ylim(0, 0.4)
        ax.set_title('%d pool size (KS = %0.2f%%)' % (pool_size, ks * 100.0))
        
        pmf_frame_path = 'output/frames/pmf_%03d.png'
        plt.savefig(pmf_frame_path % frame_index,
                    dpi = dpi, bbox_inches = "tight")
        plt.close()

        # ccdf plot
        fig = plt.figure(figsize=figsize)
        ax = plt.subplot(111)

        ax.plot(g_x, g_ccdf * 100.0, linestyle=':')
        ax.plot(x_ccdf, ccdf * 100.0, marker='.')

        ax.grid()
        ax.set_xlim(left, right)
        ax.set_xlabel('Deviation from mean (SDs)')
        ax.set_ylabel('Chance to hit (%)')
        ax.set_ylim(0, 100.0)
        ax.set_title('%d pool size (KS = %0.2f%%)' % (pool_size, ks * 100.0))
        ccdf_frame_path = 'output/frames/ccdf_%03d.png'
        plt.savefig(ccdf_frame_path % frame_index,
                    dpi = dpi, bbox_inches = "tight")
        plt.close()
    make_webm(pmf_frame_path, 'output/success_pool_roe_%s_pmf.webm' % name)
    make_webm(ccdf_frame_path, 'output/success_pool_roe_%s_ccdf.webm' % name)

#make_anim(Die.coin(1/6), 'd6_2plus')
#make_anim(Die.coin(2/6), 'd6_3plus')
make_anim(Die.coin(3/6), 'd6_4plus')
#make_anim(Die.coin(4/6), 'd6_5plus')
#make_anim(Die.coin(5/6), 'd6_6plus')
exalted2e = Die.from_faces([0]*6 + [1]*3 + [2])
owod = Die.from_faces([-1] + [0]*5 + [1]*4)
nwod = Die.from_faces([0]*7 + [1]*3).explode(10, chance=0.1)
#make_anim(exalted2e, 'exalted2e')
#make_anim(owod, 'owod')
#make_anim(nwod, 'nwod')
