"""Configuration schema definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TokenSchema:
    """Schema for a token definition in configuration.

    Attributes:
        name: Token name.
        description: Token description.
        default: Default value.
        key_values: Key-value mappings.
        required: Whether the token is required.
    """

    name: str
    description: str = ""
    default: str = ""
    key_values: dict[str, str] = field(default_factory=dict)
    required: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "default": self.default,
            "keyValues": self.key_values,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TokenSchema:
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            default=data.get("default", ""),
            key_values=data.get("keyValues", data.get("key_values", {})),
            required=data.get("required", False),
        )


@dataclass
class RuleSchema:
    """Schema for a rule definition in configuration.

    Attributes:
        name: Rule name.
        expression: Rule expression pattern.
        description: Rule description.
        example_fields: Example field values.
    """

    name: str
    expression: str
    description: str = ""
    example_fields: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "expression": self.expression,
            "description": self.description,
            "exampleFields": self.example_fields,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuleSchema:
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            expression=data.get("expression", ""),
            description=data.get("description", ""),
            example_fields=data.get(
                "exampleFields", data.get("example_fields", {})
            ),
        )


@dataclass
class PathTemplateSchema:
    """Schema for a path template definition in configuration.

    Attributes:
        name: Template name.
        pattern: Path pattern.
        description: Template description.
        references: Other templates this one references.
    """

    name: str
    pattern: str
    description: str = ""
    references: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "pattern": self.pattern,
            "description": self.description,
            "references": self.references,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PathTemplateSchema:
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            pattern=data.get("pattern", ""),
            description=data.get("description", ""),
            references=data.get("references", []),
        )


@dataclass
class AssetTypeSchema:
    """Schema for an asset type definition in configuration.

    Attributes:
        name: Asset type name.
        description: Asset type description.
        naming_rule: Associated naming rule.
        path_template: Associated path template.
        required_tokens: Required tokens for this type.
        allowed_tokens: Allowed tokens for this type.
        file_extensions: Valid file extensions.
    """

    name: str
    description: str = ""
    naming_rule: str = ""
    path_template: str = ""
    required_tokens: list[str] = field(default_factory=list)
    allowed_tokens: list[str] = field(default_factory=list)
    file_extensions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "namingRule": self.naming_rule,
            "pathTemplate": self.path_template,
            "requiredTokens": self.required_tokens,
            "allowedTokens": self.allowed_tokens,
            "fileExtensions": self.file_extensions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AssetTypeSchema:
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            naming_rule=data.get("namingRule", data.get("naming_rule", "")),
            path_template=data.get(
                "pathTemplate", data.get("path_template", "")
            ),
            required_tokens=data.get(
                "requiredTokens", data.get("required_tokens", [])
            ),
            allowed_tokens=data.get(
                "allowedTokens", data.get("allowed_tokens", [])
            ),
            file_extensions=data.get(
                "fileExtensions", data.get("file_extensions", [])
            ),
        )


@dataclass
class TemplateConfigurationSchema:
    """Complete schema for template configuration.

    Attributes:
        version: Configuration version.
        name: Configuration name.
        description: Configuration description.
        tokens: Token definitions.
        rules: Rule definitions.
        path_templates: Path template definitions.
        asset_types: Asset type definitions.
        metadata: Additional metadata.
    """

    version: str = "1.0"
    name: str = ""
    description: str = ""
    tokens: dict[str, TokenSchema] = field(default_factory=dict)
    rules: dict[str, RuleSchema] = field(default_factory=dict)
    path_templates: dict[str, PathTemplateSchema] = field(default_factory=dict)
    asset_types: dict[str, AssetTypeSchema] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "tokens": {k: v.to_dict() for k, v in self.tokens.items()},
            "rules": {k: v.to_dict() for k, v in self.rules.items()},
            "pathTemplates": {
                k: v.to_dict() for k, v in self.path_templates.items()
            },
            "assetTypes": {
                k: v.to_dict() for k, v in self.asset_types.items()
            },
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TemplateConfigurationSchema:
        """Create from dictionary."""
        tokens = {}
        for name, token_data in data.get("tokens", {}).items():
            if isinstance(token_data, dict):
                token_data["name"] = token_data.get("name", name)
                tokens[name] = TokenSchema.from_dict(token_data)

        rules = {}
        for name, rule_data in data.get("rules", {}).items():
            if isinstance(rule_data, dict):
                rule_data["name"] = rule_data.get("name", name)
                rules[name] = RuleSchema.from_dict(rule_data)

        path_templates = {}
        for name, template_data in data.get(
            "pathTemplates", data.get("path_templates", {})
        ).items():
            if isinstance(template_data, dict):
                template_data["name"] = template_data.get("name", name)
                path_templates[name] = PathTemplateSchema.from_dict(
                    template_data
                )

        asset_types = {}
        for name, type_data in data.get(
            "assetTypes", data.get("asset_types", {})
        ).items():
            if isinstance(type_data, dict):
                type_data["name"] = type_data.get("name", name)
                asset_types[name] = AssetTypeSchema.from_dict(type_data)

        return cls(
            version=data.get("version", "1.0"),
            name=data.get("name", ""),
            description=data.get("description", ""),
            tokens=tokens,
            rules=rules,
            path_templates=path_templates,
            asset_types=asset_types,
            metadata=data.get("metadata", {}),
        )

    def validate(self) -> list[str]:
        """Validate the configuration schema.

        Returns:
            List of validation error messages.
        """
        errors = []

        # Check for required fields
        if not self.name:
            errors.append("Configuration 'name' is required")

        # Validate rule expressions reference valid tokens
        for rule_name, rule in self.rules.items():
            # Extract token names from expression
            import re

            token_refs = re.findall(r"\{(\w+)\}", rule.expression)
            for token_ref in token_refs:
                if token_ref not in self.tokens:
                    errors.append(
                        f"Rule '{rule_name}' references undefined token '{token_ref}'"
                    )

        # Validate asset types reference valid rules and templates
        for type_name, asset_type in self.asset_types.items():
            if (
                asset_type.naming_rule
                and asset_type.naming_rule not in self.rules
            ):
                errors.append(
                    f"Asset type '{type_name}' references undefined rule "
                    f"'{asset_type.naming_rule}'"
                )
            if (
                asset_type.path_template
                and asset_type.path_template not in self.path_templates
            ):
                errors.append(
                    f"Asset type '{type_name}' references undefined path template "
                    f"'{asset_type.path_template}'"
                )

        return errors
