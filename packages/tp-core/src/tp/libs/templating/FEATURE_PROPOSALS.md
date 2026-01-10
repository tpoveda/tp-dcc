# Feature Proposals: `tp.libs.templating` for AAA Game Production

## Overview

This document proposes additional features to make `tp.libs.templating` a comprehensive, production-ready templating system for AAA game development pipelines.

---

## 1. Version Management

### Problem
AAA productions need robust versioning for assets, scenes, and deliverables with automatic incrementing, version comparison, and history tracking.

### Proposed Features

```python
# Version token with auto-increment
class VersionToken(Token):
    """Special token for version management."""
    
    def next_version(self, current: str) -> str:
        """Get next version string."""
    
    def parse_version(self, version_str: str) -> tuple[int, int, int]:
        """Parse 'v001', 'v1.2.3', etc."""
    
    def compare(self, v1: str, v2: str) -> int:
        """Compare two version strings."""

# Version resolver
class VersionResolver:
    """Resolve versions from filesystem or database."""
    
    def latest_version(self, path_pattern: str, **tokens) -> str:
        """Find latest version matching pattern."""
    
    def next_available_version(self, path_pattern: str, **tokens) -> str:
        """Get next available version number."""
    
    def all_versions(self, path_pattern: str, **tokens) -> list[str]:
        """List all existing versions."""
```

### Use Cases
- Auto-increment asset versions on publish
- Find latest approved version of a rig
- Compare asset versions for review
- Version rollback support

---

## 2. Platform/Target Awareness

### Problem
AAA games target multiple platforms (PC, PS5, Xbox, Switch, Mobile) with different naming conventions, path structures, and asset requirements.

### Proposed Features

```python
class PlatformContext:
    """Context for platform-specific resolution."""
    
    platforms = ["pc", "ps5", "xbox_series", "switch", "ios", "android"]
    
    def __init__(self, platform: str, config: str | None = None):
        self.platform = platform
        self.path_separator = self._get_separator()
        self.case_sensitivity = self._get_case_sensitivity()
        self.max_path_length = self._get_max_path()

# Platform-aware path resolution
resolver.resolve_path(
    "asset_texture",
    platform="ps5",
    asset="hero_character",
    texture_type="diffuse",
)
# Returns: "/content/ps5/characters/hero_character/T_hero_character_D.png"

# Platform token remapping
# pc: "normal" -> "N"
# switch: "normal" -> "Nrm"  (different convention for memory reasons)
```

### Use Cases
- Generate platform-specific asset paths
- Apply platform naming conventions (Switch has stricter limits)
- Handle case-sensitivity differences (Linux builds vs Windows)

---

## 3. Asset Type Classification & Validation

### Problem
Different asset types (characters, props, environments, VFX, audio) have different naming rules and path structures.

### Proposed Features

```python
class AssetTypeRegistry:
    """Registry for asset type definitions."""
    
    def register_type(
        self,
        name: str,
        naming_rule: str,
        path_template: str,
        allowed_tokens: list[str],
        validators: list[Callable],
    ):
        """Register an asset type with its rules."""

class AssetValidator:
    """Validate asset names and paths against rules."""
    
    def validate_name(self, name: str, asset_type: str) -> ValidationResult:
        """Validate a name against asset type rules."""
    
    def validate_path(self, path: str, asset_type: str) -> ValidationResult:
        """Validate a path against asset type rules."""
    
    def suggest_corrections(self, invalid_name: str) -> list[str]:
        """Suggest valid alternatives for invalid names."""

@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    warnings: list[str]
    suggestions: list[str]
```

### Use Cases
- Enforce naming conventions at publish time
- Provide helpful error messages for invalid names
- Auto-suggest corrections for common mistakes
- Different rules for cinematic vs gameplay assets

---

## 4. Hierarchy & Relationship Templates

