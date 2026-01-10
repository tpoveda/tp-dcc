# TP Templating Library

A comprehensive templating system for AAA game and VFX production pipelines. Provides unified name templating, path resolution, version management, asset validation, discovery, and configuration.

## Overview

The templating library (`tp.libs.templating`) provides a robust system for managing naming conventions, file paths, versions, and asset validation across your project. It supports:

- **Name Templating**: Token-based naming conventions with rules and inheritance
- **Path Templating**: Path pattern resolution with template references
- **Version Management**: Auto-increment, parsing, comparison, and filesystem discovery
- **Asset Validation**: Asset type classification and validation with built-in types
- **Pattern Discovery**: Find files matching templates across the filesystem
- **Configuration**: Unified configuration loading with schema validation and merging
- **Context Inheritance**: Hierarchical contexts (project → shot → asset)

## Installation

The templating library is part of the `tp-core` package. Ensure `tp-core` is in your Python path.

```python
from tp.libs.templating import api
```

## Quick Start

### Name Templating

```python
from tp.libs.templating import api

# Get the global naming convention
nc = api.naming_convention(name="global")

# Solve a name using tokens
name = api.solve(
    naming_convention=nc,
    description="arm",
    side="left",
    type="joint"
)
# Result: "arm_L_jnt"

# Parse a name back into tokens
parsed = api.parse("arm_L_jnt", naming_convention=nc)
# Result: {"description": "arm", "side": "left", "type": "joint"}
```

### Path Templating

```python
from tp.libs.templating import Template, PathResolver

# Create a path template
template = Template(
    name="asset_texture",
    pattern="/content/{asset_type}/{asset_name}/textures/T_{asset_name}_{texture_type}.png"
)

# Format a path from data
path = template.format({
    "asset_type": "characters",
    "asset_name": "hero",
    "texture_type": "diffuse"
})
# Result: "/content/characters/hero/textures/T_hero_diffuse.png"

# Parse a path to extract data
parsed = template.parse("/content/props/chair/textures/T_chair_normal.png")
# Result: {"asset_type": "props", "asset_name": "chair", "texture_type": "normal"}
```

### Version Management

```python
from tp.libs.templating import VersionToken

# Create a version token
token = VersionToken(prefix="v", format_str="{:03d}")

# Format versions
print(token.format_version(1))   # "v001"
print(token.format_version(42))  # "v042"

# Get next version
print(token.next_version("v001"))  # "v002"
print(token.next_version(None))    # "v001" (first version)

# Compare versions
print(token.compare("v001", "v002"))  # -1 (v001 < v002)

# Sort versions
versions = ["v003", "v001", "v010", "v002"]
sorted_versions = token.sort_versions(versions)
# Result: ["v001", "v002", "v003", "v010"]
```

### Asset Validation

```python
from tp.libs.templating import AssetTypeRegistry, AssetValidator

# Create registry with built-in types
registry = AssetTypeRegistry(include_builtin=True)

# Create validator
validator = AssetValidator(registry)

# Validate a file path
result = validator.validate_path("/content/characters/hero.fbx", "character")
if result.valid:
    print("Valid asset!")
else:
    print(f"Errors: {result.errors}")
    print(f"Suggestions: {result.suggestions}")

# Auto-detect asset type from path
detected = validator.detect_asset_type("/content/textures/T_hero_D.png")
print(detected)  # "texture"
```

---

## Name Templating

### Rules

Rules define the structure of a name using an expression with token placeholders:

```python
from tp.libs.templating import NamingConvention

nc = NamingConvention()

# Add a rule with expression and example values
nc.add_rule(
    name="rig_node",
    expression="{description}_{side}_{type}_{index}",
    example_fields={
        "description": "arm",
        "side": "left",
        "type": "joint",
        "index": "01"
    }
)
```

### Tokens

Tokens are the building blocks of naming rules. They can have:
- A lookup table mapping keys to values
- A default value
- A description
- Zero-padding for numeric values (using `padding` parameter)

```python
# Add a simple token (accepts any value)
nc.add_token("description")

# Add a token with value mappings
nc.add_token(
    "side",
    left="L",
    right="R",
    center="C",
    default="C"
)

# Add a token with multiple mappings
nc.add_token(
    "type",
    joint="jnt",
    control="ctrl",
    locator="loc",
    transform="srt",
    default="ctrl"
)

# Add an index token with zero-padding (3 digits)
nc.add_token("index", padding=3)
# This will format: 1 -> "001", 42 -> "042", 123 -> "123"
```

