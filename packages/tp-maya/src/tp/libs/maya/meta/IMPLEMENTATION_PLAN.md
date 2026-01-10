# Metadata Library Implementation Plan

## Overview

This document outlines the comparison between our current metadata implementation (`base.py`) and the Freeform metadata library, identifying features to integrate and improvements to make.

---

## 0. Critical Analysis: Upstream vs Downstream Direction

### Understanding Maya's Connection Flow

In Maya, connections have a **source** and a **destination**:
- **Source plug** → **Destination plug**
- Data flows from source to destination
- In the dependency graph, this means: **output** → **input**

### The `message` Attribute Pattern

Maya's `message` attribute is commonly used for metadata connections because:
- It's a special attribute available on all dependency nodes
- It doesn't carry actual data - just establishes a relationship
- Connection pattern: `nodeA.message` → `nodeB.someAttribute`

### Freeform's Approach

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FREEFORM CONNECTION PATTERN                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Scene Object (Joint, Mesh, etc.)                                          │
│       │                                                                     │
│       │ .message (source)                                                   │
│       └──────────────────►┐                                                 │
│                           ▼                                                 │
│                    MetaNode.affectedBy[] (destination)                      │
│                           │                                                 │
│                           │ .message (source)                               │
│                           └──────────────────►┐                             │
│                                               ▼                             │
│                                        ParentMeta.affectedBy[]              │
│                                               │                             │
│                                               │ .message                    │
│                                               └──────────────────►┐         │
│                                                                   ▼         │
│                                                              Core (root)    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ UPSTREAM (get_upstream):    Follow .affectedBy → toward Core (root)        │
│ DOWNSTREAM (get_downstream): Follow .message   → toward scene objects      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ KEY INSIGHT: In Freeform:                                                   │
│   - Core is the "root" (topmost/upstream)                                   │
│   - Properties/Scene objects are "leaves" (bottommost/downstream)           │
│   - UPSTREAM means "toward the root/core"                                   │
│   - DOWNSTREAM means "toward the leaves/scene objects"                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Freeform's traversal logic:**
- `get_upstream(type)` - follows `.affectedBy` connections (toward root)
- `get_downstream(type)` - follows `.message` connections (toward leaves)

### Our Current Approach (base.py)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     OUR CURRENT CONNECTION PATTERN                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Parent MetaNode (root)                                                    │
│       │                                                                     │
│       │ tpMetaChildren[] ◄────────┐                                         │
│       │ (array destination)       │                                         │
│       │                           │                                         │
│       └─────►  tpMetaParent[]  ───┘ (source on child)                       │
│               (child node)                                                  │
│                   │                                                         │
│                   │ tpMetaChildren[] ◄────────┐                             │
│                   │ (array destination)       │                             │
│                   │                           │                             │
│                   └─────►  tpMetaParent[]  ───┘ (source on grandchild)      │
│                           (grandchild node)                                 │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Connection: Child.tpMetaParent[i] ──► Parent.tpMetaChildren[j]              │
│             (source)                  (destination)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ iterate_meta_parents():   Follows tpMetaParent → destinations               │
│ iterate_meta_children():  Follows tpMetaChildren → sources                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Our current traversal logic:**
- `iterate_meta_parents()` - follows `tpMetaParent` destinations (toward root)
- `iterate_meta_children()` - follows `tpMetaChildren` sources (toward leaves)

### Critical Comparison

| Aspect | Freeform | Our Implementation |
|--------|----------|-------------------|
| **Meta-to-Meta connection** | `child.message` → `parent.affectedBy[]` | `child.tpMetaParent[]` → `parent.tpMetaChildren[]` |
| **Scene-to-Meta connection** | `sceneObj.message` → `meta.affectedBy[]` | Uses `connect_to()` with custom attributes |
| **Root concept** | Explicit `Core` node (upstream end) | Any node without parents (`is_root()`) |
| **Traversal names** | upstream/downstream | meta_parents/meta_children |
| **Array used** | `affectedBy[]` (multi-purpose) | Separate `tpMetaParent[]` and `tpMetaChildren[]` |

### ⚠️ IMPORTANT: Connection Direction Difference

The **semantic meaning** of upstream/downstream is the same in both systems:
- **Upstream** = toward root
- **Downstream** = toward leaves/scene objects

