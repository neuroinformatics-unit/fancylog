import time

import pytest

import fancylog


@pytest.mark.parametrize("write_env_packages", [True, False])
def test_benchmark(tmp_path, capsys, write_env_packages):
    start_time = time.perf_counter()

    for _ in range(5):
        fancylog.start_logging(
            tmp_path,
            fancylog,
            write_env_packages=write_env_packages,
            logger_name="my_logger",
        )

    time_taken = time.perf_counter() - start_time

    capsys.readouterr()
    with capsys.disabled():
        print(
            f"TIME TAKEN with "
            f"write_env_packages={write_env_packages}: {time_taken}"
        )
