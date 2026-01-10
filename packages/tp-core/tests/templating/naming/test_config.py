"""Unit tests for the naming library configuration module."""

from __future__ import annotations

import os
import tempfile

from tp.libs.templating.naming import config


class TestNamingConfiguration:
    """Tests for the NamingConfiguration dataclass."""

    def test_default_initialization(self):
        """Test that NamingConfiguration initializes with correct defaults."""
        cfg = config.NamingConfiguration()
        assert cfg.preset_paths == []
        assert cfg.default_preset_name == "default"
        assert cfg.environment_variable_resolver is None

    def test_custom_initialization(self):
        """Test NamingConfiguration with custom values."""
        custom_paths = ["/path/one", "/path/two"]
        cfg = config.NamingConfiguration(
            preset_paths=custom_paths,
            default_preset_name="custom",
        )
        assert cfg.preset_paths == custom_paths
        assert cfg.default_preset_name == "custom"

    def test_resolve_path_default(self, clean_config):
        """Test path resolution using default os.path.expandvars."""
        # Set an environment variable for testing
        os.environ["TEST_VAR"] = "test_value"
        try:
            resolved = clean_config.resolve_path("$TEST_VAR/path")
            assert "test_value" in resolved
        finally:
            del os.environ["TEST_VAR"]

    def test_resolve_path_custom_resolver(self):
        """Test path resolution using custom resolver."""

        def custom_resolver(path: str) -> str:
            return path.replace("$CUSTOM", "resolved")

        cfg = config.NamingConfiguration(
            environment_variable_resolver=custom_resolver
        )
        resolved = cfg.resolve_path("$CUSTOM/path")
        assert resolved == "resolved/path"

    def test_add_preset_path(self, clean_config, temp_dir):
        """Test adding a preset path."""
        clean_config.add_preset_path(temp_dir)
        assert temp_dir in clean_config.preset_paths

    def test_add_preset_path_no_duplicates(self, clean_config, temp_dir):
        """Test that duplicate paths are not added."""
        clean_config.add_preset_path(temp_dir)
        clean_config.add_preset_path(temp_dir)
        assert clean_config.preset_paths.count(temp_dir) == 1

    def test_add_preset_path_prepend(self, clean_config, temp_dir):
        """Test adding a preset path at the beginning."""
        clean_config.add_preset_path("/first/path")
        clean_config.add_preset_path(temp_dir, prepend=True)
        assert clean_config.preset_paths[0] == temp_dir

    def test_remove_preset_path(self, clean_config, temp_dir):
        """Test removing a preset path."""
        clean_config.add_preset_path(temp_dir)
        result = clean_config.remove_preset_path(temp_dir)
        assert result is True
        assert temp_dir not in clean_config.preset_paths

    def test_remove_nonexistent_preset_path(self, clean_config):
        """Test removing a path that doesn't exist."""
        result = clean_config.remove_preset_path("/nonexistent/path")
        assert result is False

    def test_find_preset_file(self, config_with_builtin_path):
        """Test finding a preset file."""
        preset_file = config_with_builtin_path.find_preset_file("default")
        assert preset_file is not None
        assert os.path.isfile(preset_file)
        assert preset_file.endswith(".preset")

    def test_find_preset_file_not_found(self, clean_config):
        """Test finding a preset file that doesn't exist."""
        preset_file = clean_config.find_preset_file("nonexistent")
        assert preset_file is None

    def test_find_convention_file(self, config_with_builtin_path):
        """Test finding a convention file."""
        convention_file = config_with_builtin_path.find_convention_file(
            "default-global"
        )
        assert convention_file is not None
        assert os.path.isfile(convention_file)
        assert convention_file.endswith(".yaml")

    def test_find_convention_file_not_found(self, clean_config):
        """Test finding a convention file that doesn't exist."""
        convention_file = clean_config.find_convention_file("nonexistent")
        assert convention_file is None


