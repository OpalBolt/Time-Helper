import subprocess
from time_helper.exceptions import TimeHelperError, TimewarriorError

def test_time_helper_error_inheritance():
    """Test that TimeHelperError inherits from Exception."""
    err = TimeHelperError("Something went wrong")
    assert isinstance(err, Exception)
    assert str(err) == "Something went wrong"

def test_timewarrior_error_inheritance():
    """Test that TimewarriorError inherits from TimeHelperError."""
    err = TimewarriorError("Timew command failed")
    assert isinstance(err, TimeHelperError)
    assert isinstance(err, Exception)
    assert str(err) == "Timew command failed"

def test_timewarrior_error_with_original_error():
    """Test TimewarriorError with an original subprocess error."""
    cmd = ["timew", "start"]
    original_err = subprocess.CalledProcessError(1, cmd, output="output", stderr="error")
    
    err = TimewarriorError("Command failed", original_error=original_err)
    
    assert str(err) == "Command failed"
    assert err.original_error == original_err
    assert err.original_error.returncode == 1
