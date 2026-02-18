"""Custom exceptions for the Time-Helper application."""

import subprocess
from typing import Optional


class TimeHelperError(Exception):
    """Base exception for all Time-Helper errors."""

    pass


class TimewarriorError(TimeHelperError):
    """Exception raised when a timewarrior command fails."""

    def __init__(
        self,
        message: str,
        original_error: Optional[subprocess.CalledProcessError] = None,
    ):
        super().__init__(message)
        self.original_error = original_error
