# metadict

A unified metadata dictionary library for storing and managing persistent metadata across multiple DCC (Digital Content Creation) applications.

## 🏁 Introduction

`metadict` is a Python library that implements a unified metadata management system across multiple DCC environments.

This library provides:

* **Unified metadata management** across multiple DCC environments to store and load metadata in the current scene using a consistent API.
* **DCC-specific implementations** that handle the details of storing metadata in each application's native format.
* **Schema validation** to ensure data integrity.
* **Version tracking and migration** for evolving data structures.
* **Callback hooks** for pre/post save/load operations.
* **Dot notation access** for nested dictionary keys.
* **Export/import** to JSON files for backup and transfer.
* **Multiple merge strategies** for flexible data loading.

---

## 🧠 What is `metadict`?

`metadict` is a dynamic, DCC-specific dictionary abstraction that allows you to store dictionary data within different DCCs using a unified API.

**Important**: All data stored using `metadict` must be JSON serializable.

---

## 🏗️ Basic Structure

The system is organized as follows:

```
metadict/
├── api.py                       # Core interface
├── __init__.py                  # Public exports
└── apps/
    ├── maya/metadict.py         # Maya-specific logic
    ├── houdini/metadict.py      # Houdini-specific logic
    ├── mobu/metadict.py         # MotionBuilder-specific logic
    ├── blender/metadict.py      # Blender-specific logic
    ├── unreal/metadict.py       # Unreal Engine-specific logic
    └── standalone/metadict.py   # Fallback for generic Python
```

Each host module defines a `MetadataDictionary` class that customizes metadata behavior for that application.

---

## 🚀 Getting Started

### Creating a `MetadataDictionary`

A `MetadataDictionary` can be treated as a normal dictionary.

```python
from tp.libs.metadict import get

data = get('mydata', author='Alice', frame_range=[1001, 1100])
print(data["author"])  # Alice
data["scene_name"] = "Shot001"
data.save()  # Persist the data
```

---

## 🧩 DCC Detection and Behavior

`metadict` exposes the `get` function that dynamically routes to the appropriate `MetadataDictionary` implementation based on the current application.

Each `MetadataDictionary` has an associated `identifier` to uniquely identify this specific instance.

```python
from tp.libs.metadict import get

md = get('mydata')
print(type(md))
# <class 'tp.libs.metadict.apps.maya.metadict.MayaMetadataDictionary'>  # Example output in Maya
```

This makes it possible to define metadata logic once and have it behave correctly in each application.

---

## 🛠️ DCC-Specific Features

Each DCC implementation handles storing and loading dictionary data in the current scene/context differently.

### Standalone

In standalone Python, metadata is stored in memory by default. Optional file-based persistence is available.

```python
from tp.libs.metadict import get

md = get('mydata')
md["version"] = 1.0
md.save()
```

#### Enabling File Persistence

```python
from tp.libs.metadict import get
from tp.libs.metadict.apps.standalone.metadict import set_file_storage_directory

# Enable file-based persistence
set_file_storage_directory('/path/to/storage')

# Now data will be saved to JSON files
data = get('mydata')
data['setting'] = 'value'
data.save()  # Saves to /path/to/storage/mydata.json
```

### Maya

In Maya, metadata is attached to a custom string attribute on a network node in the scene.

* The default node name is `tp_metanode`.
* The default attribute name is `tp_metadata`.
* You can pass `attribute_name` keyword to use a custom attribute name.

```python
from tp.libs.metadict import get

data = get('mydata')
data['fbx_file_path'] = 'my_path'
data.save()
```

### MotionBuilder

In MotionBuilder, metadata is stored as a property within an `FBNote` node in the scene.

```python
from tp.libs.metadict import get

data = get('mydata')
data['fbx_file_path'] = 'my_path'
data.save()
```

### Houdini

In Houdini, metadata is stored as `userData` on the root Houdini node (`hou.node("/")`).

```python
from tp.libs.metadict import get

data = get('mydata')
data['fbx_file_path'] = 'my_path'
data.save()
```

### Blender

In Blender, metadata is stored as custom properties on the scene object.

```python
from tp.libs.metadict import get

data = get('mydata')
data['render_settings'] = {'samples': 128}
data.save()
```

### Unreal Engine

In Unreal, metadata is stored as asset metadata tags on the current level or a specified asset.

```python
from tp.libs.metadict import get

# Store on current level
data = get('mydata')
data['level_info'] = {'name': 'MainLevel'}
data.save()

# Store on specific asset
data = get('asset_meta', asset_path='/Game/Characters/Hero')
data['character_type'] = 'player'
data.save()
```

---

## 📝 Schema Validation

You can define a JSON schema to validate metadata before saving.

