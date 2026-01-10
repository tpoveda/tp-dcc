"""Unit tests for the naming library validation module."""

from __future__ import annotations

from tp.libs.templating import consts, validation


class TestCanBeSerialized:
    """Tests for the can_be_serialized function."""

    def test_can_be_serialized_no_class_name(self):
        """Test serialization check when no class name is present."""
        data = {"name": "test", "value": 123}
        result = validation.can_be_serialized("Token", data)
        assert result is True

    def test_can_be_serialized_matching_class_name(self):
        """Test serialization check with matching class name."""
        data = {
            consts.CLASS_NAME_ATTR: "Token",
            "name": "test",
        }
        result = validation.can_be_serialized("Token", data)
        assert result is True

    def test_can_be_serialized_mismatched_class_name(self):
        """Test serialization check with mismatched class name."""
        data = {
            consts.CLASS_NAME_ATTR: "Rule",
            "name": "test",
        }
        result = validation.can_be_serialized("Token", data)
        assert result is False

    def test_can_be_serialized_removes_class_attrs(self):
        """Test that class attributes are removed from data."""
        data = {
            consts.CLASS_NAME_ATTR: "Token",
            consts.CLASS_VERSION_ATTR: "1.0",
            "name": "test",
        }
        validation.can_be_serialized("Token", data)
        assert consts.CLASS_NAME_ATTR not in data
        assert consts.CLASS_VERSION_ATTR not in data
        assert "name" in data

    def test_can_be_serialized_with_version(self):
        """Test serialization check with version attribute."""
        data = {
            consts.CLASS_VERSION_ATTR: "2.0",
            "name": "test",
        }
        result = validation.can_be_serialized("Token", data)
        assert result is True
        assert consts.CLASS_VERSION_ATTR not in data


class TestConstants:
    """Tests for naming library constants."""

    def test_preset_extension(self):
        """Test preset file extension constant."""
        assert consts.NAMING_PRESET_EXTENSION == "preset"

    def test_convention_extension(self):
        """Test convention file extension constant."""
        assert consts.NAMING_CONVENTION_EXTENSION == "yaml"

    def test_default_preset_name(self):
        """Test default preset name constant."""
        assert consts.DEFAULT_NAMING_PRESET_NAME == "default"

    def test_class_name_attr(self):
        """Test class name attribute constant."""
        assert consts.CLASS_NAME_ATTR == "_className"

    def test_class_version_attr(self):
        """Test class version attribute constant."""
        assert consts.CLASS_VERSION_ATTR == "_version"

    def test_regex_filter(self):
        """Test regex filter constant is valid."""
        import re

        # Should be a valid regex pattern
        pattern = re.compile(consts.REGEX_FILTER)
        assert pattern is not None

    def test_regex_token_resolver(self):
        """Test regex token resolver constant is valid."""
        import re

        # Should be a valid regex pattern (with token placeholder)
        pattern_str = consts.REGEX_TOKEN_RESOLVER.replace("{token}", "test")
        pattern = re.compile(pattern_str)
        assert pattern is not None