**BUT the Maya connection direction is OPPOSITE:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FREEFORM: Child "points to" Parent                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Child MetaNode                    Parent MetaNode                         │
│   ┌─────────────┐                   ┌─────────────┐                         │
│   │             │                   │             │                         │
│   │   .message ─┼──────────────────►│ affectedBy[]│                         │
│   │   (source)  │                   │ (dest)      │                         │
│   └─────────────┘                   └─────────────┘                         │
│                                                                             │
│   To find parent: follow where my .message CONNECTS TO (destinations)      │
│   To find children: find nodes whose .message connects TO ME               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                     OURS: Child "points to" Parent (same direction!)        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Child MetaNode                    Parent MetaNode                         │
│   ┌─────────────┐                   ┌─────────────┐                         │
│   │             │                   │             │                         │
│   │ tpMetaParent├──────────────────►│tpMetaChildren                         │
│   │   (source)  │                   │ (dest)      │                         │
│   └─────────────┘                   └─────────────┘                         │
│                                                                             │
│   To find parent: follow where tpMetaParent CONNECTS TO (destinations)     │
│   To find children: find nodes whose tpMetaParent connects to MY Children  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Insight: Both systems have the child "pointing to" the parent!**
- Freeform: `child.message` → `parent.affectedBy[]`
- Ours: `child.tpMetaParent[]` → `parent.tpMetaChildren[]`

The connection SOURCE is always on the child, the DESTINATION is on the parent.
This means Maya's data flow goes Child → Parent (downstream in Maya terms).

**To traverse UPSTREAM (toward root):**
- Freeform: `listConnections(child.message)` → finds parent
- Ours: `tpMetaParent.destinations()` → finds parent

**To traverse DOWNSTREAM (toward children):**
- Freeform: find nodes connected TO `parent.affectedBy[]` (check their .message)
- Ours: `tpMetaChildren.sources()` → finds children directly

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONCLUSION                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ✅ UPSTREAM/DOWNSTREAM SEMANTICS ARE IDENTICAL IN BOTH SYSTEMS            │
│                                                                             │
│   • Upstream = toward root = our "iterate_meta_parents()"                   │
│   • Downstream = toward leaves = our "iterate_meta_children()"              │
│                                                                             │
│   The only difference is WHICH ATTRIBUTES are used:                         │
│   • Freeform: single "affectedBy[]" for everything                          │
│   • Ours: dedicated "tpMetaParent[]" and "tpMetaChildren[]"                 │
│                                                                             │
│   Our approach is BETTER because:                                           │
│   • Clear separation of parent/child relationships                          │
│   • No need to inspect node types to distinguish meta vs scene connections │
│   • Direct access to children (sources) vs Freeform's indirect approach     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Analysis: Which Approach is Correct?

**Both are valid but have different mental models:**

1. **Freeform (Data Flow Model):**
   - Thinks in terms of Maya's data flow direction
   - "Upstream" = against data flow = toward root
   - "Downstream" = with data flow = toward leaves
   - Single `affectedBy` attribute handles both meta-meta and scene-meta connections
   - Confusing: "downstream" points toward the Core's `message` connections, which could be scene objects OR child meta nodes

2. **Our Implementation (Hierarchy Model):**
   - Thinks in terms of parent/child relationships
   - Clear separation: `tpMetaParent` for parents, `tpMetaChildren` for children
   - No scene object connection point defined by default
   - More explicit but requires separate handling for scene connections

### Recommended Approach

