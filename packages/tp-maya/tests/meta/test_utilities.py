"""Integration tests for utility enhancements.

These tests verify the functionality of select, delete_all, exists,
delete_network, and get_all_meta_nodes_of_type.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestExists:
    """Test the exists method."""

    def test_exists_for_valid_node(self, new_scene, meta_registry_clean):
        """Test exists returns True for valid node."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")
        assert meta.exists() is True

    def test_exists_for_deleted_node(self, new_scene, meta_registry_clean):
        """Test exists returns False after node is deleted."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")
        meta.delete()

        assert meta.exists() is False


@pytest.mark.integration
class TestSelect:
    """Test the select method."""

    def test_select_node(self, new_scene, meta_registry_clean):
        """Test selecting a meta node."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")

        # Clear selection
        cmds.select(clear=True)
        assert len(cmds.ls(selection=True)) == 0

        # Select meta node
        meta.select()

        selection = cmds.ls(selection=True)
        assert len(selection) == 1
        assert selection[0] == meta.name()

    def test_select_add(self, new_scene, meta_registry_clean):
        """Test adding to selection."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase

        meta1 = MetaBase(name="meta1")
        meta2 = MetaBase(name="meta2")

        # Select first
        meta1.select()
        assert len(cmds.ls(selection=True)) == 1

        # Add second
        meta2.select(add=True)
        assert len(cmds.ls(selection=True)) == 2

    def test_select_replace(self, new_scene, meta_registry_clean):
        """Test replacing selection."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase

        meta1 = MetaBase(name="meta1")
        meta2 = MetaBase(name="meta2")

        # Select first
        meta1.select()
        assert cmds.ls(selection=True)[0] == "meta1"

        # Replace with second
        meta2.select(replace=True)
        selection = cmds.ls(selection=True)
        assert len(selection) == 1
        assert selection[0] == "meta2"


@pytest.mark.integration
class TestDeleteAll:
    """Test the delete_all method."""

    def test_delete_all_with_children(self, new_scene, meta_registry_clean):
        """Test delete_all deletes node and all children."""

        from tp.libs.maya.meta.base import (
            MetaBase,
            find_meta_nodes_by_class_type,
        )

        # Create hierarchy
        parent = MetaBase(name="parent")
        child1 = MetaBase(name="child1")
        child2 = MetaBase(name="child2")

        child1.add_meta_parent(parent)
        child2.add_meta_parent(parent)

        # Verify all exist
        assert len(find_meta_nodes_by_class_type(MetaBase)) >= 3

        # Delete all from parent
        parent.delete_all()

        # All should be deleted
        remaining = find_meta_nodes_by_class_type(MetaBase)
        assert parent.name() not in [m.name() for m in remaining]
        assert "child1" not in [m.name() for m in remaining]
        assert "child2" not in [m.name() for m in remaining]

    def test_delete_all_nested_hierarchy(self, new_scene, meta_registry_clean):
        """Test delete_all with nested hierarchy."""

        from tp.libs.maya.meta.base import (
            MetaBase,
            find_meta_nodes_by_class_type,
        )

        # Create nested hierarchy
        root = MetaBase(name="root")
        level1 = MetaBase(name="level1")
        level2 = MetaBase(name="level2")

        level1.add_meta_parent(root)
        level2.add_meta_parent(level1)

        # Delete all from root
        root.delete_all()

        # All should be gone
        remaining = find_meta_nodes_by_class_type(MetaBase)
        names = [m.name() for m in remaining]
        assert "root" not in names
        assert "level1" not in names
        assert "level2" not in names


@pytest.mark.integration
class TestDeleteNetwork:
    """Test the delete_network function."""

    def test_delete_network_basic(self, new_scene, meta_registry_clean):
        """Test basic network deletion."""

        from tp.libs.maya.meta.base import (
            MetaBase,
            delete_network,
            find_meta_nodes_by_class_type,
        )

        # Create network
        root = MetaBase(name="network_root")
        child = MetaBase(name="network_child")
        child.add_meta_parent(root)

        # Delete network
        delete_network(root)

        # Network should be gone
        remaining = find_meta_nodes_by_class_type(MetaBase)
        names = [m.name() for m in remaining]
        assert "network_root" not in names
        assert "network_child" not in names


@pytest.mark.integration
class TestGetAllMetaNodesOfType:
    """Test the get_all_meta_nodes_of_type function."""

    def test_get_all_of_base_type(self, new_scene, meta_registry_clean):
        """Test getting all nodes of base type."""

        from tp.libs.maya.meta.base import (
            MetaBase,
            get_all_meta_nodes_of_type,
        )

        # Create some nodes
        meta1 = MetaBase(name="meta1")
        meta2 = MetaBase(name="meta2")
        meta3 = MetaBase(name="meta3")

        nodes = get_all_meta_nodes_of_type(MetaBase)

        assert len(nodes) >= 3
        names = [n.name() for n in nodes]
        assert "meta1" in names
        assert "meta2" in names
        assert "meta3" in names

    def test_get_all_of_custom_type(self, new_scene, meta_registry_clean):
        """Test getting all nodes of a custom type."""

        from tp.libs.maya.meta.base import (
            MetaBase,
            MetaRegistry,
            get_all_meta_nodes_of_type,
        )

        class CustomType(MetaBase):
            ID = "CustomType"
            _do_register = True

        MetaRegistry.register_meta_class(CustomType)

        # Create mixed types
        base1 = MetaBase(name="base1")
        custom1 = CustomType(name="custom1")
        custom2 = CustomType(name="custom2")

        # Get only custom type
        nodes = get_all_meta_nodes_of_type(CustomType)

        assert len(nodes) == 2
        names = [n.name() for n in nodes]
        assert "custom1" in names
        assert "custom2" in names
        assert "base1" not in names

    def test_get_all_empty_scene(self, new_scene, meta_registry_clean):
        """Test getting nodes from empty scene."""

        from tp.libs.maya.meta.base import (
            MetaBase,
            get_all_meta_nodes_of_type,
        )

        nodes = get_all_meta_nodes_of_type(MetaBase)
        assert len(nodes) == 0


@pytest.mark.integration
class TestExistsAfterOperations:
    """Test exists method after various operations."""

    def test_exists_after_scene_operations(
        self, new_scene, meta_registry_clean
    ):
        """Test exists is reliable after scene operations."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")
        assert meta.exists() is True

        # Rename the node
        cmds.rename(meta.name(), "renamed_meta")

        # Should still exist (MObject reference is still valid)
        assert meta.exists() is True

    def test_exists_with_invalid_reference(
        self, new_scene, meta_registry_clean
    ):
        """Test exists handles invalid references gracefully."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")

        # Force delete via Maya commands
        import maya.cmds as cmds

        cmds.delete(meta.name())

        # Should return False, not raise an exception
        assert meta.exists() is False
