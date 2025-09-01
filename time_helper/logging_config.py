"""Logging configuration using loguru for the time-helper application."""

import sys
from pathlib import Path
from loguru import logger


def setup_logging(verbosity: int = 0) -> None:
    """Configure loguru logging with appropriate levels and formats.
    
    Args:
        verbosity: Verbosity level (0=silent, 1=info, 2=debug)
    """
    # Remove default handler
    logger.remove()
    
    # Determine console log level based on verbosity
    if verbosity == 0:
        console_level = "ERROR"  # Only show errors in normal operation
    elif verbosity == 1:
        console_level = "INFO"   # Show info messages with -v
    else:  # verbosity >= 2
        console_level = "DEBUG"  # Show debug messages with -vv
    
    # Console handler with color (only if verbosity > 0 or showing errors)
    if verbosity > 0:
        logger.add(
            sys.stderr,
            level=console_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            colorize=True,
            enqueue=True
        )
    else:
        # In silent mode, only show ERROR and CRITICAL messages
        logger.add(
            sys.stderr,
            level="ERROR",
            format="<red>Error:</red> <level>{message}</level>",
            colorize=True,
            enqueue=True
        )
    
    # File handler for persistent logging (always log everything to file)
    # Only create file logging if we can actually write to the filesystem
    try:
        log_dir = Path.home() / ".local" / "share" / "time-helper"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "time-helper.log"
        
        logger.add(
            str(log_file),
            level="DEBUG",  # Always log debug to file
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="1 month",
            compression="gz",
            enqueue=True
        )
        
        # Only log initialization messages if verbosity is enabled
        if verbosity > 0:
            logger.info(f"Logging initialized at console level {console_level}")
            logger.debug(f"Log file: {log_file}")
    except (PermissionError, OSError):
        # If we can't create the log directory (e.g., in Nix build environment),
        # just skip file logging and continue
        if verbosity > 0:
            logger.info(f"Logging initialized at console level {console_level} (file logging disabled)")


def get_logger(name: str):
    """Get a logger instance for a specific module.
    
    Args:
        name: Usually __name__ of the calling module
        
    Returns:
        Logger instance
    """
    return logger.bind(name=name)
