import logging

from rich.logging import RichHandler

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


def test_logging_to_console(tmp_path, capsys):
    """
    Check that logs are written to stdout when
    `log_to_console` is `True`.
    """
    logger_name = "hello_world"

    fancylog.start_logging(
        tmp_path, fancylog, log_to_console=True, logger_name=logger_name
    )

    logger = logging.getLogger(logger_name)

    logger.debug("!!£%$")

    captured = capsys.readouterr()

    assert "!!£%$" in captured.out


def test_correct_handlers_are_set(tmp_path):
    """
    Test the handlers on the logger are as specified by the
    `start_logging` call. Note this cannot be tested
    on the root logger has it holds handlers that
    were assigned in earlier tests.
    """
    logger_name = "hello_world"

    # Test no handlers are assigned when not requested
    fancylog.start_logging(
        tmp_path,
        fancylog,
        logger_name=logger_name,
        log_to_console=False,
        log_to_file=False,
    )

    logger = logging.getLogger(logger_name)

    assert logger.handlers == []

    # Test RichHandler only is assigned when requested
    fancylog.start_logging(
        tmp_path,
        fancylog,
        logger_name=logger_name,
        log_to_console=True,
        log_to_file=False,
    )

    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], RichHandler)

    # Test FileHandler only is assigned when requested
    fancylog.start_logging(
        tmp_path,
        fancylog,
        logger_name=logger_name,
        log_to_console=False,
        log_to_file=True,
    )

    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.FileHandler)

    # Test both handlers are assigned when requested
    fancylog.start_logging(
        tmp_path,
        fancylog,
        logger_name=logger_name,
        log_to_console=True,
        log_to_file=True,
    )

    assert len(logger.handlers) == 2
    assert isinstance(logger.handlers[0], logging.FileHandler)
    assert isinstance(logger.handlers[1], RichHandler)


def test_handlers_are_refreshed(tmp_path):
    """
    When a named logger is requested, the handlers
    are reset to that handlers assigned on previous
    calls are not carried over to the most recent call.
    """
    logger_name = "hello_world"
    fancylog.start_logging(
        tmp_path,
        fancylog,
        logger_name=logger_name,
        log_to_console=False,
        log_to_file=False,
    )

    logger = logging.getLogger(logger_name)

    assert logger.handlers == []

    fancylog.start_logging(
        tmp_path,
        fancylog,
        logger_name=logger_name,
        log_to_console=True,
        log_to_file=False,
    )

    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], RichHandler)

    fancylog.start_logging(
        tmp_path,
        fancylog,
        logger_name=logger_name,
        log_to_console=False,
        log_to_file=False,
    )

    assert logger.handlers == []


def test_named_logger_propagate(tmp_path, capsys):
    """
    By default, named loggers will propagate through
    parent handlers. Root is always parent to named loggers.
    This means that named logger can still print to console
    through the root StreamHandler unless `propagate` is set
    to `False`. Check here that propagate is set to False and
    indeed named logger does not print to console.
    """
    logger_name = "hello_world"

    fancylog.start_logging(
        tmp_path, fancylog, logger_name=logger_name, log_to_console=False
    )

    logger = logging.getLogger(logger_name)

    assert logger.propagate is False

    logger.debug("XN$£ not in stdout")

    logging.debug("YYXX in stdout")

    logger.debug("PQ&* not in stdout")

    captured = capsys.readouterr()

    assert "XN$£" not in captured.out, "logger initially writing to stdout"
    assert "YYXX" in captured.out, "root is not writing to stdout"
    assert (
        "PQ&*" not in captured.out
    ), "logger writing to stdout through root handler"
