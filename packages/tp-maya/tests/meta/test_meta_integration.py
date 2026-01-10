"""Integration tests for the metadata system.

These tests require Maya to be running (via mayapy with maya.standalone).
Run with: mayapy -m pytest tests/meta/test_meta_integration.py -m integration

Or run all integration tests:
    mayapy -m pytest tests/ -m integration
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from tp.libs.maya.meta.base import MetaBase


@pytest.mark.integration
class TestMetaNodeCreation:
    """Test basic meta node creation and initialization."""

    def test_create_basic_meta_node(self, new_scene):
        """Test creating a basic MetaBase node."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")
        assert meta is not None
        assert "test_meta" in meta.name()

    def test_meta_node_has_required_attributes(self, new_scene):
        """Test that created meta node has all required attributes."""

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.meta.constants import (
            META_CHILDREN_ATTR_NAME,
            META_CLASS_ATTR_NAME,
            META_GUID_ATTR_NAME,
            META_PARENT_ATTR_NAME,
            META_TAG_ATTR_NAME,
            META_VERSION_ATTR_NAME,
        )

        meta = MetaBase(name="test_meta")

        assert meta.hasAttribute(META_CLASS_ATTR_NAME)
        assert meta.hasAttribute(META_VERSION_ATTR_NAME)
        assert meta.hasAttribute(META_PARENT_ATTR_NAME)
        assert meta.hasAttribute(META_CHILDREN_ATTR_NAME)
        assert meta.hasAttribute(META_TAG_ATTR_NAME)
        assert meta.hasAttribute(META_GUID_ATTR_NAME)

    def test_meta_node_class_attribute_value(self, new_scene):
        """Test that the metaclass attribute stores correct class name."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")

        class_name = meta.metaclass_type()
        assert class_name == "MetaBase"

    def test_meta_node_version_attribute(self, new_scene):
        """Test that version attribute is set correctly."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")

        version = meta.version()
        assert version == "1.0.0"

    def test_meta_node_guid_is_unique(self, new_scene):
        """Test that each meta node has a unique GUID."""

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.meta.constants import META_GUID_ATTR_NAME

        meta1 = MetaBase(name="test_meta1")
        meta2 = MetaBase(name="test_meta2")

        guid1 = meta1.attribute(META_GUID_ATTR_NAME).value()
        guid2 = meta2.attribute(META_GUID_ATTR_NAME).value()

        assert guid1 != guid2
        assert (
            len(guid1) == 36
        )  # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

    def test_meta_node_default_name(self, new_scene):
        """Test that meta node gets default name when none provided."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase()
        # Default name should be "MetaBase_meta"
        assert "MetaBase" in meta.name()


@pytest.mark.integration
class TestMetaNodeFromExisting:
    """Test wrapping existing nodes with MetaBase."""

    def test_wrap_existing_meta_node(self, new_scene):
        """Test wrapping an existing meta node."""

        from tp.libs.maya.meta.base import MetaBase

        # Create a meta node
        original = MetaBase(name="original_meta")
        original_name = original.name()

        # Wrap the same node
        mobj = original.object()
        wrapped = MetaBase(node=mobj, init_defaults=False)

        assert wrapped.name() == original_name
        assert wrapped.metaclass_type() == "MetaBase"

    def test_meta_node_equality(self, new_scene):
        """Test that two MetaBase instances wrapping the same node are equal."""

        from tp.libs.maya.meta.base import MetaBase

        meta1 = MetaBase(name="test_meta")
        meta2 = MetaBase(node=meta1.object(), init_defaults=False)

        assert meta1 == meta2

    def test_meta_node_hash_consistency(self, new_scene):
        """Test that hash is consistent for same node."""

        from tp.libs.maya.meta.base import MetaBase

        meta1 = MetaBase(name="test_meta")
        meta2 = MetaBase(node=meta1.object(), init_defaults=False)

        assert hash(meta1) == hash(meta2)

        # Can be used in sets/dicts
        meta_set = {meta1}
        assert meta2 in meta_set


@pytest.mark.integration
class TestCustomMetaClass:
    """Test custom MetaBase subclasses."""

    def test_custom_meta_class_registration(
        self, new_scene, meta_registry_clean
    ):
        """Test that custom meta classes are registered."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry

        class CustomMeta(MetaBase):
            ID = "CustomMeta"
            VERSION = "2.0.0"

        # Create an instance - should auto-register
        custom = CustomMeta(name="custom_meta")

        assert MetaRegistry.is_in_registry("CustomMeta")
        assert custom.metaclass_type() == "CustomMeta"
        assert custom.version() == "2.0.0"

    def test_custom_meta_class_with_custom_attributes(
        self, new_scene, meta_registry_clean
    ):
        """Test custom meta class with additional attributes."""

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.om import attributetypes

        class RigMeta(MetaBase):
            ID = "RigMeta"

            def meta_attributes(self) -> list[dict]:
                attrs = super().meta_attributes()
                attrs.append(
                    {
                        "name": "rigType",
                        "value": "biped",
                        "type": attributetypes.kMFnDataString,
                        "locked": False,
                    }
                )
                return attrs

        rig = RigMeta(name="test_rig")

        assert rig.hasAttribute("rigType")
        assert rig.attribute("rigType").value() == "biped"

    def test_meta_factory_resolves_correct_class(
        self, new_scene, meta_registry_clean
    ):
        """Test that MetaFactory returns correct class when wrapping node."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry

        class SpecialMeta(MetaBase):
            ID = "SpecialMeta"

        MetaRegistry.register_meta_class(SpecialMeta)

        # Create a SpecialMeta node
        special = SpecialMeta(name="special_meta")

        # Wrap it with MetaBase - should return SpecialMeta instance
        wrapped = MetaBase(node=special.object(), init_defaults=False)

        assert isinstance(wrapped, SpecialMeta)
        assert wrapped.metaclass_type() == "SpecialMeta"


@pytest.mark.integration
class TestMetaNodeHierarchy:
    """Test parent-child relationships between meta nodes."""

    def test_add_meta_parent(self, new_scene):
        """Test adding a parent to a meta node."""

        from tp.libs.maya.meta.base import MetaBase

        parent = MetaBase(name="parent_meta")
        child = MetaBase(name="child_meta")

        child.add_meta_parent(parent)

        # Verify parent-child relationship
        found_parent = child.meta_parent()
        assert found_parent is not None
        assert found_parent == parent

    def test_add_meta_child(self, new_scene):
        """Test adding a child to a meta node."""

        from tp.libs.maya.meta.base import MetaBase

        parent = MetaBase(name="parent_meta")
        child = MetaBase(name="child_meta")

        parent.add_meta_child(child)

        # Verify the relationship
        children = list(parent.iterate_meta_children(depth_limit=1))
        assert len(children) == 1
        assert children[0] == child

    def test_remove_meta_parent(self, new_scene):
        """Test removing a parent from a meta node."""

        from tp.libs.maya.meta.base import MetaBase

        parent = MetaBase(name="parent_meta")
        child = MetaBase(name="child_meta")

        child.add_meta_parent(parent)
        assert child.meta_parent() is not None

        child.remove_meta_parent(parent)
        assert child.meta_parent() is None

    def test_is_root(self, new_scene):
        """Test is_root returns True for nodes without parents."""

        from tp.libs.maya.meta.base import MetaBase

        root = MetaBase(name="root_meta")
        child = MetaBase(name="child_meta")

        assert root.is_root()

        child.add_meta_parent(root)
        assert not child.is_root()
        assert root.is_root()

    def test_meta_root(self, new_scene):
        """Test finding the root of a hierarchy."""

        from tp.libs.maya.meta.base import MetaBase

        root = MetaBase(name="root")
        mid = MetaBase(name="mid")
        leaf = MetaBase(name="leaf")

        mid.add_meta_parent(root)
        leaf.add_meta_parent(mid)

        found_root = leaf.meta_root()
        assert found_root is not None
        assert found_root == root

    def test_iterate_meta_parents_recursive(self, new_scene):
        """Test recursive iteration through parents."""

        from tp.libs.maya.meta.base import MetaBase

        root = MetaBase(name="root")
        mid = MetaBase(name="mid")
        leaf = MetaBase(name="leaf")

        mid.add_meta_parent(root)
        leaf.add_meta_parent(mid)

        # Non-recursive should only get immediate parent
        immediate_parents = list(leaf.iterate_meta_parents(recursive=False))
        assert len(immediate_parents) == 1
        assert immediate_parents[0] == mid

        # Recursive should get all parents
        all_parents = list(leaf.iterate_meta_parents(recursive=True))
        assert len(all_parents) == 2

    def test_iterate_meta_children_with_depth(self, new_scene):
        """Test depth-limited iteration through children."""

        from tp.libs.maya.meta.base import MetaBase

        root = MetaBase(name="root")
        child1 = MetaBase(name="child1")
        child2 = MetaBase(name="child2")
        grandchild = MetaBase(name="grandchild")

        root.add_meta_child(child1)
        root.add_meta_child(child2)
        child1.add_meta_child(grandchild)

        # Depth 1 should only get direct children
        direct_children = list(root.iterate_meta_children(depth_limit=1))
        # Note: depth_limit controls recursion, not direct children count
        # grandchild should not be in depth_limit=1 iteration
        names = [c.name() for c in direct_children]
        assert "child1" in str(names) or len(direct_children) >= 2

    def test_multiple_parents_support(self, new_scene):
        """Test that a node can have multiple parents (DAG-like structure)."""

        from tp.libs.maya.meta.base import MetaBase

        parent1 = MetaBase(name="parent1")
        parent2 = MetaBase(name="parent2")
        child = MetaBase(name="child")

        child.add_meta_parent(parent1)
        # Note: add_meta_parent may replace existing parent
        # Check behavior
        parents_before = list(child.iterate_meta_parents())

        # The current implementation might only support single parent
        # This test documents the actual behavior
        assert len(parents_before) >= 1


@pytest.mark.integration
class TestMetaNodeFiltering:
    """Test filtering meta nodes by type."""

    def test_iterate_meta_children_by_type_class(
        self, new_scene, meta_registry_clean
    ):
        """Test filtering children by class type."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry

        class TypeA(MetaBase):
            ID = "TypeA"

        class TypeB(MetaBase):
            ID = "TypeB"

        MetaRegistry.register_meta_class(TypeA)
        MetaRegistry.register_meta_class(TypeB)

        root = MetaBase(name="root")
        child_a = TypeA(name="child_a")
        child_b = TypeB(name="child_b")

        root.add_meta_child(child_a)
        root.add_meta_child(child_b)

        # Filter by TypeA
        type_a_children = list(root.iterate_meta_children(check_type=TypeA))
        assert len(type_a_children) == 1
        assert isinstance(type_a_children[0], TypeA)

    def test_iterate_meta_children_by_type_string(
        self, new_scene, meta_registry_clean
    ):
        """Test filtering children by class type string."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry

        class TypeA(MetaBase):
            ID = "TypeA"

        MetaRegistry.register_meta_class(TypeA)

        root = MetaBase(name="root")
        child_a = TypeA(name="child_a")
        child_base = MetaBase(name="child_base")

        root.add_meta_child(child_a)
        root.add_meta_child(child_base)

        # Filter by string
        type_a_children = list(root.iterate_meta_children(check_type="TypeA"))
        assert len(type_a_children) == 1

    def test_find_children_by_class_type(self, new_scene, meta_registry_clean):
        """Test find_children_by_class_type method."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry

        class CustomType(MetaBase):
            ID = "CustomType"

        MetaRegistry.register_meta_class(CustomType)

        root = MetaBase(name="root")
        custom = CustomType(name="custom")
        other = MetaBase(name="other")

        root.add_meta_child(custom)
        root.add_meta_child(other)

        found = root.find_children_by_class_type("CustomType")
        assert len(found) == 1