### Problem
Game assets have complex hierarchies (characters have skeleton, mesh, materials, textures, animations). Need to define and resolve entire hierarchies at once.

### Proposed Features

```python
class AssetHierarchyTemplate:
    """Template for complete asset hierarchies."""
    
    def __init__(self, name: str):
        self.name = name
        self.children: dict[str, AssetHierarchyTemplate] = {}
        self.path_template: str | None = None
    
    def add_child(self, role: str, template: AssetHierarchyTemplate):
        """Add a child template with a role."""

# Define a character asset structure
character_template = AssetHierarchyTemplate("character")
character_template.add_child("skeleton", skeleton_template)
character_template.add_child("mesh", mesh_template)
character_template.add_child("materials", materials_template)
character_template.add_child("textures", textures_template)
character_template.add_child("animations", animations_folder_template)

# Resolve entire hierarchy
paths = resolver.resolve_hierarchy(
    character_template,
    character="hero_soldier",
    variant="default",
)
# Returns dict with all paths for the character's components
```

### Use Cases
- Create complete folder structures for new assets
- Validate asset completeness (all required files present)
- Bulk operations on related assets
- Asset dependency tracking

---

## 5. Context Inheritance & Overrides

### Problem
Projects have global conventions, but specific areas (cinematics, multiplayer, DLC) may need overrides.

### Proposed Features

```python
class TemplateContext:
    """Hierarchical context for template resolution."""
    
    def __init__(self, name: str, parent: TemplateContext | None = None):
        self.name = name
        self.parent = parent
        self._tokens: dict[str, Token] = {}
        self._rules: dict[str, Rule] = {}
        self._templates: dict[str, Template] = {}
    
    def with_override(self, **overrides) -> TemplateContext:
        """Create child context with overrides."""
    
    def resolve(self, key: str) -> Any:
        """Resolve with inheritance chain."""

# Example usage
global_context = TemplateContext("global")
global_context.set_token("project", "MyGame")

dlc_context = global_context.with_override(
    project_suffix="_DLC1",
    content_root="/dlc1/content",
)

cinematic_context = global_context.with_override(
    quality_suffix="_CIN",
    resolution="4k",
)
```

### Use Cases
- DLC with different paths but same conventions
- Cinematic assets with higher quality suffixes
- Per-level or per-sequence overrides
- Team-specific workspace paths

---

## 6. Pattern Matching & Discovery

### Problem
Need to find assets matching patterns, discover what exists on disk, and batch process files.

### Proposed Features

```python
class TemplateDiscovery:
    """Discover files matching templates."""
    
    def find_matching(
        self,
        template_name: str,
        root_path: str,
        **partial_tokens,
    ) -> list[DiscoveredAsset]:
        """Find all files matching template with optional filters."""
    
    def glob_from_template(
        self,
        template_name: str,
        **tokens,
    ) -> str:
        """Generate glob pattern from template."""

@dataclass
class DiscoveredAsset:
    path: str
    parsed_tokens: dict[str, str]
    metadata: dict[str, Any]

# Example: Find all hero character textures
textures = discovery.find_matching(
    "character_texture",
    root_path="/content",
    character="hero_*",  # Wildcard support
    texture_type="diffuse",
)
```

### Use Cases
- Asset browser/picker tools
- Batch rename/migrate operations
- Find all assets of a type
- Audit naming compliance across project

---

## 7. Serialization & Configuration Formats

### Problem
Need to store, share, and version control naming configurations across teams and projects.

### Proposed Features

```python
class TemplateConfiguration:
    """Complete serializable configuration."""
    
    @classmethod
    def from_yaml(cls, path: str) -> TemplateConfiguration:
        """Load from YAML file."""
    
    @classmethod
    def from_json(cls, path: str) -> TemplateConfiguration:
        """Load from JSON file."""
    
    def to_yaml(self, path: str):
        """Save to YAML file."""
    
    def merge_with(self, other: TemplateConfiguration) -> TemplateConfiguration:
        """Merge two configurations (for layered configs)."""
    
    def validate(self) -> list[str]:
        """Validate configuration integrity."""
```