### Index Tokens with Padding

For index or counter tokens, you can specify zero-padding to ensure consistent digit counts:

```python
from tp.libs.templating import NamingConvention

nc = NamingConvention()

# Add tokens including a padded index
nc.add_token("description")
nc.add_token("side", left="L", right="R", center="C")
nc.add_token("type", joint="jnt", control="ctrl")
nc.add_token("index", padding=2)  # Pad to 2 digits

# Add rule using the index
nc.add_rule(
    "rig_node",
    "{description}_{side}_{type}_{index}",
    {"description": "arm", "side": "left", "type": "joint", "index": "01"}
)

# Solve with different index values
name1 = nc.solve(
    rule_name="rig_node",
    description="arm",
    side="left",
    type="joint",
    index="1"  # Will be padded to "01"
)
# Result: "arm_L_jnt_01"

name2 = nc.solve(
    rule_name="rig_node",
    description="arm",
    side="left",
    type="joint",
    index="12"  # Already 2 digits, no padding needed
)
# Result: "arm_L_jnt_12"

# Values exceeding the padding width are NOT truncated
name3 = nc.solve(
    rule_name="rig_node",
    description="arm",
    side="left",
    type="joint",
    index="123"  # 3 digits, kept as-is
)
# Result: "arm_L_jnt_123"
```

### Solving Names

Use `solve()` to generate names from token values:

```python
# Explicit token values
name = nc.solve(
    description="spine",
    side="center",
    type="joint",
    index="02"
)
# Result: "spine_C_jnt_02"

# Using defaults (side defaults to "C", type defaults to "ctrl")
name = nc.solve(description="hand", index="01")
# Result: "hand_C_ctrl_01"

# Using a specific rule
name = nc.solve(
    rule_name="rig_node",
    description="finger",
    side="left",
    type="joint",
    index="03"
)
```

### Parsing Names

Use `parse()` to extract token values from a name:

```python
parsed = nc.parse("arm_L_jnt_01")
# Result: {
#     "description": "arm",
#     "side": "left",
#     "type": "joint",
#     "index": "01"
# }
```

### Naming Convention Inheritance

Naming conventions can inherit from parent conventions:

```python
from tp.libs.templating import NamingConvention

# Create a base convention with common tokens
base = NamingConvention(naming_data={"name": "base"})
base.add_token("side", left="L", right="R", center="C", default="C")
base.add_token("index", default="01")

# Create a child convention that inherits from base
rigging = NamingConvention(
    naming_data={"name": "rigging"},
    parent=base
)
rigging.add_token("type", joint="jnt", control="ctrl")
rigging.add_rule(
    "rig_node",
    "{type}_{side}_{index}",
    {"type": "joint", "side": "left", "index": "01"}
)

# Child has access to parent's tokens
name = rigging.solve(type="joint", side="left", index="02")
# Result: "jnt_L_02"
```

---

## Path Templating

### Basic Path Templates

```python
from tp.libs.templating import Template

# Create a template
template = Template(
    name="asset_file",
    pattern="/content/{asset_type}/{asset_name}/v{version}/{asset_name}_v{version}.fbx"
)

# Get placeholder keys
print(template.keys())  # {'asset_type', 'asset_name', 'version'}

# Format a path
path = template.format({
    "asset_type": "characters",
    "asset_name": "hero",
    "version": "001"
})
# Result: "/content/characters/hero/v001/hero_v001.fbx"

# Parse a path
parsed = template.parse("/content/props/chair/v002/chair_v002.fbx")
# Result: {"asset_type": "props", "asset_name": "chair", "version": "002"}
```

### Path Resolver with Template References

Templates can reference other templates using `{@template_name}` syntax:

