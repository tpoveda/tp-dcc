"""Configuration loader for template configurations."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from tp.libs.templating.config.merger import ConfigurationMerger, deep_merge
from tp.libs.templating.config.schema import (
    AssetTypeSchema,
    PathTemplateSchema,
    RuleSchema,
    TemplateConfigurationSchema,
    TokenSchema,
)

if TYPE_CHECKING:
    from tp.libs.templating.assets.registry import AssetTypeRegistry
    from tp.libs.templating.naming.convention import NamingConvention
    from tp.libs.templating.paths.resolver import PathResolver


class TemplateConfiguration:
    """Complete serializable configuration for the templating system.

    This class provides a unified way to load, save, and build
    templating components from configuration files.

    Example:
        >>> # Load from YAML
        >>> config = TemplateConfiguration.from_yaml("/path/to/config.yaml")
        >>>
        >>> # Validate
        >>> errors = config.validate()
        >>> if errors:
        ...     print(f"Validation errors: {errors}")
        >>>
        >>> # Build components
        >>> naming_convention = config.build_naming_convention()
        >>> path_resolver = config.build_path_resolver()
        >>> asset_registry = config.build_asset_registry()
    """

    def __init__(self, schema: TemplateConfigurationSchema | None = None):
        """TemplateConfiguration constructor.

        Args:
            schema: Configuration schema. If None, creates empty schema.
        """

        self._schema = schema or TemplateConfigurationSchema()
        self._source_path: str | None = None

    @property
    def schema(self) -> TemplateConfigurationSchema:
        """Returns the configuration schema."""
        return self._schema

    @property
    def name(self) -> str:
        """Returns the configuration name."""
        return self._schema.name

    @property
    def version(self) -> str:
        """Returns the configuration version."""
        return self._schema.version

    @property
    def source_path(self) -> str | None:
        """Returns the path this configuration was loaded from."""
        return self._source_path

    @classmethod
    def from_yaml(cls, path: str) -> TemplateConfiguration:
        """Load configuration from YAML file.

        Args:
            path: Path to YAML file.

        Returns:
            TemplateConfiguration instance.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If YAML is invalid.
        """

        try:
            from tp.libs.python import yamlio
        except ImportError:
            raise ImportError("YAML support requires tp.libs.python.yamlio")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Configuration file not found: {path}")

        data = yamlio.read_yaml_file(path)
        if data is None:
            raise ValueError(f"Failed to load YAML from: {path}")

        schema = TemplateConfigurationSchema.from_dict(data)
        config = cls(schema)
        config._source_path = path

        return config

    @classmethod
    def from_json(cls, path: str) -> TemplateConfiguration:
        """Load configuration from JSON file.

        Args:
            path: Path to JSON file.

        Returns:
            TemplateConfiguration instance.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If JSON is invalid.
        """

        if not os.path.exists(path):
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        schema = TemplateConfigurationSchema.from_dict(data)
        config = cls(schema)
        config._source_path = path

        return config

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TemplateConfiguration:
        """Create configuration from dictionary.

        Args:
            data: Configuration dictionary.

        Returns:
            TemplateConfiguration instance.
        """

        schema = TemplateConfigurationSchema.from_dict(data)
        return cls(schema)

    def to_yaml(self, path: str):
        """Save configuration to YAML file.

        Args:
            path: Path to save to.
        """

        try:
            from tp.libs.python import yamlio
        except ImportError:
            raise ImportError("YAML support requires tp.libs.python.yamlio")

        data = self._schema.to_dict()
        yamlio.write_yaml_file(data, path)

    def to_json(self, path: str, indent: int = 2):
        """Save configuration to JSON file.

        Args:
            path: Path to save to.
            indent: JSON indentation level.
        """

        data = self._schema.to_dict()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration dictionary.
        """

        return self._schema.to_dict()

    def validate(self) -> list[str]:
        """Validate configuration integrity.

        Returns:
            List of validation error messages.
        """

        return self._schema.validate()

    def merge_with(
        self, other: TemplateConfiguration
    ) -> TemplateConfiguration:
        """Merge with another configuration.

        Values from the other configuration take precedence.

        Args:
            other: Configuration to merge with.

        Returns:
            New merged configuration.
        """

        merged_data = deep_merge(self.to_dict(), other.to_dict())
        return TemplateConfiguration.from_dict(merged_data)

    def build_naming_convention(self) -> NamingConvention:
        """Build NamingConvention from configuration.

        Returns:
            NamingConvention instance.
        """

        from tp.libs.templating.naming.convention import NamingConvention

        # Create convention with name
        convention = NamingConvention(naming_data={"name": self._schema.name})

        # Add tokens
        for token_name, token_schema in self._schema.tokens.items():
            convention.add_token(
                token_name,
                default=token_schema.default or None,
                **token_schema.key_values,
            )

        # Add rules
        for rule_name, rule_schema in self._schema.rules.items():
            convention.add_rule(
                rule_name,
                rule_schema.expression,
                rule_schema.example_fields,
            )

        return convention

    def build_path_resolver(self) -> PathResolver:
        """Build PathResolver from configuration.

        Returns:
            PathResolver instance.
        """

        from tp.libs.templating.paths import PathResolver, Template

        resolver = PathResolver()

        # Register path templates
        for (
            template_name,
            template_schema,
        ) in self._schema.path_templates.items():
            template = Template(
                name=template_name,
                pattern=template_schema.pattern,
                template_resolver=resolver,
            )
            resolver.register_template(template)

        return resolver

    def build_asset_registry(self) -> AssetTypeRegistry:
        """Build AssetTypeRegistry from configuration.

        Returns:
            AssetTypeRegistry instance.
        """

        from tp.libs.templating.assets import (
            AssetTypeDefinition,
            AssetTypeRegistry,
        )

        registry = AssetTypeRegistry(include_builtin=False)

        # Register asset types
        for type_name, type_schema in self._schema.asset_types.items():
            asset_type = AssetTypeDefinition(
                name=type_name,
                description=type_schema.description,
                naming_rule=type_schema.naming_rule,
                path_template=type_schema.path_template,
                required_tokens=type_schema.required_tokens,
                allowed_tokens=type_schema.allowed_tokens,
                file_extensions=type_schema.file_extensions,
            )
            registry.register_type(asset_type)

        return registry

    # Token management
    def add_token(
        self,
        name: str,
        description: str = "",
        default: str = "",
        **key_values,
    ):
        """Add a token to the configuration.

        Args:
            name: Token name.
            description: Token description.
            default: Default value.
            **key_values: Key-value mappings.
        """

        self._schema.tokens[name] = TokenSchema(
            name=name,
            description=description,
            default=default,
            key_values=key_values,
        )

    # Rule management
    def add_rule(
        self,
        name: str,
        expression: str,
        description: str = "",
        **example_fields,
    ):
        """Add a rule to the configuration.

        Args:
            name: Rule name.
            expression: Rule expression.
            description: Rule description.
            **example_fields: Example field values.
        """

        self._schema.rules[name] = RuleSchema(
            name=name,
            expression=expression,
            description=description,
            example_fields=example_fields,
        )

    # Path template management
    def add_path_template(
        self,
        name: str,
        pattern: str,
        description: str = "",
    ):
        """Add a path template to the configuration.

        Args:
            name: Template name.
            pattern: Path pattern.
            description: Template description.
        """

        self._schema.path_templates[name] = PathTemplateSchema(
            name=name,
            pattern=pattern,
            description=description,
        )

    # Asset type management
    def add_asset_type(
        self,
        name: str,
        description: str = "",
        naming_rule: str = "",
        path_template: str = "",
        required_tokens: list[str] | None = None,
        allowed_tokens: list[str] | None = None,
        file_extensions: list[str] | None = None,
    ):
        """Add an asset type to the configuration.

        Args:
            name: Asset type name.
            description: Asset type description.
            naming_rule: Associated naming rule.
            path_template: Associated path template.
            required_tokens: Required tokens.
            allowed_tokens: Allowed tokens.
            file_extensions: Valid file extensions.
        """

        self._schema.asset_types[name] = AssetTypeSchema(
            name=name,
            description=description,
            naming_rule=naming_rule,
            path_template=path_template,
            required_tokens=required_tokens or [],
            allowed_tokens=allowed_tokens or [],
            file_extensions=file_extensions or [],
        )
