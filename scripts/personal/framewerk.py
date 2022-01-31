import _context

import hdroller

class CthulhuTechEval(hdroller.PoolEval):
  def initial_state(self, pool):
    # The state consists of the best score so far and the current run length.
    return 0, 0

  def next_state(self, prev_state, outcome, count):
    prev_score, prev_run = prev_state
    if count > 0:
      set_score = outcome * count
      run_score = 0
      run = prev_run + 1
      if run >= 3:
        # This could be the triangular formula, but it's clearer this way.
      	for i in range(run): run_score += (outcome - i)
      score = max(set_score, run_score, prev_score)
    else:
      # No dice rolled this number, so the score remains the same.
      score = prev_score
      run = 0
    return score, run

  def final_outcome(self, prev_state, pool):
    # Return just the score.
    return prev_state[0]

import cProfile
cProfile.run('CthulhuTechEval().eval(hdroller.pool(hdroller.d10, 10))')

import numpy
import matplotlib.pyplot as plt

default_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

evaluator = CthulhuTechEval()

figsize = (16, 9)
fig, ax = plt.subplots(figsize=figsize)

for i in range(1, 11):
  pool = hdroller.pool(hdroller.d10, i)
  result = evaluator.eval(pool)
  ax.plot(result.outcomes(), numpy.array(result.sf()) * 100.0)
  marker_size = 64 if i < 10 else 128
  ax.scatter(result.median(), 50.0,
             marker=('$%d$' % i),
             facecolor=default_colors[i-1],
             s=marker_size)

ax.set_xticks(numpy.arange(0, 61, 5))
ax.set_yticks(numpy.arange(0, 101, 10))
ax.set_xlim(0, 60)
ax.set_ylim(0, 100)
ax.set_xlabel('Result')
ax.set_ylabel('Chance of getting at least (%)')
ax.grid()
plt.show()
