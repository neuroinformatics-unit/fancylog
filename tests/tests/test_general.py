import json
import logging
import os
import platform
import subprocess
import sys
from importlib.metadata import distributions
from unittest.mock import MagicMock, patch

import pytest
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
    """Quick check that expecter logger name is created
    when specified.
    """
    logger_name = "hello_world"

    # Logger name should not already exist
    assert logger_name not in logging.root.manager.loggerDict

    # Logger name should be created
    fancylog.start_logging(tmp_path, fancylog, logger_name=logger_name)

    assert logger_name in logging.root.manager.loggerDict


def test_assert_named_logger_with_multiprocessing(tmp_path):
    """Test an error is raised if trying to use multiprocess
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


def test_logging_to_console(tmp_path, capsys):
    """Check that logs are written to stdout when
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
    """Test the handlers on the logger are as specified by the
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
    """When a named logger is requested, the handlers
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


def test_named_logger_doesnt_propagate(tmp_path, capsys):
    """By default, named loggers will propagate through
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
    assert "PQ&*" not in captured.out, (
        "logger writing to stdout through root handler"
    )


@pytest.mark.parametrize("boolean, operator", [(True, True), (False, False)])
def test_python_version_header(boolean, operator, tmp_path):
    ver_header = f"{lateral_separator}  PYTHON VERSION  {lateral_separator}\n"

    fancylog.start_logging(tmp_path, fancylog, write_python=boolean)

    log_file = next(tmp_path.glob("*.log"))

    with open(log_file) as file:
        assert (ver_header in file.read()) == operator


def test_correct_python_version_logged(tmp_path):
    """Python version logged should be equal to
    the output of platform.python_version().
    """

    fancylog.start_logging(tmp_path, fancylog, write_python=True)

    log_file = next(tmp_path.glob("*.log"))

    # Test logged python version is equal to platform.python_version()
    with open(log_file) as file:
        assert f"Python version: {platform.python_version()}" in file.read()


@pytest.mark.parametrize("boolean, operator", [(True, True), (False, False)])
def test_environment_header(boolean, operator, tmp_path):
    ver_header = f"{lateral_separator}  ENVIRONMENT  {lateral_separator}\n"

    fancylog.start_logging(tmp_path, fancylog, write_env_packages=boolean)

    log_file = next(tmp_path.glob("*.log"))

    with open(log_file) as file:
        assert (ver_header in file.read()) == operator


def test_correct_pkg_version_logged(tmp_path):
    """Package versions logged should be equal to
    the output of `conda list` or `pip list`.
    """
    fancylog.start_logging(tmp_path, fancylog, write_env_packages=True)

    log_file = next(tmp_path.glob("*.log"))

    try:
        # If there is a conda environment, assert that the correct
        # version is logged for all pkgs
        conda_exe = os.environ["CONDA_EXE"]
        conda_list = subprocess.run(
            [conda_exe, "list", "--json"], capture_output=True, text=True
        )

        conda_pkgs = json.loads(conda_list.stdout)
        for pkg in conda_pkgs:
            assert f"{pkg['name']:20} {pkg['version']:15}\n"

    except KeyError:
        # If there is no conda environment, assert that the correct
        # version is logged for all packages logged with pip list
        with open(log_file) as file:
            file_content = file.read()

            # Test local environment versions
            local_site_packages = next(
                p for p in sys.path if "site-packages" in p
            )

            for dist in distributions():
                if str(dist.locate_file("")).startswith(local_site_packages):
                    assert (
                        f"{dist.metadata['Name']:20} {dist.version}"
                        in file_content
                    )


def test_mock_pip_pkgs(tmp_path):
    """Mock pip list subprocess
    and test that packages are logged correctly.
    """

    # Simulated `conda list --json` output
    fake_pip_output = json.dumps(
        [
            {"name": "fancylog", "version": "1.1.1", "location": "fake_env"},
            {"name": "pytest", "version": "1.1.1", "location": "global_env"},
        ]
    )

    # Patch the environment and subprocess
    with (
        patch.dict(os.environ, {}, clear=False),
        patch("os.getenv") as mock_getenv,
        patch("subprocess.run") as mock_run,
    ):
        # Eliminate conda environment packages triggers logging pip list
        (os.environ.pop("CONDA_PREFIX", None),)
        os.environ.pop("CONDA_EXE", None)

        mock_getenv.return_value = "fake_env"

        # Mocked subprocess result
        mock_run.return_value = MagicMock(stdout=fake_pip_output, returncode=0)

        fancylog.start_logging(tmp_path, fancylog, write_env_packages=True)

        log_file = next(tmp_path.glob("*.log"))

        # Log contains conda subheaders and mocked pkgs versions
        with open(log_file) as file:
            file_content = file.read()

            assert (
                "No conda environment found, reporting pip packages"
            ) in file_content

            assert f"{'fancylog':20} {'1.1.1'}"
            assert f"{'pytest':20} {'1.1.1'}"


def test_mock_conda_pkgs(tmp_path):
    """Mock conda environment variables
    and test that packages are logged correctly.
    """

    fake_conda_env_name = "test_env"
    fake_conda_prefix = os.path.join(
        "path", "conda", "envs", fake_conda_env_name
    )
    fake_conda_exe = os.path.join("fake", "conda")

    # Simulated `conda list --json` output
    fake_conda_output = json.dumps(
        [
            {"name": "fancylog", "version": "1.1.1"},
            {"name": "pytest", "version": "1.1.1"},
        ]
    )

    # Patch the environment and subprocess
    with (
        patch.dict(
            os.environ,
            {"CONDA_PREFIX": fake_conda_prefix, "CONDA_EXE": fake_conda_exe},
        ),
        patch("subprocess.run") as mock_run,
    ):
        # Mocked subprocess result
        mock_run.return_value = MagicMock(
            stdout=fake_conda_output, returncode=0
        )

        fancylog.start_logging(tmp_path, fancylog, write_env_packages=True)

        log_file = next(tmp_path.glob("*.log"))

        # Log contains conda subheaders and mocked pkgs versions
        with open(log_file) as file:
            file_content = file.read()

            assert "Conda environment:" in file_content
            assert "Environment packages (conda):" in file_content
            assert f"{'fancylog':20} {'1.1.1'}"
            assert f"{'pytest':20} {'1.1.1'}"
