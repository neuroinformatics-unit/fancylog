import pytest

import fancylog


def test_no_package_passed(tmp_path):
    """
    Test error is raised if `package` is not passed.
    """
    with pytest.raises(ValueError) as e:
        fancylog.start_logging(tmp_path)

    assert "`package` must be passed" in str(e.value)
