"""Tests for the LoggingHeader formatting methods and disable_logging.

These tests focus on the header-writing helpers of
``fancylog.fancylog.LoggingHeader`` and on ``disable_logging``,
which were previously not directly exercised by the test suite.
They are deterministic and avoid asserting on timestamps or on
environment-specific package lists.

Resolves part of issue #8 ("Add more tests").
"""

import logging
from collections import namedtuple

import fancylog
from fancylog.fancylog import LoggingHeader, disable_logging

lateral_separator = "**************"


def _read_log(tmp_path):
    """Return the contents of the single ``*.log`` file in ``tmp_path``."""
    log_file = next(tmp_path.glob("*.log"))
    with open(log_file, encoding="utf-8") as file:
        return file.read()


def test_write_separator(tmp_path):
    """A custom separator string is written verbatim."""
    log_file = tmp_path / "sep.log"
    with open(log_file, "w", encoding="utf-8") as file:
        header = LoggingHeader.__new__(LoggingHeader)
        header.file = file
        header.write_separator(separator="---SEP---")

    assert log_file.read_text(encoding="utf-8") == "---SEP---"


def test_write_separator_default(tmp_path):
    """The default separator is three newlines."""
    log_file = tmp_path / "sep_default.log"
    with open(log_file, "w", encoding="utf-8") as file:
        header = LoggingHeader.__new__(LoggingHeader)
        header.file = file
        header.write_separator()

    assert log_file.read_text(encoding="utf-8") == "\n\n\n"


def test_write_section_header(tmp_path):
    """A section header is framed by the lateral separator."""
    log_file = tmp_path / "section.log"
    with open(log_file, "w", encoding="utf-8") as file:
        header = LoggingHeader.__new__(LoggingHeader)
        header.file = file
        header.write_section_header("MY SECTION")

    expected = f"{lateral_separator}  MY SECTION  {lateral_separator}"
    assert log_file.read_text(encoding="utf-8") == expected


def test_write_section_header_custom_separator(tmp_path):
    """A custom lateral separator is used to frame the header."""
    log_file = tmp_path / "section_custom.log"
    with open(log_file, "w", encoding="utf-8") as file:
        header = LoggingHeader.__new__(LoggingHeader)
        header.file = file
        header.write_section_header("X", lateral_separator="===")

    assert log_file.read_text(encoding="utf-8") == "===  X  ==="


def test_write_separated_section_header_with_separators(tmp_path):
    """Top and bottom separators wrap the framed section header."""
    log_file = tmp_path / "separated.log"
    with open(log_file, "w", encoding="utf-8") as file:
        header = LoggingHeader.__new__(LoggingHeader)
        header.file = file
        header.write_separated_section_header(
            "TITLE",
            top_separator="<T>",
            bottom_separator="<B>",
        )

    expected = f"<T>{lateral_separator}  TITLE  {lateral_separator}<B>"
    assert log_file.read_text(encoding="utf-8") == expected


def test_write_separated_section_header_no_separators(tmp_path):
    """Disabling the separators writes only the framed header."""
    log_file = tmp_path / "separated_none.log"
    with open(log_file, "w", encoding="utf-8") as file:
        header = LoggingHeader.__new__(LoggingHeader)
        header.file = file
        header.write_separated_section_header(
            "TITLE",
            top_sep=False,
            bottom_sep=False,
        )

    expected = f"{lateral_separator}  TITLE  {lateral_separator}"
    assert log_file.read_text(encoding="utf-8") == expected


def test_write_command_line_arguments(tmp_path):
    """The command line arguments section logs argv[0] and argv[1:]."""
    log_file = tmp_path / "cli.log"
    with open(log_file, "w", encoding="utf-8") as file:
        header = LoggingHeader.__new__(LoggingHeader)
        header.file = file
        header.write_command_line_arguments()

    content = log_file.read_text(encoding="utf-8")
    cli_header = (
        f"{lateral_separator}  COMMAND LINE ARGUMENTS  {lateral_separator}"
    )
    assert cli_header in content
    assert "Command: " in content
    assert "Input arguments: " in content


def test_write_python_version(tmp_path):
    """The Python version section logs the running interpreter version."""
    import platform

    log_file = tmp_path / "py.log"
    with open(log_file, "w", encoding="utf-8") as file:
        header = LoggingHeader.__new__(LoggingHeader)
        header.file = file
        header.write_python_version()

    content = log_file.read_text(encoding="utf-8")
    assert f"Python version: {platform.python_version()}" in content


