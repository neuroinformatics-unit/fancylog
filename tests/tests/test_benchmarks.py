import time

import fancylog


def test_benchmark(tmp_path, capsys):
    """
    A very rough benchmark to check for large regressions
    in performance. Based on testing on GitHub CI:
        Windows	test_benchmark	0.026
        Ubuntu	test_benchmark	0.024
        macOS	test_benchmark	0.0104
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
        print(f"`test_benchmark` time taken: {time_taken:.4f}")

    assert time_taken < 0.05, "Set up is running slower than expected."
