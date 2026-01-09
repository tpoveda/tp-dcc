# TP Naming Library

A flexible and extensible naming convention library for managing asset naming standards in game and VFX production pipelines.

## Overview

The naming library provides a robust system for defining, parsing, and generating standardized names across your project. It supports:

- **Rules**: Expression-based naming patterns (e.g., `{type}_{name}_{side}_{index}`)
- **Tokens**: Configurable placeholders with value mappings and defaults
- **Presets**: Collections of naming conventions organized
- **Inheritance**: Parent-child relationships for convention reuse
- **Custom Paths**: Project-specific preset locations via environment variables

## Installation

The naming library is part of the `tp-core` package. Ensure `tp-core` is in your Python path.

```python
from tp.libs.naming import api
```

## Quick Start

### Basic Usage

```python
from tp.libs.naming import api

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

### Using Active Convention

```python
from tp.libs.naming import api

# Set a naming convention as active
nc = api.naming_convention(name="global", set_as_active=True)

# Now solve without specifying convention
name = api.solve(description="leg", side="right", type="control")
# Result: "leg_R_ctrl"
```

## Core Concepts

### Rules

Rules define the structure of a name using an expression with token placeholders:

```python
from tp.libs.naming import convention

nc = convention.NamingConvention()

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

## Presets

Presets are collections of naming conventions organized for different asset types or departments.

### Preset Structure

A preset file (`.preset`) defines which naming conventions to use:

```yaml
name: my_project
namingConventions:
  - name: default-global
    type: global
  - name: project-characters
    type: characters
  - name: project-environments
    type: environments
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

  - name: character_mesh
    creator: artist_name
    description: Character mesh naming
    expression: "SM_CHR_{character_name}_{body_part}_{variant}"
    exampleFields:
      character_name: Hero
      body_part: Body
      variant: A

tokens:
  - name: character_name
    description: Name of the character

  - name: body_part
    description: Body part of the character
    table:
      body: Body
      head: Head
      hands: Hands
      feet: Feet

  - name: variant
    description: Asset variant
    default: A
```

### Loading Presets

```python
from tp.libs.naming import api, preset

# Get the preset manager
pm = api.naming_preset_manager()

# Find a specific preset
my_preset = pm.find_preset("my_project")

# Get naming conventions by type
rigging_conventions = pm.find_naming_conventions_by_type("rigging")
```

## Configuration

### Custom Preset Paths

Add custom paths where the library should look for presets using the `TP_NAMING_PRESET_PATHS` environment variable:

```bash
# Windows
set TP_NAMING_PRESET_PATHS=C:\projects\my_game\naming_presets;D:\shared\presets

# Linux/macOS
export TP_NAMING_PRESET_PATHS=/projects/my_game/naming_presets:/shared/presets
```

### Programmatic Configuration

```python
from tp.libs.naming import config

# Add a preset path
config.add_preset_path("/path/to/my/presets", prepend=True)

# Remove a preset path
config.remove_preset_path("/path/to/remove")

# Get all configured preset paths
paths = config.preset_paths()

# Get the built-in presets path
builtin = config.builtin_presets_path()
```

### Package Integration

For tp-dcc packages, add the preset path in `package.yaml`:

```yaml
environment:
  TP_NAMING_PRESET_PATHS:
    - "{self}/presets"
```

## Naming Convention Inheritance

Naming conventions can inherit from parent conventions:

```python
from tp.libs.naming import convention

# Create a base convention with common tokens
base = convention.NamingConvention(naming_data={"name": "base"})
base.add_token("side", left="L", right="R", center="C", default="C")
base.add_token("index", default="01")

# Create a child convention that inherits from base
rigging = convention.NamingConvention(
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

## API Reference

### Main API Functions (`tp.libs.naming.api`)

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

### Configuration Functions (`tp.libs.naming.config`)

| Function | Description |
|----------|-------------|
| `get_configuration()` | Get the global configuration |
| `set_configuration(config)` | Set the global configuration |
| `reset_configuration()` | Reset to default configuration |
| `add_preset_path(path, prepend)` | Add a preset search path |
| `remove_preset_path(path)` | Remove a preset search path |
| `preset_paths()` | Get all configured preset paths |
| `builtin_presets_path()` | Get the built-in presets directory |

### NamingConvention Class

| Method | Description |
|--------|-------------|
| `add_token(name, **values)` | Add a token with optional value mappings |
| `add_rule(name, expression, example_fields)` | Add a naming rule |
| `add_rule_from_tokens(name, *token_names)` | Create a rule from token names |
| `solve(**tokens)` | Generate a name from token values |
| `parse(name)` | Parse a name into token values |
| `has_token(name)` | Check if a token exists |
| `has_rule(name)` | Check if a rule exists |
| `token(name)` | Get a token by name |
| `rule(name)` | Get a rule by name |
| `set_active_rule(rule)` | Set the active rule |
| `save_to_file(path)` | Save convention to file |
| `from_path(path)` | Load convention from file |

## Examples

### Rigging Naming Convention

```python
from tp.libs.naming import convention, api

