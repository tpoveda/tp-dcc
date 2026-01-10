# Maya Meta Node Library

A powerful metadata network system for Maya that allows you to create, manage, and query metadata nodes using Python classes. This library enables persistent metadata storage in Maya scenes with automatic class reconstruction.

## Overview

The meta node system provides:

- **Automatic Class Reconstruction**: Meta nodes store their Python class type, allowing automatic reconstruction of the correct Python class when loading from a scene.
- **Hierarchical Relationships**: Build parent-child relationships between meta nodes to create complex metadata networks.
- **Registry System**: Centralized registration of meta classes with automatic discovery from packages, modules, or environment variables.
- **Tag System**: Tag meta nodes for easy filtering and querying.
- **Serialization**: Export meta node data to dictionaries for debugging or data exchange.

## Architecture

### Core Components

1. **MetaRegistry**: Singleton that manages registration of all meta classes.
2. **MetaFactory**: Metaclass that enables automatic class instantiation based on stored type.
3. **MetaBase**: Base class for all meta nodes, extending `DGNode`.

### Meta Node Attributes

Each meta node automatically has these attributes:

| Attribute | Description |
|-----------|-------------|
| `tpMetaClass` | Stores the class name/ID for reconstruction |
| `tpMetaVersion` | Version string for migration support |
| `tpMetaParent` | Message array for parent connections |
| `tpMetaChildren` | Message array for child connections |
| `tpMetaTag` | String tag for filtering |

## Quick Start

### Creating a Custom Meta Class

```python
from tp.libs.maya.meta.base import MetaBase, MetaRegistry

class CharacterMeta(MetaBase):
    """Meta node for storing character data."""
    
    ID = "CharacterMeta"  # Registry identifier
    VERSION = "1.0.0"
    DEFAULT_NAME = "character_meta"
    
    def setup(self, character_name: str = "", rig_type: str = "biped"):
        """Called after the meta node is created."""
        # Add custom attributes
        self.addAttribute("characterName", value=character_name, type=attributetypes.kMFnDataString)
        self.addAttribute("rigType", value=rig_type, type=attributetypes.kMFnDataString)
    
    def meta_attributes(self):
        """Override to add custom meta attributes."""
        attrs = super().meta_attributes()
        # Add your custom meta attributes here
        return attrs
```

### Registering Meta Classes

```python
# Register from environment variable
MetaRegistry().register_by_env("MY_META_PATHS")

# Register a single class
MetaRegistry.register_meta_class(CharacterMeta)

# Register all classes in a module
import my_meta_module
MetaRegistry.register_by_module(my_meta_module)

# Register all classes in a package
MetaRegistry.register_by_package("/path/to/meta/package")
```

### Creating Meta Nodes

```python
# Create a new meta node
character = CharacterMeta(name="hero_meta", character_name="Hero", rig_type="biped")

# Create with namespace
character = CharacterMeta(namespace="HERO", character_name="Hero")

# Create from existing node (auto-reconstructs correct class)
existing = MetaBase(node=some_maya_node)  # Returns CharacterMeta if that's what's stored
```

### Building Hierarchies

```python
# Create parent-child relationships
root_meta = CharacterMeta(name="root_meta")
limb_meta = LimbMeta(name="arm_meta")
joint_meta = JointMeta(name="shoulder_meta")

# Add children
root_meta.add_meta_child(limb_meta)
limb_meta.add_meta_child(joint_meta)

# Query relationships
parent = joint_meta.meta_parent()  # Returns limb_meta
children = root_meta.meta_children()  # Returns [limb_meta]
children_recursive = root_meta.meta_children(depth_limit=256)  # Returns [limb_meta, joint_meta]

# Get root of hierarchy
root = joint_meta.meta_root()  # Returns root_meta

# Check if node is root
is_root = root_meta.is_root()  # Returns True
```

### Querying Meta Nodes

```python
from tp.libs.maya.meta.base import (
    iterate_scene_meta_nodes,
    find_meta_nodes_by_class_type,
    find_meta_nodes_by_tag,
    is_meta_node,
    connected_meta_nodes,
)

# Iterate all meta nodes in scene
for meta_node in iterate_scene_meta_nodes():
    print(meta_node.name(), meta_node.metaclass_type())

# Find by class type
characters = find_meta_nodes_by_class_type(CharacterMeta)
characters = find_meta_nodes_by_class_type("CharacterMeta")  # String also works

# Find by tag
tagged_nodes = find_meta_nodes_by_tag("hero")

# Check if a node is a meta node
if is_meta_node(some_node):
    print("It's a meta node!")

# Get meta nodes connected to a regular Maya node
meta_nodes = connected_meta_nodes(some_transform)
```

### Using Tags

```python
# Set a tag
character.set_tag("main_character")

# Get the tag
tag = character.tag()

# Find children by tag
hero_parts = character.find_children_by_tag("hero_part")
```

### Connecting Regular Maya Nodes

```python
# Connect a Maya node to the meta node
character.connect_to("skeleton_root", skeleton_joint)
character.connect_to("geometry", mesh_node)

# The connected nodes can be queried through the attribute
skeleton = character.attribute("skeleton_root").source().node()
```

### Serialization

