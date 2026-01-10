"""Tests for tp.libs.templating.assets module."""

from __future__ import annotations

import pytest

from tp.libs.templating.assets import (
    BUILTIN_ASSET_TYPES,
    CHARACTER_ASSET,
    AssetTypeDefinition,
    AssetTypeRegistry,
    AssetValidator,
    ValidationResult,
)


class TestAssetTypeDefinition:
    """Tests for AssetTypeDefinition class."""

    def test_initialization_basic(self):
        """Test basic initialization."""
        asset_type = AssetTypeDefinition(
            name="test",
            description="Test asset",
        )
        assert asset_type.name == "test"
        assert asset_type.description == "Test asset"

    def test_initialization_with_tokens(self):
        """Test initialization with tokens."""
        asset_type = AssetTypeDefinition(
            name="test",
            required_tokens=["name", "type"],
            allowed_tokens=["name", "type", "variant"],
        )
        assert asset_type.required_tokens == ["name", "type"]
        assert "name" in asset_type.allowed_tokens
        assert "variant" in asset_type.allowed_tokens

    def test_required_tokens_added_to_allowed(self):
        """Test that required tokens are added to allowed tokens."""
        asset_type = AssetTypeDefinition(
            name="test",
            required_tokens=["name", "type"],
            allowed_tokens=["variant"],
        )
        # Required tokens should be added to allowed
        assert "name" in asset_type.allowed_tokens
        assert "type" in asset_type.allowed_tokens
        assert "variant" in asset_type.allowed_tokens

    def test_file_extensions_normalized(self):
        """Test that file extensions are normalized with dots."""
        asset_type = AssetTypeDefinition(
            name="test",
            file_extensions=["fbx", ".ma", "mb"],
        )
        assert ".fbx" in asset_type.file_extensions
        assert ".ma" in asset_type.file_extensions
        assert ".mb" in asset_type.file_extensions

    def test_has_required_tokens(self):
        """Test checking for required tokens."""
        asset_type = AssetTypeDefinition(
            name="test",
            required_tokens=["name", "type"],
        )
        assert (
            asset_type.has_required_tokens({"name": "hero", "type": "char"})
            is True
        )
        assert asset_type.has_required_tokens({"name": "hero"}) is False
        assert asset_type.has_required_tokens({}) is False

    def test_has_valid_extension(self):
        """Test checking for valid file extension."""
        asset_type = AssetTypeDefinition(
            name="test",
            file_extensions=[".fbx", ".ma"],
        )
        assert asset_type.has_valid_extension("/path/to/file.fbx") is True
        assert asset_type.has_valid_extension("/path/to/file.FBX") is True
        assert asset_type.has_valid_extension("/path/to/file.ma") is True
        assert asset_type.has_valid_extension("/path/to/file.obj") is False

    def test_has_valid_extension_no_extensions(self):
        """Test that empty extensions list allows all."""
        asset_type = AssetTypeDefinition(name="test")
        assert asset_type.has_valid_extension("/path/to/file.any") is True

    def test_run_validators(self):
        """Test running custom validators."""

        def always_pass(name, tokens):
            return True

        def always_fail(name, tokens):
            return False

        asset_type = AssetTypeDefinition(
            name="test",
            validators=[always_pass],
        )
        errors = asset_type.run_validators("test", {})
        assert len(errors) == 0

        asset_type.validators.append(always_fail)
        errors = asset_type.run_validators("test", {})
        assert len(errors) == 1