def test_write_packages(tmp_path):
    """Packages are written as aligned name/version columns."""
    log_file = tmp_path / "pkgs.log"
    pkgs = [
        {"name": "alpha", "version": "1.0"},
        {"name": "beta", "version": "2.3.4"},
    ]
    with open(log_file, "w", encoding="utf-8") as file:
        header = LoggingHeader.__new__(LoggingHeader)
        header.file = file
        header.write_packages(pkgs)

    content = log_file.read_text(encoding="utf-8")
    assert f"{'Name':20} {'Version':15}" in content
    assert f"{'alpha':20} {'1.0':15}" in content
    assert f"{'beta':20} {'2.3.4':15}" in content


def test_write_log_header_default_title(tmp_path):
    """When ``log_header`` is None, the default 'LOG' title is used."""
    log_file = tmp_path / "header.log"
    with open(log_file, "w", encoding="utf-8") as file:
        header = LoggingHeader.__new__(LoggingHeader)
        header.file = file
        header.package = fancylog
        header.write_log_header(str(tmp_path), None)

    content = log_file.read_text(encoding="utf-8")
    assert f"{lateral_separator}  LOG  {lateral_separator}" in content
    assert "Ran at : " in content
    assert f"Output directory: {tmp_path}" in content
    assert "Current directory: " in content


def test_write_log_header_custom_title(tmp_path):
    """A custom ``log_header`` title is used to frame the header."""
    log_file = tmp_path / "header_custom.log"
    with open(log_file, "w", encoding="utf-8") as file:
        header = LoggingHeader.__new__(LoggingHeader)
        header.file = file
        header.package = fancylog
        header.write_log_header(str(tmp_path), "CUSTOM TITLE")

    content = log_file.read_text(encoding="utf-8")
    assert f"{lateral_separator}  CUSTOM TITLE  {lateral_separator}" in content


def test_write_variables_from_object_list(tmp_path):
    """Attributes of plain objects are written under their class name."""

    class Config:
        def __init__(self):
            self.threshold = 5
            self.name = "demo"

    log_file = tmp_path / "vars_obj.log"
    with open(log_file, "w", encoding="utf-8") as file:
        header = LoggingHeader.__new__(LoggingHeader)
        header.file = file
        header.write_variables([Config()])

    content = log_file.read_text(encoding="utf-8")
    assert f"{lateral_separator}  VARIABLES  {lateral_separator}" in content
    assert "Config:" in content
    assert "threshold: 5" in content
    assert "name: demo" in content


def test_write_variables_from_slot_type_list(tmp_path):
    """Attributes of a namedtuple are written via its ``_asdict`` mapping."""
    Settings = namedtuple("Settings", ["alpha", "beta"])
    settings = Settings(alpha=1, beta="two")

    log_file = tmp_path / "vars_slot.log"
    with open(log_file, "w", encoding="utf-8") as file:
        header = LoggingHeader.__new__(LoggingHeader)
        header.file = file
        header.write_variables(settings)

    content = log_file.read_text(encoding="utf-8")
    assert f"{lateral_separator}  VARIABLES  {lateral_separator}" in content
    assert "alpha: 1" in content
    assert "beta: two" in content


def test_start_logging_writes_variables_section(tmp_path):
    """``start_logging`` writes a VARIABLES section for passed objects."""

    class Params:
        def __init__(self):
            self.learning_rate = 0.01

    fancylog.start_logging(
        tmp_path,
        fancylog,
        variables=[Params()],
        write_variables=True,
    )

    content = _read_log(tmp_path)
    assert f"{lateral_separator}  VARIABLES  {lateral_separator}" in content
    assert "Params:" in content
    assert "learning_rate: 0.01" in content


def test_disable_logging_blocks_records(tmp_path):
    """``disable_logging`` prevents further records from being emitted."""
    logger_name = "disable_logging_test_logger"
    fancylog.start_logging(
        tmp_path,
        fancylog,
        logger_name=logger_name,
        log_to_console=False,
        log_to_file=True,
    )
    logger = logging.getLogger(logger_name)
    log_file = next(tmp_path.glob("*.log"))

    logger.critical("BEFORE_DISABLE_MARKER")
    for handler in logger.handlers:
        handler.flush()

    disable_logging()

    logger.critical("AFTER_DISABLE_MARKER")
    for handler in logger.handlers:
        handler.flush()

    # Re-enable logging so this test does not affect other tests.
    logging.disable(logging.NOTSET)

    content = log_file.read_text(encoding="utf-8")
    assert "BEFORE_DISABLE_MARKER" in content
    assert "AFTER_DISABLE_MARKER" not in content
