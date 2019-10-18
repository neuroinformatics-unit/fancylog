# fancylog
Fancier logging with python.

Uses the standard python logging library, but (optionally) in addition:
* Logs code when using the multiprocessing module using 
[multiprocessing-logging](https://github.com/jruere/multiprocessing-logging)
* Uses [gitpython](https://github.com/gitpython-developers/GitPython) 
to log information about the git environment. 
* Logs the command-line arguments used to run the software
* Logs object attributes


#### To install
```bash
pip install fancylog
```

#### To run example
```bash
git clone https://github.com/adamltyson/fancylog
pip install -e .
python fancylog/example.py /path/to/output/log/dir
```

If you run the example, you should get a log file that resembles 
[this](fancylog_2019-10-18_15-30-12.log)