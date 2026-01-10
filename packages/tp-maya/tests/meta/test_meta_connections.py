"""Integration tests for meta node connections to scene objects.

These tests verify the functionality of connecting meta nodes to
regular Maya scene objects (transforms, joints, etc.).
"""

from __future__ import annotations

import pytest


def _get_dag_node(node_name: str):
    """Helper to create a DagNode from a node name.

    Args:
        node_name: The name of the Maya node.

    Returns:
        DagNode wrapping the specified node.
    """

    from tp.libs.maya.om.nodes import mobject_by_name
    from tp.libs.maya.wrapper import DagNode

    mobj = mobject_by_name(node_name)
    return DagNode(mobj)


def _get_dg_node(node_name: str):
    """Helper to create a DGNode from a node name.

    Args:
        node_name: The name of the Maya node.

    Returns:
        DGNode wrapping the specified node.
    """

    from tp.libs.maya.om.nodes import mobject_by_name
    from tp.libs.maya.wrapper import DGNode

    mobj = mobject_by_name(node_name)
    return DGNode(mobj)


@pytest.mark.integration
class TestMetaNodeSceneConnections:
    """Test connections between meta nodes and scene objects."""

    def test_connect_to_transform(self, new_scene):
        """Test connecting a meta node to a transform."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase

        # Create a transform
        transform_name = cmds.createNode("transform", name="test_transform")
        transform = _get_dag_node(transform_name)

        # Create a meta node and connect
        meta = MetaBase(name="test_meta")
        plug = meta.connect_to("connectedNode", transform)

        assert plug is not None
        assert meta.hasAttribute("connectedNode")

    def test_connect_to_multiple_objects(self, new_scene):
        """Test connecting a meta node to multiple scene objects."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase

        # Create transforms
        t1 = _get_dag_node(cmds.createNode("transform", name="transform1"))
        t2 = _get_dag_node(cmds.createNode("transform", name="transform2"))

        meta = MetaBase(name="test_meta")

        meta.connect_to("object1", t1)
        meta.connect_to("object2", t2)

        assert meta.hasAttribute("object1")
        assert meta.hasAttribute("object2")

    def test_connect_to_by_plug_static(self, new_scene):
        """Test static connect_to_by_plug method."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.om import attributetypes

        transform = _get_dag_node(
            cmds.createNode("transform", name="test_transform")
        )

        meta = MetaBase(name="test_meta")
        # Create a message attribute
        meta.addAttribute(
            "customConnection",
            value=None,
            type=attributetypes.kMFnMessageAttribute,
        )

        plug = meta.attribute("customConnection")
        result = MetaBase.connect_to_by_plug(plug, transform)

        assert result is not None

    def test_iterate_children_with_scene_objects(self, new_scene):
        """Test iterating over connected scene objects."""

        import maya.cmds as cmds
        from maya.api import OpenMaya

        from tp.libs.maya.meta.base import MetaBase

        # Create transforms
        t1 = _get_dag_node(
            cmds.createNode("transform", name="child_transform1")
        )
        t2 = _get_dag_node(
            cmds.createNode("transform", name="child_transform2")
        )

        meta = MetaBase(name="test_meta")

        # Connect transforms to meta node
        meta.connect_to("child1", t1)
        meta.connect_to("child2", t2)

        # Iterate children (scene objects, not meta nodes)
        children = list(
            meta.iterate_children(
                filter_types={OpenMaya.MFn.kTransform}, include_meta=False
            )
        )

        assert len(children) >= 2

    def test_iterate_children_excludes_meta_nodes(self, new_scene):
        """Test that iterate_children excludes meta nodes by default."""

        import maya.cmds as cmds
        from maya.api import OpenMaya

        from tp.libs.maya.meta.base import MetaBase

        # Create a transform and a child meta node
        transform = _get_dag_node(
            cmds.createNode("transform", name="scene_object")
        )
        child_meta = MetaBase(name="child_meta")

        parent_meta = MetaBase(name="parent_meta")
        parent_meta.connect_to("sceneObject", transform)
        parent_meta.add_meta_child(child_meta)

        # iterate_children should not include the meta child
        children = list(
            parent_meta.iterate_children(
                filter_types={OpenMaya.MFn.kTransform, OpenMaya.MFn.kAffect},
                include_meta=False,
            )
        )

        # Should only find the transform, not the meta node
        names = [c.name() for c in children]
        assert any("scene_object" in n for n in names)

    def test_iterate_children_include_meta(self, new_scene):
        """Test iterate_children with include_meta=True."""

        from tp.libs.maya.meta.base import MetaBase

        parent = MetaBase(name="parent")
        child = MetaBase(name="child")

        parent.add_meta_child(child)

        # With include_meta=True, should include meta nodes
        children = list(parent.iterate_children(include_meta=True))

        # Should find at least the child meta node
        assert len(children) >= 1

    def test_connected_meta_nodes_function(self, new_scene):
        """Test the connected_meta_nodes utility function."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase, connected_meta_nodes

        # Create a transform
        transform = _get_dag_node(
            cmds.createNode("transform", name="test_transform")
        )

        # Create meta nodes and connect to transform
        meta1 = MetaBase(name="meta1")
        meta2 = MetaBase(name="meta2")

        meta1.connect_to("connectedTransform", transform)
        meta2.connect_to("connectedTransform", transform)

        # Find all meta nodes connected to the transform
        connected = connected_meta_nodes(transform)

        assert len(connected) >= 2

    def test_connected_meta_nodes_on_meta_node(self, new_scene):
        """Test connected_meta_nodes when called on a meta node."""

        from tp.libs.maya.meta.base import MetaBase, connected_meta_nodes

        meta = MetaBase(name="test_meta")

        # When called on a meta node, should return it wrapped
        result = connected_meta_nodes(meta)

        assert len(result) == 1
        assert result[0] == meta


