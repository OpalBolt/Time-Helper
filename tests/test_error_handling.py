"""Tests for global error handling."""

import pytest
import sys
from unittest.mock import patch, MagicMock
from time_helper.cli import main
from time_helper.exceptions import TimeHelperError


def test_main_handles_time_helper_error(capsys):
    """Test that main catches TimeHelperError and prints a clean message."""
    with patch("time_helper.cli.app") as mock_app:
        mock_app.side_effect = TimeHelperError("Something went wrong")
        
        with pytest.raises(SystemExit) as excinfo:
            main()
        
        assert excinfo.value.code == 1
        
        captured = capsys.readouterr()
        # Rich prints to stdout by default unless specified. 
        assert "Error: Something went wrong" in captured.out or "Error: Something went wrong" in captured.err
        assert "Traceback" not in captured.out
        assert "Traceback" not in captured.err


def test_main_handles_generic_exception(capsys):
    """Test that main catches generic Exceptions, logs them, and prints a generic message."""
    with patch("time_helper.cli.app") as mock_app:
        mock_app.side_effect = ValueError("Unexpected bug")
        
        with patch("time_helper.cli.logger") as mock_logger:
            with pytest.raises(SystemExit) as excinfo:
                main()
                
            assert excinfo.value.code == 1
            
            captured = capsys.readouterr()
            assert "An unexpected error occurred" in captured.out or "An unexpected error occurred" in captured.err
            assert "Unexpected bug" not in captured.out
            
            # Verify logging
            mock_logger.exception.assert_called_once_with("An unexpected error occurred")


def test_main_debug_mode_shows_traceback():
    """Test that tracebacks are shown (exception re-raised) when debug mode is enabled."""
    with patch("time_helper.cli.app") as mock_app:
        mock_app.side_effect = ValueError("Crash!")
        
        # Mock sys.argv to include --debug
        with patch("sys.argv", ["th", "--debug"]):
             with pytest.raises(ValueError, match="Crash!"):
                 main()