**Keep our hierarchical model (parent/child) but add upstream/downstream as ALIASES that match Freeform's semantics for compatibility:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     RECOMMENDED UNIFIED MODEL                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                           ┌─────────────────┐                               │
│                           │   Root/Core     │                               │
│                           │   (no parent)   │                               │
│                           │                 │                               │
│                           │ tpMetaChildren[]│◄────────┐                     │
│                           └─────────────────┘         │                     │
│                                   ▲                   │                     │
│                                   │ UPSTREAM          │                     │
│                                   │ (toward root)     │                     │
│                                   │                   │                     │
│                           ┌───────┴─────────┐         │                     │
│                           │   MetaNode A    │         │                     │
│                           │                 │         │                     │
│                           │ tpMetaParent[] ─┼─────────┘                     │
│                           │ tpMetaChildren[]│◄────────┐                     │
│                           │ rootJoint ◄─────┼──┐      │  (named attrs)      │
│                           │ meshGroup ◄─────┼──┤      │                     │
│                           └─────────────────┘  │      │                     │
│                                   ▲            │      │                     │
│                                   │ UPSTREAM   │      │                     │
│                                   │            │      │                     │
│                           ┌───────┴─────────┐  │      │                     │
│                           │   MetaNode B    │  │      │                     │
│                           │                 │  │      │                     │
│                           │ tpMetaParent[] ─┼──┼──────┘                     │
│                           │ tpMetaChildren[]│  │                            │
│                           │ controls ◄──────┼──┤       (named attrs)        │
│                           └─────────────────┘  │                            │
│                                   ▲            │                            │
│                                   │ DOWNSTREAM │                            │
│                                   │ (toward    │                            │
│                                   │  leaves)   │                            │
│                           ┌───────┴─────────┐  │                            │
│                           │  Scene Objects  │  │                            │
│                           │  (joints, mesh) │  │                            │
│                           │                 │  │                            │
│                           │    .message ────┼──┘                            │
│                           └─────────────────┘                               │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ NAMED ATTRIBUTES for scene connections (NOT a generic array):              │
│   - connect_to("rootJoint", joint) → creates "rootJoint" message attr      │
│   - connect_to("meshGroup", grp)   → creates "meshGroup" message attr      │
│   - Semantic meaning preserved, easy to query specific connections          │
│                                                                             │
│ Connection patterns:                                                        │
│   Meta Parent-Child: child.tpMetaParent[i] → parent.tpMetaChildren[j]       │
│   Scene-to-Meta:     sceneObj.message → meta.namedAttribute                 │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ TRAVERSAL METHODS (new names as aliases):                                   │
│                                                                             │
│   get_upstream(type)     = iterate_meta_parents(type)   → toward root       │
│   get_downstream(type)   = iterate_meta_children(type)  → toward leaves     │
│   get_all_upstream(type) = meta_parents(recursive, type)                    │
│   get_all_downstream(type) = meta_children(type)                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Decisions

1. **Keep `tpMetaParent` and `tpMetaChildren`** - More explicit than single `affectedBy`
2. **Keep named attributes for scene connections** - Our `connect_to("attrName", node)` approach is better than a generic array because:
   - Named attributes provide semantic meaning (`rootJoint`, `meshes`, etc.)
   - You can still iterate all connections via `iterate_children()` or message destinations
   - No redundancy between generic array and named attributes
3. **Add `get_upstream`/`get_downstream` methods** - As aliases matching Freeform's semantics
4. **Upstream = toward root (parents)** - Consistent with Freeform
5. **Downstream = toward leaves (children/scene objects)** - Consistent with Freeform

> **Note**: We intentionally do NOT add a generic `tpConnections[]` attribute. Freeform uses
> `affectedBy[]` as a catch-all for both meta-to-meta and scene-to-meta connections, which
> loses semantic meaning. Our approach of named attributes (`connect_to("joints", node)`)
> combined with dedicated parent/child arrays is more explicit and maintainable.

---

## 1. Architecture Comparison

### 1.1 Current Implementation (base.py)

```
MetaRegistry (Singleton)
    └── Manages class registration
    
MetaFactory (metaclass)
    └── Enables automatic class instantiation from scene nodes
    
MetaBase (DGNode)
    └── Base class for all meta nodes
    └── Uses Maya API 2.0 (OpenMaya)
    └── Parent/Child hierarchy via message attributes
```

### 1.2 Freeform Implementation

```
Network_Registry / Property_Registry (Singletons)
    └── Separate registries for networks and properties
    
Network_Meta / Property_Meta (metaclasses)
    └── Auto-registration with _do_register flag
    └── Supports "hidden" (non-public) types
    
MetaNode (base)
    └── Core (root of graph)
        └── DependentNode (auto-creates parent dependencies)
            └── CharacterCore, RigCore, JointsCore, etc.
    
PropertyNode (MetaNode)
    └── Leaf nodes attached to scene objects
    └── ModelProperty, RigProperty, CommonProperty, etc.
```

---

## 2. Feature Comparison Matrix