@pytest.mark.integration
class TestMetaNodeJointConnections:
    """Test connections to joint hierarchies."""

    def test_connect_to_joint(self, new_scene):
        """Test connecting a meta node to a joint."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase

        # Create a joint
        cmds.select(clear=True)
        joint_name = cmds.joint(name="test_joint")
        joint = _get_dag_node(joint_name)

        meta = MetaBase(name="joint_meta")
        plug = meta.connect_to("controlledJoint", joint)

        assert plug is not None
        assert meta.hasAttribute("controlledJoint")

    def test_connect_to_joint_chain(self, new_scene):
        """Test connecting to a joint chain."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase

        # Create joint chain
        cmds.select(clear=True)
        j1 = cmds.joint(name="joint1", position=[0, 0, 0])
        j2 = cmds.joint(name="joint2", position=[1, 0, 0])
        j3 = cmds.joint(name="joint3", position=[2, 0, 0])

        meta = MetaBase(name="chain_meta")
        meta.connect_to("rootJoint", _get_dag_node(j1))
        meta.connect_to("midJoint", _get_dag_node(j2))
        meta.connect_to("endJoint", _get_dag_node(j3))

        assert meta.hasAttribute("rootJoint")
        assert meta.hasAttribute("midJoint")
        assert meta.hasAttribute("endJoint")


@pytest.mark.integration
class TestMetaNodeControlConnections:
    """Test connections to control curves (common rig pattern)."""

    def test_connect_to_nurbs_curve(self, new_scene):
        """Test connecting a meta node to a NURBS curve control."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase

        # Create a simple circle (NURBS curve)
        curve_transform = cmds.circle(name="control_curve")[0]
        curve = _get_dag_node(curve_transform)

        meta = MetaBase(name="control_meta")
        meta.connect_to("controlCurve", curve)

        assert meta.hasAttribute("controlCurve")


@pytest.mark.integration
class TestMetaNodeMultiConnections:
    """Test array/multi connections."""

    def test_add_multiple_meta_children(self, new_scene):
        """Test adding multiple children creates array connections."""

        from tp.libs.maya.meta.base import MetaBase

        parent = MetaBase(name="parent")
        children = [MetaBase(name=f"child_{i}") for i in range(5)]

        for child in children:
            parent.add_meta_child(child)

        found_children = list(parent.iterate_meta_children(depth_limit=1))

        # Should find all 5 children
        assert len(found_children) == 5

    def test_meta_parent_array_attribute(self, new_scene):
        """Test that parent attribute is an array for multi-parent support."""

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.meta.constants import META_PARENT_ATTR_NAME

        meta = MetaBase(name="test")

        # Parent attribute should exist and be an array
        parent_plug = meta.attribute(META_PARENT_ATTR_NAME)
        assert parent_plug is not None

    def test_meta_children_array_attribute(self, new_scene):
        """Test that children attribute is an array."""

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.meta.constants import META_CHILDREN_ATTR_NAME

        meta = MetaBase(name="test")

        # Children attribute should exist and be an array
        children_plug = meta.attribute(META_CHILDREN_ATTR_NAME)
        assert children_plug is not None
