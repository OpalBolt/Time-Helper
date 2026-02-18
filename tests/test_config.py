"""Tests for configuration management."""

import pytest
import tempfile
import os
from unittest.mock import patch
from typer.testing import CliRunner
from time_helper.config import Config, ColorScheme, get_config_path
from time_helper.cli import app


class TestColorScheme:
    """Test color scheme functionality."""

    def test_color_scheme_has_required_colors(self):
        """Color scheme should define all required colors."""
        scheme = ColorScheme(
            name="test",
            colors=[
                "red",
                "green",
                "yellow",
                "blue",
                "magenta",
                "cyan",
            ],
        )
        assert len(scheme.colors) == 6
        assert "red" in scheme.colors

    def test_color_scheme_get_color_for_tag(self):
        """Should consistently return same color for same tag."""
        scheme = ColorScheme(
            name="test",
            colors=["red", "green", "blue"],
        )
        color1 = scheme.get_color_for_tag("work")
        color2 = scheme.get_color_for_tag("work")
        assert color1 == color2

    def test_color_scheme_different_tags_can_have_different_colors(self):
        """Different tags should be able to get different colors."""
        scheme = ColorScheme(
            name="test",
            colors=["red", "green", "blue"],
        )
        # With multiple colors available, it's extremely unlikely
        # all different tags would hash to the same color
        colors = set()
        for i in range(20):
            colors.add(scheme.get_color_for_tag(f"tag{i}"))
        # At least 2 different colors should be used
        assert len(colors) >= 2


class TestConfig:
    """Test configuration management."""

    def test_config_default_scheme(self):
        """Config should have default color scheme."""
        config = Config()
        assert config.color_scheme == "default"

    def test_config_set_color_scheme(self):
        """Should be able to set color scheme."""
        config = Config()
        config.color_scheme = "monochrome"
        assert config.color_scheme == "monochrome"

    def test_config_get_available_schemes(self):
        """Should return list of available color schemes."""
        schemes = Config.get_available_schemes()
        assert isinstance(schemes, dict)
        assert "default" in schemes
        assert "monochrome" in schemes
        assert "pastel" in schemes
        assert "vibrant" in schemes

    def test_config_get_current_scheme_object(self):
        """Should return ColorScheme object for current scheme."""
        config = Config()
        config.color_scheme = "default"
        scheme = config.get_scheme()
        assert isinstance(scheme, ColorScheme)
        assert scheme.name == "default"

    def test_config_invalid_scheme_raises_error(self):
        """Setting invalid scheme should raise ValueError."""
        with pytest.raises(ValueError):
            Config(color_scheme="nonexistent")


class TestConfigPersistence:
    """Test configuration file persistence."""

    def test_config_save_and_load(self, tmp_path):
        """Config should be saved and loaded correctly."""
        config_file = tmp_path / "config.toml"

        # Save config
        config = Config()
        config.color_scheme = "monochrome"
        config.save(str(config_file))

        # Load config
        loaded_config = Config.load(str(config_file))
        assert loaded_config.color_scheme == "monochrome"

    def test_config_load_missing_file_returns_default(self, tmp_path):
        """Loading missing config file should return default config."""
        config_file = tmp_path / "nonexistent.toml"
        config = Config.load(str(config_file))
        assert config.color_scheme == "default"

    def test_config_path_follows_xdg_spec(self):
        """Config path should follow XDG Base Directory Specification."""
        # Test with XDG_CONFIG_HOME set
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["XDG_CONFIG_HOME"] = tmpdir
            path = get_config_path()
            assert str(path).startswith(tmpdir)
            assert "time-helper" in str(path)
            del os.environ["XDG_CONFIG_HOME"]

    def test_config_path_default_location(self):
        """Config path should use ~/.config by default on posix."""
        if os.name == "posix":
            # Clear XDG_CONFIG_HOME if set
            old_xdg = os.environ.pop("XDG_CONFIG_HOME", None)
            try:
                path = get_config_path()
                assert ".config" in str(path)
                assert "time-helper" in str(path)
            finally:
                if old_xdg:
                    os.environ["XDG_CONFIG_HOME"] = old_xdg