| Feature | base.py | Freeform | Priority | Notes |
|---------|---------|----------|----------|-------|
| **Registry System** |
| Class registration | ✅ | ✅ | - | Both have this |
| Environment variable loading | ✅ | ❌ | - | We have this, they don't |
| Hidden/private types | ❌ | ✅ | Medium | Useful for internal classes |
| Separate property registry | ❌ | ✅ | High | Clean separation of concerns |
| `_do_register` flag | ❌ | ✅ | High | Control auto-registration |
| **Node Identification** |
| Class type attribute | ✅ | ✅ | - | `tpMetaClass` vs `meta_type` |
| Version attribute | ✅ | ✅ | - | Both have this |
| GUID attribute | ❌ | ✅ | High | Unique identification across scenes |
| **Data Access** |
| `data` property (dict of all attrs) | ❌ | ✅ | High | Very convenient |
| `get(attr_name)` with auto-create | ❌ | ✅ | High | Simplifies attribute access |
| `set(attr_name, value)` with auto-create | ❌ | ✅ | High | Simplifies attribute setting |
| Type dictionary (Python → Maya) | ❌ | ✅ | Medium | Auto type conversion |
| **Hierarchy/Traversal** |
| Parent/child connections | ✅ | ✅ | - | Both have this |
| `meta_parent()` / `meta_children()` | ✅ | ❌ | - | We have this |
| `get_upstream(type)` | ❌ | ✅ | High | Find first node of type upstream |
| `get_downstream(type)` | ❌ | ✅ | High | Find first node of type downstream |
| `get_all_upstream(type)` | ❌ | ✅ | High | Find all nodes of type upstream |
| `get_all_downstream(type)` | ❌ | ✅ | High | Find all nodes of type downstream |
| Depth limit traversal | ✅ | ❌ | - | We have this |
| Type filtering in traversal | ✅ | ✅ | - | Both have this |
| **Dependent Node Pattern** |
| `dependent_node` class attribute | ❌ | ✅ | High | Auto-create parent chain |
| Auto-create missing hierarchy | ❌ | ✅ | High | Ensures graph integrity |
| **Connection to Scene Objects** |
| Connect meta to scene nodes | ✅ | ✅ | - | Both have `connect_to` |
| `affectedBy` array attribute | ❌ | ✅ | Skip | We use named attrs instead (better) |
| `is_in_network()` check | ❌ | ✅ | Medium | Check if object has metadata |
| `get_network_entries()` | ❌ | ✅ | High | Get meta nodes from scene object |
| `get_connections()` | Partial | ✅ | Medium | Get all connected scene nodes |
| `disconnect_node()` / `disconnect_nodes()` | Partial | ✅ | Medium | Clean disconnection |
| **Property System** |
| Property base class | ❌ | ✅ | High | Leaf nodes for scene objects |
| `multi_allowed` flag | ❌ | ✅ | High | Single vs multiple properties |
| `auto_run` flag | ❌ | ✅ | Medium | Auto-execute on load |
| `priority` attribute | ❌ | ✅ | Medium | Execution ordering |
| `act()` method | ❌ | ✅ | High | Property action pattern |
| `on_add()` hook | ❌ | ✅ | High | Called when property added |
| `compare()` method | ❌ | ✅ | Medium | Compare property data |
| **Serialization** |
| `to_dict()` | ✅ | ❌ | - | We have this |
| `data` property | ❌ | ✅ | High | Get all user attrs as dict |
| `data_equals()` | ❌ | ✅ | Medium | Compare data dictionaries |
| `bake_to_object()` | ❌ | ✅ | Medium | Serialize to object attrs |
| `bake_to_connected()` | ❌ | ✅ | Medium | Serialize to connected objects |
| `load_properties_from_obj()` | ❌ | ✅ | Medium | Deserialize from object attrs |
| **Utility Methods** |
| `select()` | ❌ | ✅ | Low | Select node in Maya |
| `delete()` | ✅ | ✅ | - | Both have this |
| `delete_all()` | ❌ | ✅ | Medium | Delete node and all downstream |
| `exists()` check | ❌ | ✅ | Medium | Wrapper uses `isValid()` |
| Tag system | ✅ | Partial | - | We have dedicated tag attr |
| **Scene Utilities** |
| `iterate_scene_meta_nodes()` | ✅ | ❌ | - | We have this |
| `find_meta_nodes_by_class_type()` | ✅ | ✅ | - | Both have this |
| `find_meta_nodes_by_tag()` | ✅ | ❌ | - | We have this |
| `get_all_network_nodes(type)` | ❌ | ✅ | Medium | Get all nodes of type in scene |
| `get_network_core()` | ❌ | ✅ | Medium | Get/create root node |
| `delete_network()` | ❌ | ✅ | Medium | Delete entire network chain |

---

## 3. Implementation Plan

