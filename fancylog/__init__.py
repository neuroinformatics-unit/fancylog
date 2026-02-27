from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fancylog")
except PackageNotFoundError:
    # package is not installed
    pass

from fancylog.fancylog import start_logging
from fancylog.sublog import SubLog, sub_log