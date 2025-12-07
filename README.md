# <img width="32" height="32" src="https://highdiceroller.github.io/icepool/favicon.png" /> Icepool

Python dice probability package.

[GitHub repository.](https://github.com/HighDiceRoller/icepool)

[PyPi page.](https://pypi.org/project/icepool/)

Try coding in your browser using [Icecup](https://highdiceroller.github.io/icepool/apps/icecup.html), a simple frontend for scripting and graphing similar to AnyDice, SnakeEyes, and Troll. You can find a series of tutorials [here](https://highdiceroller.github.io/icepool/notebooks/lab?path=tutorial%2Fc00_introduction.ipynb).

## Features

* Pure Python implementation using only the Standard Library. Run it almost anywhere Python runs: program locally, share Jupyter notebooks, or build your own client-side web apps using Pyodide.
* Dice support all standard operators (+, -, <, >, etc.) as well as an extensive library of functions (rerolling, exploding, etc.)
* Efficient dice pool algorithm can solve keep-highest, finding sets and/or straights, *RISK*-like mechanics, and more in milliseconds, even for large pools.
* Exact fractional probabilities using Python `int`s.
* Some support for decks (aka sampling without replacement).

## Installing

```
pip install icepool
```

The source is pure Python, so including a direct copy in your project can work as well.

## Contact

Feel free to open a [discussion](https://github.com/HighDiceRoller/icepool/discussions) or [issue](https://github.com/HighDiceRoller/icepool/issues) on GitHub. You can also find me on [Reddit](https://www.reddit.com/user/HighDiceRoller) or [Twitter](https://twitter.com/highdiceroller).

## API documentation

[pdoc on GitHub.](https://highdiceroller.github.io/icepool/apidoc/latest/icepool.html)

## JupyterLite notebooks

See this [JupyterLite distribution](https://highdiceroller.github.io/icepool/notebooks/lab/index.html) for a collection of interactive, editable examples. These include mechanics from published games, StackExchange, Reddit, and academic papers. 

[JupyterLite REPL.](https://highdiceroller.github.io/icepool/notebooks/repl/index.html?kernel=python&toolbar=1&code=%25pip%20install%20icepool%0Aimport%20icepool)

As a backup, you can [open the notebooks in Google Colab.](https://colab.research.google.com/github/HighDiceRoller/icepool)

### Tutorial notebooks

In particular, here is a series of [tutorial notebooks.](https://highdiceroller.github.io/icepool/notebooks/lab?path=tutorial%2Fc00_introduction.ipynb)

## StackExchange answers

* [Call-on traits in *Burning Wheel*](https://rpg.stackexchange.com/a/216021/72732): Success-counting dice pools with explosions and rerolls.
* [*Vampire the Masquerade V*](https://rpg.stackexchange.com/a/209266/72732)
* [Roll multiple ability score arrays and pick the one with the highest total. What is the distribution of each ranked score?](https://rpg.stackexchange.com/a/214450/72732)
* [*Year Zero Engine*](https://rpg.stackexchange.com/a/210217/72732)
* [*Neon City Overdrive*](https://rpg.stackexchange.com/a/208640/72732)
* [*Broken Compass* / *Household* / *Outgunned*](https://rpg.stackexchange.com/a/203715/72732)
* [Probability that 0/4 players is dealt Blackjack](https://math.stackexchange.com/a/4817254/1035142)

[Here is a full search of answers in which I mention Icepool.](https://rpg.stackexchange.com/search?q=user%3A72732+icepool)

## Web applications

These are all client-side, powered by [Pyodide](https://pyodide.org/). Perhaps you will find inspiration for your own application.

* [Icecup](https://highdiceroller.github.io/icepool/apps/icecup.html), a simple frontend for scripting and graphing.
* Alex Recarey's [Face 2 Face Calculator](https://infinitythecalculator.com/) for *Infinity the Game* -- including the ability to be installed on Android and iOS and run without an internet connection.
* [Ability score rolling method calculator.](https://highdiceroller.github.io/icepool/apps/ability_scores.html)
* [Cortex Prime calculator.](https://highdiceroller.github.io/icepool/apps/cortex_prime.html)
* [*Legends of the Wulin* calculator.](https://highdiceroller.github.io/icepool/apps/legends_of_the_wulin.html)
* [Year Zero Engine calculator.](https://highdiceroller.github.io/icepool/apps/year_zero_engine.html)

## Paper on algorithm

Presented at [Artificial Intelligence and Interactive Digital Entertainment (AIIDE) 2022](https://sites.google.com/view/aiide-2022/).

[In the official proceedings.](https://ojs.aaai.org/index.php/AIIDE/article/view/21971)

[Preprint in this repository.](https://github.com/HighDiceRoller/icepool/blob/main/papers/icepool_preprint.pdf)

BibTeX:

```bibtex
@inproceedings{liu2022icepool,
    title={Icepool: Efficient Computation of Dice Pool Probabilities},
    author={Albert Julius Liu},
    booktitle={Eighteenth AAAI Conference on Artificial Intelligence and Interactive Digital Entertainment},
    volume={18},
    number={1},
    pages={258-265},
    year={2022},
    month={Oct.},
    eventdate={2022-10-24/2022-10-28},
    venue={Pomona, California},
    url={https://ojs.aaai.org/index.php/AIIDE/article/view/21971},
    doi={10.1609/aiide.v18i1.21971}
}
```

## Versioning

Frankly, I haven't made backwards compatibility a top priority. If you need specific behavior, I recommend version pinning. Typing is especially unstable.

## Similar projects

In roughly chronological order:

### Troll by Torben Ægidius Mogensen

http://hjemmesider.diku.dk/~torbenm/Troll/

The oldest general-purpose dice probability calculator I know of. It has an accompanying peer-reviewed paper.

### AnyDice by Jasper Flick

https://anydice.com/

Probably the most popular dice probability calculator in existence, and with good reason---its accessibility and shareability remains unparalleled. I still use it often for prototyping and as a second opinion.

### SnakeEyes by Noé Falzon

https://snake-eyes.io/

SnakeEyes demonstrated the viability of browser-based, client-side dice calculation, as well as introducing me to [Chart.js](https://www.chartjs.org/).

### dice_roll.py by Ilmari Karonen

https://gist.github.com/vyznev/8f5e62c91ce4d8ca7841974c87271e2f

This demonstrated the trick of iterating "vertically" over the outcomes of dice in a dice pool, rather than "horizontally" through the dice---one of the insights into creating a much faster dice pool algorithm.

### `dyce` by Matt Bogosian

https://github.com/posita/dyce

Another Python dice probability package. I've benefited greatly from exchanging our experiences.
