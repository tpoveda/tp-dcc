# MetaHuman Body Rig Builder

A comprehensive Python library for building production-ready animation rigs for Unreal Engine MetaHuman characters in Autodesk Maya.

## Overview

The MetaHuman Body Rig Builder automatically generates a complete animation control rig for MetaHuman body skeletons. It creates intuitive controls for animators, including FK/IK switching, reverse foot setups, finger controls with curl and spread, and space switching systems.

## Features

- **Motion Skeleton Creation**: Generates a motion skeleton for animation that can be transferred back to the MetaHuman
- **FK/IK Limb Systems**: Full FK and IK controls for arms and legs with seamless blending
- **Reverse Foot Setup**: Professional foot roll controls with heel, ball, and toe pivots
- **Finger Controls**: Curl and spread controls for efficient hand animation
- **Space Switching**: IK controls can follow different parent spaces (world, body, head, etc.)
- **Automatic Skeleton Detection**: Detects MetaHuman skeleton variants and adapts accordingly
- **Color-Coded Controls**: Left (blue), right (red), and center (orange) control coloring
- **Progress Callbacks**: Track build progress for UI integration
- **Serializable Options**: Save and load rig configuration as JSON

## Installation

The library is part of the `tp-tools-metahuman` package. Ensure it's installed in your Maya Python environment.

```python
# The module is typically imported as:
from tp.tools.metahuman.body_rig_builder import RigAPI, RigOptions
```

## Quick Start

### Basic Usage

```python
from tp.tools.metahuman.body_rig_builder import RigAPI

# Build a rig with default settings (motion skeleton enabled)
result = RigAPI.build_quick()

if result.success:
    print(f"Rig built successfully: {result.message}")
    print(f"Root joint: {result._root_joint}")
else:
    print(f"Build failed: {result.message}")
```

### Using RigOptions

```python
from tp.tools.metahuman.body_rig_builder import RigAPI, RigOptions, BuildMode

# Create custom options
options = RigOptions(
    motion=True,                    # Create motion skeleton
    build_mode=BuildMode.MOTION,    # Full motion rig
    use_space_switch=True,          # Enable space switching
    create_finger_controls=True,    # Create finger curl/spread controls
    create_reverse_foot=True,       # Create reverse foot setup
    create_fkik_switches=True,      # Create FK/IK switches
    scale=1.0,                      # Control scale factor
)

# Build with custom options
result = RigAPI.build(options)
```

### Progress Tracking

```python
from tp.tools.metahuman.body_rig_builder import RigAPI, RigOptions

def on_progress(percent: float, message: str) -> None:
    """Callback for progress updates."""
    print(f"{percent:.0f}% - {message}")

options = RigOptions(motion=True)
result = RigAPI.build(options, progress=on_progress)
```

## Build Modes

The library supports three build modes:

| Mode | Description |
|------|-------------|
| `BuildMode.MOTION` | Creates a motion skeleton with full animation controls (default) |
| `BuildMode.IN_PLACE` | Creates controls for existing skeleton without motion skeleton |
| `BuildMode.PREVIEW` | Validates configuration without modifying the scene |

```python
from tp.tools.metahuman.body_rig_builder import RigOptions, BuildMode

# Animation mode (default)
anim_options = RigOptions(build_mode=BuildMode.MOTION)

# Layout mode (no motion skeleton)
layout_options = RigOptions(build_mode=BuildMode.IN_PLACE)

# Preview mode (validation only)
preview_options = RigOptions(build_mode=BuildMode.PREVIEW)
```

## Presets

Use built-in presets for common workflows:

```python
from tp.tools.metahuman.body_rig_builder import RigAPI

# Get animation preset
anim_options = RigAPI.get_preset('animation')

# Get layout preset
layout_options = RigAPI.get_preset('layout')

# List available presets
presets = RigAPI.list_presets()  # ['animation', 'layout']
```

## Validation

Validate options and scene before building:

```python
from tp.tools.metahuman.body_rig_builder import RigAPI, RigOptions

# Validate options
options = RigOptions(scale=1.5)
validation = RigAPI.validate_options(options)

if not validation.is_valid:
    for error in validation.errors:
        print(f"Error: {error}")
for warning in validation.warnings:
    print(f"Warning: {warning}")

# Validate scene (check for MetaHuman skeleton)
scene_validation = RigAPI.validate_scene()
if not scene_validation.is_valid:
    print("Scene is not ready for rig building")
    print(scene_validation.errors)
```