class TestColorSchemes:
    """Test predefined color schemes."""

    def test_default_scheme_has_bright_colors(self):
        """Default scheme should include bright colors."""
        schemes = Config.get_available_schemes()
        default = schemes["default"]
        colors = default.colors
        assert "bright_red" in colors or "bright_green" in colors

    def test_monochrome_scheme_grayscale(self):
        """Monochrome scheme should use grayscale colors."""
        schemes = Config.get_available_schemes()
        monochrome = schemes["monochrome"]
        colors = monochrome.colors
        # Should use white/bright_white/bold/dim/grey
        expected = ["white", "bright_white", "bold", "dim", "grey"]
        assert any(c in colors for c in expected)

    def test_all_schemes_have_enough_colors(self):
        """All schemes should have at least 6 colors for variety."""
        schemes = Config.get_available_schemes()
        for name, scheme in schemes.items():
            msg = f"{name} scheme has too few colors"
            assert len(scheme.colors) >= 6, msg

    def test_all_schemes_use_valid_rich_colors(self):
        """All color names should be valid Rich color names."""
        from rich.color import ANSI_COLOR_NAMES

        schemes = Config.get_available_schemes()
        valid_colors = set(ANSI_COLOR_NAMES.keys())
        # Add Rich's standard color names
        valid_colors.update(
            [
                "red",
                "green",
                "yellow",
                "blue",
                "magenta",
                "cyan",
                "white",
                "bright_red",
                "bright_green",
                "bright_yellow",
                "bright_blue",
                "bright_magenta",
                "bright_cyan",
                "bright_white",
                "black",
                "bright_black",
                "grey",
                "bold",
                "dim",
            ]
        )

        for name, scheme in schemes.items():
            for color in scheme.colors:
                # Rich also supports hex colors and rgb colors,
                # but we'll stick to named colors for now
                assert color in valid_colors or color.startswith(
                    "#"
                ), f"Invalid color '{color}' in {name} scheme"


