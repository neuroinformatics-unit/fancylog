import logging
import sys

import fancylog


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
    logger.warning("This fun logging experience is about to end :(")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fancylog example")
    parser.add_argument("directory", metavar="directory", nargs=1, help="Directory for log files.")

    args = parser.parse_args()
    main(args.directory[0])