```python
from tp.libs.templating import Template, PathResolver

# Create a resolver
resolver = PathResolver()

# Register base templates
resolver.register_template(Template(
    name="project_root",
    pattern="/projects/{project}"
))

resolver.register_template(Template(
    name="asset_root",
    pattern="{@project_root}/assets/{asset_type}",
    template_resolver=resolver
))

resolver.register_template(Template(
    name="asset_texture",
    pattern="{@asset_root}/{asset_name}/textures/T_{asset_name}_{texture_type}.png",
    template_resolver=resolver
))

# Resolve a path (references are expanded automatically)
path = resolver.resolve_path(
    "asset_texture",
    project="MyGame",
    asset_type="characters",
    asset_name="hero",
    texture_type="diffuse"
)
# Result: "/projects/MyGame/assets/characters/hero/textures/T_hero_diffuse.png"
```

### Linking Path Resolver to Naming Convention

```python
from tp.libs.templating import NamingConvention, PathResolver, Template

# Create naming convention with token mappings
nc = NamingConvention()
nc.add_token("asset_type", character="CHR", prop="PRP", environment="ENV")

# Create path resolver linked to naming convention
resolver = PathResolver(naming_convention=nc)
resolver.register_template(Template(
    name="asset_path",
    pattern="/content/{asset_type}/{asset_name}"
))

# Resolve path with token resolution
path = resolver.resolve_path(
    "asset_path",
    asset_type="character",  # Will be resolved to "CHR"
    asset_name="hero"
)
# Result: "/content/CHR/hero"
```

---

## Version Management

### VersionToken

The `VersionToken` class handles version string parsing, formatting, and incrementing:

```python
from tp.libs.templating import VersionToken

# Simple numeric versioning (001, 002, 003)
simple = VersionToken(format_str="{:03d}")
print(simple.format_version(1))   # "001"
print(simple.format_version(42))  # "042"

# Prefixed versioning (v001, v002, v003)
prefixed = VersionToken(prefix="v", format_str="{:03d}")
print(prefixed.format_version(1))  # "v001"
print(prefixed.next_version("v001"))  # "v002"

# Semantic versioning (1.0.0, 1.2.3)
semantic = VersionToken(semantic=True)
print(semantic.format_version((1, 0, 0)))  # "1.0.0"
print(semantic.format_version((1, 2, 3)))  # "1.2.3"

# Increment semantic versions
print(semantic.next_version("1.0.0", increment="patch"))  # "1.0.1"
print(semantic.next_version("1.0.0", increment="minor"))  # "1.1.0"
print(semantic.next_version("1.0.0", increment="major"))  # "2.0.0"
```

### Parsing and Comparing Versions

```python
token = VersionToken(prefix="v")

# Parse version strings
print(token.parse_version("v001"))  # 1
print(token.parse_version("v042"))  # 42

# Compare versions
print(token.compare("v001", "v002"))  # -1 (less than)
print(token.compare("v002", "v001"))  # 1  (greater than)
print(token.compare("v001", "v001"))  # 0  (equal)

# Validate versions
print(token.is_valid_version("v001"))    # True
print(token.is_valid_version("invalid")) # False

# Sort versions
versions = ["v003", "v001", "v010", "v002"]
sorted_versions = token.sort_versions(versions)
# Result: ["v001", "v002", "v003", "v010"]
```

### VersionResolver - Filesystem Version Discovery

```python
from tp.libs.templating import PathResolver, Template, VersionResolver, VersionToken

# Set up path resolver with versioned template
resolver = PathResolver()
resolver.register_template(Template(
    name="asset_version",
    pattern="/content/assets/{asset_name}/v{version}/{asset_name}_v{version}.fbx"
))

# Create version resolver
version_token = VersionToken(format_str="{:03d}")
version_resolver = VersionResolver(resolver, version_token)

# Find all versions of an asset
versions = version_resolver.all_versions(
    "asset_version",
    root_path="/content/assets",
    asset_name="hero"
)
print(versions)  # ['001', '002', '003']

# Get latest version
latest = version_resolver.latest_version(
    "asset_version",
    root_path="/content/assets",
    asset_name="hero"
)
print(latest)  # '003'

# Get next available version
next_ver = version_resolver.next_available_version(
    "asset_version",
    root_path="/content/assets",
    asset_name="hero"
)
print(next_ver)  # '004'

# Check if version exists
exists = version_resolver.version_exists(
    "asset_version",
    root_path="/content/assets",
    version="002",
    asset_name="hero"
)
print(exists)  # True

# Resolve full path to latest version
path = version_resolver.resolve_latest(
    "asset_version",
    root_path="/content/assets",
    asset_name="hero"
)
print(path)  # '/content/assets/hero/v003/hero_v003.fbx'
```

