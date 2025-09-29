import pytest

import fancylog


def test_no_package_passed(tmp_path):
    """
    Test error is wrong if neither `package` or
    `program` (deprecated) is raised.
    """
    with pytest.raises(ValueError) as e:
        fancylog.start_logging(tmp_path)

    assert "`package` or `program`" in str(e.value)


def test_program_warning_shown(tmp_path):
    """
    Test depreciation warning is shown for `program`.
    """
    with pytest.warns(DeprecationWarning) as w:
        fancylog.start_logging(tmp_path, program=fancylog)
    assert (
        "`program` is deprecated since 0.6.0 and will be removed in 0.7.0;"
        in str(w[0].message)
    )
