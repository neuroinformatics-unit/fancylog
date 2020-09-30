import sys
import logging

from fancylog import fancylog

import fancylog as package


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
        package,
        variables=[args, args.paths],
        verbose=verbose,
        timestamp=True,
    )

    logging.info("This is an info message")
    logging.debug("This is a debug message")
    logging.warning("This fun logging experience is about to end :(")


if __name__ == "__main__":
    main(sys.argv[1])