### YAML Configuration Example
```yaml
# project_naming.yaml
version: "1.0"
name: "MyGame Naming Convention"

tokens:
  side:
    description: "Body side indicator"
    required: true
    values:
      left: "L"
      right: "R"
      center: "C"
      
  asset_type:
    description: "Type of asset"
    required: true
    pattern: "[a-z]+"  # Regex validation
    
  version:
    type: "version"  # Special version token
    format: "v{:03d}"
    
rules:
  character_name:
    expression: "{asset_type}_{character}_{variant}"
    example:
      asset_type: "CH"
      character: "hero"
      variant: "default"

path_templates:
  character_root:
    pattern: "/content/characters/{character}"
    
  character_texture:
    pattern: "{@character_root}/textures/T_{character}_{texture_type}.png"
    references:
      - character_root

asset_types:
  character:
    naming_rule: "character_name"
    path_template: "character_root"
    required_files:
      - role: "skeleton"
        template: "character_skeleton"
      - role: "mesh"
        template: "character_mesh"
```

---

## 8. Event Hooks & Callbacks

### Problem
Need to trigger actions when assets are named, paths are resolved, or validation occurs.

### Proposed Features

```python
class TemplateEventSystem:
    """Event system for template operations."""
    
    events = [
        "pre_resolve",
        "post_resolve", 
        "validation_failed",
        "validation_passed",
        "version_incremented",
        "asset_discovered",
    ]
    
    def on(self, event: str, callback: Callable):
        """Register event callback."""
    
    def emit(self, event: str, **data):
        """Emit event with data."""

# Example: Log all path resolutions
template_system.on("post_resolve", lambda data: 
    logger.info(f"Resolved: {data['template']} -> {data['result']}")
)

# Example: Notify on validation failures
template_system.on("validation_failed", lambda data:
    slack_notify(f"Invalid name: {data['name']}, errors: {data['errors']}")
)
```

### Use Cases
- Logging and auditing
- Integration with external systems (Perforce, Shotgrid, etc.)
- Custom validation hooks
- UI notifications

---

## 9. Caching & Performance

### Problem
Large projects have thousands of assets. Resolution and discovery need to be fast.

### Proposed Features

```python
class TemplateCache:
    """Caching layer for template operations."""
    
    def __init__(self, backend: CacheBackend = MemoryCache()):
        self.backend = backend
    
    def cache_resolution(self, template: str, tokens: dict, result: str):
        """Cache a resolution result."""
    
    def get_cached(self, template: str, tokens: dict) -> str | None:
        """Get cached result if available."""
    
    def invalidate(self, pattern: str | None = None):
        """Invalidate cache entries."""

class CacheBackend(Protocol):
    """Cache backend protocol."""
    
    def get(self, key: str) -> Any: ...
    def set(self, key: str, value: Any, ttl: int | None = None): ...
    def delete(self, key: str): ...

# Implementations
class MemoryCache(CacheBackend): ...
class RedisCache(CacheBackend): ...
class FileCache(CacheBackend): ...
```

### Use Cases
- Fast asset browser responsiveness
- Reduce filesystem access for discovery
- Distributed caching for farm/cloud builds

---

## 10. Migration & Refactoring Tools

### Problem
Naming conventions evolve. Need to migrate existing assets to new conventions without breaking references.

### Proposed Features

