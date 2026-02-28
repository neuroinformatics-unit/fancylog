"""Tests for the sub-logging feature."""

import os
import sys

import pytest

import fancylog
from fancylog.sublog import SubLog, sub_log


class TestSubLogCreation:
    """Test that sub-logs are created correctly."""

    def test_sub_log_creates_file(self, tmp_path):
        """A sub-log should create a separate log file."""
        fancylog.start_logging(
            tmp_path,
            fancylog,
            logger_name="main_test",
            log_to_console=False,
        )

        sl = SubLog(
            "preprocessing",
            tmp_path,
            parent_logger_name="main_test",
            timestamp=False,
        )

        assert os.path.exists(sl.log_file)
        assert sl.log_file == os.path.join(tmp_path, "preprocessing.log")

        sl.close()

    def test_sub_log_creates_file_with_timestamp(self, tmp_path):
        """A sub-log with timestamp=True should have a timestamped filename."""
        fancylog.start_logging(
            tmp_path,
            fancylog,
            logger_name="main_ts",
            log_to_console=False,
        )

        sl = SubLog(
            "preprocessing",
            tmp_path,
            parent_logger_name="main_ts",
            timestamp=True,
        )

        # Should not be just "preprocessing.log"
        assert "preprocessing_" in os.path.basename(sl.log_file)
        assert sl.log_file.endswith(".log")
        assert os.path.exists(sl.log_file)

        sl.close()

    def test_sub_log_has_own_logger(self, tmp_path):
        """The sub-log should have its own named logger."""
        fancylog.start_logging(
            tmp_path,
            fancylog,
            logger_name="main_logger_test",
            log_to_console=False,
        )

        sl = SubLog(
            "mysublog",
            tmp_path,
            parent_logger_name="main_logger_test",
            timestamp=False,
        )

        assert sl.logger.name == "main_logger_test.sublog.mysublog"
        assert sl.logger.propagate is False

        sl.close()

    def test_sub_log_without_parent_name(self, tmp_path):
        """Sub-log without parent_logger_name uses fancylog prefix."""
        sl = SubLog(
            "orphan",
            tmp_path,
            parent_logger_name=None,
            timestamp=False,
        )

        assert sl.logger.name == "fancylog.sublog.orphan"

        sl.close()


class TestSubLogWriting:
    """Test that sub-logs write messages correctly."""

    def test_sub_log_writes_to_own_file(self, tmp_path):
        """Messages logged to sub-log should appear in its file."""
        fancylog.start_logging(
            tmp_path,
            fancylog,
            logger_name="main_write",
            log_to_console=False,
        )

        sl = SubLog(
            "step1",
            tmp_path,
            parent_logger_name="main_write",
            timestamp=False,
        )

        sl.logger.info("Sub-log specific message")
        sl.close()

        with open(sl.log_file) as f:
            content = f.read()

        assert "Sub-log specific message" in content

    def test_sub_log_does_not_write_to_main_log(self, tmp_path):
        """Messages logged to sub-log should NOT appear in the main log."""
        main_log = fancylog.start_logging(
            tmp_path,
            fancylog,
            logger_name="main_isolated",
            log_to_console=False,
            timestamp=False,
        )

        sl = SubLog(
            "isolated_step",
            tmp_path,
            parent_logger_name="main_isolated",
            timestamp=False,
        )

        sl.logger.info("ONLY_IN_SUBLOG_12345")
        sl.close()

        with open(main_log) as f:
            main_content = f.read()

        # The sub-log message itself should not be in the main log
        # (only the reference messages should be)
        assert "ONLY_IN_SUBLOG_12345" not in main_content

    def test_main_log_contains_reference(self, tmp_path):
        """The main log should contain a reference to the sub-log file."""
        main_log = fancylog.start_logging(
            tmp_path,
            fancylog,
            logger_name="main_ref",
            log_to_console=False,
            timestamp=False,
        )

        sl = SubLog(
            "referenced_step",
            tmp_path,
            parent_logger_name="main_ref",
            timestamp=False,
        )

        sl.logger.info("doing work")
        sl.close()

        with open(main_log) as f:
            main_content = f.read()

        assert "Starting sub-log 'referenced_step'" in main_content
        assert "referenced_step.log" in main_content
        assert "Sub-log 'referenced_step' finished" in main_content


