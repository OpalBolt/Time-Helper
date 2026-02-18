import pytest
import subprocess
from unittest.mock import patch, MagicMock
from time_helper.cli.utils import run_timew_command, handle_timew_errors
from time_helper.exceptions import TimewarriorError


def test_run_timew_command_success():
    """Test that run_timew_command returns CompletedProcess on success."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = "success output"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = run_timew_command(["args"])
        assert result.stdout == "success output"


def test_run_timew_command_raises_timewarrior_error():
    """Test that run_timew_command raises TimewarriorError on failure."""
    with patch("subprocess.run") as mock_run:
        # Simulate subprocess.run raising CalledProcessError
        cmd = ["timew", "args"]
        error = subprocess.CalledProcessError(
            1, cmd, output="output", stderr="Error message"
        )  # noqa: E501
        mock_run.side_effect = error

        with pytest.raises(TimewarriorError) as excinfo:
            run_timew_command(["args"])

        assert str(excinfo.value) == "Error message"
        assert excinfo.value.original_error == error


def test_run_timew_command_extracts_stdout_if_stderr_empty():
    """Test that run_timew_command uses stdout if stderr is empty."""
    with patch("subprocess.run") as mock_run:
        cmd = ["timew", "args"]
        error = subprocess.CalledProcessError(
            1, cmd, output="Error in stdout", stderr=""
        )  # noqa: E501
        mock_run.side_effect = error

        with pytest.raises(TimewarriorError) as excinfo:
            run_timew_command(["args"])

        assert str(excinfo.value) == "Error in stdout"


def test_handle_timew_errors_catches_timewarrior_error():
    """Test that handle_timew_errors catches TimewarriorError and prints message, then re-raises."""  # noqa: E501

    @handle_timew_errors
    def failing_func():
        raise TimewarriorError("No data found")

    with patch("time_helper.cli.utils.rprint") as mock_rprint:
        # It should raise the exception after printing
        with pytest.raises(TimewarriorError):
            failing_func()

        mock_rprint.assert_called_with(
            "[yellow]No data found for the specified timespan[/yellow]"
        )  # noqa: E501


def test_handle_timew_errors_catches_timewarrior_error_unknown():
    """Test that handle_timew_errors catches unknown TimewarriorError and re-raises."""  # noqa: E501

    @handle_timew_errors
    def failing_func():
        raise TimewarriorError("Some unknown error")

    with patch("time_helper.cli.utils.rprint") as mock_rprint:
        with pytest.raises(TimewarriorError):
            failing_func()

        # Should NOT print unknown errors anymore, as the global handler does it  # noqa: E501
        mock_rprint.assert_not_called()