class TestAssetTypeRegistry:
    """Tests for AssetTypeRegistry class."""

    def test_initialization_empty(self):
        """Test initialization without built-in types."""
        registry = AssetTypeRegistry(include_builtin=False)
        assert registry.type_count() == 0

    def test_initialization_with_builtin(self):
        """Test initialization with built-in types."""
        registry = AssetTypeRegistry(include_builtin=True)
        assert registry.type_count() > 0
        assert registry.has_type("character")
        assert registry.has_type("texture")

    def test_register_type(self):
        """Test registering a custom type."""
        registry = AssetTypeRegistry(include_builtin=False)
        custom_type = AssetTypeDefinition(
            name="custom", description="Custom type"
        )
        registry.register_type(custom_type)
        assert registry.has_type("custom")
        assert registry.get_type("custom") == custom_type

    def test_register_type_duplicate_error(self):
        """Test registering duplicate type raises error."""
        registry = AssetTypeRegistry(include_builtin=False)
        type1 = AssetTypeDefinition(name="test")
        type2 = AssetTypeDefinition(name="test")
        registry.register_type(type1)
        with pytest.raises(ValueError):
            registry.register_type(type2)

    def test_register_type_overwrite(self):
        """Test registering with overwrite."""
        registry = AssetTypeRegistry(include_builtin=False)
        type1 = AssetTypeDefinition(name="test", description="First")
        type2 = AssetTypeDefinition(name="test", description="Second")
        registry.register_type(type1)
        registry.register_type(type2, overwrite=True)
        assert registry.get_type("test").description == "Second"

    def test_unregister_type(self):
        """Test unregistering a type."""
        registry = AssetTypeRegistry(include_builtin=False)
        registry.register_type(AssetTypeDefinition(name="test"))
        assert registry.unregister_type("test") is True
        assert registry.has_type("test") is False

    def test_unregister_nonexistent_type(self):
        """Test unregistering nonexistent type."""
        registry = AssetTypeRegistry(include_builtin=False)
        assert registry.unregister_type("nonexistent") is False

    def test_list_types(self):
        """Test listing all types."""
        registry = AssetTypeRegistry(include_builtin=False)
        registry.register_type(AssetTypeDefinition(name="type1"))
        registry.register_type(AssetTypeDefinition(name="type2"))
        types = registry.list_types()
        assert "type1" in types
        assert "type2" in types

    def test_types_by_category(self):
        """Test getting types by category."""
        registry = AssetTypeRegistry(include_builtin=True)
        types_3d = registry.types_by_category("3d_asset")
        assert len(types_3d) > 0
        assert all(t.metadata.get("category") == "3d_asset" for t in types_3d)

    def test_types_with_extension(self):
        """Test getting types by file extension."""
        registry = AssetTypeRegistry(include_builtin=True)
        types_fbx = registry.types_with_extension(".fbx")
        assert len(types_fbx) > 0

    def test_clear(self):
        """Test clearing the registry."""
        registry = AssetTypeRegistry(include_builtin=True)
        assert registry.type_count() > 0
        registry.clear()
        assert registry.type_count() == 0

    def test_to_dict_from_dict(self):
        """Test serialization round-trip."""
        registry = AssetTypeRegistry(include_builtin=False)
        registry.register_type(
            AssetTypeDefinition(
                name="test",
                description="Test type",
                required_tokens=["name"],
            )
        )

        data = registry.to_dict()
        new_registry = AssetTypeRegistry.from_dict(data)

        assert new_registry.has_type("test")
        assert new_registry.get_type("test").description == "Test type"


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_initialization_defaults(self):
        """Test default initialization."""
        result = ValidationResult()
        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_add_error(self):
        """Test adding an error."""
        result = ValidationResult()
        result.add_error("Test error")
        assert result.valid is False
        assert "Test error" in result.errors

    def test_add_warning(self):
        """Test adding a warning."""
        result = ValidationResult()
        result.add_warning("Test warning")
        assert result.valid is True  # Warnings don't invalidate
        assert "Test warning" in result.warnings

    def test_bool_conversion(self):
        """Test boolean conversion."""
        valid_result = ValidationResult()
        invalid_result = ValidationResult()
        invalid_result.add_error("Error")

        assert bool(valid_result) is True
        assert bool(invalid_result) is False

    def test_merge(self):
        """Test merging results."""
        result1 = ValidationResult()
        result1.add_error("Error 1")

        result2 = ValidationResult()
        result2.add_warning("Warning 1")
        result2.parsed_tokens = {"name": "test"}

        result1.merge(result2)
        assert "Error 1" in result1.errors
        assert "Warning 1" in result1.warnings
        assert result1.parsed_tokens.get("name") == "test"


class TestAssetValidator:
    """Tests for AssetValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a validator with built-in types."""
        registry = AssetTypeRegistry(include_builtin=True)
        return AssetValidator(registry)

    def test_initialization(self, validator):
        """Test validator initialization."""
        assert validator.registry is not None
        assert validator.naming_convention is None

    def test_validate_path_valid_extension(self, validator):
        """Test validating path with valid extension."""
        result = validator.validate_path("/content/hero.fbx", "character")
        # Should not have extension error
        ext_errors = [e for e in result.errors if "extension" in e.lower()]
        assert len(ext_errors) == 0

    def test_validate_path_invalid_extension(self, validator):
        """Test validating path with invalid extension."""
        result = validator.validate_path("/content/hero.txt", "character")
        # Should have extension error
        ext_errors = [e for e in result.errors if "extension" in e.lower()]
        assert len(ext_errors) > 0

    def test_validate_unknown_asset_type(self, validator):
        """Test validating with unknown asset type."""
        result = validator.validate_name("test", "unknown_type")
        assert result.valid is False
        assert any("Unknown asset type" in e for e in result.errors)

    def test_suggest_corrections_spaces(self, validator):
        """Test suggesting corrections for spaces."""
        suggestions = validator.suggest_corrections(
            "hero character", "character"
        )
        assert "hero_character" in suggestions

    def test_suggest_corrections_case(self, validator):
        """Test suggesting corrections for case."""
        suggestions = validator.suggest_corrections("HERO", "character")
        assert "hero" in suggestions

    def test_detect_asset_type_texture(self, validator):
        """Test detecting texture asset type."""
        detected = validator.detect_asset_type(
            "/content/textures/T_hero_D.png"
        )
        assert detected == "texture"

    def test_detect_asset_type_character(self, validator):
        """Test detecting character asset type."""
        detected = validator.detect_asset_type("/content/characters/hero.fbx")
        assert detected == "character"

    def test_batch_validate(self, validator):
        """Test batch validation."""
        items = [
            ("hero", "character"),
            ("/content/texture.png", "texture"),
        ]
        results = validator.batch_validate(items)
        assert len(results) == 2
        assert "hero" in results
        assert "/content/texture.png" in results


class TestBuiltinAssetTypes:
    """Tests for built-in asset types."""

    def test_builtin_types_exist(self):
        """Test that built-in types are defined."""
        assert "character" in BUILTIN_ASSET_TYPES
        assert "prop" in BUILTIN_ASSET_TYPES
        assert "texture" in BUILTIN_ASSET_TYPES
        assert "animation" in BUILTIN_ASSET_TYPES

    def test_character_asset_definition(self):
        """Test CHARACTER_ASSET definition."""
        assert CHARACTER_ASSET.name == "character"
        assert "name" in CHARACTER_ASSET.required_tokens
        assert ".fbx" in CHARACTER_ASSET.file_extensions
        assert CHARACTER_ASSET.metadata.get("category") == "3d_asset"