## Saving and Loading Options

Options can be serialized for pipeline integration:

```python
from tp.tools.metahuman.body_rig_builder import RigAPI, RigOptions

options = RigOptions(
    motion=True,
    scale=1.5,
    create_finger_controls=True
)

# Save to JSON file
RigAPI.save_options(options, "rig_config.json")

# Load from JSON file
loaded_options = RigAPI.load_options("rig_config.json")

# Convert to/from JSON string
json_str = RigAPI.options_to_json(options)
options_from_str = RigAPI.options_from_json(json_str)
```

## Custom Colors

Override default control colors:

```python
from tp.tools.metahuman.body_rig_builder import RigOptions, Color

options = RigOptions(
    motion=True,
    left_side_color=Color(0.0, 0.4, 0.8),    # Custom blue
    right_side_color=Color(0.8, 0.2, 0.2),   # Custom red
    center_color=Color(1.0, 0.5, 0.0),       # Orange
    global_color=Color(0.9, 0.9, 0.0),       # Yellow
)

# Get default colors
default_colors = RigAPI.get_default_colors()
# {'LEFT': (0.0, 0.0, 0.5), 'RIGHT': (0.5, 0.0, 0.0), ...}
```

## Low-Level Builder Access

For advanced use cases, access individual builders directly:

```python
from tp.tools.metahuman.body_rig_builder import (
    MetaHumanBodyRigBuilder,
    ControlBuilder,
    SkeletonBuilder,
    ReverseFootBuilder,
    SpaceSwitchBuilder,
    FingerControlBuilder,
    FKIKSwitchBuilder,
    Side,
)

# Use the main builder directly
builder = MetaHumanBodyRigBuilder(motion=True)
result = builder.build()

# Access individual builder classes
control_builder = ControlBuilder("rig_ctrls")
skeleton_builder = SkeletonBuilder()
finger_builder = FingerControlBuilder("rig_ctrls")

# Build specific systems
from tp.tools.metahuman.body_rig_builder import Side
reverse_foot = ReverseFootBuilder("rig_setup", "rig_ctrls")
foot_result = reverse_foot.build_reverse_foot(Side.LEFT, "_motion")
```

## API Reference

### RigAPI Methods

| Method | Description |
|--------|-------------|
| `build(options, progress)` | Build rig with full options |
| `build_quick(motion, progress)` | Quick build with minimal configuration |
| `validate_options(options)` | Validate RigOptions |
| `validate_scene()` | Validate Maya scene for rig building |
| `get_preset(name)` | Get named options preset |
| `list_presets()` | List available presets |
| `save_options(options, path)` | Save options to JSON file |
| `load_options(path)` | Load options from JSON file |
| `options_to_json(options)` | Convert options to JSON string |
| `options_from_json(json_str)` | Create options from JSON string |
| `get_default_colors()` | Get default rig colors |
| `get_builders()` | Get available builder classes |
| `get_version()` | Get API version |

### RigOptions Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `motion` | bool | `True` | Create motion skeleton |
| `build_mode` | BuildMode | `MOTION` | Build mode |
| `use_space_switch` | bool | `True` | Enable space switching |
| `create_finger_controls` | bool | `True` | Create finger controls |
| `create_reverse_foot` | bool | `True` | Create reverse foot |
| `create_fkik_switches` | bool | `True` | Create FK/IK switches |
| `namespace` | str | `""` | Optional namespace |
| `scale` | float | `1.0` | Control scale factor |
| `left_side_color` | Color | `None` | Left side color override |
| `right_side_color` | Color | `None` | Right side color override |
| `center_color` | Color | `None` | Center color override |
| `global_color` | Color | `None` | Global control color override |
| `custom_data` | dict | `{}` | Custom user data |

### RigBuildResult Properties

| Property | Type | Description |
|----------|------|-------------|
| `success` | bool | Whether the build succeeded |
| `message` | str | Status message |
| `root_joint` | str | Name of root joint |
| `motion_skeleton` | str | Name of motion skeleton root |
| `controls_created` | list | List of created control names |

## Requirements

- Autodesk Maya 2022+
- Python 3.9+
- MetaHuman character imported in scene
- `lookdevKit` Maya plugin (auto-loaded)

## License

This library is part of the tp-dcc tools suite.