# Create a rigging naming convention
rig_nc = convention.NamingConvention(naming_data={"name": "rigging"})

# Define tokens
rig_nc.add_token("description")
rig_nc.add_token("side", left="L", right="R", center="C", default="C")
rig_nc.add_token("type",
    joint="jnt",
    control="ctrl",
    locator="loc",
    group="grp",
    ikHandle="ikh",
    default="ctrl"
)
rig_nc.add_token("index", default="01")

# Define rules
rig_nc.add_rule(
    "rig_joint",
    "{description}_{side}_{type}_{index}",
    {"description": "arm", "side": "left", "type": "joint", "index": "01"}
)
rig_nc.add_rule(
    "rig_control",
    "{description}_{side}_{type}",
    {"description": "arm", "side": "left", "type": "control"}
)

# Set as active and use
api.set_active_naming_convention(rig_nc)

# Generate joint name
joint_name = api.solve(
    rule_name="rig_joint",
    description="upperArm",
    side="left",
    type="joint",
    index="01"
)
# Result: "upperArm_L_jnt_01"

# Generate control name
ctrl_name = api.solve(
    rule_name="rig_control",
    description="arm",
    side="left",
    type="control"
)
# Result: "arm_L_ctrl"
```

### Game Asset Naming

```python
from tp.libs.naming import convention, api

# Create a game asset naming convention
game_nc = convention.NamingConvention(naming_data={"name": "game_assets"})

# Define tokens
game_nc.add_token("prefix",
    static_mesh="SM",
    skeletal_mesh="SK",
    texture="T",
    material="M",
    material_instance="MI",
    blueprint="BP",
    animation="A",
    particle="PS"
)
game_nc.add_token("asset_type",
    character="CHR",
    weapon="WPN",
    prop="PRP",
    environment="ENV",
    vehicle="VEH"
)
game_nc.add_token("asset_name")
game_nc.add_token("variant", default="A")

# Define rules
game_nc.add_rule(
    "static_mesh",
    "{prefix}_{asset_type}_{asset_name}_{variant}",
    {"prefix": "static_mesh", "asset_type": "prop", "asset_name": "Barrel", "variant": "A"}
)

api.set_active_naming_convention(game_nc)

# Generate asset name
mesh_name = api.solve(
    prefix="static_mesh",
    asset_type="weapon",
    asset_name="Sword",
    variant="B"
)
# Result: "SM_WPN_Sword_B"
```

## Best Practices

1. **Use Descriptive Token Names**: Choose clear, meaningful names for tokens that describe their purpose.

2. **Provide Example Fields**: Always include example fields in rules to help users understand expected values.

3. **Set Sensible Defaults**: Use defaults for commonly used values to reduce repetition.

4. **Organize by Department/Asset Type**: Create separate convention files for different departments or asset types.

5. **Use Inheritance**: Create base conventions with common tokens and inherit from them.

6. **Version Your Presets**: Keep presets in version control and document changes.

7. **Validate Names**: Use the parse function to validate names conform to conventions.

## File Structure

```
project/
├── presets/
│   ├── project.preset           # Main preset file
│   ├── project-global.yaml      # Global naming rules
│   ├── project-characters.yaml  # Character naming rules
│   ├── project-environments.yaml
│   ├── project-rigging.yaml
│   └── project-animation.yaml
```

## Troubleshooting

### Preset Not Found

Ensure the preset path is configured:

```python
from tp.libs.naming import config

# Check configured paths
print(config.preset_paths())

# Add your preset path
config.add_preset_path("/path/to/presets")
```

### Parse Errors

If parsing fails, ensure:
1. The name matches one of your defined rules
2. Token values in the name match the token table values
3. The active rule is set if using `parse_by_active_rule()`

### Convention Not Loading

Check that:
1. The `.preset` file references the correct convention names
2. Convention `.yaml` files exist in configured paths
3. YAML syntax is valid

## License

This library is part of the TP-DCC framework. See the main repository for license information.

