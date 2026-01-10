"""Tests for tp.libs.templating.versioning.token module."""

from __future__ import annotations

import pytest

from tp.libs.templating.versioning import VersionToken


class TestVersionTokenBasic:
    """Basic tests for VersionToken class."""

    def test_initialization_defaults(self):
        """Test VersionToken initialization with defaults."""
        token = VersionToken()
        assert token.name == "version"
        assert token.prefix == ""
        assert token.semantic is False
        assert token.start_version == 1

    def test_initialization_with_prefix(self):
        """Test VersionToken initialization with prefix."""
        token = VersionToken(prefix="v")
        assert token.prefix == "v"

    def test_initialization_semantic(self):
        """Test VersionToken initialization for semantic versioning."""
        token = VersionToken(semantic=True)
        assert token.semantic is True

    def test_repr(self):
        """Test VersionToken string representation."""
        token = VersionToken(name="ver", prefix="v", semantic=True)
        repr_str = repr(token)
        assert "VersionToken" in repr_str
        assert "ver" in repr_str
        assert "v" in repr_str
        assert "True" in repr_str


class TestVersionTokenFormatting:
    """Tests for version formatting."""

    def test_format_simple_version(self):
        """Test formatting simple version numbers."""
        token = VersionToken(format_str="{:03d}")
        assert token.format_version(1) == "001"
        assert token.format_version(42) == "042"
        assert token.format_version(999) == "999"

    def test_format_prefixed_version(self):
        """Test formatting prefixed version numbers."""
        token = VersionToken(prefix="v", format_str="{:03d}")
        assert token.format_version(1) == "v001"
        assert token.format_version(42) == "v042"

    def test_format_semantic_version(self):
        """Test formatting semantic version numbers."""
        token = VersionToken(semantic=True)
        assert token.format_version((1, 0, 0)) == "1.0.0"
        assert token.format_version((1, 2, 3)) == "1.2.3"
        assert token.format_version((10, 20, 30)) == "10.20.30"

    def test_format_semantic_with_prefix(self):
        """Test formatting semantic version with prefix."""
        token = VersionToken(semantic=True, prefix="v")
        assert token.format_version((1, 0, 0)) == "v1.0.0"
        assert token.format_version((1, 2, 3)) == "v1.2.3"

    def test_format_semantic_partial_tuple(self):
        """Test formatting with partial tuple."""
        token = VersionToken(semantic=True)
        assert token.format_version((1,)) == "1.0.0"
        assert token.format_version((1, 2)) == "1.2.0"

    def test_format_semantic_from_int(self):
        """Test formatting semantic from integer."""
        token = VersionToken(semantic=True)
        assert token.format_version(1) == "1.0.0"


class TestVersionTokenParsing:
    """Tests for version parsing."""

    def test_parse_simple_numeric(self):
        """Test parsing simple numeric versions."""
        token = VersionToken()
        assert token.parse_version("001") == 1
        assert token.parse_version("042") == 42
        assert token.parse_version("999") == 999

    def test_parse_prefixed_numeric(self):
        """Test parsing prefixed numeric versions."""
        token = VersionToken(prefix="v")
        assert token.parse_version("v001") == 1
        assert token.parse_version("v042") == 42

    def test_parse_semantic(self):
        """Test parsing semantic versions."""
        token = VersionToken(semantic=True)
        assert token.parse_version("1.0.0") == (1, 0, 0)
        assert token.parse_version("1.2.3") == (1, 2, 3)
        assert token.parse_version("10.20.30") == (10, 20, 30)

    def test_parse_semantic_with_prefix(self):
        """Test parsing semantic versions with prefix."""
        token = VersionToken(semantic=True, prefix="v")
        assert token.parse_version("v1.0.0") == (1, 0, 0)
        assert token.parse_version("v1.2.3") == (1, 2, 3)

    def test_parse_invalid_version(self):
        """Test parsing invalid version strings."""
        token = VersionToken()
        with pytest.raises(ValueError):
            token.parse_version("invalid")
        with pytest.raises(ValueError):
            token.parse_version("abc")


