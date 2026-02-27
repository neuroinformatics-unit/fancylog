"""Sub-logging support for fancylog.

purpose: to create separate log files for specific
computations or third-party tools, linked from the main log.
"""

import logging
import os
import subprocess
from contextlib import contextmanager
from datetime import datetime


class SubLog:
    """A sub-log linked to a parent logger.

    Creates a separate log file for a specific computation or tool,
    and logs a reference in the parent logger pointing to the sub-log.

    Parameters
    ----------
    name : str
        Name of the sub-log .
    output_dir : str
        directory where the sub-log file will be saved.
    parent_logger_name : str or None
        name of the parent logger. If None, uses the root logger.
    file_log_level : str
        Logging level for the sub-log file. Default: 'DEBUG'.
    log_to_console : bool
        Whether to also print sub-log messages to the console.
        Default: False.
    timestamp : bool
        Whether to add a timestamp to the sub-log filename.
        Default: True.

    Attributes
    ----------
    logger : logging.Logger
        The sub-log's logger instance.
    log_file : str
        Path to the sub-log file.

    """

    def __init__(
        self,
        name,
        output_dir,
        parent_logger_name=None,
        file_log_level="DEBUG",
        log_to_console=False,
        timestamp=True,
    ):
        self.name = name
        self.output_dir = str(output_dir)
        self.parent_logger_name = parent_logger_name
        self.file_log_level = file_log_level

        filename = name
        if timestamp:
            filename = datetime.now().strftime(filename + "_%Y-%m-%d_%H-%M-%S")
        self.log_file = os.path.join(self.output_dir, filename + ".log")

        # sublogger as a child of the parent
        if parent_logger_name:
            sub_logger_name = f"{parent_logger_name}.sublog.{name}"
        else:
            sub_logger_name = f"fancylog.sublog.{name}"

        self.logger = logging.getLogger(sub_logger_name)
        self.logger.handlers = []
        self.logger.propagate = False
        self.logger.setLevel(getattr(logging, file_log_level))

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s"
            " - %(processName)s %(filename)s:%(lineno)s"
            " - %(message)s"
        )
        formatter.datefmt = "%Y-%m-%d %H:%M:%S %p"

        fh = logging.FileHandler(self.log_file, encoding="utf-8")
        fh.setLevel(getattr(logging, file_log_level))
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        if log_to_console:
            try:
                from rich.logging import RichHandler

                ch = RichHandler()
            except ImportError:
                ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

        # get the parent logger and log a reference
        if parent_logger_name:
            self._parent_logger = logging.getLogger(parent_logger_name)
        else:
            self._parent_logger = logging.getLogger()

        self._parent_logger.info(
            "Starting sub-log '%s', see %s for details", name, self.log_file
        )
        self.logger.info("Sub-log '%s' started", name)

    def close(self):
        """Close the sub-log and log a completion message in the parent."""
        self.logger.info("Sub-log '%s' finished", self.name)

        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

        self._parent_logger.info(
            "Sub-log '%s' finished, log saved to %s",
            self.name,
            self.log_file,
        )

    def run_subprocess(self, command, **kwargs):
        """Run a subprocess and capture its output in the sub-log.

        Parameters
        ----------
        command : list or str
            The command to run (passed to subprocess.run).
        **kwargs
            Additional keyword arguments passed to subprocess.run.
            Note: stdout and stderr will be set to subprocess.PIPE
            and cannot be overridden.

        Returns
        -------
        subprocess.CompletedProcess
            The result of the subprocess execution.

        """
        self.logger.info("Running command: %s", command)

        kwargs.pop("stdout", None)
        kwargs.pop("stderr", None)
        kwargs.pop("capture_output", None)

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            **kwargs,
        )

        if result.stdout:
            for line in result.stdout.strip().splitlines():
                self.logger.info("[stdout] %s", line)

        if result.stderr:
            for line in result.stderr.strip().splitlines():
                self.logger.warning("[stderr] %s", line)

        self.logger.info(
            "Command finished with return code %d", result.returncode
        )

        return result


@contextmanager
def sub_log(
    name,
    output_dir,
    parent_logger_name=None,
    file_log_level="DEBUG",
    log_to_console=False,
    timestamp=True,
):
    """Context manager for creating a sub-log.

    Creates a SubLog on entry and closes it on exit, ensuring
    that the sub-log is properly cleaned up even if an exception occurs.

    Parameters
    ----------
    name : str
        Name of the sub-log.
    output_dir : str
        Directory where the sub-log file will be saved.
    parent_logger_name : str or None
        Name of the parent logger. If None, uses the root logger.
    file_log_level : str
        Logging level for the sub-log file. Default: 'DEBUG'.
    log_to_console : bool
        Whether to also print sub-log messages to the console.
        Default: False.
    timestamp : bool
        whether to add a timestamp to the sub-log filename.
        Default: True.

    outputs:
    SubLog
        The sub-log instance.

    """
    sl = SubLog(
        name,
        output_dir,
        parent_logger_name=parent_logger_name,
        file_log_level=file_log_level,
        log_to_console=log_to_console,
        timestamp=timestamp,
    )
    try:
        yield sl
    finally:
        sl.close()