```python
from tp.libs.metadict import get

# Define a schema
schema = {
    'type': 'object',
    'required': ['name', 'version'],
    'properties': {
        'name': {'type': 'string'},
        'version': {'type': 'integer'},
        'tags': {'type': 'array'}
    }
}

# Create with schema
data = get('validated_data', schema=schema)
data['name'] = 'MyProject'
data['version'] = 1

# Validate manually
is_valid, errors = data.validate()
print(f"Valid: {is_valid}, Errors: {errors}")

# Validate before saving
data.save(validate_before=True)  # Raises ValueError if invalid
```

---

## 🔄 Versioning and Migration

Track data versions and migrate data when structure changes.

```python
from tp.libs.metadict import get

# Define migration functions
def migrate_v1_to_v2(data):
    """Rename 'old_key' to 'new_key'"""
    if 'old_key' in data:
        data['new_key'] = data.pop('old_key')
    return data

def migrate_v2_to_v3(data):
    """Split 'full_name' into 'first_name' and 'last_name'"""
    if 'full_name' in data:
        parts = data.pop('full_name').split(' ', 1)
        data['first_name'] = parts[0]
        data['last_name'] = parts[1] if len(parts) > 1 else ''
    return data

# Create versioned metadata (current version is 3)
data = get('user_data', version=3)

# Apply migrations (runs v1->v2 and v2->v3 if needed)
data.migrate({
    2: migrate_v1_to_v2,
    3: migrate_v2_to_v3
})

# Save with version
data.save()
```

---

## 🔗 Callback/Hooks System

Register callbacks for metadata events.

```python
from tp.libs.metadict import get

def on_pre_save(data):
    print(f"About to save: {data.id}")
    # Add timestamp
    import time
    data['last_saved'] = time.time()

def on_post_save(data):
    print(f"Saved: {data.id}")

def on_change(data, key, value):
    print(f"Changed {key} = {value}")

# Create and register callbacks
data = get('mydata')
data.add_callback('pre_save', on_pre_save)
data.add_callback('post_save', on_post_save)
data.add_callback('on_change', on_change)

# Changes will trigger on_change
data['name'] = 'test'  # Prints: Changed name = test

# Save will trigger pre_save and post_save
data.save()

# Remove callbacks
data.remove_callback('on_change', on_change)
data.clear_callbacks()  # Clear all callbacks
```

---

## 🔍 Dot Notation Access

Access nested dictionary keys using dot notation.

```python
from tp.libs.metadict import get

data = get('config')

# Set nested values (creates intermediate dicts)
data.set_nested('render.quality.samples', 128)
data.set_nested('render.quality.denoise', True)
data.set_nested('audio.volume', 0.8)

print(data)
# {'render': {'quality': {'samples': 128, 'denoise': True}}, 'audio': {'volume': 0.8}}

# Get nested values
samples = data.get_nested('render.quality.samples')
print(samples)  # 128

# Get with default value
unknown = data.get_nested('render.unknown.value', default='N/A')
print(unknown)  # N/A

# Delete nested values
data.delete_nested('render.quality.denoise')
```

---

## 🔀 Merge Strategies

Control how data is loaded and merged.

```python
from tp.libs.metadict import get, MergeStrategy

# REPLACE (default): Replace current data with loaded data
data = get('mydata', merge_strategy=MergeStrategy.REPLACE)

# MERGE: Shallow merge (update)
data = get('mydata', merge_strategy=MergeStrategy.MERGE)

# DEEP_MERGE: Deep merge nested dictionaries
data = get('mydata', merge_strategy=MergeStrategy.DEEP_MERGE)

# Merge manually with specific strategy
existing_data = {'a': 1, 'nested': {'x': 1, 'y': 2}}
new_data = {'b': 2, 'nested': {'y': 3, 'z': 4}}

data = get('mydata')
data.update(existing_data)

# Shallow merge
data.merge_with(new_data, MergeStrategy.MERGE)
# Result: {'a': 1, 'b': 2, 'nested': {'y': 3, 'z': 4}}

# Deep merge
data.clear()
data.update(existing_data)
data.merge_with(new_data, MergeStrategy.DEEP_MERGE)
# Result: {'a': 1, 'b': 2, 'nested': {'x': 1, 'y': 3, 'z': 4}}
```

---

## 📤 Export/Import

Export metadata to JSON files and import from them.

```python
from tp.libs.metadict import get, MergeStrategy

data = get('project_settings')
data['name'] = 'MyProject'
data['version'] = '1.0.0'
data.save()

# Export to file
data.export_to_file('backup/project_settings.json')

# Export without version
data.export_to_file('backup/settings_no_version.json', include_version=False)

# Import from file (replaces current data by default)
data.import_from_file('backup/project_settings.json')

# Import with merge strategy
data.import_from_file('backup/other_settings.json', strategy=MergeStrategy.DEEP_MERGE)

# Import with validation
data.import_from_file('backup/project_settings.json', validate_after=True)
```