class TestVersionTokenNextVersion:
    """Tests for next version calculation."""

    def test_next_version_from_none(self):
        """Test getting first version."""
        token = VersionToken(prefix="v", format_str="{:03d}")
        assert token.next_version(None) == "v001"

    def test_next_version_simple(self):
        """Test incrementing simple version."""
        token = VersionToken(prefix="v", format_str="{:03d}")
        assert token.next_version("v001") == "v002"
        assert token.next_version("v042") == "v043"
        assert token.next_version("v999") == "v1000"

    def test_next_version_semantic_patch(self):
        """Test incrementing semantic version (patch)."""
        token = VersionToken(semantic=True)
        assert token.next_version("1.0.0", increment="patch") == "1.0.1"
        assert token.next_version("1.2.3", increment="patch") == "1.2.4"

    def test_next_version_semantic_minor(self):
        """Test incrementing semantic version (minor)."""
        token = VersionToken(semantic=True)
        assert token.next_version("1.0.0", increment="minor") == "1.1.0"
        assert token.next_version("1.2.3", increment="minor") == "1.3.0"

    def test_next_version_semantic_major(self):
        """Test incrementing semantic version (major)."""
        token = VersionToken(semantic=True)
        assert token.next_version("1.0.0", increment="major") == "2.0.0"
        assert token.next_version("1.2.3", increment="major") == "2.0.0"

    def test_next_version_semantic_from_none(self):
        """Test getting first semantic version."""
        token = VersionToken(semantic=True, start_version=1)
        assert token.next_version(None) == "1.0.0"


class TestVersionTokenComparison:
    """Tests for version comparison."""

    def test_compare_simple_versions(self):
        """Test comparing simple versions."""
        token = VersionToken()
        assert token.compare("001", "002") == -1
        assert token.compare("002", "001") == 1
        assert token.compare("001", "001") == 0

    def test_compare_prefixed_versions(self):
        """Test comparing prefixed versions."""
        token = VersionToken(prefix="v")
        assert token.compare("v001", "v002") == -1
        assert token.compare("v002", "v001") == 1
        assert token.compare("v001", "v001") == 0

    def test_compare_semantic_versions(self):
        """Test comparing semantic versions."""
        token = VersionToken(semantic=True)
        assert token.compare("1.0.0", "1.0.1") == -1
        assert token.compare("1.0.1", "1.0.0") == 1
        assert token.compare("1.0.0", "1.0.0") == 0
        assert token.compare("1.0.9", "1.1.0") == -1
        assert token.compare("1.9.0", "2.0.0") == -1


class TestVersionTokenValidation:
    """Tests for version validation."""

    def test_is_valid_version_simple(self):
        """Test validating simple versions."""
        token = VersionToken()
        assert token.is_valid_version("001") is True
        assert token.is_valid_version("v001") is True
        assert token.is_valid_version("invalid") is False

    def test_is_valid_version_semantic(self):
        """Test validating semantic versions."""
        token = VersionToken(semantic=True)
        assert token.is_valid_version("1.0.0") is True
        assert token.is_valid_version("v1.0.0") is True
        assert token.is_valid_version("invalid") is False


class TestVersionTokenSorting:
    """Tests for version sorting."""

    def test_sort_simple_versions(self):
        """Test sorting simple versions."""
        token = VersionToken()
        versions = ["003", "001", "010", "002"]
        sorted_versions = token.sort_versions(versions)
        assert sorted_versions == ["001", "002", "003", "010"]

    def test_sort_prefixed_versions(self):
        """Test sorting prefixed versions."""
        token = VersionToken(prefix="v")
        versions = ["v003", "v001", "v010", "v002"]
        sorted_versions = token.sort_versions(versions)
        assert sorted_versions == ["v001", "v002", "v003", "v010"]

    def test_sort_semantic_versions(self):
        """Test sorting semantic versions."""
        token = VersionToken(semantic=True)
        versions = ["1.0.1", "1.0.0", "1.1.0", "2.0.0"]
        sorted_versions = token.sort_versions(versions)
        assert sorted_versions == ["1.0.0", "1.0.1", "1.1.0", "2.0.0"]

    def test_sort_versions_reverse(self):
        """Test sorting versions in reverse order."""
        token = VersionToken()
        versions = ["001", "003", "002"]
        sorted_versions = token.sort_versions(versions, reverse=True)
        assert sorted_versions == ["003", "002", "001"]
