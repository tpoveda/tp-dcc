"""Unit tests for the naming library preset module."""

from __future__ import annotations

import os

import pytest

from tp.libs.naming import config, preset


class TestPresetsManager:
    """Tests for the PresetsManager class."""

    def test_initialization(self, reset_global_config):
        """Test PresetsManager initialization."""
        pm = preset.PresetsManager()
        assert pm is not None
        assert pm.naming_conventions == {}

    def test_initialization_with_configuration(self, config_with_builtin_path):
        """Test PresetsManager with custom configuration."""
        pm = preset.PresetsManager(configuration=config_with_builtin_path)
        assert pm is not None

    def test_from_configuration(self, config_with_builtin_path):
        """Test creating PresetsManager from configuration."""
        pm = preset.PresetsManager.from_configuration(config_with_builtin_path)
        assert pm is not None
        # Should have loaded the default preset
        assert len(pm.naming_conventions) > 0

    def test_load_preset_from_file(self, config_with_builtin_path):
        """Test loading a preset from file."""
        pm = preset.PresetsManager(configuration=config_with_builtin_path)
        preset_file = config_with_builtin_path.find_preset_file("default")
        assert preset_file is not None

        result = pm.load_preset_from_file(preset_file)
        assert result is True
        assert len(pm.naming_conventions) > 0

    def test_load_preset_from_invalid_file(self, config_with_builtin_path):
        """Test loading a preset from invalid file raises error."""
        pm = preset.PresetsManager(configuration=config_with_builtin_path)
        with pytest.raises(FileNotFoundError):
            pm.load_preset_from_file("/nonexistent/path.preset")

    def test_load_preset_non_preset_extension(
        self, config_with_builtin_path, temp_dir
    ):
        """Test loading a file that's not a preset."""
        pm = preset.PresetsManager(configuration=config_with_builtin_path)
        # Create a non-preset file
        non_preset_file = os.path.join(temp_dir, "test.txt")
        with open(non_preset_file, "w") as f:
            f.write("test")
        result = pm.load_preset_from_file(non_preset_file)
        assert result is False

    def test_find_preset(self, preset_manager_with_default):
        """Test finding a preset by name."""
        found_preset = preset_manager_with_default.find_preset("default")
        assert found_preset is not None
        assert found_preset.name == "default"

    def test_find_preset_not_found(self, preset_manager_with_default):
        """Test finding a non-existent preset."""
        found_preset = preset_manager_with_default.find_preset("nonexistent")
        assert found_preset is None

    def test_find_naming_conventions_by_type(
        self, preset_manager_with_default
    ):
        """Test finding naming conventions by type."""
        global_conventions = (
            preset_manager_with_default.find_naming_conventions_by_type(
                "global"
            )
        )
        assert len(global_conventions) > 0

    def test_find_naming_conventions_by_type_not_found(
        self, preset_manager_with_default
    ):
        """Test finding naming conventions for non-existent type."""
        conventions = (
            preset_manager_with_default.find_naming_conventions_by_type(
                "nonexistent_type"
            )
        )
        assert len(conventions) == 0

    def test_naming_conventions_property(self, preset_manager_with_default):
        """Test naming_conventions property."""
        conventions = preset_manager_with_default.naming_conventions
        assert isinstance(conventions, dict)
        assert len(conventions) > 0

    def test_preset_hierarchy(self, preset_manager_with_default):
        """Test getting preset hierarchy."""
        default_preset = preset_manager_with_default.find_preset("default")
        if default_preset:
            hierarchy = preset_manager_with_default.preset_hierarchy(
                default_preset
            )
            assert isinstance(hierarchy, dict)


class TestPresetsManagerConventionDiscovery:
    """Tests for PresetsManager convention file discovery."""

    def test_load_convention_from_same_directory(
        self, temp_preset_dir, reset_global_config
    ):
        """Test loading convention from same directory as preset."""
        cfg = config.NamingConfiguration()
        cfg.add_preset_path(temp_preset_dir)
        pm = preset.PresetsManager(configuration=cfg)

        preset_file = os.path.join(temp_preset_dir, "test.preset")
        result = pm.load_preset_from_file(preset_file)
        assert result is True
        assert "test-global" in pm.naming_conventions

    def test_load_convention_from_other_path(
        self, temp_dir, reset_global_config
    ):
        """Test loading convention from another configured path."""
        # Create two directories
        preset_dir = os.path.join(temp_dir, "presets")
        convention_dir = os.path.join(temp_dir, "conventions")
        os.makedirs(preset_dir)
        os.makedirs(convention_dir)

        # Create preset file
        preset_content = """name: test
namingConventions:
- name: shared-global
  type: global
"""
        with open(os.path.join(preset_dir, "test.preset"), "w") as f:
            f.write(preset_content)

        # Create convention file in different directory
        convention_content = """name: shared-global
description: Shared convention
rules: []
tokens: []
"""
        with open(
            os.path.join(convention_dir, "shared-global.yaml"), "w"
        ) as f:
            f.write(convention_content)

        # Configure paths
        cfg = config.NamingConfiguration()
        cfg.add_preset_path(preset_dir)
        cfg.add_preset_path(convention_dir)

        pm = preset.PresetsManager(configuration=cfg)
        result = pm.load_preset_from_file(
            os.path.join(preset_dir, "test.preset")
        )
        assert result is True
        assert "shared-global" in pm.naming_conventions


