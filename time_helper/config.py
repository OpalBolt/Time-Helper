"""Configuration management for time-helper."""

import os
import tomllib
import tomli_w
from pathlib import Path
from typing import Dict, Optional
from pydantic import BaseModel, field_validator


class ColorScheme(BaseModel):
    """Color scheme definition for terminal output."""

    name: str
    colors: list[str]

    def get_color_for_tag(self, tag: str) -> str:
        """Get a consistent color for a tag based on its name.

        Args:
            tag: Tag name to get color for

        Returns:
            Rich color name
        """
        color_index = hash(tag) % len(self.colors)
        return self.colors[color_index]


# Predefined color schemes
DEFAULT_SCHEME = ColorScheme(
    name="default",
    colors=[
        "red",
        "green",
        "yellow",
        "blue",
        "magenta",
        "cyan",
        "bright_red",
        "bright_green",
        "bright_yellow",
        "bright_blue",
        "bright_magenta",
        "bright_cyan",
    ],
)

MONOCHROME_SCHEME = ColorScheme(
    name="monochrome",
    colors=[
        "white",
        "bright_white",
        "grey",
        "bright_black",
        "white",
        "bright_white",
    ],
)

PASTEL_SCHEME = ColorScheme(
    name="pastel",
    colors=[
        "bright_red",
        "bright_green",
        "bright_yellow",
        "bright_blue",
        "bright_magenta",
        "bright_cyan",
    ],
)

VIBRANT_SCHEME = ColorScheme(
    name="vibrant",
    colors=[
        "red",
        "green",
        "yellow",
        "blue",
        "magenta",
        "cyan",
    ],
)

AVAILABLE_SCHEMES: Dict[str, ColorScheme] = {
    "default": DEFAULT_SCHEME,
    "monochrome": MONOCHROME_SCHEME,
    "pastel": PASTEL_SCHEME,
    "vibrant": VIBRANT_SCHEME,
}


class Config(BaseModel):
    """Application configuration."""

    color_scheme: str = "default"

    @field_validator("color_scheme")
    @classmethod
    def validate_color_scheme(cls, v: str) -> str:
        """Validate that color scheme exists."""
        if v not in AVAILABLE_SCHEMES:
            raise ValueError(
                f"Invalid color scheme: {v}. "
                f"Available schemes: {', '.join(AVAILABLE_SCHEMES.keys())}"
            )
        return v

    def get_scheme(self) -> ColorScheme:
        """Get the current ColorScheme object.

        Returns:
            ColorScheme object for the current scheme
        """
        return AVAILABLE_SCHEMES[self.color_scheme]

    @staticmethod
    def get_available_schemes() -> Dict[str, ColorScheme]:
        """Get all available color schemes.

        Returns:
            Dictionary mapping scheme names to ColorScheme objects
        """
        return AVAILABLE_SCHEMES.copy()

    def save(self, path: Optional[str] = None) -> None:
        """Save configuration to file.

        Args:
            path: Path to save config to (uses default if None)
        """
        if path is None:
            path = str(get_config_path())

        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "wb") as f:
            tomli_w.dump(self.model_dump(), f)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "Config":
        """Load configuration from file.

        Args:
            path: Path to load config from (uses default if None)

        Returns:
            Config object
        """
        if path is None:
            path = str(get_config_path())

        config_path = Path(path)

        if not config_path.exists():
            # Return default config if file doesn't exist
            return cls()

        try:
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
            return cls(**data)
        except Exception:
            # If config file is corrupted, return default
            return cls()


def get_config_path() -> Path:
    """Get the path to the configuration file.

    Follows XDG Base Directory Specification.

    Returns:
        Path to config file
    """
    # Use XDG_CONFIG_HOME if set, otherwise default to ~/.config
    if os.name == "posix":
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            base_dir = Path(config_home)
        else:
            base_dir = Path.home() / ".config"
    elif os.name == "nt":
        # Windows uses APPDATA/Local
        app_data = os.environ.get("LOCALAPPDATA")
        if app_data:
            base_dir = Path(app_data)
        else:
            base_dir = Path.home() / "AppData" / "Local"
    else:
        # Fallback
        base_dir = Path.home() / ".config"

    return base_dir / "time-helper" / "config.toml"
