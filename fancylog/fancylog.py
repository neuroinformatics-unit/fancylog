"""Wrapper around the standard logging module, with additional information."""

import contextlib
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from importlib.util import find_spec
from pathlib import Path

import numpy as np
import tifffile
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
    write_python=True,
    write_env_packages=True,
    write_variables=True,
    log_to_file=True,
    log_to_console=True,
    timestamp=True,
    logger_name=None,
):
    """Prepare the log file, and then begin logging.

    Parameters
    ----------
    output_dir
        Directory to save the log file.
    package
        What Python package are we logging?
    variables
        List of objects whose attributes we want to log at the
        beginning of the log file.
    verbose
        If True, all info (i.e. 'DEBUG') is printed to console;
        else only 'INFO' and above. Default: True
    file_log_level
        What level of logging to print to file. Default: 'DEBUG'
    filename
        Filename for log file. Default: 'package.__name__'
    log_header
        Header for the log file, if the args are written.
    multiprocessing_aware
        Log from multiple processes. Default: True
    write_header
        Write a header for the log file. Default: True
    write_git
        Write information about the git repository. Default: True
    write_cli_args
        Log the command-line arguments. Default: True
    write_python
        Log the Python version. Default: True
    write_env_packages
        Log the packages in the environment. Default: True
    write_variables
        Write the attributes of selected objects. Default: True
    log_to_file
        If True, write a log file; otherwise just print to terminal.
    log_to_console
        Print logs to the console or not. Default: True
    timestamp
        If True, add a timestamp to the filename.
    logger_name
        If None, logger uses default logger; otherwise, logger
        name is set to `logger_name`.

    Returns
    -------
    path
        Path to the logging file.

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
            write_python=write_python,
            write_env_packages=write_env_packages,
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
    """Manage and write the log header."""

    def __init__(
        self,
        file,
        program,
        variable_objects,
        output_dir,
        write_header=True,
        write_git=True,
        write_cli_args=True,
        write_python=True,
        write_env_packages=True,
        write_variables=True,
        log_header=None,
    ):
        """Initialize LoggingHeader and write header to the log file.

        See start_logging() for parameters.
        """
        self.program = program

        with open(file, "w", encoding="utf-8") as self.file:
            if write_header:
                self.write_log_header(output_dir, log_header)
            if write_git:
                self.write_git_info(self.program.__name__)
            if write_cli_args:
                self.write_command_line_arguments()
            if write_python:
                self.write_python_version()
            if write_env_packages:
                self.write_environment_packages()
            if write_variables and variable_objects:
                self.write_variables(variable_objects)

    def write_git_info(self, program_name, header="GIT INFO"):
        """Write information about the git repository state.

        Parameters
        ----------
        program_name
            The name of the installed package, to
            locate and inspect its Git repository.
        header
            The section header to use. Default is "GIT INFO".

        """
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
        """Write the command-line arguments used to run the script.

        Parameters
        ----------
        header
            Title of the section that will be written to the log file.

        """
        self.write_separated_section_header(header)
        self.file.write(f"Command: {sys.argv[0]} \n")
        self.file.write(f"Input arguments: {sys.argv[1:]}")

    def write_python_version(self, header="PYTHON VERSION"):
        """Write the Python version used to run the script.

        Parameters
        ----------
        header
            Title of the section that will be written to the log file.

        """
        self.write_separated_section_header(header)
        self.file.write(f"Python version: {sys.version.split()[0]}")

    def write_environment_packages(self, header="ENVIRONMENT"):
        """Write the local/global environment packages used to run the script.

        Attempt to collect conda packages and, if this fails,
        collect pip packages.

        Parameters
        ----------
        header
            Title of the section that will be written to the log file

        """
        self.write_separated_section_header(header)

        # Attempt to log conda env name and packages
        try:
            conda_env = os.environ["CONDA_PREFIX"].split(os.sep)[-1]
            conda_exe = os.environ["CONDA_EXE"]
            conda_list = subprocess.run(
                [conda_exe, "list", "--json"], capture_output=True, text=True
            )

            env_pkgs = json.loads(conda_list.stdout)

            self.file.write(f"Conda environment: {conda_env}\n\n")
            self.file.write("Environment packages (conda):\n")
            self.write_packages(env_pkgs)

        # If no conda env, fall back to logging pip
        except KeyError:
            python_executable = sys.executable
            pip_list = subprocess.run(
                [
                    python_executable,
                    "-m",
                    "pip",
                    "list",
                    "--verbose",
                    "--format=json",
                ],
                capture_output=True,
                text=True,
            )

            all_pkgs = json.loads(pip_list.stdout)

            try:
                # If there is a local env, log local packages first
                env_pkgs = [
                    pkg
                    for pkg in all_pkgs
                    if os.getenv("VIRTUAL_ENV") in pkg["location"]
                ]

                self.file.write(
                    "No conda environment found, reporting pip packages\n\n"
                )
                self.file.write("Local environment packages (pip):\n")
                self.write_packages(env_pkgs)
                self.file.write("\n")

                # Log global-available packages (if any)
                global_pkgs = [pkg for pkg in all_pkgs if pkg not in env_pkgs]

                self.file.write("Global environment packages (pip):\n")
                self.write_packages(global_pkgs)

            except TypeError:
                self.file.write(
                    "No environment found, reporting global pip packages\n\n"
                )
                self.write_packages(all_pkgs)

    def write_packages(self, env_pkgs):
        """Write the packages in the local environment.

        Parameters
        ----------
        env_pkgs
            A dictionary of environment packages, the name and version
            of which will be written.

        """
        self.file.write(f"{'Name':20} {'Version':15}\n")
        for pkg in env_pkgs:
            self.file.write(f"{pkg['name']:20} {pkg['version']:15}\n")

    def write_variables(self, variable_objects):
        """Write a section for variables with their values.

        Parameters
        ----------
        variable_objects
            A list of python objects, the attributes of which will be written.

        """
        self.write_separated_section_header("VARIABLES", bottom_separator="\n")
        if hasattr(variable_objects[0], "__dict__"):
            self.write_variables_from_object_list(variable_objects)
        else:
            self.write_variables_from_slot_type_list(variable_objects)
        self.write_separated_section_header("LOGGING")

    def write_variables_from_slot_type_list(self, variable_objects):
        """Write variables and their values from a namedtuple-like object.

        Parameters
        ----------
        variable_objects
            An object with a `_asdict()` method (e.g., a namedtuple)
            containing variables to write.

        """
        for attr, value in variable_objects._asdict().items():
            self.file.write(f"{attr}: {value}\n")

    def write_variables_from_object_list(self, variable_objects):
        """Write attributes of each object in a list.

        Parameters
        ----------
        variable_objects
            A list of objects whose attributes will be written to the file.

        """
        for variable_object in variable_objects:
            self.file.write(f"\n{variable_object.__class__.__name__}:\n")
            for attr, value in variable_object.__dict__.items():
                # if one object belongs to another
                if value not in variable_objects:
                    self.file.write(f"{attr}: {value}\n")

    def write_log_header(self, output_dir, log_header):
        """Write the log header.

         The header includes time, output directory,
         and current directory.

        Parameters
        ----------
        output_dir
            The path to the output directory to include in the log.
        log_header
            Optional custom header text. If None, defaults to "LOG".

        """
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
        r"""Write a section header with optional top and bottom separators.

        Parameters
        ----------
        section_header
            The section header text to write.
        top_sep
            Whether to write the top separator before the section header.
        bottom_sep
            Whether to write the bottom separator after the section header.
        top_separator
            The string to use as the top separator. Default: "\\n\\n"
        bottom_separator
            The string to use as the bottom separator. Default: "\\n\\n"

        """
        if top_sep:
            self.write_separator(separator=top_separator)
        self.write_section_header(section_header)
        if bottom_sep:
            self.write_separator(separator=bottom_separator)

    def write_separator(self, separator="\n\n\n"):
        r"""Write a separator string to the file.

        Parameters
        ----------
        separator
            The separator string to write. Default: "\\n\\n\\n"

        """
        self.file.write(separator)

    def write_section_header(
        self, section_header, lateral_separator="**************"
    ):
        """Write a section header framed by a lateral separator.

        Parameters
        ----------
        section_header
            The section header text to write.
        lateral_separator
            The string used to frame the section header.
            Default: "**************"

        """
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
    """Set up (possibly multiprocessing aware) logging.

    Parameters
    ----------
    filename
        Where to save the logs to.
    print_level
        What level of logging to print to console. Default: 'INFO'
    file_level
        What level of logging to print to file. Default: 'DEBUG'
    log_to_console
        Print logs to the console or not.
    logger_name
        If None, logger uses default logger. Otherwise, logger name
        is set to `logger_name`.

    """
    if logger_name:
        logger = logging.getLogger(logger_name)
        logger.handlers = []
        logger.propagate = False
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
    """Set up (possibly multiprocessing-aware) logging.

    Parameters
    ----------
    filename
        Path to the file where logs will be saved.
    print_level
        Logging level for console output. Default is 'INFO'.
    file_level
        Logging level for file output. Default is 'DEBUG'.
    multiprocessing_aware
        If True, enables multiprocessing-safe logging. Default is True.
    log_to_console
        If True, logs will also be printed to the console. Default is True.
    logger_name
        Name of the logger to use. If None, the default logger is used.

    """
    logger = initialise_logger(
        filename,
        print_level=print_level,
        file_level=file_level,
        log_to_console=log_to_console,
        logger_name=logger_name,
    )
    if multiprocessing_aware:
        if logger_name:
            raise ValueError(
                "`multiprocessing_aware` is not supported"
                "with `logger_name`. Multiprocess logging"
                "must be performed with the root logger."
            )

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
        logger.info("Starting logging")
        logger.info("Not logging multiple processes")


def disable_logging():
    """Prevent any more logging.

    Saves remembering that logging.disable() with
    no argument doesn't work.
    """
    logging.disable(2**63 - 1)


def log_image(
    image: np.ndarray,
    name: str,
    logging_dir: str,
    subfolder: str = "media/images",
    metadata: dict | None = None,
):
    """Save an image to the logging dir and record its path in the log."""
    output_dir = Path(logging_dir)
    image_dir = output_dir / subfolder
    image_dir.mkdir(parents=True, exist_ok=True)

    filepath = image_dir / f"{name}.tiff"
    tifffile.imwrite(filepath, image)

    if metadata:
        meta_path = image_dir / f"{name}_meta.json"
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

    logging.getLogger(__name__).info(f"[fancylog] Saved image: {filepath}")
    return filepath


def log_data_object(
    data,
    name: str,
    logging_dir: str,
    subfolder: str = "media/data",
    ext: str = "json",
):
    """Save structured data (e.g., dict, list, numpy array) to disk."""
    output_dir = Path(logging_dir)
    data_dir = output_dir / subfolder
    data_dir.mkdir(parents=True, exist_ok=True)

    filepath = data_dir / f"{name}.{ext}"

    if isinstance(data, (dict | list)):
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    elif isinstance(data, np.ndarray):
        np.save(filepath, data)
    else:
        raise ValueError("Unsupported data type for logging")

    logging.getLogger(__name__).info(
        f"[fancylog] Saved data object: {filepath}"
    )
    return filepath
