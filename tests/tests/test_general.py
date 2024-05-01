import logging

import pytest

import fancylog

lateral_separator = "**************"


def test_import():
    print(fancylog.__version__)


def test_start_logging(tmp_path):
    fancylog.start_logging(tmp_path, fancylog)

    log_file = next(tmp_path.glob("*.log"))
    with open(log_file) as file:
        lines = file.readlines()

    assert lines[0] == f"{lateral_separator}  LOG  {lateral_separator}\n"
    assert lines[1] == "\n"
    assert lines[2].startswith("Ran at")
    assert lines[3].startswith("Output directory: ")
    assert lines[4].startswith("Current directory: ")
    assert lines[5].startswith("Version: ")


def test_logger_name(tmp_path):
    """
    Quick check that expecter logger name is created
    when specified.
    """
    logger_name = "hello_world"

    # Logger name should not already exist
    assert logger_name not in logging.root.manager.loggerDict

    # Logger name should be created
    fancylog.start_logging(tmp_path, fancylog, logger_name=logger_name)

    assert logger_name in logging.root.manager.loggerDict


def test_assert_named_logger_with_multiprocessing(tmp_path):
    """
    Test an error is raised if trying to use multiprocess
    logging with a named logger.
    """
    with pytest.raises(ValueError) as e:
        fancylog.start_logging(
            tmp_path,
            fancylog,
            logger_name="hello_world",
            multiprocessing_aware=True,
        )

    assert "root logger" in str(e.value)
