[![Python Version](https://img.shields.io/pypi/pyversions/cellfinder.svg)](https://pypi.org/project/cellfinder)
[![PyPI](https://img.shields.io/pypi/v/fancylog.svg)](https://pypi.org/project/fancylog)
[![Downloads](https://pepy.tech/badge/fancylog)](https://pepy.tech/project/fancylog)
[![Wheel](https://img.shields.io/pypi/wheel/fancylog.svg)](https://pypi.org/project/fancylog)
[![Development Status](https://img.shields.io/pypi/status/fancylog.svg)](https://github.com/neuroinformatics-unit/fancylog)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
[![Contributions](https://img.shields.io/badge/Contributions-Welcome-brightgreen.svg)](https://github.com/neuroinformatics-unit/fancylog)

# fancylog
Fancier logging with python.

Uses the standard python logging library, but (optionally) in addition:
* Logs code when using the multiprocessing module using
[multiprocessing-logging](https://github.com/jruere/multiprocessing-logging)
* Uses [GitPython](https://github.com/gitpython-developers/GitPython)
to log information about the git environment.
* Logs the command-line arguments used to run the software
* Logs object attributes


#### To install
```bash
pip install fancylog
```

N.B. For the git logging to work, you need to have [git](https://git-scm.com/) and the
[GitPython](https://github.com/gitpython-developers/GitPython) package
installed. The latter can be installed along with `fancylog` using:

```bash
pip install fancylog[git]
```

#### To run example
```bash
git clone https://github.com/neuroinformatics-unit/fancylog
pip install -e .
python fancylog/example.py /path/to/output/log/dir
```

If you run the example, you should get a log file that resembles
[this](fancylog_2019-10-18_15-30-12.log)
