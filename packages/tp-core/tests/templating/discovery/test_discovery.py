"""Tests for tp.libs.templating.discovery module."""

from __future__ import annotations

import os
import tempfile

import pytest

from tp.libs.templating.discovery import (
    DiscoveredAsset,
    TemplateDiscovery,
    glob_from_template,
    regex_from_template,
)
from tp.libs.templating.paths import PathResolver, Template


class TestGlobFromTemplate:
    """Tests for glob_from_template function."""

    def test_simple_pattern(self):
        """Test glob generation from simple pattern."""
        template = Template(name="test", pattern="/content/{type}/{name}")
        glob = glob_from_template(template)
        assert glob == "/content/*/*"

    def test_with_known_tokens(self):
        """Test glob generation with known tokens."""
        template = Template(name="test", pattern="/content/{type}/{name}")
        glob = glob_from_template(template, type="characters")
        assert glob == "/content/characters/*"

    def test_with_all_known_tokens(self):
        """Test glob generation with all tokens known."""
        template = Template(name="test", pattern="/content/{type}/{name}")
        glob = glob_from_template(template, type="characters", name="hero")
        assert glob == "/content/characters/hero"

    def test_version_pattern(self):
        """Test glob generation with version token."""
        template = Template(
            name="test", pattern="/content/{asset}/v{version}/{asset}.fbx"
        )
        glob = glob_from_template(template, asset="hero")
        assert glob == "/content/hero/v*/hero.fbx"


class TestRegexFromTemplate:
    """Tests for regex_from_template function."""

    def test_simple_pattern(self):
        """Test regex generation from simple pattern."""
        template = Template(name="test", pattern="/content/{type}/{name}")
        regex = regex_from_template(template)

        match = regex.match("/content/characters/hero")
        assert match is not None
        assert match.group("type") == "characters"
        assert match.group("name") == "hero"

    def test_with_known_tokens(self):
        """Test regex generation with known tokens."""
        template = Template(name="test", pattern="/content/{type}/{name}")
        regex = regex_from_template(template, type="characters")

        # Should match when type is "characters"
        match = regex.match("/content/characters/hero")
        assert match is not None
        assert match.group("name") == "hero"

        # Should not match when type is different
        match = regex.match("/content/props/chair")
        assert match is None

    def test_no_match(self):
        """Test regex doesn't match wrong paths."""
        template = Template(name="test", pattern="/content/{type}/{name}")
        regex = regex_from_template(template)

        match = regex.match("/other/path/format")
        assert match is None


class TestDiscoveredAsset:
    """Tests for DiscoveredAsset class."""

    def test_properties(self):
        """Test DiscoveredAsset properties."""
        asset = DiscoveredAsset(
            path="/content/characters/hero/hero_v001.fbx",
            parsed_tokens={"name": "hero", "version": "001"},
            template_name="character",
            version="001",
        )

        assert asset.filename == "hero_v001.fbx"
        assert asset.directory == "/content/characters/hero"
        assert asset.extension == ".fbx"
        assert asset.name_without_extension == "hero_v001"
        assert asset.get_token("name") == "hero"
        assert asset.get_token("missing", "default") == "default"


class TestTemplateDiscovery:
    """Tests for TemplateDiscovery class."""

    @pytest.fixture
    def temp_structure(self):
        """Create a temporary directory structure for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test structure
            # /content/characters/hero/v001/hero_v001.fbx
            # /content/characters/hero/v002/hero_v002.fbx
            # /content/characters/villain/v001/villain_v001.fbx
            # /content/props/chair/v001/chair_v001.fbx

            paths = [
                "content/characters/hero/v001/hero_v001.fbx",
                "content/characters/hero/v002/hero_v002.fbx",
                "content/characters/villain/v001/villain_v001.fbx",
                "content/props/chair/v001/chair_v001.fbx",
            ]

            for path in paths:
                full_path = os.path.join(temp_dir, path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w") as f:
                    f.write("test")

            yield temp_dir

    @pytest.fixture
    def resolver(self):
        """Create a path resolver with test templates."""
        resolver = PathResolver()
        resolver.register_template(
            Template(
                name="asset",
                pattern="/content/{type}/{name}/v{version}/{name}_v{version}.fbx",
            )
        )
        return resolver

    def test_initialization(self, resolver):
        """Test TemplateDiscovery initialization."""
        discovery = TemplateDiscovery(resolver)
        assert discovery.path_resolver is resolver

    def test_find_matching_no_files(self, resolver):
        """Test finding when no files match."""
        discovery = TemplateDiscovery(resolver)
        with tempfile.TemporaryDirectory() as temp_dir:
            assets = discovery.find_matching("asset", temp_dir)
            assert len(assets) == 0

    def test_group_by_token(self, resolver):
        """Test grouping assets by token."""
        discovery = TemplateDiscovery(resolver)

        assets = [
            DiscoveredAsset(path="/a", parsed_tokens={"type": "character"}),
            DiscoveredAsset(path="/b", parsed_tokens={"type": "character"}),
            DiscoveredAsset(path="/c", parsed_tokens={"type": "prop"}),
        ]

        groups = discovery.group_by_token(assets, "type")
        assert "character" in groups
        assert "prop" in groups
        assert len(groups["character"]) == 2
        assert len(groups["prop"]) == 1


class TestTemplateDiscoveryIntegration:
    """Integration tests for TemplateDiscovery with real filesystem."""

    @pytest.fixture
    def temp_content(self):
        """Create temporary content structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create structure: temp_dir/type/name/v{version}/{name}_v{version}.fbx
            content = temp_dir.replace("\\", "/")

            structure = [
                f"{content}/characters/hero/v001/hero_v001.fbx",
                f"{content}/characters/hero/v002/hero_v002.fbx",
                f"{content}/props/chair/v001/chair_v001.fbx",
            ]

            for path in structure:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    f.write("test")

            yield content

    def test_find_all(self, temp_content):
        """Test finding all matching assets."""
        resolver = PathResolver()
        # Use the actual temp_content path as base
        resolver.register_template(
            Template(
                name="asset",
                pattern=f"{temp_content}/{{type}}/{{name}}/v{{version}}/{{name}}_v{{version}}.fbx",
            )
        )

        discovery = TemplateDiscovery(resolver)
        assets = discovery.find_matching("asset", temp_content)

        assert len(assets) == 3

    def test_find_filtered(self, temp_content):
        """Test finding with token filter."""
        resolver = PathResolver()
        resolver.register_template(
            Template(
                name="asset",
                pattern=f"{temp_content}/{{type}}/{{name}}/v{{version}}/{{name}}_v{{version}}.fbx",
            )
        )

        discovery = TemplateDiscovery(resolver)
        assets = discovery.find_matching(
            "asset", temp_content, type="characters"
        )

        # Should only find character assets (hero has 2 versions)
        assert len(assets) == 2
        for asset in assets:
            # type is not in parsed_tokens because it was a known filter
            assert asset.parsed_tokens.get("name") == "hero"