---

## Asset Validation

### Asset Type Definitions

The library includes built-in asset types for common game production assets:

```python
from tp.libs.templating import (
    AssetTypeRegistry,
    AssetTypeDefinition,
    BUILTIN_ASSET_TYPES
)

# List built-in types
print(BUILTIN_ASSET_TYPES.keys())
# {'character', 'prop', 'environment', 'texture', 'material', 'animation', 'rig', 'audio'}

# Create a registry with built-in types
registry = AssetTypeRegistry(include_builtin=True)

# Get a type definition
character = registry.get_type("character")
print(character.description)      # "Character asset (humanoid, creature, NPC)"
print(character.file_extensions)  # ['.fbx', '.ma', '.mb', '.blend']
print(character.required_tokens)  # ['name']
```

### Custom Asset Types

```python
from tp.libs.templating import AssetTypeDefinition, AssetTypeRegistry

# Create custom asset type
vehicle_type = AssetTypeDefinition(
    name="vehicle",
    description="Vehicle asset (cars, planes, ships)",
    required_tokens=["name", "type"],
    allowed_tokens=["name", "type", "variant", "lod"],
    file_extensions=[".fbx", ".blend"],
    metadata={"category": "3d_asset"}
)

# Register custom type
registry = AssetTypeRegistry(include_builtin=True)
registry.register_type(vehicle_type)

# Query types
types_3d = registry.types_by_category("3d_asset")
types_fbx = registry.types_with_extension(".fbx")
```

### Asset Validation

```python
from tp.libs.templating import AssetTypeRegistry, AssetValidator

registry = AssetTypeRegistry(include_builtin=True)
validator = AssetValidator(registry)

# Validate a file path
result = validator.validate_path(
    "/content/characters/hero.fbx",
    "character"
)

if result.valid:
    print("Valid asset!")
    print(f"Parsed tokens: {result.parsed_tokens}")
else:
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
    print(f"Suggestions: {result.suggestions}")

# Validate a name
result = validator.validate_name("hero_character_v001", "character")

# Auto-detect asset type
detected = validator.detect_asset_type("/content/textures/T_hero_D.png")
print(detected)  # "texture"

# Get correction suggestions
suggestions = validator.suggest_corrections("Hero Character", "character")
print(suggestions)  # ['hero_character', 'hero character' -> 'hero_character']

# Batch validation
items = [
    ("hero", "character"),
    ("/content/texture.png", "texture"),
    ("invalid name!", "prop"),
]
results = validator.batch_validate(items)
for item, result in results.items():
    print(f"{item}: {'Valid' if result.valid else 'Invalid'}")
```

---

## Pattern Discovery

### Finding Files Matching Templates

```python
from tp.libs.templating import PathResolver, Template, TemplateDiscovery

# Set up resolver with templates
resolver = PathResolver()
resolver.register_template(Template(
    name="character_model",
    pattern="/content/characters/{name}/v{version}/{name}_v{version}.fbx"
))

# Create discovery
discovery = TemplateDiscovery(resolver)

# Find all matching files
assets = discovery.find_matching("character_model", "/content")
for asset in assets:
    print(f"Found: {asset.path}")
    print(f"  Name: {asset.parsed_tokens['name']}")
    print(f"  Version: {asset.version}")

# Find with filters
character_assets = discovery.find_matching(
    "character_model",
    "/content",
    name="hero"  # Only find "hero" character
)

# Find with extension filter
fbx_only = discovery.find_matching(
    "character_model",
    "/content",
    file_extensions=[".fbx"]
)
```

### Finding Latest Versions

```python
from tp.libs.templating import VersionToken

# Find latest version of each unique asset
version_token = VersionToken()
latest_assets = discovery.find_latest_versions(
    "character_model",
    "/content",
    version_token=version_token
)

for asset in latest_assets:
    print(f"{asset.parsed_tokens['name']}: v{asset.version}")
```

### Grouping Discovered Assets

```python
# Find all assets
all_assets = discovery.find_matching("character_model", "/content")

# Group by a token
groups = discovery.group_by_token(all_assets, "name")
for name, assets in groups.items():
    print(f"{name}: {len(assets)} versions")
```

### Memory-Efficient Iteration

