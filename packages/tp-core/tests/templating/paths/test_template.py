"""Tests for tp.libs.templating.paths.template module."""

from __future__ import annotations

import pytest

from tp.libs.templating import errors
from tp.libs.templating.paths import PathResolver, Template


class TestTemplate:
    """Tests for the Template class."""

    def test_initialization(self):
        """Test Template initialization."""
        template = Template(name="test", pattern="/path/{placeholder}")
        assert template.name == "test"
        assert template.pattern == "/path/{placeholder}"

    def test_repr(self):
        """Test Template string representation."""
        template = Template(name="test", pattern="/path/{placeholder}")
        assert "test" in repr(template)
        assert "/path/{placeholder}" in repr(template)

    def test_keys(self):
        """Test Template keys extraction."""
        template = Template(
            name="test", pattern="/jobs/{job}/assets/{asset_name}/model/{lod}"
        )
        keys = template.keys()
        assert keys == {"job", "asset_name", "lod"}

    def test_keys_with_duplicates(self):
        """Test Template keys extraction with duplicate placeholders."""
        template = Template(
            name="test",
            pattern="/jobs/{job}/assets/{asset_name}/{asset_name}.txt",
        )
        keys = template.keys()
        assert keys == {"job", "asset_name"}

    def test_parse_simple(self):
        """Test parsing a simple path."""
        template = Template(
            name="test", pattern="/content/{asset_type}/{asset_name}"
        )
        result = template.parse("/content/characters/hero")
        assert result == {"asset_type": "characters", "asset_name": "hero"}

    def test_parse_complex(self):
        """Test parsing a complex path with multiple placeholders."""
        template = Template(
            name="test",
            pattern="/jobs/{job}/assets/{asset_name}/v{version}.{ext}",
        )
        result = template.parse("/jobs/project1/assets/hero_model/v001.fbx")
        assert result == {
            "job": "project1",
            "asset_name": "hero_model",
            "version": "001",
            "ext": "fbx",
        }

    def test_parse_no_match(self):
        """Test parsing when path doesn't match."""
        template = Template(name="test", pattern="/content/{type}/{name}")
        with pytest.raises(errors.ParseError):
            template.parse("/other/path/format")

    def test_format_simple(self):
        """Test formatting a simple path."""
        template = Template(
            name="test", pattern="/content/{asset_type}/{asset_name}"
        )
        result = template.format(
            {"asset_type": "characters", "asset_name": "hero"}
        )
        assert result == "/content/characters/hero"

    def test_format_complex(self):
        """Test formatting a complex path."""
        template = Template(
            name="test",
            pattern="/jobs/{job}/assets/{asset_name}/v{version}.{ext}",
        )
        result = template.format(
            {
                "job": "project1",
                "asset_name": "hero_model",
                "version": "001",
                "ext": "fbx",
            }
        )
        assert result == "/jobs/project1/assets/hero_model/v001.fbx"

    def test_format_missing_key(self):
        """Test formatting with missing key."""
        template = Template(name="test", pattern="/content/{type}/{name}")
        with pytest.raises(errors.FormatError):
            template.format({"type": "characters"})  # Missing 'name'

    def test_roundtrip(self):
        """Test that parse and format are inverse operations."""
        template = Template(
            name="test",
            pattern="/content/{asset_type}/{asset_name}/v{version}",
        )
        original_path = "/content/props/chair/v003"
        parsed = template.parse(original_path)
        formatted = template.format(parsed)
        assert formatted == original_path


class TestPathResolver:
    """Tests for the PathResolver class."""

    def test_initialization(self):
        """Test PathResolver initialization."""
        resolver = PathResolver()
        assert resolver.naming_convention is None
        assert len(resolver.templates) == 0

    def test_register_template(self):
        """Test registering a template."""
        resolver = PathResolver()
        template = Template(name="test", pattern="/path/{placeholder}")
        resolver.register_template(template)
        assert "test" in resolver.list_templates()
        assert resolver.get_template("test") == template

    def test_unregister_template(self):
        """Test unregistering a template."""
        resolver = PathResolver()
        template = Template(name="test", pattern="/path/{placeholder}")
        resolver.register_template(template)
        assert resolver.unregister_template("test") is True
        assert "test" not in resolver.list_templates()

    def test_unregister_nonexistent_template(self):
        """Test unregistering a template that doesn't exist."""
        resolver = PathResolver()
        assert resolver.unregister_template("nonexistent") is False

    def test_resolve_path(self):
        """Test resolving a path without naming convention."""
        resolver = PathResolver()
        resolver.register_template(
            Template(name="asset", pattern="/content/{type}/{name}")
        )
        path = resolver.resolve_path("asset", type="characters", name="hero")
        assert path == "/content/characters/hero"

    def test_resolve_path_not_found(self):
        """Test resolving with a non-existent template."""
        resolver = PathResolver()
        with pytest.raises(KeyError):
            resolver.resolve_path("nonexistent", type="test")

    def test_parse_path(self):
        """Test parsing a path without naming convention."""
        resolver = PathResolver()
        resolver.register_template(
            Template(name="asset", pattern="/content/{type}/{name}")
        )
        result = resolver.parse_path("asset", "/content/characters/hero")
        assert result == {"type": "characters", "name": "hero"}

    def test_clear_templates(self):
        """Test clearing all templates."""
        resolver = PathResolver()
        resolver.register_template(Template(name="t1", pattern="/p1/{a}"))
        resolver.register_template(Template(name="t2", pattern="/p2/{b}"))
        resolver.clear_templates()
        assert len(resolver.list_templates()) == 0


class TestTemplateReferences:
    """Tests for template references using @ syntax."""

    def test_template_reference(self):
        """Test resolving template references."""
        resolver = PathResolver()

        # Register base template
        resolver.register_template(
            Template(name="project_root", pattern="/projects/{project}")
        )

        # Register template that references base
        resolver.register_template(
            Template(
                name="asset_path",
                pattern="{@project_root}/assets/{asset_name}",
                template_resolver=resolver,
            )
        )

        # Resolve path using the referencing template
        path = resolver.resolve_path(
            "asset_path", project="game1", asset_name="hero"
        )
        assert path == "/projects/game1/assets/hero"

    def test_nested_template_references(self):
        """Test resolving nested template references."""
        resolver = PathResolver()

        resolver.register_template(Template(name="root", pattern="/content"))

        resolver.register_template(
            Template(
                name="assets",
                pattern="{@root}/assets/{type}",
                template_resolver=resolver,
            )
        )

        resolver.register_template(
            Template(
                name="asset_file",
                pattern="{@assets}/{name}.{ext}",
                template_resolver=resolver,
            )
        )

        path = resolver.resolve_path(
            "asset_file", type="textures", name="hero_diffuse", ext="png"
        )
        assert path == "/content/assets/textures/hero_diffuse.png"
