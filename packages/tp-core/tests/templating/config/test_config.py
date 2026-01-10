"""Tests for tp.libs.templating.config module."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from tp.libs.templating.config import (
    AssetTypeSchema,
    ConfigurationMerger,
    PathTemplateSchema,
    RuleSchema,
    TemplateConfiguration,
    TemplateConfigurationSchema,
    TokenSchema,
    apply_overrides,
    deep_merge,
    merge_lists_by_key,
)


class TestDeepMerge:
    """Tests for deep_merge function."""

    def test_simple_merge(self):
        """Test simple dictionary merge."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        """Test nested dictionary merge."""
        base = {"a": {"b": 1, "c": 2}}
        override = {"a": {"c": 3, "d": 4}}
        result = deep_merge(base, override)
        assert result == {"a": {"b": 1, "c": 3, "d": 4}}

    def test_list_replace(self):
        """Test that lists are replaced, not merged."""
        base = {"a": [1, 2, 3]}
        override = {"a": [4, 5]}
        result = deep_merge(base, override)
        assert result == {"a": [4, 5]}

    def test_original_unchanged(self):
        """Test that original dictionaries are unchanged."""
        base = {"a": 1}
        override = {"b": 2}
        result = deep_merge(base, override)
        assert base == {"a": 1}
        assert override == {"b": 2}


class TestMergeListsByKey:
    """Tests for merge_lists_by_key function."""

    def test_merge_by_name(self):
        """Test merging lists by name key."""
        base = [{"name": "a", "value": 1}, {"name": "b", "value": 2}]
        override = [{"name": "a", "value": 10}, {"name": "c", "value": 3}]
        result = merge_lists_by_key(base, override, "name")

        assert len(result) == 3
        assert result[0] == {"name": "a", "value": 10}
        assert result[1] == {"name": "b", "value": 2}
        assert result[2] == {"name": "c", "value": 3}


class TestApplyOverrides:
    """Tests for apply_overrides function."""

    def test_dot_notation(self):
        """Test applying overrides with dot notation."""
        config = {"tokens": {"side": {"default": "L"}}}
        overrides = {"tokens.side.default": "R"}
        result = apply_overrides(config, overrides)
        assert result["tokens"]["side"]["default"] == "R"

    def test_simple_override(self):
        """Test applying simple overrides."""
        config = {"a": 1, "b": 2}
        overrides = {"a": 10}
        result = apply_overrides(config, overrides)
        assert result == {"a": 10, "b": 2}


class TestConfigurationMerger:
    """Tests for ConfigurationMerger class."""

    def test_empty_merger(self):
        """Test empty merger."""
        merger = ConfigurationMerger()
        assert merger.merge() == {}

    def test_single_layer(self):
        """Test single layer."""
        merger = ConfigurationMerger()
        merger.add_layer({"a": 1}, "base")
        assert merger.merge() == {"a": 1}

    def test_multiple_layers(self):
        """Test multiple layers with precedence."""
        merger = ConfigurationMerger()
        merger.add_layer({"a": 1, "b": 2}, "base")
        merger.add_layer({"b": 3, "c": 4}, "override")
        result = merger.merge()
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_get_value_dot_notation(self):
        """Test getting nested values."""
        merger = ConfigurationMerger()
        merger.add_layer({"a": {"b": {"c": 42}}}, "base")
        assert merger.get_value("a.b.c") == 42
        assert merger.get_value("a.b.missing", "default") == "default"

    def test_layer_count(self):
        """Test layer count."""
        merger = ConfigurationMerger()
        merger.add_layer({}, "layer1")
        merger.add_layer({}, "layer2")
        assert merger.layer_count == 2

    def test_layer_names(self):
        """Test layer names."""
        merger = ConfigurationMerger()
        merger.add_layer({}, "base")
        merger.add_layer({}, "override")
        assert merger.layer_names == ["base", "override"]


class TestSchemaClasses:
    """Tests for schema dataclasses."""

    def test_token_schema_round_trip(self):
        """Test TokenSchema to_dict/from_dict."""
        schema = TokenSchema(
            name="side",
            description="Side of body",
            default="L",
            key_values={"left": "L", "right": "R"},
        )
        data = schema.to_dict()
        restored = TokenSchema.from_dict(data)
        assert restored.name == schema.name
        assert restored.default == schema.default

    def test_rule_schema_round_trip(self):
        """Test RuleSchema to_dict/from_dict."""
        schema = RuleSchema(
            name="asset",
            expression="{side}_{name}_{type}",
            description="Asset naming rule",
        )
        data = schema.to_dict()
        restored = RuleSchema.from_dict(data)
        assert restored.name == schema.name
        assert restored.expression == schema.expression

    def test_path_template_schema_round_trip(self):
        """Test PathTemplateSchema to_dict/from_dict."""
        schema = PathTemplateSchema(
            name="asset_path",
            pattern="/content/{type}/{name}",
            description="Asset path template",
        )
        data = schema.to_dict()
        restored = PathTemplateSchema.from_dict(data)
        assert restored.name == schema.name
        assert restored.pattern == schema.pattern

    def test_asset_type_schema_round_trip(self):
        """Test AssetTypeSchema to_dict/from_dict."""
        schema = AssetTypeSchema(
            name="character",
            description="Character asset",
            file_extensions=[".fbx", ".ma"],
        )
        data = schema.to_dict()
        restored = AssetTypeSchema.from_dict(data)
        assert restored.name == schema.name
        assert ".fbx" in restored.file_extensions


class TestTemplateConfigurationSchema:
    """Tests for TemplateConfigurationSchema class."""

    def test_from_dict(self):
        """Test creating schema from dictionary."""
        data = {
            "version": "1.0",
            "name": "test",
            "tokens": {"side": {"default": "L", "keyValues": {"left": "L"}}},
            "rules": {"asset": {"expression": "{side}_{name}"}},
        }
        schema = TemplateConfigurationSchema.from_dict(data)
        assert schema.name == "test"
        assert "side" in schema.tokens
        assert "asset" in schema.rules

    def test_validation_missing_name(self):
        """Test validation catches missing name."""
        schema = TemplateConfigurationSchema()
        errors = schema.validate()
        assert any("name" in e.lower() for e in errors)

    def test_validation_undefined_token(self):
        """Test validation catches undefined token in rule."""
        schema = TemplateConfigurationSchema(name="test")
        schema.rules["asset"] = RuleSchema(
            name="asset", expression="{undefined_token}_{name}"
        )
        errors = schema.validate()
        assert any("undefined_token" in e for e in errors)


class TestTemplateConfiguration:
    """Tests for TemplateConfiguration class."""

    def test_initialization(self):
        """Test configuration initialization."""
        config = TemplateConfiguration()
        assert config.name == ""
        assert config.version == "1.0"

    def test_add_token(self):
        """Test adding a token."""
        config = TemplateConfiguration()
        config.add_token("side", default="L", left="L", right="R")
        assert "side" in config.schema.tokens
        assert config.schema.tokens["side"].default == "L"

    def test_add_rule(self):
        """Test adding a rule."""
        config = TemplateConfiguration()
        config.add_rule("asset", "{side}_{name}", description="Asset rule")
        assert "asset" in config.schema.rules

    def test_add_path_template(self):
        """Test adding a path template."""
        config = TemplateConfiguration()
        config.add_path_template("asset_path", "/content/{type}/{name}")
        assert "asset_path" in config.schema.path_templates

    def test_add_asset_type(self):
        """Test adding an asset type."""
        config = TemplateConfiguration()
        config.add_asset_type(
            "character",
            description="Character asset",
            file_extensions=[".fbx"],
        )
        assert "character" in config.schema.asset_types

    def test_to_dict_from_dict(self):
        """Test serialization round-trip."""
        config = TemplateConfiguration()
        config.add_token("side", default="L")
        config.add_rule("asset", "{side}_{name}")

        data = config.to_dict()
        restored = TemplateConfiguration.from_dict(data)

        assert "side" in restored.schema.tokens
        assert "asset" in restored.schema.rules

    def test_merge_with(self):
        """Test merging configurations."""
        config1 = TemplateConfiguration()
        config1.add_token("a", default="1")

        config2 = TemplateConfiguration()
        config2.add_token("b", default="2")

        merged = config1.merge_with(config2)
        assert "a" in merged.schema.tokens
        assert "b" in merged.schema.tokens

    def test_json_save_load(self):
        """Test saving and loading JSON."""
        config = TemplateConfiguration()
        config.add_token("side", default="L")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = f.name

        try:
            config.to_json(temp_path)
            loaded = TemplateConfiguration.from_json(temp_path)
            assert "side" in loaded.schema.tokens
        finally:
            os.unlink(temp_path)

    def test_build_naming_convention(self):
        """Test building naming convention from config."""
        config = TemplateConfiguration()
        config.add_token("side", default="L", left="L", right="R")
        config.add_rule("asset", "{side}_{name}")

        convention = config.build_naming_convention()
        assert convention is not None
        assert convention.token("side") is not None

    def test_build_path_resolver(self):
        """Test building path resolver from config."""
        config = TemplateConfiguration()
        config.add_path_template("asset", "/content/{type}/{name}")

        resolver = config.build_path_resolver()
        assert resolver is not None
        assert resolver.get_template("asset") is not None

    def test_build_asset_registry(self):
        """Test building asset registry from config."""
        config = TemplateConfiguration()
        config.add_asset_type("character", file_extensions=[".fbx"])

        registry = config.build_asset_registry()
        assert registry is not None
        assert registry.has_type("character")
