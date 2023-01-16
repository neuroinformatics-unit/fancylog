from pathlib import Path

import fancylog

lateral_separator = "**************"


def test_import():
    print(fancylog.__version__)


def test_start_logging(tmpdir):
    fancylog.start_logging(tmpdir, fancylog)

    log_file = next(Path(tmpdir).glob("*.log"))
    with open(log_file) as file:
        lines = file.readlines()

    assert len(lines) == 20

    assert lines[0] == f"{lateral_separator}  LOG  {lateral_separator}\n"
    assert lines[1] == "\n"
    assert lines[2].startswith("Ran at")
    assert lines[3].startswith("Output directory: ")
    assert lines[4].startswith("Current directory: ")
    assert lines[5].startswith("Version: ")