---

## 🔧 API Reference

### MetadataDictionary

The base class for all metadata dictionary implementations.

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `identifier` | `str` | required | Unique identifier for this dictionary |
| `schema` | `dict` | `None` | JSON schema for validation |
| `version` | `int` | `1` | Version number for versioning support |
| `merge_strategy` | `MergeStrategy` | `REPLACE` | Default merge strategy |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `str` | Unique identifier |
| `version` | `int` | Current version number |
| `schema` | `dict \| None` | JSON schema (read/write) |

#### Methods

| Method | Description |
|--------|-------------|
| `load(strategy=None)` | Load data from storage |
| `save(validate_before=False)` | Save data to storage |
| `delete()` | Delete from storage |
| `clear_and_save()` | Clear and save empty state |
| `update_and_save(data=None, **kwargs)` | Update and save |
| `get_nested(key_path, default=None)` | Get value by dot notation |
| `set_nested(key_path, value)` | Set value by dot notation |
| `delete_nested(key_path)` | Delete value by dot notation |
| `validate()` | Validate against schema |
| `validate_and_raise()` | Validate or raise ValueError |
| `migrate(migrations)` | Apply version migrations |
| `merge_with(data, strategy=None)` | Merge data with strategy |
| `export_to_file(path, ...)` | Export to JSON file |
| `import_from_file(path, ...)` | Import from JSON file |
| `add_callback(event, callback)` | Register event callback |
| `remove_callback(event, callback)` | Remove event callback |
| `clear_callbacks(event=None)` | Clear callbacks |

### MergeStrategy Enum

| Value | Description |
|-------|-------------|
| `REPLACE` | Replace current data with new data |
| `MERGE` | Shallow merge (dict.update) |
| `DEEP_MERGE` | Deep merge nested dictionaries |

### Functions

| Function | Description |
|----------|-------------|
| `get(identifier, **kwargs)` | Get MetadataDictionary for current DCC |

---

## 🔧 Extending `metadict`

To add support for a new DCC:

1. Create a new folder under `metadict/apps/<app_name>/`
2. Add an empty `__init__.py` file
3. Add a `metadict.py` with your implementation:

```python
from __future__ import annotations
from typing import Any
from tp.libs.metadict import MetadataDictionary
from tp.bootstrap.utils import dcc

class MyDCCMetadataDictionary(MetadataDictionary):
    priority = 2  # Higher than standalone (1)
    
    @classmethod
    def usable(cls) -> bool:
        return dcc.is_my_dcc()  # Check if running in your DCC
    
    def _load_data(self) -> dict[str, Any]:
        # Load and return data from DCC-specific storage
        return {}
    
    def _save_data(self, data: dict[str, Any]) -> None:
        # Save data to DCC-specific storage
        pass
    
    def delete(self) -> bool:
        # Delete from DCC-specific storage
        return False
```

---

## 📎 Complete Examples

### Basic Usage

```python
from tp.libs.metadict import get

# Create and save metadata
data = get('sequence', artist="Bob", resolution="1920x1080", fps=24)
data.save()

# Load existing metadata
data = get('sequence')
print(data)  # {'artist': 'Bob', 'resolution': '1920x1080', 'fps': 24}

# Update and save in one call
data.update_and_save(artist="Alice", frame_count=100)

# Clear all data
data.clear_and_save()

# Delete the metadata storage
data.delete()
```

### Advanced Usage with All Features

```python
from tp.libs.metadict import get, MergeStrategy

# Schema for validation
schema = {
    'type': 'object',
    'required': ['project_name'],
    'properties': {
        'project_name': {'type': 'string'},
        'settings': {'type': 'object'}
    }
}

# Migrations for version updates
def migrate_v2(data):
    if 'name' in data:
        data['project_name'] = data.pop('name')
    return data

# Create with all features
data = get(
    'project_config',
    schema=schema,
    version=2,
    merge_strategy=MergeStrategy.DEEP_MERGE
)

# Add callbacks
data.add_callback('pre_save', lambda d: print(f"Saving {d.id}..."))

# Apply migrations if needed
data.migrate({2: migrate_v2})

# Set nested configuration
data.set_nested('settings.render.quality', 'high')
data.set_nested('settings.render.samples', 256)
data['project_name'] = 'MyAwesomeProject'

# Validate and save
is_valid, errors = data.validate()
if is_valid:
    data.save()
    
# Export for backup
data.export_to_file('backups/project_config.json')
```
