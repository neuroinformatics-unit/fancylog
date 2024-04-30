"""fancylog
===============

Wrapper around the standard logging module, with additional information.

"""

import contextlib
import logging
import os
import sys
from datetime import datetime
from importlib.util import find_spec

from rich.logging import RichHandler

from fancylog.tools.git import (
    GitEnvironmentError,
    GitPythonError,
    get_git_info,
)


def start_logging(
    output_dir,
    package,
    variables=None,
    verbose=True,
    file_log_level="DEBUG",
    filename=None,
    log_header="LOG",
    multiprocessing_aware=False,
    write_header=True,
    write_git=True,
    write_cli_args=True,
    write_variables=True,
    log_to_file=True,
    log_to_console=True,
    timestamp=True,
    logger_name=None,
):
    """Prepares the log file, and then begins logging.

    :param output_dir: Directory to save the log file
    :param package: What python package are we logging?
    :param variables: List of objects whose attributes we want to log at the
    beginning of the log file
    :param verbose: If true, all info (i.e. 'DEBUG') is printed to
    console. Else, only 'INFO' and above. Default: True
    :param file_log_level: What level of logging to print to file.
    Default: 'DEBUG'
    :param filename: Filename for log file. Default: 'package.__name__'
    :param log_header: Header for the log file, if the args are written'
    :param multiprocessing_aware: Log from multiple processes. Default: True
    :param write_header: Write a header for the log file. Default: True
    :param write_git: Write information about the git repository.
    Default: True
    :param write_cli_args: Log the command-line arguments. Default: True
    :param write_variables: Write the attributes of selected objects.
    Default: True
    :param log_to_file: If True, write a log file, otherwise just print to
    terminal.
    :param log_to_console: Print logs to the console or not: Default: True
    :param timestamp: If True, add a timestamp to the filename
    :param logger_name: If None, logger uses default logger. Otherwise,
        logger name is set to `logger_name`.
    :return: Path to the logging file#
    """
    output_dir = str(output_dir)
    print_log_level = "DEBUG" if verbose else "INFO"

    if log_to_file:
        if filename is None:
            filename = package.__name__
        if timestamp:
            filename = datetime.now().strftime(filename + "_%Y-%m-%d_%H-%M-%S")
        logging_file = filename + ".log"
        try:
            logging_file = os.path.join(output_dir, logging_file)
        except TypeError:
            logging_file = output_dir.joinpath(logging_file)
    else:
        logging_file = None

    if logging_file is not None:
        LoggingHeader(
            logging_file,
            package,
            variables,
            output_dir,
            write_header=write_header,
            write_git=write_git,
            write_cli_args=write_cli_args,
            write_variables=write_variables,
            log_header=log_header,
        )

    setup_logging(
        logging_file,
        print_level=print_log_level,
        file_level=file_log_level,
        multiprocessing_aware=multiprocessing_aware,
        log_to_console=log_to_console,
        logger_name=logger_name,
    )
    return logging_file