### Phase 1: Core Enhancements (High Priority) ✅ COMPLETED

#### 1.1 Add GUID Support ✅
- Added `META_GUID_ATTR_NAME = "tpMetaGuid"` constant in `constants.py`
- Added GUID to `meta_attributes()` - generated on creation using `uuid.uuid4()`
- Updated `__eq__` and `__hash__` to use GUID when available
- Added `guid()` method

#### 1.2 Add `data` Property and `get`/`set` Methods ✅
```python
@property
def data(self) -> dict[str, Any]:
    """Return all user-defined attributes as a dictionary."""
    
@data.setter
def data(self, values: dict[str, Any]):
    """Set multiple attributes from a dictionary."""
    
def get(self, attr_name: str, default: Any = None, auto_create: bool = False, attr_type: int | None = None) -> Any:
    """Get attribute value, optionally creating if missing."""
    
def set(self, attr_name: str, value: Any, attr_type: int | None = None, mod: OpenMaya.MDGModifier | None = None):
    """Set attribute value, creating if missing."""
```

#### 1.3 Add Type Mapping ✅
Created `constants.py` with:
```python
TYPE_TO_MAYA_ATTR: dict[type, int] = {
    str: attributetypes.kMFnDataString,
    int: attributetypes.kMFnNumericInt,
    float: attributetypes.kMFnNumericDouble,
    bool: attributetypes.kMFnNumericBoolean,
    list: attributetypes.kMFnNumeric3Double,
}
```

#### 1.4 Add Upstream/Downstream Traversal ✅
```python
def get_upstream(self, check_type: type[MetaBase] | str) -> MetaBase | None:
    """Find first meta node of type by traversing upstream (toward parents)."""
    
def get_downstream(self, check_type: type[MetaBase] | str) -> MetaBase | None:
    """Find first meta node of type by traversing downstream (toward children)."""
    
def get_all_upstream(self, check_type: type[MetaBase] | str | None = None) -> list[MetaBase]:
    """Find all meta nodes of type upstream."""
    
def get_all_downstream(self, check_type: type[MetaBase] | str | None = None) -> list[MetaBase]:
    """Find all meta nodes of type downstream."""
```

#### 1.5 Add `_do_register` Flag ✅
- Added class attribute `_do_register: bool = True` to `MetaBase`
- Modified `MetaRegistry.register_meta_class()` to check this flag
- Added `_HIDDEN` cache to `MetaRegistry`
- Added `get_hidden()` and `hidden_types()` methods to `MetaRegistry`

### Phase 2: Property System (High Priority) ✅ COMPLETED

#### 2.1 Create PropertyRegistry ✅
```python
class PropertyRegistry(metaclass=Singleton):
    """Separate registry for property-type meta nodes."""
    _CACHE: dict[str, type[MetaProperty]] = {}
    _HIDDEN: dict[str, type[MetaProperty]] = {}
```

#### 2.2 Create MetaProperty Base Class ✅
```python
class MetaProperty(MetaBase):
    """Base class for property nodes that attach to scene objects.
    
    Properties are leaf nodes in the metadata graph that store
    data about specific scene objects.
    """
    _do_register: bool = False
    multi_allowed: bool = False
    auto_run: bool = False
    priority: int = 0
    
    def act(self, *args, **kwargs) -> Any:
        """Perform the property's action. Override in subclasses."""
        
    def on_add(self, obj: DGNode | DagNode, **kwargs):
        """Called when property is added to an object. Override in subclasses."""
        
    def compare(self, data: dict[str, Any]) -> bool:
        """Compare property data with given dictionary."""
```

#### 2.3 Add Property Utilities ✅
```python
def get_properties(node: DGNode) -> list[MetaProperty]:
    """Get all properties attached to a scene node."""
    
def get_property(node: DGNode, property_type: type[MetaProperty]) -> MetaProperty | None:
    """Get first property of type attached to node."""
    
def add_property(node: DGNode, property_type: type[MetaProperty], **kwargs) -> MetaProperty | None:
    """Add a property to a scene node."""
    
def get_properties_dict(node: DGNode) -> dict[type, list[MetaProperty]]:
    """Get all properties grouped by type."""

# Additional utilities implemented:
def remove_property(node, property_type=None, mod=None) -> bool:
    """Remove properties from a scene node."""

def run_properties(node, property_type=None, *args, **kwargs) -> list[Any]:
    """Run the act() method on properties attached to a node."""

def iterate_scene_properties(property_type=None) -> list[MetaProperty]:
    """Iterate all properties in the scene."""
```

