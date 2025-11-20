import os
import time

import pytest

import fancylog


@pytest.mark.skipif(
    not os.getenv("GITHUB_ACTIONS"), reason="`RUN_BENCHMARKS` was false`"
)
def test_benchmark(tmp_path, capsys):
    """
    A very rough benchmark to check for large regressions
    in performance. Based on testing on GitHub CI:
        Windows	test_benchmark	0.026
        Ubuntu	test_benchmark	0.024
        macOS	test_benchmark	0.0104

    Only run in CI otherwise might fail on different systems as
    the cutoff threshold is based on GitHub runners.
    """
    start_time = time.perf_counter()

    for _ in range(5):
        fancylog.start_logging(
            tmp_path,
            fancylog,
            logger_name="my_logger",
        )

    time_taken = time.perf_counter() - start_time

    capsys.readouterr()
    with capsys.disabled():
        print(f"`test_benchmark` time taken: {time_taken}")

    assert time_taken < 0.04, "Set up is running slower than expected."