class LoggingHeader:
    def __init__(
        self,
        file,
        program,
        variable_objects,
        output_dir,
        write_header=True,
        write_git=True,
        write_cli_args=True,
        write_variables=True,
        log_header=None,
    ):
        self.program = program

        with open(file, "w", encoding="utf-8") as self.file:
            if write_header:
                self.write_log_header(output_dir, log_header)
            if write_git:
                self.write_git_info(self.program.__name__)
            if write_cli_args:
                self.write_command_line_arguments()
            if write_variables and variable_objects:
                self.write_variables(variable_objects)

    def write_git_info(self, program_name, header="GIT INFO"):
        self.write_separated_section_header(header)
        try:
            program_path = find_spec(program_name).submodule_search_locations[
                0
            ]
            program_path = os.path.split(program_path)[0]
            git_info = get_git_info(program_path)

            self.file.write(f"Commit hash: {git_info.head.hash} \n")
            self.file.write(f"Commit message: {git_info.head.message} \n")
            self.file.write(f"Commit date & time: {git_info.head.datetime} \n")
            self.file.write(
                f"Commit author: {git_info.head.committer_name} \n"
            )
            self.file.write(
                f"Commit author email: {git_info.head.committer_email}"
            )

        except GitPythonError:
            self.file.write(
                "Gitpython is not installed. "
                "Cannot check if software is in a git repository"
            )

        except GitEnvironmentError:
            self.file.write(
                "Software does not appear to be in a git repository. "
                "Perhaps it was installed in some other way?"
            )

    def write_command_line_arguments(self, header="COMMAND LINE ARGUMENTS"):
        self.write_separated_section_header(header)
        self.file.write(f"Command: {sys.argv[0]} \n")
        self.file.write(f"Input arguments: {sys.argv[1:]}")

    def write_variables(self, variable_objects):
        self.write_separated_section_header("VARIABLES", bottom_separator="\n")
        if hasattr(variable_objects[0], "__dict__"):
            self.write_variables_from_object_list(variable_objects)
        else:
            self.write_variables_from_slot_type_list(variable_objects)
        self.write_separated_section_header("LOGGING")

    def write_variables_from_slot_type_list(self, variable_objects):
        for attr, value in variable_objects._asdict().items():
            self.file.write(f"{attr}: {value}\n")

    def write_variables_from_object_list(self, variable_objects):
        for variable_object in variable_objects:
            self.file.write(f"\n{variable_object.__class__.__name__}:\n")
            for attr, value in variable_object.__dict__.items():
                # if one object belongs to another
                if value not in variable_objects:
                    self.file.write(f"{attr}: {value}\n")

    def write_log_header(self, output_dir, log_header):
        if log_header is None:
            log_header = "LOG"
        self.write_separated_section_header(log_header, top_sep=False)
        self.file.write(
            "Ran at : " + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "\n"
        )
        self.file.write("Output directory: " + output_dir + "\n")
        self.file.write("Current directory: " + os.getcwd() + "\n")
        with contextlib.suppress(AttributeError):
            self.file.write(f"Version: {self.program.__version__}")

    def write_separated_section_header(
        self,
        section_header,
        top_sep=True,
        bottom_sep=True,
        top_separator="\n\n",
        bottom_separator="\n\n",
    ):
        if top_sep:
            self.write_separator(separator=top_separator)
        self.write_section_header(section_header)
        if bottom_sep:
            self.write_separator(separator=bottom_separator)

    def write_separator(self, separator="\n\n\n"):
        self.file.write(separator)

    def write_section_header(
        self, section_header, lateral_separator="**************"
    ):
        self.file.write(
            f"{lateral_separator}  {section_header}  {lateral_separator}"
        )


def initialise_logger(
    filename,
    print_level="INFO",
    file_level="DEBUG",
    log_to_console=True,
    logger_name=None,
):
    """Sets up (possibly multiprocessing aware) logging.
    :param filename: Where to save the logs to
    :param print_level: What level of logging to print to console.
    Default: 'INFO'
    :param file_level: What level of logging to print to file.
    Default: 'DEBUG'
    :param log_to_console: Print logs to the console or not
    :param logger_name: If None, logger uses default logger. Otherwise,
    logger name is set to `logger_name`.
    """
    if logger_name:
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger()

    logger.setLevel(getattr(logging, file_level))

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s"
        " - %(processName)s %(filename)s:%(lineno)s"
        " - %(message)s"
    )
    formatter.datefmt = "%Y-%m-%d %H:%M:%S %p"

    if filename is not None:
        fh = logging.FileHandler(filename, encoding="utf-8")
        fh.setLevel(getattr(logging, file_level))
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    if log_to_console:
        ch = RichHandler()
        ch.setLevel(getattr(logging, print_level))
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


def setup_logging(
    filename,
    print_level="INFO",
    file_level="DEBUG",
    multiprocessing_aware=True,
    log_to_console=True,
    logger_name=None,
):
    """Sets up (possibly multiprocessing aware) logging.
    :param filename: Where to save the logs to
    :param print_level: What level of logging to print to console.
    Default: 'INFO'
    :param file_level: What level of logging to print to file.
    Default: 'DEBUG'
    :param multiprocessing_aware: Default: True
    :param log_to_console: Print logs to the console or no.
    Default: True
    :param logger_name: If None, logger uses default logger. Otherwise,
        logger name is set to `logger_name`.
    """
    initialise_logger(
        filename,
        print_level=print_level,
        file_level=file_level,
        log_to_console=log_to_console,
        logger_name=logger_name,
    )
    if multiprocessing_aware:
        try:
            import multiprocessing_logging

            multiprocessing_logging.install_mp_handler()
            logging.info("Starting logging")
            logging.info(
                "Multiprocessing-logging module found. Logging from all"
                " processes"
            )
        except ModuleNotFoundError:
            logging.info("Starting logging")
            logging.info(
                "Multiprocessing-logging module not found, not logging "
                "multiple processes."
            )
    else:
        logging.info("Starting logging")
        logging.info("Not logging multiple processes")


def disable_logging():
    """Prevents any more logging. Saves remembering that logging.disable() with
    no argument doesn't work.
    :return:
    """
    logging.disable(2**63 - 1)
