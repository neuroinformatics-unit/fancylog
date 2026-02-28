import logging
import sys

import fancylog
from fancylog.sublog import sub_log


class MadeUpPaths:
    def __init__(self):
        self.path1 = "/path/to/the_first_place"
        self.path2 = "/path/to/the_second_place"
        self.path3 = "/path/to/the_third_place"


class MadeUpArgs:
    def __init__(self):
        self.arg1 = True
        self.another_arg = "path/to/somewhere"
        self.the_last_arg = 1000

        self.paths = MadeUpPaths()


def main(directory):
    args = MadeUpArgs()
    verbose = True

    fancylog.start_logging(
        directory,
        fancylog,
        variables=[args, args.paths],
        verbose=verbose,
        timestamp=True,
        logger_name="my_logger",
    )

    logger = logging.getLogger("my_logger")

    logger.info("This is an info message")
    logger.debug("This is a debug message")

    logger.info("Starting pipeline...")

    with sub_log(
        "preprocessing",
        directory,
        parent_logger_name="my_logger",
        timestamp=True,
    ) as sl:
        sl.logger.info("Running preprocessing step 1")
        sl.logger.debug("Detailed preprocessing debug info")
        sl.logger.info("Running preprocessing step 2")

    with sub_log(
        "external_tool",
        directory,
        parent_logger_name="my_logger",
        timestamp=True,
    ) as sl:
        sl.logger.info("About to run external tool")
        sl.run_subprocess(
            [sys.executable, "-c", "print('Tool output line 1')"]
        )

    logger.info("here comes the completion of the example :(")
    logger.warning("This fun logging experience is about to end :(")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fancylog example")
    parser.add_argument(
        "directory",
        metavar="directory",
        nargs=1,
        help="Directory for log files.",
    )

    args = parser.parse_args()
    main(args.directory[0])