class TestSubLogContextManager:
    """Test the sub_log context manager."""

    def test_context_manager_creates_and_closes(self, tmp_path):
        """The context manager should create a sub-log and close it."""
        fancylog.start_logging(
            tmp_path,
            fancylog,
            logger_name="main_ctx",
            log_to_console=False,
        )

        with sub_log(
            "ctx_step",
            tmp_path,
            parent_logger_name="main_ctx",
            timestamp=False,
        ) as sl:
            sl.logger.info("Inside context manager")
            log_file = sl.log_file

        # After context manager exits, file should exist with content
        with open(log_file) as f:
            content = f.read()

        assert "Inside context manager" in content
        assert "Sub-log 'ctx_step' finished" in content

    def test_context_manager_closes_on_exception(self, tmp_path):
        """The context manager should close the sub-log even on exception."""
        fancylog.start_logging(
            tmp_path,
            fancylog,
            logger_name="main_exc",
            log_to_console=False,
        )

        log_file = None
        with (
            pytest.raises(ValueError, match="test error"),
            sub_log(
                "exc_step",
                tmp_path,
                parent_logger_name="main_exc",
                timestamp=False,
            ) as sl,
        ):
            log_file = sl.log_file
            sl.logger.info("Before exception")
            raise ValueError("test error")

        # Sub-log should still have been written and closed
        assert log_file is not None
        with open(log_file) as f:
            content = f.read()

        assert "Before exception" in content
        assert "Sub-log 'exc_step' finished" in content

    def test_multiple_sub_logs(self, tmp_path):
        """Multiple sub-logs can be created sequentially."""
        main_log = fancylog.start_logging(
            tmp_path,
            fancylog,
            logger_name="main_multi",
            log_to_console=False,
            timestamp=False,
        )

        with sub_log(
            "step1",
            tmp_path,
            parent_logger_name="main_multi",
            timestamp=False,
        ) as sl1:
            sl1.logger.info("Step 1 message")

        with sub_log(
            "step2",
            tmp_path,
            parent_logger_name="main_multi",
            timestamp=False,
        ) as sl2:
            sl2.logger.info("Step 2 message")

        # Both sub-log files should exist
        assert os.path.exists(os.path.join(tmp_path, "step1.log"))
        assert os.path.exists(os.path.join(tmp_path, "step2.log"))

        # Main log should reference both
        with open(main_log) as f:
            main_content = f.read()

        assert "step1" in main_content
        assert "step2" in main_content


class TestSubLogSubprocess:
    """Test subprocess capture in sub-logs."""

    def test_run_subprocess_captures_stdout(self, tmp_path):
        """Subprocess stdout should be captured in the sub-log."""
        fancylog.start_logging(
            tmp_path,
            fancylog,
            logger_name="main_proc",
            log_to_console=False,
        )

        with sub_log(
            "tool_output",
            tmp_path,
            parent_logger_name="main_proc",
            timestamp=False,
        ) as sl:
            result = sl.run_subprocess(
                [sys.executable, "-c", "print('hello from tool')"]
            )

        assert result.returncode == 0

        with open(sl.log_file) as f:
            content = f.read()

        assert "[stdout] hello from tool" in content

    def test_run_subprocess_captures_stderr(self, tmp_path):
        """Subprocess stderr should be captured in the sub-log."""
        fancylog.start_logging(
            tmp_path,
            fancylog,
            logger_name="main_stderr",
            log_to_console=False,
        )

        with sub_log(
            "tool_errors",
            tmp_path,
            parent_logger_name="main_stderr",
            timestamp=False,
        ) as sl:
            result = sl.run_subprocess(
                [
                    sys.executable,
                    "-c",
                    "import sys; sys.stderr.write('warning msg\\n')",
                ]
            )

        with open(sl.log_file) as f:
            content = f.read()

        assert "[stderr] warning msg" in content

    def test_run_subprocess_logs_return_code(self, tmp_path):
        """Subprocess return code should be logged."""
        fancylog.start_logging(
            tmp_path,
            fancylog,
            logger_name="main_rc",
            log_to_console=False,
        )

        with sub_log(
            "tool_rc",
            tmp_path,
            parent_logger_name="main_rc",
            timestamp=False,
        ) as sl:
            sl.run_subprocess([sys.executable, "-c", "exit(0)"])

        with open(sl.log_file) as f:
            content = f.read()

        assert "Command finished with return code 0" in content

    def test_run_subprocess_nonzero_exit(self, tmp_path):
        """Non-zero return codes from subprocesses should be logged."""
        fancylog.start_logging(
            tmp_path,
            fancylog,
            logger_name="main_nz",
            log_to_console=False,
        )

        with sub_log(
            "tool_fail",
            tmp_path,
            parent_logger_name="main_nz",
            timestamp=False,
        ) as sl:
            result = sl.run_subprocess([sys.executable, "-c", "exit(1)"])

        assert result.returncode == 1

        with open(sl.log_file) as f:
            content = f.read()

        assert "Command finished with return code 1" in content


class TestSubLogHandlerCleanup:
    """Test that handlers are properly cleaned up."""

    def test_handlers_removed_on_close(self, tmp_path):
        """All handlers should be removed when sub-log is closed."""
        sl = SubLog(
            "cleanup_test",
            tmp_path,
            timestamp=False,
        )

        assert len(sl.logger.handlers) > 0

        sl.close()

        assert len(sl.logger.handlers) == 0

    def test_handlers_removed_after_context_manager(self, tmp_path):
        """Handlers should be removed after context manager exits."""
        with sub_log("ctx_cleanup", tmp_path, timestamp=False) as sl:
            logger = sl.logger
            assert len(logger.handlers) > 0

        assert len(logger.handlers) == 0


class TestSubLogImports:
    """Test that sub-log classes are importable from fancylog."""

    def test_sublog_importable_from_fancylog(self):
        """SubLog should be importable from fancylog package."""
        assert hasattr(fancylog, "SubLog")
        assert hasattr(fancylog, "sub_log")

    def test_sublog_is_correct_class(self):
        """Imported SubLog should be the correct class."""
        assert fancylog.SubLog is SubLog
        assert fancylog.sub_log is sub_log