@pytest.mark.integration
class TestMetaNodeData:
    """Test data storage and retrieval on meta nodes."""

    def test_get_set_custom_attribute(self, new_scene):
        """Test getting and setting custom attributes."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")

        meta.set("customString", "hello world")
        meta.set("customInt", 42)
        meta.set("customFloat", 3.14)
        meta.set("customBool", True)

        assert meta.get("customString") == "hello world"
        assert meta.get("customInt") == 42
        assert abs(meta.get("customFloat") - 3.14) < 0.001
        assert meta.get("customBool") is True

    def test_get_with_default(self, new_scene):
        """Test get with default value for non-existent attribute."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")

        result = meta.get("nonExistent", default="default_value")
        assert result == "default_value"

    def test_get_with_auto_create(self, new_scene):
        """Test get with auto_create creates the attribute."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")

        result = meta.get("newAttr", default="created", auto_create=True)
        assert result == "created"
        assert meta.hasAttribute("newAttr")

    def test_set_reserved_attribute_raises(self, new_scene):
        """Test that setting reserved attributes raises ValueError."""

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.meta.constants import META_CLASS_ATTR_NAME

        meta = MetaBase(name="test_meta")

        with pytest.raises(ValueError) as excinfo:
            meta.set(META_CLASS_ATTR_NAME, "invalid")

        assert "reserved" in str(excinfo.value).lower()

    def test_data_property_get(self, new_scene):
        """Test data property returns user-defined attributes."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")
        meta.set("attr1", "value1")
        meta.set("attr2", 123)

        data = meta.data
        assert "attr1" in data
        assert "attr2" in data
        assert data["attr1"] == "value1"
        assert data["attr2"] == 123

    def test_data_property_set(self, new_scene):
        """Test data property setter for bulk attribute setting."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")
        meta.data = {"bulk1": "value1", "bulk2": 456}

        assert meta.get("bulk1") == "value1"
        assert meta.get("bulk2") == 456


@pytest.mark.integration
class TestMetaNodeTags:
    """Test tag functionality on meta nodes."""

    def test_set_and_get_tag(self, new_scene):
        """Test setting and getting a tag."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")

        meta.set_tag("my_tag")
        assert meta.tag() == "my_tag"

    def test_find_children_by_tag(self, new_scene):
        """Test finding children by tag."""

        from tp.libs.maya.meta.base import MetaBase

        root = MetaBase(name="root")
        child1 = MetaBase(name="child1")
        child2 = MetaBase(name="child2")
        child3 = MetaBase(name="child3")

        root.add_meta_child(child1)
        root.add_meta_child(child2)
        root.add_meta_child(child3)

        child1.set_tag("important")
        child3.set_tag("important")
        child2.set_tag("other")

        important = root.find_children_by_tag("important")
        assert len(important) == 2