```python
# For large directories, use the iterator version
for asset in discovery.find_matching_iter("character_model", "/content"):
    # Process one at a time without loading all into memory
    process_asset(asset)

# Count matching files without loading all
count = discovery.count_matching("character_model", "/content")
print(f"Found {count} matching files")
```

---

## Configuration

### TemplateConfiguration

The `TemplateConfiguration` class provides unified configuration for the entire templating system:

```python
from tp.libs.templating.config import TemplateConfiguration

# Create configuration
config = TemplateConfiguration()

# Add tokens
config.add_token("side", default="C", left="L", right="R", center="C")
config.add_token("type", joint="jnt", control="ctrl")

# Add rules
config.add_rule("asset", "{side}_{name}_{type}", description="Asset naming")

# Add path templates
config.add_path_template("asset_path", "/content/{type}/{name}")

# Add asset types
config.add_asset_type(
    "character",
    description="Character asset",
    file_extensions=[".fbx", ".ma"]
)

# Build components from configuration
naming_convention = config.build_naming_convention()
path_resolver = config.build_path_resolver()
asset_registry = config.build_asset_registry()
```

### Loading and Saving Configuration

```python
# Save to JSON
config.to_json("/path/to/config.json")

# Load from JSON
config = TemplateConfiguration.from_json("/path/to/config.json")

# Save to YAML (requires tp.libs.python.yamlio)
config.to_yaml("/path/to/config.yaml")

# Load from YAML
config = TemplateConfiguration.from_yaml("/path/to/config.yaml")

# Create from dictionary
config = TemplateConfiguration.from_dict({
    "name": "my_config",
    "tokens": {
        "side": {"default": "C", "keyValues": {"left": "L", "right": "R"}}
    }
})
```

### Configuration Merging

```python
from tp.libs.templating.config import ConfigurationMerger, deep_merge

# Deep merge dictionaries
base = {"a": 1, "b": {"c": 2}}
override = {"b": {"d": 3}}
result = deep_merge(base, override)
# Result: {"a": 1, "b": {"c": 2, "d": 3}}

# Use ConfigurationMerger for layered configs
merger = ConfigurationMerger()
merger.add_layer(base_config, "base")
merger.add_layer(project_config, "project")
merger.add_layer(user_config, "user")

# Get merged configuration
merged = merger.merge()

# Get specific values with dot notation
value = merger.get_value("tokens.side.default", default="C")
```

### Merging Configurations

```python
# Merge two configurations
base_config = TemplateConfiguration()
base_config.add_token("side", left="L", right="R")

project_config = TemplateConfiguration()
project_config.add_token("type", joint="jnt", control="ctrl")

merged = base_config.merge_with(project_config)
# merged now has both "side" and "type" tokens
```

### Validation

```python
# Validate configuration integrity
errors = config.validate()
if errors:
    for error in errors:
        print(f"Error: {error}")
```

---

## Context Inheritance

### Hierarchical Contexts

The `TemplateContext` class provides hierarchical value inheritance:

```python
from tp.libs.templating import TemplateContext

# Create project-level context
project_ctx = TemplateContext(name="project")
project_ctx.set("project", "MyGame")
project_ctx.set("root", "/content")
project_ctx.set("studio", "MyStudio")

# Create shot-level context that inherits from project
shot_ctx = project_ctx.with_override(
    name="shot_010",
    shot="010",
    episode="ep01"
)

# Values inherit from parent
print(shot_ctx.get("project"))  # "MyGame" (inherited)
print(shot_ctx.get("shot"))     # "010" (local)
print(shot_ctx.get("root"))     # "/content" (inherited)

# Create asset-level context
asset_ctx = shot_ctx.with_override(
    name="hero_asset",
    asset="hero",
    version="001"
)

# All values accessible through hierarchy
print(asset_ctx.get("project"))  # "MyGame"
print(asset_ctx.get("shot"))     # "010"
print(asset_ctx.get("asset"))    # "hero"

# Get all values as dictionary
all_values = asset_ctx.to_dict()
# {'project': 'MyGame', 'root': '/content', 'studio': 'MyStudio',
#  'shot': '010', 'episode': 'ep01', 'asset': 'hero', 'version': '001'}
```

### Context with Templating Components