### Phase 3: Dependent Node Pattern (High Priority) ✅ COMPLETED

#### 3.1 Create DependentMeta Base Class ✅
```python
class DependentMeta(MetaBase):
    """Meta node that requires a parent meta node to exist.
    
    If the parent doesn't exist, it will be auto-created.
    """
    dependent_node: type[MetaBase] | None = None
    auto_create_parent: bool = True
    
    def __init__(self, parent: MetaBase | None = None, ...):
        # Auto-create dependency chain if needed
        
    def get_dependency_parent(self) -> MetaBase | None:
        """Get the parent that satisfies the dependency requirement."""
        
    def ensure_dependency_chain(self, mod=None) -> bool:
        """Ensure the entire dependency chain is satisfied."""
        
    @classmethod
    def get_dependency_chain(cls) -> list[type[MetaBase]]:
        """Get the full dependency chain for this class."""

# Utility functions:
def create_dependency_chain(leaf_type, mod=None, **kwargs) -> DependentMeta:
    """Create a complete dependency chain ending with the specified type."""

def get_or_create_parent(node, parent_type=None, mod=None) -> MetaBase | None:
    """Get or create a parent node for the given dependent node."""
```

### Phase 4: Connection Improvements (Medium Priority) ✅ COMPLETED

#### 4.1 Enhance Scene Object Connection Methods ✅
```python
def connect_node(self, node: DGNode | DagNode, attribute_name: str):
    """Connect a scene node to this meta node via a named attribute.
    
    This is an alias for connect_to() with clearer semantics.
    """
    
def disconnect_node(self, node: DGNode | DagNode, attribute_name: str | None = None):
    """Disconnect a scene node from this meta node.
    
    If attribute_name is None, disconnects from all attributes.
    """
    
def get_connected_nodes(self, attribute_name: str | None = None) -> list[DGNode]:
    """Get scene nodes connected to this meta node.
    
    If attribute_name is given, returns only nodes connected to that attr.
    If None, returns all non-meta connected nodes.
    """
```

#### 4.2 Add Network Entry Points ✅
```python
def is_in_network(node: DGNode) -> bool:
    """Check if a scene node is connected to any meta network."""
    
def get_network_entries(node: DGNode, network_type: type[MetaBase] | None = None) -> list[MetaBase]:
    """Get all meta nodes connected to a scene node."""
```

### Phase 5: Serialization Enhancements (Medium Priority) ✅ COMPLETED

#### 5.1 Add Bake/Load Methods ✅
```python
def bake_to_object(self, obj: DGNode | DagNode, prefix: str = "meta_", include_class_info: bool = True):
    """Serialize meta node data as attributes on scene object."""
    
def bake_to_connected(self, prefix: str = "meta_"):
    """Bake data to all connected scene objects."""
    
@classmethod
def load_from_object(cls, obj: DGNode | DagNode, prefix: str = "meta_", create_if_missing: bool = True) -> MetaBase | None:
    """Reconstruct meta node from baked attributes on object."""
```

#### 5.2 Add Data Comparison ✅
```python
def data_equals(self, other_data: dict[str, Any]) -> bool:
    """Compare this node's data with a dictionary."""
```

### Phase 6: Utility Enhancements (Low-Medium Priority) ✅ COMPLETED

#### 6.1 Add Utility Methods ✅
```python
def select(self, add: bool = False, replace: bool = True):
    """Select this node in Maya."""
    
def delete_all(self, mod: OpenMaya.MDGModifier | None = None) -> bool:
    """Delete this node and all downstream meta nodes."""
    
def exists(self) -> bool:
    """Check if the underlying Maya node still exists."""
    # Note: Inherited from DGNode base class
```

#### 6.2 Add Scene Utilities ✅
```python
def delete_network(root: MetaBase, mod=None) -> bool:
    """Delete an entire meta network starting from root."""
    
def get_all_meta_nodes_of_type(meta_type: type[MetaBase]) -> list[MetaBase]:
    """Get all meta nodes of a specific type in the scene."""
```

---

## 4. File Structure (Confirmed)

