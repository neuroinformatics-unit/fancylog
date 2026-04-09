from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fancylog")
except PackageNotFoundError:
    # package is not installed
    pass

from fancylog.fancylog import (
    start_logging,
    get_default_logging_dir,
    log_image,
    log_data_object,
)