```python
from tp.libs.templating import TemplateContext
from tp.libs.templating.config import TemplateConfiguration

# Create configuration
config = TemplateConfiguration()
config.add_token("side", left="L", right="R")
config.add_rule("asset", "{side}_{name}")
config.add_path_template("asset_path", "/content/{project}/{asset}")

# Create context with configuration
ctx = TemplateContext(name="project", configuration=config)
ctx.set("project", "MyGame")

# Resolve names using context
name = ctx.resolve_name("asset", side="left", name="arm")
# Result: "L_arm"

# Resolve paths using context
path = ctx.resolve_path("asset_path", asset="hero")
# Result: "/content/MyGame/hero"
```

### Context Stack

For simpler temporary context management:

```python
from tp.libs.templating import ContextStack

stack = ContextStack()

# Push contexts
stack.push(project="MyGame")
stack.push(shot="010")
stack.push(asset="hero")

# Values inherit through stack
print(stack.get("project"))  # "MyGame"
print(stack.get("shot"))     # "010"
print(stack.get("asset"))    # "hero"

# Pop to remove contexts
stack.pop()  # Remove asset level
print(stack.get("asset"))    # None
print(stack.get("shot"))     # "010" (still there)

# Clear back to root
stack.clear_to_root()
```

---

## Presets (Naming Conventions)

### Preset Structure

A preset file (`.preset`) defines which naming conventions to use:

```yaml
name: my_project
namingConventions:
  - name: default-global
    type: global
  - name: project-characters
    type: characters
  - name: project-rigging
    type: rigging
```

### Naming Convention Files

Convention files (`.yaml`) define rules and tokens:

```yaml
name: project-characters
description: Character asset naming conventions

rules:
  - name: character_asset
    creator: artist_name
    description: Standard character asset naming
    expression: "CHR_{character_name}_{variant}"
    exampleFields:
      character_name: Hero
      variant: A

tokens:
  - name: character_name
    description: Name of the character

  - name: variant
    description: Asset variant
    default: A
```

### Loading Presets

```python
from tp.libs.templating import api

# Get the preset manager
pm = api.naming_preset_manager()

# Find a specific preset
my_preset = pm.find_preset("my_project")

# Get naming conventions by type
rigging_conventions = pm.find_naming_conventions_by_type("rigging")
```

### Custom Preset Paths

Add custom paths using the `TP_NAMING_PRESET_PATHS` environment variable:

```bash
# Windows
set TP_NAMING_PRESET_PATHS=C:\projects\my_game\naming_presets;D:\shared\presets

# Linux/macOS
export TP_NAMING_PRESET_PATHS=/projects/my_game/naming_presets:/shared/presets
```

Or programmatically:

```python
from tp.libs.templating import add_preset_path, remove_preset_path, preset_paths

# Add a preset path
add_preset_path("/path/to/my/presets", prepend=True)

# Remove a preset path
remove_preset_path("/path/to/remove")

# Get all configured preset paths
paths = preset_paths()
```

---

## API Reference

### Main API Functions (`tp.libs.templating.api`)

| Function | Description |
|----------|-------------|
| `naming_preset_manager()` | Get the global preset manager |
| `naming_convention(name, set_as_active)` | Get a naming convention by type |
| `active_naming_convention()` | Get the currently active naming convention |
| `set_active_naming_convention(nc)` | Set the active naming convention |
| `solve(**tokens)` | Generate a name from token values |
| `parse(name)` | Parse a name into token values |
| `parse_by_rule(name, rule_name)` | Parse using a specific rule |
| `reset_preset_manager()` | Reset the global preset manager |

### Path Templating Classes

| Class | Description |
|-------|-------------|
| `Template` | Path template with placeholders |
| `PathResolver` | Resolver for path templates with references |
| `Resolver` | Abstract base class for template resolvers |

### Versioning Classes

| Class | Description |
|-------|-------------|
| `VersionToken` | Version string parsing, formatting, and incrementing |
| `VersionResolver` | Filesystem-based version discovery |

### Asset Validation Classes

| Class | Description |
|-------|-------------|
| `AssetTypeDefinition` | Definition of an asset type |
| `AssetTypeRegistry` | Registry for managing asset types |
| `AssetValidator` | Validate names and paths against asset types |
| `ValidationResult` | Result of a validation operation |

### Discovery Classes

