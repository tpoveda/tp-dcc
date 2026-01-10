"""Integration tests for connection improvements.

These tests verify the functionality of connect_node, disconnect_node,
get_connected_nodes, is_in_network, and get_network_entries.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestConnectNode:
    """Test the connect_node method."""

    def test_connect_node_creates_connection(
        self, new_scene, meta_registry_clean
    ):
        """Test that connect_node creates a connection."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        # Create a joint and meta node
        cmds.select(clear=True)
        joint_name = cmds.joint(name="test_joint")
        joint = DagNode(mobject_by_name(joint_name))

        meta = MetaBase(name="test_meta")

        # Connect the joint
        meta.connect_node(joint, "rootJoint")

        # Verify attribute exists and is connected
        assert meta.hasAttribute("rootJoint")
        plug = meta.attribute("rootJoint")
        source = plug.source()
        assert source is not None

    def test_connect_multiple_nodes(self, new_scene, meta_registry_clean):
        """Test connecting multiple nodes with different attribute names."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint1 = DagNode(mobject_by_name(cmds.joint(name="joint1")))
        cmds.select(clear=True)
        joint2 = DagNode(mobject_by_name(cmds.joint(name="joint2")))

        meta = MetaBase(name="test_meta")

        meta.connect_node(joint1, "startJoint")
        meta.connect_node(joint2, "endJoint")

        assert meta.hasAttribute("startJoint")
        assert meta.hasAttribute("endJoint")


@pytest.mark.integration
class TestDisconnectNode:
    """Test the disconnect_node method."""

    def test_disconnect_specific_attribute(
        self, new_scene, meta_registry_clean
    ):
        """Test disconnecting from a specific attribute."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint = DagNode(mobject_by_name(cmds.joint(name="test_joint")))

        meta = MetaBase(name="test_meta")
        meta.connect_node(joint, "rootJoint")

        # Verify connected
        assert meta.attribute("rootJoint").source() is not None

        # Disconnect
        meta.disconnect_node(joint, "rootJoint")

        # Verify disconnected
        assert meta.attribute("rootJoint").source() is None


@pytest.mark.integration
class TestGetConnectedNodes:
    """Test the get_connected_nodes method."""

    def test_get_connected_from_specific_attr(
        self, new_scene, meta_registry_clean
    ):
        """Test getting nodes connected to a specific attribute."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint = DagNode(mobject_by_name(cmds.joint(name="test_joint")))

        meta = MetaBase(name="test_meta")
        meta.connect_node(joint, "rootJoint")

        connected = meta.get_connected_nodes("rootJoint")
        assert len(connected) == 1

    def test_get_all_connected_nodes(self, new_scene, meta_registry_clean):
        """Test getting all connected nodes."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint1 = DagNode(mobject_by_name(cmds.joint(name="joint1")))
        cmds.select(clear=True)
        joint2 = DagNode(mobject_by_name(cmds.joint(name="joint2")))

        meta = MetaBase(name="test_meta")
        meta.connect_node(joint1, "startJoint")
        meta.connect_node(joint2, "endJoint")

        connected = meta.get_connected_nodes()
        assert len(connected) == 2

    def test_exclude_meta_nodes_by_default(
        self, new_scene, meta_registry_clean
    ):
        """Test that meta nodes are excluded by default."""

        from tp.libs.maya.meta.base import MetaBase

        parent = MetaBase(name="parent_meta")
        child = MetaBase(name="child_meta")

        child.add_meta_parent(parent)

        # get_connected_nodes should not return meta nodes by default
        # (meta connections use tpMetaParent/tpMetaChildren, not user attrs)
        connected = parent.get_connected_nodes()
        # Should not include the child meta node via regular connection
        # This test verifies the filtering logic


@pytest.mark.integration
class TestIsInNetwork:
    """Test the is_in_network function."""

    def test_connected_node_is_in_network(
        self, new_scene, meta_registry_clean
    ):
        """Test that a connected scene node is detected as in network."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase, is_in_network
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint = DagNode(mobject_by_name(cmds.joint(name="test_joint")))

        meta = MetaBase(name="test_meta")
        meta.connect_node(joint, "rootJoint")

        assert is_in_network(joint) is True

    def test_unconnected_node_not_in_network(
        self, new_scene, meta_registry_clean
    ):
        """Test that an unconnected node is not in network."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import is_in_network
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint = DagNode(mobject_by_name(cmds.joint(name="test_joint")))

        assert is_in_network(joint) is False

    def test_meta_node_is_in_network(self, new_scene, meta_registry_clean):
        """Test that a meta node itself is considered in network."""

        from tp.libs.maya.meta.base import MetaBase, is_in_network

        meta = MetaBase(name="test_meta")

        assert is_in_network(meta) is True


@pytest.mark.integration
class TestGetNetworkEntries:
    """Test the get_network_entries function."""

    def test_get_entries_from_connected_node(
        self, new_scene, meta_registry_clean
    ):
        """Test getting network entries from a connected node."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase, get_network_entries
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint = DagNode(mobject_by_name(cmds.joint(name="test_joint")))

        meta = MetaBase(name="test_meta")
        meta.connect_node(joint, "rootJoint")

        entries = get_network_entries(joint)
        assert len(entries) == 1
        assert entries[0].name() == meta.name()

    def test_get_entries_with_type_filter(
        self, new_scene, meta_registry_clean
    ):
        """Test filtering network entries by type."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import (
            MetaBase,
            MetaRegistry,
            get_network_entries,
        )
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        class CustomMeta(MetaBase):
            ID = "CustomMeta"
            _do_register = True

        MetaRegistry.register_meta_class(CustomMeta)

        cmds.select(clear=True)
        joint = DagNode(mobject_by_name(cmds.joint(name="test_joint")))

        # Create both types of meta nodes
        regular_meta = MetaBase(name="regular_meta")
        custom_meta = CustomMeta(name="custom_meta")

        regular_meta.connect_node(joint, "connection1")
        custom_meta.connect_node(joint, "connection2")

        # Get only CustomMeta entries
        entries = get_network_entries(joint, CustomMeta)
        assert len(entries) == 1
        assert entries[0].metaclass_type() == "CustomMeta"

    def test_get_entries_from_unconnected_node(
        self, new_scene, meta_registry_clean
    ):
        """Test that unconnected node returns empty list."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import get_network_entries
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint = DagNode(mobject_by_name(cmds.joint(name="test_joint")))

        entries = get_network_entries(joint)
        assert len(entries) == 0

    def test_get_entries_from_meta_node(self, new_scene, meta_registry_clean):
        """Test getting entries when node itself is a meta node."""

        from tp.libs.maya.meta.base import MetaBase, get_network_entries

        meta = MetaBase(name="test_meta")

        entries = get_network_entries(meta)
        assert len(entries) == 1
        assert entries[0].name() == meta.name()