```python
class NamingMigration:
    """Tools for migrating between naming conventions."""
    
    def __init__(
        self,
        source_convention: NamingConvention,
        target_convention: NamingConvention,
    ):
        self.source = source_convention
        self.target = target_convention
    
    def plan_migration(self, paths: list[str]) -> MigrationPlan:
        """Create a migration plan (dry run)."""
    
    def execute_migration(
        self,
        plan: MigrationPlan,
        on_conflict: str = "skip",  # "skip", "overwrite", "rename"
    ) -> MigrationResult:
        """Execute a migration plan."""
    
    def generate_redirect_map(self, plan: MigrationPlan) -> dict[str, str]:
        """Generate old->new path mapping for redirectors."""

@dataclass
class MigrationPlan:
    renames: list[tuple[str, str]]  # (old_path, new_path)
    conflicts: list[str]
    unchanged: list[str]
    warnings: list[str]
```

### Use Cases
- Rename assets when conventions change
- Generate Unreal redirectors
- Audit impact before executing
- Reversible migrations

---

## 11. DCC Integration Helpers

### Problem
Different DCCs (Maya, Houdini, Unreal, Blender) have different path handling and naming constraints.

### Proposed Features

```python
class DCCAdapter(Protocol):
    """Adapter for DCC-specific behavior."""
    
    def normalize_path(self, path: str) -> str:
        """Normalize path for DCC."""
    
    def validate_name(self, name: str) -> bool:
        """Check if name is valid in DCC."""
    
    def get_illegal_characters(self) -> str:
        """Get characters not allowed in names."""
    
    def max_name_length(self) -> int:
        """Maximum name length in DCC."""

class MayaAdapter(DCCAdapter):
    def get_illegal_characters(self) -> str:
        return "|:*?\"<>"
    
    def max_name_length(self) -> int:
        return 256  # Maya node name limit

class UnrealAdapter(DCCAdapter):
    def normalize_path(self, path: str) -> str:
        # Convert filesystem path to /Game/ path
        ...
```

### Use Cases
- Validate names before creating nodes
- Sanitize names for specific DCCs
- Path conversion between DCC and filesystem

---

## 12. Localization Support

### Problem
AAA games are localized. Assets may have language-specific variants.

### Proposed Features

```python
class LocalizationToken(Token):
    """Token for language/locale handling."""
    
    locales = ["en", "ja", "de", "fr", "es", "pt-br", "zh-cn", "ko"]
    
    def __init__(self):
        super().__init__(
            name="locale",
            values={loc: loc.upper() for loc in self.locales},
        )

# Locale-aware resolution
resolver.resolve_path(
    "dialogue_audio",
    character="npc_merchant",
    line_id="greeting_01",
    locale="ja",
)
# Returns: "/content/audio/dialogue/ja/npc_merchant/VO_npc_merchant_greeting_01_JA.wav"
```

### Use Cases
- Localized audio files
- Language-specific textures (signs, UI)
- Region-specific content

---

## Priority Ranking for Implementation

| Priority | Feature | Complexity | Value |
|----------|---------|------------|-------|
| **P0** | Version Management | Medium | Critical |
| **P0** | Asset Type Classification & Validation | Medium | Critical |
| **P1** | Pattern Matching & Discovery | Medium | High |
| **P1** | Serialization & Configuration | Low | High |
| **P1** | Context Inheritance & Overrides | Medium | High |
| **P2** | Platform/Target Awareness | Medium | Medium |
| **P2** | Hierarchy & Relationship Templates | High | Medium |
| **P2** | DCC Integration Helpers | Low | Medium |
| **P3** | Event Hooks & Callbacks | Low | Medium |
| **P3** | Caching & Performance | Medium | Medium |
| **P3** | Migration & Refactoring Tools | High | Medium |
| **P3** | Localization Support | Low | Low |

---

## Recommended Phase 1 Additions

For the initial `templating` library release, I recommend adding these features alongside the core migration:

1. **Version Management** - Essential for any pipeline
2. **Asset Type Classification & Validation** - Prevents naming errors at source
3. **Enhanced Configuration (YAML)** - Already partially exists, formalize it
4. **Pattern Discovery** - Enables asset browsing tools

These four features would make `tp.libs.templating` immediately useful for production while keeping scope manageable.