| Class | Description |
|-------|-------------|
| `TemplateDiscovery` | Find files matching templates |
| `DiscoveredAsset` | A discovered asset with parsed tokens |

### Configuration Classes

| Class | Description |
|-------|-------------|
| `TemplateConfiguration` | Unified serializable configuration |
| `TemplateConfigurationSchema` | Schema for configuration validation |
| `ConfigurationMerger` | Merge multiple configurations |

### Context Classes

| Class | Description |
|-------|-------------|
| `TemplateContext` | Hierarchical context with inheritance |
| `ContextStack` | Stack-based context management |

### Error Classes

| Error | Description |
|-------|-------------|
| `ParseError` | Raised when parsing fails |
| `FormatError` | Raised when formatting fails |
| `ResolveError` | Raised when template reference cannot be resolved |
| `TokenNotFoundError` | Raised when a token is not found |
| `RuleNotFoundError` | Raised when a rule is not found |
| `ConventionNotFoundError` | Raised when a convention is not found |
| `ValidationError` | Raised on validation failure |
| `VersionParseError` | Raised on version parsing failure |
| `ConfigurationError` | Raised on configuration error |

---

## Examples

### Complete Rigging Workflow

```python
from tp.libs.templating import (
    NamingConvention, Template, PathResolver,
    VersionToken, VersionResolver,
    AssetTypeRegistry, AssetValidator,
    TemplateContext
)

# === 1. Set up naming convention ===
nc = NamingConvention(naming_data={"name": "rigging"})

# Define tokens
nc.add_token("description")
nc.add_token("side", left="L", right="R", center="C", default="C")
nc.add_token("type",
    joint="jnt",
    control="ctrl",
    locator="loc",
    group="grp",
    default="ctrl"
)
nc.add_token("index", default="01")

# Define rules
nc.add_rule(
    "rig_joint",
    "{description}_{side}_{type}_{index}",
    {"description": "arm", "side": "left", "type": "joint", "index": "01"}
)
nc.add_rule(
    "rig_control",
    "{description}_{side}_{type}",
    {"description": "arm", "side": "left", "type": "control"}
)

# === 2. Set up path templates ===
resolver = PathResolver(naming_convention=nc)

resolver.register_template(Template(
    name="rig_file",
    pattern="/content/rigs/{character}/v{version}/{character}_rig_v{version}.ma"
))

# === 3. Set up versioning ===
version_token = VersionToken(format_str="{:03d}")

# === 4. Create context ===
ctx = TemplateContext(name="rig_session")
ctx.set("character", "hero")
ctx.naming_convention = nc
ctx.path_resolver = resolver

# === 5. Use everything together ===

# Generate joint names
for i, part in enumerate(["shoulder", "elbow", "wrist"], 1):
    name = nc.solve(
        rule_name="rig_joint",
        description=part,
        side="left",
        type="joint",
        index=f"{i:02d}"
    )
    print(f"Joint: {name}")
# Output:
# Joint: shoulder_L_jnt_01
# Joint: elbow_L_jnt_02
# Joint: wrist_L_jnt_03

# Generate control names
ctrl_name = nc.solve(
    rule_name="rig_control",
    description="arm",
    side="left",
    type="control"
)
print(f"Control: {ctrl_name}")  # Control: arm_L_ctrl

# Get next version for rig file
next_version = version_token.next_version("003")
path = resolver.resolve_path(
    "rig_file",
    character="hero",
    version=next_version
)
print(f"Save to: {path}")  # Save to: /content/rigs/hero/v004/hero_rig_v004.ma
```

### Game Asset Pipeline