```python
# Export to dictionary
data = character.to_dict()
# {
#     "name": "hero_meta",
#     "class": "CharacterMeta",
#     "version": "1.0.0",
#     "tag": "main_character",
#     "is_root": True
# }

# Include children recursively
data = character.to_dict(include_children=True)
```

### Dynamic Creation by Type Name

```python
from tp.libs.maya.meta.base import create_meta_node_by_type

# Create meta node by registered type name
meta = create_meta_node_by_type("CharacterMeta", name="new_character")
```

## Advanced Usage

### Custom Meta Attributes

Override `meta_attributes()` to define additional attributes that are created when the meta node is initialized:

```python
class RigMeta(MetaBase):
    ID = "RigMeta"
    VERSION = "2.0.0"
    
    def meta_attributes(self):
        attrs = super().meta_attributes()
        attrs.extend([
            {
                "name": "rigScale",
                "value": 1.0,
                "type": attributetypes.kMFnNumericFloat,
                "locked": False,
                "storable": True,
            },
            {
                "name": "controlColor",
                "value": [1.0, 0.0, 0.0],
                "type": attributetypes.kMFn3Float,
                "locked": False,
            },
        ])
        return attrs
```

### Filtering Children by Type

```python
# Find all children of a specific class type
arms = character.find_children_by_class_type("ArmMeta")

# Find children matching multiple types
limbs = character.find_children_by_class_types(["ArmMeta", "LegMeta"])

# Using the iterator with type filter
for limb in character.iterate_meta_children(check_type=LimbMeta):
    print(limb.name())
```

### Registry Management

```python
# Check if type is registered
if MetaRegistry.is_in_registry("CharacterMeta"):
    print("CharacterMeta is registered")

# Get registered type
cls = MetaRegistry.get_type("CharacterMeta")

# Get all registered types
all_types = MetaRegistry.types()

# Unregister a class
MetaRegistry.unregister_meta_class(CharacterMeta)

# Clear entire cache
MetaRegistry.clear_cache()
```

### Using Modifiers for Batch Operations

```python
from maya.api import OpenMaya

mod = OpenMaya.MDGModifier()

# Create with modifier (deferred execution)
meta1 = CharacterMeta(name="char1", mod=mod)
meta2 = CharacterMeta(name="char2", mod=mod)

# Build hierarchy with modifier
meta1.add_meta_child(meta2, mod=mod)

# Execute all at once
mod.doIt()
```

## Environment Setup

Set the `TP_DCC_META_PATHS` environment variable to automatically register meta classes from specified paths:

```bash
# Windows
set TP_DCC_META_PATHS=C:\path\to\meta\classes;C:\another\path

# Linux/Mac
export TP_DCC_META_PATHS=/path/to/meta/classes:/another/path
```

The registry will automatically load all `MetaBase` subclasses found in these paths.

## Best Practices

1. **Always define an ID**: Use a unique `ID` class attribute for reliable reconstruction.

2. **Use semantic versioning**: Set the `VERSION` attribute for migration support.

3. **Implement setup()**: Put initialization logic in `setup()` rather than `__init__()`.

4. **Use modifiers for batch operations**: When creating many nodes, use `MDGModifier` for better performance.

5. **Tag your nodes**: Use tags for logical grouping and filtering.

6. **Clean up connections**: Use `remove_meta_parent()` before reassigning parents.

## API Reference

### MetaRegistry

| Method | Description |
|--------|-------------|
| `register_meta_class(cls)` | Register a single meta class |
| `register_by_module(module)` | Register all classes from a module |
| `register_by_package(path)` | Register all classes from a package |
| `register_by_env(env_name)` | Register from environment variable |
| `get_type(type_name)` | Get registered class by name |
| `types()` | Get all registered types |
| `is_in_registry(type_name)` | Check if type is registered |
| `unregister_meta_class(cls)` | Remove class from registry |
| `clear_cache()` | Clear all registered classes |

### MetaBase

| Method | Description |
|--------|-------------|
| `meta_parent()` | Get immediate parent meta node |
| `meta_parents(recursive)` | Get list of parent meta nodes |
| `meta_children(depth_limit)` | Get list of child meta nodes |
| `meta_root()` | Get root of hierarchy |
| `is_root()` | Check if node has no parents |
| `add_meta_child(child)` | Add child meta node |
| `add_meta_parent(parent)` | Add parent meta node |
| `remove_meta_parent(parent)` | Remove parent connection |
| `metaclass_type()` | Get stored class type name |
| `version()` | Get stored version |
| `tag()` / `set_tag(tag)` | Get/set tag |
| `connect_to(attr, node)` | Connect Maya node via message attr |
| `to_dict(include_children)` | Serialize to dictionary |
| `find_children_by_class_type(type)` | Find children by class |
| `find_children_by_tag(tag)` | Find children by tag |

### Module Functions

| Function | Description |
|----------|-------------|
| `iterate_scene_meta_nodes()` | Iterate all meta nodes in scene |
| `find_meta_nodes_by_class_type(type)` | Find by class type |
| `find_meta_nodes_by_tag(tag)` | Find by tag |
| `is_meta_node(node)` | Check if node is a meta node |
| `is_meta_node_of_types(node, types)` | Check if node is specific type |
| `create_meta_node_by_type(name)` | Create node by type name |
| `connected_meta_nodes(node)` | Get meta nodes connected to node |

