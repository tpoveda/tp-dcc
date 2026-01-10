"""Asset validator for validating names and paths against asset type rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tp.libs.templating.assets.registry import AssetTypeRegistry

if TYPE_CHECKING:
    from tp.libs.templating.naming.convention import NamingConvention


@dataclass
class ValidationResult:
    """Result of a validation operation.

    Attributes:
        valid: Whether the validation passed.
        errors: List of error messages.
        warnings: List of warning messages.
        suggestions: List of suggested corrections.
        parsed_tokens: Parsed token values (if applicable).
    """

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    parsed_tokens: dict[str, str] = field(default_factory=dict)

    def add_error(self, message: str):
        """Add an error message and mark as invalid."""
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)

    def add_suggestion(self, message: str):
        """Add a suggestion."""
        self.suggestions.append(message)

    def merge(self, other: ValidationResult):
        """Merge another validation result into this one."""
        if not other.valid:
            self.valid = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.suggestions.extend(other.suggestions)
        self.parsed_tokens.update(other.parsed_tokens)

    def __bool__(self) -> bool:
        """Return True if validation passed."""
        return self.valid


class AssetValidator:
    """Validate asset names and paths against asset type rules.

    This class provides validation functionality for asset names and paths,
    checking them against registered asset type definitions and naming conventions.

    Example:
        >>> from tp.libs.templating.assets import AssetValidator, AssetTypeRegistry
        >>> from tp.libs.templating.naming import NamingConvention
        >>>
        >>> # Create validator with registry
        >>> registry = AssetTypeRegistry(include_builtin=True)
        >>> validator = AssetValidator(registry)
        >>>
        >>> # Validate an asset name
        >>> result = validator.validate_name("hero_character_v001", "character")
        >>> if result.valid:
        ...     print("Valid name!")
        ... else:
        ...     print(f"Errors: {result.errors}")
    """

    def __init__(
        self,
        registry: AssetTypeRegistry,
        naming_convention: NamingConvention | None = None,
    ):
        """AssetValidator constructor.

        Args:
            registry: Asset type registry for type definitions.
            naming_convention: Optional naming convention for token validation.
        """

        self._registry = registry
        self._naming_convention = naming_convention

    @property
    def registry(self) -> AssetTypeRegistry:
        """Returns the asset type registry."""
        return self._registry

    @property
    def naming_convention(self) -> NamingConvention | None:
        """Returns the naming convention."""
        return self._naming_convention

    @naming_convention.setter
    def naming_convention(self, value: NamingConvention | None):
        """Sets the naming convention."""
        self._naming_convention = value

    def validate_name(
        self,
        name: str,
        asset_type: str,
        strict: bool = False,
    ) -> ValidationResult:
        """Validate a name against asset type rules.

        Args:
            name: Asset name to validate.
            asset_type: Asset type name.
            strict: If True, all tokens must match allowed tokens.

        Returns:
            Validation result with errors, warnings, and suggestions.
        """

        result = ValidationResult()

        # Get asset type definition
        type_def = self._registry.get_type(asset_type)
        if type_def is None:
            result.add_error(f"Unknown asset type: {asset_type}")
            return result

        # Validate against naming convention if available
        if self._naming_convention and type_def.naming_rule:
            try:
                rule = self._naming_convention.rule(type_def.naming_rule)
                if rule:
                    parsed = self._naming_convention.parse_by_rule(rule, name)
                    result.parsed_tokens = parsed
                else:
                    result.add_warning(
                        f"Naming rule '{type_def.naming_rule}' not found in convention"
                    )
            except ValueError as e:
                result.add_error(f"Name does not match naming rule: {e}")
                return result

        # Check required tokens
        if type_def.required_tokens and result.parsed_tokens:
            for required in type_def.required_tokens:
                if required not in result.parsed_tokens:
                    result.add_error(f"Missing required token: {required}")

        # Check allowed tokens in strict mode
        if strict and type_def.allowed_tokens and result.parsed_tokens:
            for token in result.parsed_tokens:
                if token not in type_def.allowed_tokens:
                    result.add_error(
                        f"Token not allowed for this asset type: {token}"
                    )

        # Run custom validators
        validator_errors = type_def.run_validators(name, result.parsed_tokens)
        for error in validator_errors:
            result.add_error(error)

        return result

    def validate_path(
        self,
        path: str,
        asset_type: str,
        strict: bool = False,
    ) -> ValidationResult:
        """Validate a path against asset type rules.

        Args:
            path: File path to validate.
            asset_type: Asset type name.
            strict: If True, enforce strict validation.

        Returns:
            Validation result with errors, warnings, and suggestions.
        """

        result = ValidationResult()

        # Get asset type definition
        type_def = self._registry.get_type(asset_type)
        if type_def is None:
            result.add_error(f"Unknown asset type: {asset_type}")
            return result

        # Check file extension
        if not type_def.has_valid_extension(path):
            result.add_error(
                f"Invalid file extension. Allowed: {', '.join(type_def.file_extensions)}"
            )

        # Extract filename and validate as name
        import os

        filename = os.path.splitext(os.path.basename(path))[0]
        name_result = self.validate_name(filename, asset_type, strict=strict)
        result.merge(name_result)

        return result

    def suggest_corrections(
        self,
        invalid_name: str,
        asset_type: str,
        max_suggestions: int = 5,
    ) -> list[str]:
        """Suggest valid alternatives for an invalid name.

        Args:
            invalid_name: Invalid asset name.
            asset_type: Asset type name.
            max_suggestions: Maximum number of suggestions.

        Returns:
            List of suggested corrections.
        """

        suggestions = []

        # Get asset type definition
        type_def = self._registry.get_type(asset_type)
        if type_def is None:
            return suggestions

        # Try to parse and fix common issues

        # 1. Fix case issues
        lower_name = invalid_name.lower()
        if lower_name != invalid_name:
            suggestions.append(lower_name)

        # 2. Replace spaces with underscores
        if " " in invalid_name:
            suggestions.append(invalid_name.replace(" ", "_"))

        # 3. Remove invalid characters
        import re

        cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", invalid_name)
        if cleaned != invalid_name:
            suggestions.append(cleaned)

        # 4. Remove double underscores
        if "__" in invalid_name:
            suggestions.append(re.sub(r"_+", "_", invalid_name))

        # 5. Remove leading/trailing underscores
        stripped = invalid_name.strip("_")
        if stripped != invalid_name:
            suggestions.append(stripped)

        # Remove duplicates and limit
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s not in seen and s != invalid_name:
                seen.add(s)
                unique_suggestions.append(s)
                if len(unique_suggestions) >= max_suggestions:
                    break

        return unique_suggestions

    def detect_asset_type(self, path: str) -> str | None:
        """Attempt to detect asset type from file path.

        Args:
            path: File path to analyze.

        Returns:
            Detected asset type name or None.
        """

        import os

        ext = os.path.splitext(path)[1].lower()

        if not ext:
            return None

        # Find types that support this extension
        matching_types = self._registry.types_with_extension(ext)

        if len(matching_types) == 1:
            return matching_types[0].name

        # Try to infer from path patterns
        path_lower = path.lower()

        if "texture" in path_lower or "/t_" in path_lower:
            return "texture"
        if "character" in path_lower or "/chr" in path_lower:
            return "character"
        if "prop" in path_lower:
            return "prop"
        if "anim" in path_lower:
            return "animation"
        if "rig" in path_lower:
            return "rig"
        if "audio" in path_lower or "sfx" in path_lower:
            return "audio"
        if "material" in path_lower or "mat" in path_lower:
            return "material"

        return None

    def batch_validate(
        self,
        items: list[tuple[str, str]],
        strict: bool = False,
    ) -> dict[str, ValidationResult]:
        """Validate multiple items at once.

        Args:
            items: List of (name_or_path, asset_type) tuples.
            strict: If True, enforce strict validation.

        Returns:
            Dictionary mapping items to validation results.
        """

        results = {}

        for item, asset_type in items:
            # Detect if it's a path or name
            if "/" in item or "\\" in item or "." in item:
                results[item] = self.validate_path(
                    item, asset_type, strict=strict
                )
            else:
                results[item] = self.validate_name(
                    item, asset_type, strict=strict
                )

        return results