```python
from tp.libs.templating import (
    NamingConvention, Template, PathResolver,
    AssetTypeRegistry, AssetValidator, AssetTypeDefinition,
    TemplateDiscovery, VersionToken
)

# === Set up naming convention ===
nc = NamingConvention(naming_data={"name": "game_assets"})

nc.add_token("prefix",
    static_mesh="SM",
    skeletal_mesh="SK",
    texture="T",
    material="M",
    blueprint="BP"
)
nc.add_token("asset_type",
    character="CHR",
    weapon="WPN",
    prop="PRP",
    environment="ENV"
)
nc.add_token("asset_name")
nc.add_token("variant", default="A")
nc.add_token("texture_type",
    diffuse="D",
    normal="N",
    roughness="R",
    metallic="M"
)

nc.add_rule(
    "static_mesh",
    "{prefix}_{asset_type}_{asset_name}_{variant}",
    {"prefix": "static_mesh", "asset_type": "prop", "asset_name": "Barrel"}
)
nc.add_rule(
    "texture",
    "{prefix}_{asset_name}_{texture_type}",
    {"prefix": "texture", "asset_name": "Hero", "texture_type": "diffuse"}
)

# === Set up path resolver ===
resolver = PathResolver(naming_convention=nc)

resolver.register_template(Template(
    name="mesh_path",
    pattern="/Content/{asset_type}/{asset_name}/Meshes/{prefix}_{asset_type}_{asset_name}.uasset"
))
resolver.register_template(Template(
    name="texture_path",
    pattern="/Content/{asset_type}/{asset_name}/Textures/{prefix}_{asset_name}_{texture_type}.uasset"
))

# === Set up asset validation ===
registry = AssetTypeRegistry(include_builtin=True)
validator = AssetValidator(registry, naming_convention=nc)

# === Example usage ===

# Generate mesh name
mesh_name = nc.solve(
    prefix="static_mesh",
    asset_type="weapon",
    asset_name="Sword",
    variant="B"
)
print(f"Mesh: {mesh_name}")  # SM_WPN_Sword_B

# Generate texture name
texture_name = nc.solve(
    rule_name="texture",
    prefix="texture",
    asset_name="Sword",
    texture_type="normal"
)
print(f"Texture: {texture_name}")  # T_Sword_N

# Resolve paths
mesh_path = resolver.resolve_path(
    "mesh_path",
    asset_type="weapon",
    asset_name="Sword",
    prefix="static_mesh"
)
print(f"Mesh path: {mesh_path}")

# Validate assets
result = validator.validate_path(mesh_path, "prop")
print(f"Valid: {result.valid}")
```

---

## Best Practices

1. **Use Descriptive Token Names**: Choose clear, meaningful names for tokens.

2. **Provide Example Fields**: Always include example fields in rules.

3. **Set Sensible Defaults**: Use defaults for commonly used values.

4. **Organize by Department/Asset Type**: Create separate convention files.

5. **Use Inheritance**: Create base conventions with common tokens.

6. **Use Context for Hierarchies**: Leverage `TemplateContext` for project/shot/asset hierarchies.

7. **Validate Early**: Use `AssetValidator` to catch naming issues early.

8. **Version Your Configurations**: Keep configurations in version control.

9. **Use Path Templates with References**: Build modular path templates that reference each other.

10. **Leverage Discovery**: Use `TemplateDiscovery` to find and audit existing assets.

---

## File Structure

```
project/
├── config/
│   └── templating.yaml          # Main configuration file
├── presets/
│   ├── project.preset           # Main preset file
│   ├── project-global.yaml      # Global naming rules
│   ├── project-characters.yaml  # Character naming rules
│   ├── project-rigging.yaml     # Rigging naming rules
│   └── project-animation.yaml   # Animation naming rules
└── content/
    ├── characters/
    ├── props/
    ├── environments/
    └── textures/
```

---

## Troubleshooting

### Preset Not Found

```python
from tp.libs.templating import preset_paths, add_preset_path

# Check configured paths
print(preset_paths())

# Add your preset path
add_preset_path("/path/to/presets")
```

### Parse Errors

If parsing fails, ensure:
1. The name matches one of your defined rules
2. Token values match the token table values
3. The active rule is set if using `parse_by_active_rule()`

### Version Not Detected

If version discovery fails:
1. Check that the template pattern matches your file structure
2. Ensure the version key matches your template placeholder
3. Verify files exist in the expected locations

### Validation Errors

When validation fails:
1. Check the `result.errors` list for specific issues
2. Review `result.suggestions` for corrections
3. Verify the asset type definition matches your files

---

## Migration from tp.libs.naming

If you're migrating from the old `tp.libs.naming` library:

```python
# Old import
# from tp.libs.naming import api

# New import
from tp.libs.templating import api

# Or use the naming submodule directly
from tp.libs.templating.naming import api
```

All existing naming functionality is preserved and works identically. The new library adds path templating, versioning, asset validation, discovery, configuration, and context features.

---

## License

This library is part of the TP-DCC framework. See the main repository for license information.