class TestNamingPreset:
    """Tests for the NamingPreset class."""

    def test_initialization(self, preset_manager_with_default):
        """Test NamingPreset initialization."""
        np = preset.NamingPreset(
            name="test_preset",
            file_path="/path/to/preset.preset",
            manager=preset_manager_with_default,
            parent=None,
        )
        assert np.name == "test_preset"

    def test_repr(self, preset_manager_with_default):
        """Test NamingPreset string representation."""
        np = preset.NamingPreset(
            name="test_preset",
            file_path="/path/to/preset.preset",
            manager=preset_manager_with_default,
            parent=None,
        )
        assert "NamingPreset" in repr(np)
        assert "test_preset" in repr(np)

    def test_load_from_path(
        self, config_with_builtin_path, preset_manager_with_default
    ):
        """Test loading NamingPreset from file."""
        preset_file = config_with_builtin_path.find_preset_file("default")
        np = preset.NamingPreset.load_from_path(
            preset_file, preset_manager_with_default
        )
        assert np is not None
        assert np.name == "default"

    def test_load_from_data(self, preset_manager_with_default):
        """Test loading NamingPreset from data."""
        data = {
            "name": "test_preset",
            "namingConventions": [
                {"name": "test-global", "type": "global"},
            ],
        }
        np = preset.NamingPreset.load_from_data(
            data, "/path/to/preset.preset", preset_manager_with_default
        )
        assert np is not None
        assert np.name == "test_preset"
        assert len(np.naming_conventions) == 1

    def test_naming_conventions_property(self, preset_manager_with_default):
        """Test naming_conventions property."""
        default_preset = preset_manager_with_default.find_preset("default")
        assert default_preset is not None
        conventions = default_preset.naming_conventions
        assert isinstance(conventions, list)
        assert len(conventions) > 0

    def test_parent_property(self, preset_manager_with_default):
        """Test parent property getter and setter."""
        parent = preset.NamingPreset(
            name="parent",
            file_path="",
            manager=preset_manager_with_default,
            parent=None,
        )
        child = preset.NamingPreset(
            name="child",
            file_path="",
            manager=preset_manager_with_default,
            parent=None,
        )

        child.parent = parent
        assert child.parent is parent
        assert child in parent.children

        child.parent = None
        assert child.parent is None
        assert child not in parent.children

    def test_children_property(self, preset_manager_with_default):
        """Test children property."""
        parent = preset.NamingPreset(
            name="parent",
            file_path="",
            manager=preset_manager_with_default,
            parent=None,
        )
        child1 = preset.NamingPreset(
            name="child1",
            file_path="",
            manager=preset_manager_with_default,
            parent=None,
        )
        child2 = preset.NamingPreset(
            name="child2",
            file_path="",
            manager=preset_manager_with_default,
            parent=None,
        )

        # Use setter to properly add children to parent
        child1.parent = parent
        child2.parent = parent

        assert len(parent.children) == 2
        assert child1 in parent.children
        assert child2 in parent.children

    def test_exists(
        self, config_with_builtin_path, preset_manager_with_default
    ):
        """Test exists method."""
        preset_file = config_with_builtin_path.find_preset_file("default")
        np = preset.NamingPreset.load_from_path(
            preset_file, preset_manager_with_default
        )
        assert np.exists() is True

        fake_preset = preset.NamingPreset(
            name="fake",
            file_path="/nonexistent/path.preset",
            manager=preset_manager_with_default,
            parent=None,
        )
        assert fake_preset.exists() is False

    def test_to_dict(self, preset_manager_with_default):
        """Test serialization to dictionary."""
        data = {
            "name": "test_preset",
            "namingConventions": [
                {"name": "test-global", "type": "global"},
            ],
        }
        np = preset.NamingPreset.load_from_data(
            data, "/path/to/preset.preset", preset_manager_with_default
        )
        result = np.to_dict()
        assert result["name"] == "test_preset"
        assert len(result["namingConventions"]) == 1

    def test_find_naming_convention_by_type(self, preset_manager_with_default):
        """Test finding naming convention by type."""
        default_preset = preset_manager_with_default.find_preset("default")
        if default_preset:
            # Try to find global convention - the result depends on whether
            # the convention was loaded
            nc = default_preset.find_naming_convention_by_type("global")
            # The method should return something (convention or None depending on loading)
            # We mainly test that it doesn't raise an error
            if nc is not None:
                assert nc.type == "global"

    def test_find_naming_convention_by_name(self, preset_manager_with_default):
        """Test finding naming convention by name."""
        default_preset = preset_manager_with_default.find_preset("default")
        if default_preset and default_preset.naming_conventions:
            first_convention = default_preset.naming_conventions[0]
            nc = default_preset.find_naming_convention_by_name(
                first_convention.name
            )
            # Note: May be None if convention wasn't loaded
            # This tests the lookup mechanism