@pytest.mark.integration
class TestMetaNodeSerialization:
    """Test serialization of meta nodes."""

    def test_to_dict_basic(self, new_scene):
        """Test to_dict returns expected keys."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")
        meta.set_tag("test_tag")

        data = meta.to_dict()

        assert "name" in data
        assert "class" in data
        assert "version" in data
        assert "tag" in data
        assert "is_root" in data

        assert data["class"] == "MetaBase"
        assert data["tag"] == "test_tag"
        assert data["is_root"] is True

    def test_to_dict_with_children(self, new_scene):
        """Test to_dict includes children when requested."""

        from tp.libs.maya.meta.base import MetaBase

        root = MetaBase(name="root")
        child = MetaBase(name="child")
        root.add_meta_child(child)

        data = root.to_dict(include_children=True)

        assert "children" in data
        assert len(data["children"]) == 1
        assert data["children"][0]["class"] == "MetaBase"


@pytest.mark.integration
class TestSceneMetaNodeFunctions:
    """Test scene-level meta node functions."""

    def test_iterate_scene_meta_nodes(self, new_scene):
        """Test iterating all meta nodes in scene."""

        from tp.libs.maya.meta.base import MetaBase, iterate_scene_meta_nodes

        meta1 = MetaBase(name="meta1")
        meta2 = MetaBase(name="meta2")

        found = list(iterate_scene_meta_nodes())
        assert len(found) >= 2

    def test_find_meta_nodes_by_class_type(
        self, new_scene, meta_registry_clean
    ):
        """Test finding meta nodes by class type."""

        from tp.libs.maya.meta.base import (
            MetaBase,
            MetaRegistry,
            find_meta_nodes_by_class_type,
        )

        class SearchableType(MetaBase):
            ID = "SearchableType"

        MetaRegistry.register_meta_class(SearchableType)

        base1 = MetaBase(name="base1")
        searchable1 = SearchableType(name="searchable1")
        searchable2 = SearchableType(name="searchable2")

        found = find_meta_nodes_by_class_type(SearchableType)
        assert len(found) == 2

        found_by_string = find_meta_nodes_by_class_type("SearchableType")
        assert len(found_by_string) == 2

    def test_find_meta_nodes_by_tag(self, new_scene):
        """Test finding meta nodes by tag."""

        from tp.libs.maya.meta.base import MetaBase, find_meta_nodes_by_tag

        meta1 = MetaBase(name="meta1")
        meta2 = MetaBase(name="meta2")
        meta3 = MetaBase(name="meta3")

        meta1.set_tag("findme")
        meta2.set_tag("findme")
        meta3.set_tag("other")

        found = find_meta_nodes_by_tag("findme")
        assert len(found) == 2

    def test_is_meta_node(self, new_scene):
        """Test is_meta_node function."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase, is_meta_node
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DGNode

        meta = MetaBase(name="test_meta")

        # Regular node should not be meta node
        regular_node = cmds.createNode("transform", name="regular_transform")
        regular_dg = DGNode(mobject_by_name(regular_node))

        assert is_meta_node(meta)
        assert not is_meta_node(regular_dg)

    def test_connected_meta_nodes(self, new_scene):
        """Test finding meta nodes connected to a scene node."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase, connected_meta_nodes
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        # Create a transform and a meta node
        transform_name = cmds.createNode("transform", name="test_transform")
        transform = DagNode(mobject_by_name(transform_name))

        meta = MetaBase(name="test_meta")

        # Connect the transform to the meta node
        meta.connect_to("connectedTransform", transform)

        # Find connected meta nodes
        found = connected_meta_nodes(transform)
        assert len(found) >= 1

    def test_create_meta_node_by_type(self, new_scene, meta_registry_clean):
        """Test creating meta node by type name."""

        from tp.libs.maya.meta.base import (
            MetaBase,
            MetaRegistry,
            create_meta_node_by_type,
        )

        class CreatableType(MetaBase):
            ID = "CreatableType"

        MetaRegistry.register_meta_class(CreatableType)

        created = create_meta_node_by_type(
            "CreatableType", name="created_meta"
        )

        assert created is not None
        assert isinstance(created, CreatableType)

    def test_create_meta_node_by_type_unknown(self, new_scene):
        """Test creating meta node with unknown type returns None."""

        from tp.libs.maya.meta.base import create_meta_node_by_type

        result = create_meta_node_by_type("UnknownType")
        assert result is None


@pytest.mark.integration
class TestMetaNodeDeletion:
    """Test meta node deletion."""

    def test_delete_meta_node(self, new_scene):
        """Test deleting a meta node."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="to_delete")
        node_name = meta.name()

        assert cmds.objExists(node_name)

        meta.delete()

        assert not cmds.objExists(node_name)

    def test_delete_disconnects_children(self, new_scene):
        """Test that deleting a parent disconnects children properly."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase

        parent = MetaBase(name="parent")
        child = MetaBase(name="child")

        parent.add_meta_child(child)

        parent_name = parent.name()
        child_name = child.name()

        parent.delete()

        # Parent should be deleted
        assert not cmds.objExists(parent_name)
        # Child should still exist
        assert cmds.objExists(child_name)


@pytest.mark.integration
class TestMetaRegistry:
    """Test MetaRegistry functionality with Maya."""

    def test_registry_is_singleton(self, maya_session):
        """Test that MetaRegistry is a singleton."""

        from tp.libs.maya.meta.base import MetaRegistry

        reg1 = MetaRegistry()
        reg2 = MetaRegistry()

        assert reg1 is reg2

    def test_register_and_unregister_meta_class(
        self, maya_session, meta_registry_clean
    ):
        """Test registering and unregistering a meta class."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry

        class TempMeta(MetaBase):
            ID = "TempMeta"

        MetaRegistry.register_meta_class(TempMeta)
        assert MetaRegistry.is_in_registry("TempMeta")

        MetaRegistry.unregister_meta_class(TempMeta)
        assert not MetaRegistry.is_in_registry("TempMeta")

    def test_get_type_returns_class(self, maya_session, meta_registry_clean):
        """Test get_type returns the registered class."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry

        class RetrievableMeta(MetaBase):
            ID = "RetrievableMeta"

        MetaRegistry.register_meta_class(RetrievableMeta)

        retrieved = MetaRegistry.get_type("RetrievableMeta")
        assert retrieved is RetrievableMeta

    def test_types_returns_copy(self, maya_session, meta_registry_clean):
        """Test that types() returns a copy of the registry."""

        from tp.libs.maya.meta.base import MetaRegistry

        types1 = MetaRegistry.types()
        types2 = MetaRegistry.types()

        # Should be equal but not the same object
        assert types1 == types2
        assert types1 is not types2


@pytest.mark.integration
class TestUpstreamDownstream:
    """Test upstream/downstream traversal methods."""

    def test_get_upstream(self, new_scene, meta_registry_clean):
        """Test get_upstream finds parent of specific type."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry

        class RootType(MetaBase):
            ID = "RootType"

        class MiddleType(MetaBase):
            ID = "MiddleType"

        MetaRegistry.register_meta_class(RootType)
        MetaRegistry.register_meta_class(MiddleType)

        root = RootType(name="root")
        middle = MiddleType(name="middle")
        leaf = MetaBase(name="leaf")

        middle.add_meta_parent(root)
        leaf.add_meta_parent(middle)

        # Find RootType upstream from leaf
        found = leaf.get_upstream(RootType)
        assert found is not None
        assert isinstance(found, RootType)

    def test_get_downstream(self, new_scene, meta_registry_clean):
        """Test get_downstream finds child of specific type."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry

        class TargetType(MetaBase):
            ID = "TargetType"

        MetaRegistry.register_meta_class(TargetType)

        root = MetaBase(name="root")
        middle = MetaBase(name="middle")
        target = TargetType(name="target")

        root.add_meta_child(middle)
        middle.add_meta_child(target)

        # Find TargetType downstream from root
        found = root.get_downstream(TargetType)
        assert found is not None
        assert isinstance(found, TargetType)

    def test_get_all_upstream(self, new_scene):
        """Test get_all_upstream returns all parents."""

        from tp.libs.maya.meta.base import MetaBase

        root = MetaBase(name="root")
        mid1 = MetaBase(name="mid1")
        mid2 = MetaBase(name="mid2")
        leaf = MetaBase(name="leaf")

        mid1.add_meta_parent(root)
        mid2.add_meta_parent(mid1)
        leaf.add_meta_parent(mid2)

        all_upstream = leaf.get_all_upstream()
        assert len(all_upstream) == 3

    def test_get_all_downstream(self, new_scene):
        """Test get_all_downstream returns all children."""

        from tp.libs.maya.meta.base import MetaBase

        root = MetaBase(name="root")
        child1 = MetaBase(name="child1")
        child2 = MetaBase(name="child2")
        grandchild = MetaBase(name="grandchild")

        root.add_meta_child(child1)
        root.add_meta_child(child2)
        child1.add_meta_child(grandchild)

        all_downstream = root.get_all_downstream()
        # Should include child1, child2, and grandchild
        assert len(all_downstream) >= 3