class TestGlobalConfiguration:
    """Tests for global configuration functions."""

    def test_get_configuration_singleton(self, reset_global_config):
        """Test that get_configuration returns the same instance."""
        cfg1 = config.get_configuration()
        cfg2 = config.get_configuration()
        assert cfg1 is cfg2

    def test_get_configuration_includes_builtin_path(
        self, reset_global_config
    ):
        """Test that get_configuration adds built-in presets path."""
        cfg = config.get_configuration()
        builtin_path = config.builtin_presets_path()
        assert builtin_path in cfg.preset_paths

    def test_set_configuration(self, reset_global_config):
        """Test setting a custom global configuration."""
        custom_cfg = config.NamingConfiguration(default_preset_name="custom")
        config.set_configuration(custom_cfg)
        assert config.get_configuration() is custom_cfg
        assert config.get_configuration().default_preset_name == "custom"

    def test_reset_configuration(self, reset_global_config):
        """Test resetting the global configuration."""
        cfg1 = config.get_configuration()
        config.reset_configuration()
        cfg2 = config.get_configuration()
        assert cfg1 is not cfg2

    def test_add_preset_path_global(self, reset_global_config, temp_dir):
        """Test the global add_preset_path function."""
        config.add_preset_path(temp_dir)
        assert temp_dir in config.preset_paths()

    def test_remove_preset_path_global(self, reset_global_config, temp_dir):
        """Test the global remove_preset_path function."""
        config.add_preset_path(temp_dir)
        result = config.remove_preset_path(temp_dir)
        assert result is True
        assert temp_dir not in config.preset_paths()

    def test_preset_paths_returns_copy(self, reset_global_config):
        """Test that preset_paths returns a copy, not the original list."""
        paths = config.preset_paths()
        original_length = len(paths)
        paths.append("/new/path")
        assert len(config.preset_paths()) == original_length

    def test_builtin_presets_path(self):
        """Test that builtin_presets_path returns a valid directory."""
        builtin_path = config.builtin_presets_path()
        assert os.path.isdir(builtin_path)
        assert "presets" in builtin_path


class TestEnvironmentVariableLoading:
    """Tests for loading preset paths from environment variables."""

    def test_load_from_env_var(self, reset_global_config, temp_dir):
        """Test loading preset paths from environment variable."""
        os.environ[config.NAMING_PRESET_PATHS_ENV_VAR] = temp_dir
        try:
            config.reset_configuration()
            cfg = config.get_configuration()
            assert temp_dir in cfg.preset_paths
        finally:
            del os.environ[config.NAMING_PRESET_PATHS_ENV_VAR]

    def test_load_multiple_paths_from_env_var(
        self, reset_global_config, temp_dir
    ):
        """Test loading multiple preset paths from environment variable."""
        # Create a second temp directory
        temp_dir2 = tempfile.mkdtemp()
        try:
            paths = f"{temp_dir}{os.pathsep}{temp_dir2}"
            os.environ[config.NAMING_PRESET_PATHS_ENV_VAR] = paths
            config.reset_configuration()
            cfg = config.get_configuration()
            assert temp_dir in cfg.preset_paths
            assert temp_dir2 in cfg.preset_paths
        finally:
            del os.environ[config.NAMING_PRESET_PATHS_ENV_VAR]
            os.rmdir(temp_dir2)

    def test_env_var_paths_have_priority(self, reset_global_config, temp_dir):
        """Test that env var paths are added before built-in path."""
        os.environ[config.NAMING_PRESET_PATHS_ENV_VAR] = temp_dir
        try:
            config.reset_configuration()
            cfg = config.get_configuration()
            # Env var paths should come first
            assert cfg.preset_paths.index(temp_dir) < cfg.preset_paths.index(
                config.builtin_presets_path()
            )
        finally:
            del os.environ[config.NAMING_PRESET_PATHS_ENV_VAR]

    def test_nonexistent_env_path_not_added(self, reset_global_config):
        """Test that non-existent paths from env var are not added."""
        fake_path = "/nonexistent/path/12345"
        os.environ[config.NAMING_PRESET_PATHS_ENV_VAR] = fake_path
        try:
            config.reset_configuration()
            cfg = config.get_configuration()
            assert fake_path not in cfg.preset_paths
        finally:
            del os.environ[config.NAMING_PRESET_PATHS_ENV_VAR]

    def test_empty_env_var(self, reset_global_config):
        """Test that empty environment variable doesn't cause issues."""
        os.environ[config.NAMING_PRESET_PATHS_ENV_VAR] = ""
        try:
            config.reset_configuration()
            cfg = config.get_configuration()
            # Should still have built-in path
            assert config.builtin_presets_path() in cfg.preset_paths
        finally:
            del os.environ[config.NAMING_PRESET_PATHS_ENV_VAR]


class TestConfigConstants:
    """Tests for configuration constants."""

    def test_env_var_name_constant(self):
        """Test that the environment variable name constant is defined."""
        assert config.NAMING_PRESET_PATHS_ENV_VAR == "TP_NAMING_PRESET_PATHS"