```
tp/libs/maya/meta/
├── __init__.py             # Package exports
├── base.py                 # Core MetaBase, MetaRegistry, MetaFactory (existing)
├── properties.py           # MetaProperty, PropertyRegistry, PropertyFactory (NEW)
├── dependent.py            # DependentMeta base class (NEW)
├── utils.py                # Scene utilities, network helpers, connection utils (NEW)
├── constants.py            # Attribute names, type mappings (NEW)
└── README.md               # Documentation
```

### File Responsibilities:

#### `constants.py`
- All attribute name constants (`META_CLASS_ATTR_NAME`, etc.)
- Type mapping dictionary (`TYPE_TO_MAYA_ATTR`)
- Move existing constants from `base.py` here

#### `base.py` (refactored)
- `MetaRegistry` - Class registration singleton
- `MetaFactory` - Metaclass for automatic instantiation
- `MetaBase` - Core base class for all meta nodes
- Imports constants from `constants.py`

#### `properties.py`
- `PropertyRegistry` - Separate registry for properties
- `PropertyFactory` - Metaclass for properties
- `MetaProperty` - Base class for property nodes
- Property-specific utilities

#### `dependent.py`
- `DependentMeta` - Base class for nodes that auto-create parents
- Dependency chain creation logic

#### `utils.py`
- `is_in_network()` - Check if node has metadata
- `get_network_entries()` - Get meta nodes from scene object
- `get_network_root()` - Find/create root node
- `delete_network()` - Delete network chain
- `get_all_meta_nodes_of_type()` - Scene queries
- Bake/load utilities

---

## 5. Backwards Compatibility Considerations

1. **Existing meta nodes**: Must still work with nodes created before GUID was added
2. **Attribute names**: Keep `tpMetaClass`, `tpMetaVersion`, etc.
3. **Method signatures**: Don't change existing method signatures
4. **New methods only**: Add new functionality without breaking existing code

---

## 6. Testing Requirements

### Unit Tests Needed:
1. GUID generation and persistence
2. `data` property get/set
3. `get()`/`set()` with auto-create
4. Upstream/downstream traversal
5. Property registration and instantiation
6. `multi_allowed` enforcement
7. Dependent node auto-creation
8. Bake/load serialization
9. `delete_all()` cascade deletion

### Integration Tests:
1. Complex hierarchy creation and traversal
2. Property attachment to scene objects
3. Scene save/load with meta networks
4. Reference handling

---

## 7. Implementation Order

1. **Week 1**: Phase 1 (Core Enhancements)
   - GUID support
   - `data` property and `get`/`set`
   - Type mapping
   - Upstream/downstream traversal

2. **Week 2**: Phase 2 & 3 (Property System + Dependent Nodes)
   - PropertyRegistry
   - MetaProperty base class
   - DependentMeta base class
   - Property utilities

3. **Week 3**: Phase 4 & 5 (Connections + Serialization)
   - Enhanced connection methods (connect_node, disconnect_node, get_connected_nodes)
   - Network entry points
   - Bake/load methods

4. **Week 4**: Phase 6 + Testing + Documentation
   - Utility methods
   - Comprehensive testing
   - Update README.md

---

## 8. Resolved Design Decisions

### ✅ Decision 1: Multiple files for better organization
**Resolution**: Split into multiple files:
- `base.py` - Core MetaBase, MetaRegistry, MetaFactory
- `properties.py` - MetaProperty, PropertyRegistry
- `dependent.py` - DependentMeta base class
- `utils.py` - Scene utilities, connection helpers
- `constants.py` - Attribute names, type mappings

### ✅ Decision 2: Keep OpenMaya 2.0
**Resolution**: Continue using OpenMaya 2.0 for performance. No PyMEL.

### ✅ Decision 3: Flexible root approach
**Resolution**: Keep our flexible approach - any node without parents is a root.
- Do NOT enforce a single "Core" node pattern
- Users can create their own root structures as needed
- Add optional utility to find/create a default root if desired

### ✅ Decision 4: Separate MetaProperty class
**Resolution**: Create a separate `MetaProperty` base class:
- Properties are leaf nodes attached to scene objects
- Has special behavior (multi_allowed, act(), on_add(), etc.)
- Separate PropertyRegistry for clean organization
- MetaProperty inherits from MetaBase

### ✅ Decision 5: Naming conventions
**Resolution**: 
- Keep `tp` prefix for attributes (`tpMetaClass`, `tpMetaVersion`, etc.)
- Use snake_case for method names (`get_upstream`, `meta_children`)
- Keep existing method names, add new ones alongside