class TestConfigCliCommands:
    """Test configuration CLI commands with error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_set_scheme_command_success(self, tmp_path):
        """Test set-scheme command successfully sets color scheme."""
        config_file = tmp_path / "config.toml"
        with patch(
            "time_helper.cli.config_commands.get_config_path"
        ) as mock_path:
            mock_path.return_value = config_file
            result = self.runner.invoke(
                app, ["config", "set-scheme", "monochrome"]
            )
            assert result.exit_code == 0
            assert "✓ Color scheme set to:" in result.stdout
            assert "monochrome" in result.stdout

    def test_set_scheme_command_invalid_scheme(self, tmp_path):
        """Test set-scheme command with invalid scheme name."""
        config_file = tmp_path / "config.toml"
        with patch(
            "time_helper.cli.config_commands.get_config_path"
        ) as mock_path:
            mock_path.return_value = config_file
            result = self.runner.invoke(
                app, ["config", "set-scheme", "nonexistent_scheme"]
            )
            assert result.exit_code == 1
            assert "Error" in result.stdout

    def test_set_scheme_command_oserror_handling(self, tmp_path):
        """Test set-scheme command handles OSError when writing config."""
        config_file = tmp_path / "config.toml"
        with patch(
            "time_helper.cli.config_commands.get_config_path"
        ) as mock_path:
            mock_path.return_value = config_file
            with patch(
                "time_helper.cli.config_commands.Config.save"
            ) as mock_save:
                mock_save.side_effect = OSError("Permission denied")
                result = self.runner.invoke(
                    app, ["config", "set-scheme", "pastel"]
                )
                assert result.exit_code == 1
                assert "Failed to write configuration file" in result.stdout
                assert "permissions" in result.stdout.lower()

    def test_set_scheme_command_ioerror_handling(self, tmp_path):
        """Test set-scheme command handles IOError when writing config."""
        config_file = tmp_path / "config.toml"
        with patch(
            "time_helper.cli.config_commands.get_config_path"
        ) as mock_path:
            mock_path.return_value = config_file
            with patch(
                "time_helper.cli.config_commands.Config.save"
            ) as mock_save:
                mock_save.side_effect = IOError("Disk full")
                result = self.runner.invoke(
                    app, ["config", "set-scheme", "vibrant"]
                )
                assert result.exit_code == 1
                assert "Failed to write configuration file" in result.stdout

    def test_reset_config_command_success(self, tmp_path):
        """Test reset command successfully resets configuration."""
        config_file = tmp_path / "config.toml"
        with patch(
            "time_helper.cli.config_commands.get_config_path"
        ) as mock_path:
            mock_path.return_value = config_file
            result = self.runner.invoke(
                app, ["config", "reset"], input="y\n"
            )
            assert result.exit_code == 0
            assert "✓ Configuration reset to defaults" in result.stdout

    def test_reset_config_command_cancelled(self, tmp_path):
        """Test reset command when user cancels."""
        config_file = tmp_path / "config.toml"
        with patch(
            "time_helper.cli.config_commands.get_config_path"
        ) as mock_path:
            mock_path.return_value = config_file
            result = self.runner.invoke(
                app, ["config", "reset"], input="n\n"
            )
            assert result.exit_code == 0
            assert "Cancelled" in result.stdout

    def test_reset_config_command_oserror_handling(self, tmp_path):
        """Test reset command handles OSError when writing config."""
        config_file = tmp_path / "config.toml"
        with patch(
            "time_helper.cli.config_commands.get_config_path"
        ) as mock_path:
            mock_path.return_value = config_file
            with patch(
                "time_helper.cli.config_commands.Config.save"
            ) as mock_save:
                mock_save.side_effect = OSError("Access denied")
                result = self.runner.invoke(
                    app, ["config", "reset"], input="y\n"
                )
                assert result.exit_code == 1
                assert "Failed to write configuration file" in result.stdout
                assert "permissions" in result.stdout.lower()

    def test_reset_config_command_oserror_permission_error(self, tmp_path):
        """Test reset handles PermissionError (subclass of OSError)."""
        config_file = tmp_path / "config.toml"
        with patch(
            "time_helper.cli.config_commands.get_config_path"
        ) as mock_path:
            mock_path.return_value = config_file
            with patch(
                "time_helper.cli.config_commands.Config.save"
            ) as mock_save:
                mock_save.side_effect = PermissionError("Not authorized")
                result = self.runner.invoke(
                    app, ["config", "reset"], input="y\n"
                )
                assert result.exit_code == 1
                assert "Failed to write configuration file" in result.stdout

    def test_reset_config_command_ioerror_handling(self, tmp_path):
        """Test reset command handles IOError when writing config."""
        config_file = tmp_path / "config.toml"
        with patch(
            "time_helper.cli.config_commands.get_config_path"
        ) as mock_path:
            mock_path.return_value = config_file
            with patch(
                "time_helper.cli.config_commands.Config.save"
            ) as mock_save:
                mock_save.side_effect = IOError("Write failed")
                result = self.runner.invoke(
                    app, ["config", "reset"], input="y\n"
                )
                assert result.exit_code == 1
                assert "Failed to write configuration file" in result.stdout

    def test_set_scheme_successful_update_creates_config_file(
        self, tmp_path
    ):
        """Test set-scheme creates config file when it doesn't exist."""
        config_file = tmp_path / "config.toml"
        assert not config_file.exists()
        with patch(
            "time_helper.cli.config_commands.get_config_path"
        ) as mock_path:
            mock_path.return_value = config_file
            with patch(
                "time_helper.config.get_config_path"
            ) as mock_path_config:
                mock_path_config.return_value = config_file
                result = self.runner.invoke(
                    app, ["config", "set-scheme", "pastel"]
                )
                assert result.exit_code == 0
                assert config_file.exists()

    def test_reset_config_successful_update_creates_config_file(
        self, tmp_path
    ):
        """Test reset creates config file when it doesn't exist."""
        config_file = tmp_path / "config.toml"
        assert not config_file.exists()
        with patch(
            "time_helper.cli.config_commands.get_config_path"
        ) as mock_path:
            mock_path.return_value = config_file
            with patch(
                "time_helper.config.get_config_path"
            ) as mock_path_config:
                mock_path_config.return_value = config_file
                result = self.runner.invoke(
                    app, ["config", "reset"], input="y\n"
                )
                assert result.exit_code == 0
                assert config_file.exists()

    def test_set_scheme_error_message_helpful(self, tmp_path):
        """Test set-scheme error message is helpful to user."""
        config_file = tmp_path / "config.toml"
        with patch(
            "time_helper.cli.config_commands.get_config_path"
        ) as mock_path:
            mock_path.return_value = config_file
            with patch(
                "time_helper.cli.config_commands.Config.save"
            ) as mock_save:
                mock_save.side_effect = OSError("Permission denied")
                result = self.runner.invoke(
                    app, ["config", "set-scheme", "default"]
                )
                assert result.exit_code == 1
                # Error message should guide user to check permissions
                assert "Check file permissions" in result.stdout

    def test_reset_config_error_message_helpful(self, tmp_path):
        """Test reset error message is helpful to user."""
        config_file = tmp_path / "config.toml"
        with patch(
            "time_helper.cli.config_commands.get_config_path"
        ) as mock_path:
            mock_path.return_value = config_file
            with patch(
                "time_helper.cli.config_commands.Config.save"
            ) as mock_save:
                mock_save.side_effect = OSError("Disk full")
                result = self.runner.invoke(
                    app, ["config", "reset"], input="y\n"
                )
                assert result.exit_code == 1
                # Error message should guide user to check permissions
                assert "Check file permissions" in result.stdout