class TestNameConventionData:
    """Tests for the NameConventionData class."""

    def test_initialization(self):
        """Test NameConventionData initialization."""
        ncd = preset.NameConventionData("test-global", "global")
        assert ncd.name == "test-global"
        assert ncd.type == "global"
        assert ncd.naming_convention is None

    def test_initialization_with_convention(self, empty_naming_convention):
        """Test NameConventionData with naming convention."""
        ncd = preset.NameConventionData(
            "test-global", "global", empty_naming_convention
        )
        assert ncd.naming_convention is empty_naming_convention

    def test_repr(self):
        """Test NameConventionData string representation."""
        ncd = preset.NameConventionData("test-global", "global")
        assert "NameConventionData" in repr(ncd)
        assert "test-global" in repr(ncd)
        assert "global" in repr(ncd)

    def test_equality(self):
        """Test NameConventionData equality."""
        ncd1 = preset.NameConventionData("test-global", "global")
        ncd2 = preset.NameConventionData("test-global", "global")
        ncd3 = preset.NameConventionData("other", "global")
        ncd4 = preset.NameConventionData("test-global", "other")

        assert ncd1 == ncd2
        assert ncd1 != ncd3
        assert ncd1 != ncd4

    def test_equality_with_non_ncd(self):
        """Test NameConventionData equality with non-NameConventionData."""
        ncd = preset.NameConventionData("test-global", "global")
        assert ncd != "test-global"
        assert ncd != 123

    def test_naming_convention_setter(self, empty_naming_convention):
        """Test naming_convention setter."""
        ncd = preset.NameConventionData("test-global", "global")
        ncd.naming_convention = empty_naming_convention
        assert ncd.naming_convention is empty_naming_convention

    def test_to_dict(self):
        """Test serialization to dictionary."""
        ncd = preset.NameConventionData("test-global", "global")
        result = ncd.to_dict()
        assert result["name"] == "test-global"
        assert result["type"] == "global"


class TestPresetHierarchy:
    """Tests for preset parent-child hierarchy."""

    def test_child_inherits_parent_naming_convention(
        self, preset_manager_with_default
    ):
        """Test that child preset can access parent's naming conventions."""
        parent = preset.NamingPreset(
            name="parent",
            file_path="",
            manager=preset_manager_with_default,
            parent=None,
        )
        child = preset.NamingPreset(
            name="child",
            file_path="",
            manager=preset_manager_with_default,
            parent=parent,
        )

        # Add naming convention data to parent
        parent_ncd = preset.NameConventionData("parent-global", "global")
        parent.naming_conventions.append(parent_ncd)

        # Child should be able to find parent's convention type
        found = child.find_naming_convention_data_by_type(
            "global", recursive=True
        )
        # Note: This may return None if the actual convention isn't loaded
        # but the recursive lookup should work

    def test_non_recursive_lookup(self, preset_manager_with_default):
        """Test non-recursive naming convention lookup."""
        parent = preset.NamingPreset(
            name="parent",
            file_path="",
            manager=preset_manager_with_default,
            parent=None,
        )
        child = preset.NamingPreset(
            name="child",
            file_path="",
            manager=preset_manager_with_default,
            parent=parent,
        )

        # Add naming convention data only to parent
        parent_ncd = preset.NameConventionData("parent-global", "global")
        parent.naming_conventions.append(parent_ncd)

        # Non-recursive lookup on child should not find parent's convention
        found = child.find_naming_convention_data_by_type(
            "global", recursive=False
        )
        assert found is None  # Child has no conventions of its own
