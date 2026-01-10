"""Maya Metadata Network System.

This package provides a framework for creating and managing metadata networks
in Maya. It allows attaching Python class information to network nodes,
enabling reconstruction of complex data structures from scene data.

Example:
    >>> from tp.libs.maya.meta import MetaBase, MetaRegistry
    >>>
    >>> class MyMeta(MetaBase):
    ...     ID = "myMeta"
    ...     VERSION = "1.0.0"
    ...
    >>> # Create a new meta node
    >>> node = MyMeta(name="my_meta_node")
    >>>
    >>> # Find existing meta nodes
    >>> from tp.libs.maya.meta import find_meta_nodes_by_class_type
    >>> nodes = find_meta_nodes_by_class_type(MyMeta)

Property System Example:
    >>> from tp.libs.maya.meta import MetaProperty, add_property
    >>>
    >>> class RigProperty(MetaProperty):
    ...     ID = "rigProperty"
    ...     multi_allowed = False
    ...
    ...     def act(self, *args, **kwargs):
    ...         return self.get("rigType")
    >>>
    >>> # Add property to a scene object
    >>> prop = add_property(my_joint, RigProperty, rigType="FK")
"""

from .base import (
    MetaBase,
    MetaFactory,
    MetaRegistry,
    connected_meta_nodes,
    create_meta_node_by_type,
    delete_network,
    find_meta_nodes_by_class_type,
    find_meta_nodes_by_tag,
    get_all_meta_nodes_of_type,
    get_network_entries,
    is_in_network,
    is_meta_node,
    is_meta_node_of_types,
    iterate_scene_meta_nodes,
)
from .constants import (
    MAYA_ATTR_TO_TYPE,
    META_CHILDREN_ATTR_NAME,
    META_CLASS_ATTR_NAME,
    META_GUID_ATTR_NAME,
    META_PARENT_ATTR_NAME,
    META_TAG_ATTR_NAME,
    META_VERSION_ATTR_NAME,
    RESERVED_ATTR_NAMES,
    TYPE_TO_MAYA_ATTR,
)
from .dependent import (
    DependentMeta,
    create_dependency_chain,
    get_or_create_parent,
)
from .properties import (
    MetaProperty,
    PropertyFactory,
    PropertyRegistry,
    add_property,
    get_properties,
    get_properties_by_type,
    get_properties_dict,
    get_property,
    iterate_scene_properties,
    remove_property,
    run_properties,
)

__all__ = [
    # Constants
    "META_CLASS_ATTR_NAME",
    "META_VERSION_ATTR_NAME",
    "META_PARENT_ATTR_NAME",
    "META_CHILDREN_ATTR_NAME",
    "META_TAG_ATTR_NAME",
    "META_GUID_ATTR_NAME",
    "TYPE_TO_MAYA_ATTR",
    "MAYA_ATTR_TO_TYPE",
    "RESERVED_ATTR_NAMES",
    # Core Classes
    "MetaRegistry",
    "MetaFactory",
    "MetaBase",
    # Dependent Classes
    "DependentMeta",
    # Property Classes
    "PropertyRegistry",
    "PropertyFactory",
    "MetaProperty",
    # Core Functions
    "iterate_scene_meta_nodes",
    "find_meta_nodes_by_class_type",
    "find_meta_nodes_by_tag",
    "is_meta_node",
    "is_meta_node_of_types",
    "is_in_network",
    "create_meta_node_by_type",
    "connected_meta_nodes",
    "get_network_entries",
    "get_all_meta_nodes_of_type",
    "delete_network",
    # Dependent Functions
    "create_dependency_chain",
    "get_or_create_parent",
    # Property Functions
    "get_properties",
    "get_property",
    "get_properties_by_type",
    "get_properties_dict",
    "add_property",
    "remove_property",
    "run_properties",
    "iterate_scene_properties",
]
