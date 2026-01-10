"""Asset type definitions for validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class AssetTypeDefinition:
    """Definition of an asset type with its rules and constraints.

    This class defines the structure and validation rules for a specific
    type of asset (e.g., character, prop, texture, animation).

    Example:
        >>> character_type = AssetTypeDefinition(
        ...     name="character",
        ...     description="Character asset",
        ...     naming_rule="character_asset",
        ...     path_template="character_path",
        ...     required_tokens=["name", "type"],
        ...     allowed_tokens=["name", "type", "variant", "lod"],
        ...     file_extensions=[".fbx", ".ma", ".mb"],
        ... )
    """

    name: str
    description: str = ""
    naming_rule: str = ""
    path_template: str = ""
    required_tokens: list[str] = field(default_factory=list)
    allowed_tokens: list[str] = field(default_factory=list)
    file_extensions: list[str] = field(default_factory=list)
    validators: list[Callable[[str, dict[str, Any]], bool]] = field(
        default_factory=list
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the definition after initialization."""
        # Ensure required tokens are subset of allowed tokens
        if self.allowed_tokens:
            for token in self.required_tokens:
                if token not in self.allowed_tokens:
                    self.allowed_tokens.append(token)

        # Normalize file extensions
        self.file_extensions = [
            ext if ext.startswith(".") else f".{ext}"
            for ext in self.file_extensions
        ]

    def has_required_tokens(self, tokens: dict[str, Any]) -> bool:
        """Check if all required tokens are present.

        Args:
            tokens: Dictionary of token values.

        Returns:
            True if all required tokens are present.
        """
        return all(token in tokens for token in self.required_tokens)

    def has_valid_extension(self, path: str) -> bool:
        """Check if path has a valid file extension.

        Args:
            path: File path to check.

        Returns:
            True if extension is valid or no extensions are defined.
        """
        if not self.file_extensions:
            return True

        path_lower = path.lower()
        return any(
            path_lower.endswith(ext.lower()) for ext in self.file_extensions
        )

    def run_validators(self, name: str, tokens: dict[str, Any]) -> list[str]:
        """Run all custom validators.

        Args:
            name: Asset name to validate.
            tokens: Parsed token values.

        Returns:
            List of error messages from failed validators.
        """
        errors = []
        for validator in self.validators:
            try:
                if not validator(name, tokens):
                    errors.append(f"Validator {validator.__name__} failed")
            except Exception as e:
                errors.append(f"Validator {validator.__name__} raised: {e}")
        return errors


# =============================================================================
# Built-in asset type definitions
# =============================================================================

CHARACTER_ASSET = AssetTypeDefinition(
    name="character",
    description="Character asset (humanoid, creature, NPC)",
    required_tokens=["name"],
    allowed_tokens=["name", "type", "variant", "lod", "version"],
    file_extensions=[".fbx", ".ma", ".mb", ".blend"],
    metadata={"category": "3d_asset"},
)

PROP_ASSET = AssetTypeDefinition(
    name="prop",
    description="Prop asset (items, objects)",
    required_tokens=["name"],
    allowed_tokens=["name", "type", "variant", "lod", "version"],
    file_extensions=[".fbx", ".ma", ".mb", ".blend"],
    metadata={"category": "3d_asset"},
)

ENVIRONMENT_ASSET = AssetTypeDefinition(
    name="environment",
    description="Environment asset (levels, terrain, buildings)",
    required_tokens=["name"],
    allowed_tokens=["name", "type", "variant", "lod", "version", "zone"],
    file_extensions=[".fbx", ".ma", ".mb", ".blend", ".umap"],
    metadata={"category": "3d_asset"},
)

TEXTURE_ASSET = AssetTypeDefinition(
    name="texture",
    description="Texture asset",
    required_tokens=["name", "texture_type"],
    allowed_tokens=["name", "texture_type", "resolution", "version"],
    file_extensions=[".png", ".tga", ".exr", ".tif", ".tiff", ".psd"],
    metadata={"category": "2d_asset"},
)

MATERIAL_ASSET = AssetTypeDefinition(
    name="material",
    description="Material asset",
    required_tokens=["name"],
    allowed_tokens=["name", "type", "version"],
    file_extensions=[".mat", ".sbsar", ".sbs"],
    metadata={"category": "shader"},
)

ANIMATION_ASSET = AssetTypeDefinition(
    name="animation",
    description="Animation asset",
    required_tokens=["name", "animation_type"],
    allowed_tokens=["name", "animation_type", "character", "version"],
    file_extensions=[".fbx", ".anim", ".ma", ".mb"],
    metadata={"category": "animation"},
)

RIG_ASSET = AssetTypeDefinition(
    name="rig",
    description="Rig asset",
    required_tokens=["name"],
    allowed_tokens=["name", "type", "version"],
    file_extensions=[".ma", ".mb", ".blend"],
    metadata={"category": "rig"},
)

AUDIO_ASSET = AssetTypeDefinition(
    name="audio",
    description="Audio asset (SFX, music, dialogue)",
    required_tokens=["name"],
    allowed_tokens=["name", "type", "version"],
    file_extensions=[".wav", ".mp3", ".ogg", ".flac"],
    metadata={"category": "audio"},
)


# Dictionary of all built-in asset types
BUILTIN_ASSET_TYPES: dict[str, AssetTypeDefinition] = {
    "character": CHARACTER_ASSET,
    "prop": PROP_ASSET,
    "environment": ENVIRONMENT_ASSET,
    "texture": TEXTURE_ASSET,
    "material": MATERIAL_ASSET,
    "animation": ANIMATION_ASSET,
    "rig": RIG_ASSET,
    "audio": AUDIO_ASSET,
}
