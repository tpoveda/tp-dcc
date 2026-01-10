"""Integration tests for Skeleton Layer integration with body rig builder.

These tests require Maya to be running (via mayapy with maya.standalone).
Run with: mayapy scripts/run_maya_tests.py tests/rig/test_skeleton_layer_integration.py

These tests focus on Phase 2: Skeleton Layer integration with the body rig builder.
They test that skeleton layers are created and joints are properly registered.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestSkeletonLayerCreation:
    """Test that skeleton layer is created during motion skeleton build."""

    def test_skeleton_layer_created_via_rig(self, new_scene):
        """Test creating a skeleton layer through the rig metanode."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)

        # Create rig metanode
        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        # Create skeleton layer
        layer = meta_rig.create_layer(
            constants.METAHUMAN_SKELETON_LAYER_TYPE,
            "skeleton_layer",
            "skeleton_layer_meta",
        )

        assert layer is not None
        assert cmds.objExists("skeleton_layer_meta")
        assert cmds.objExists("skeleton_layer")

    def test_skeleton_layer_has_correct_type(self, new_scene):
        """Test that skeleton layer has the correct type ID."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_SKELETON_LAYER_TYPE,
            "skeleton_layer",
            "skeleton_layer_meta",
        )

        assert (
            layer.metaclass_type() == constants.METAHUMAN_SKELETON_LAYER_TYPE
        )


@pytest.mark.integration
class TestSkeletonLayerRootJoint:
    """Test skeleton layer root joint connection."""

    def test_connect_root_joint(self, new_scene):
        """Test connecting a root joint to the skeleton layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)

        # Create skeleton layer directly
        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        # Create a root joint
        cmds.select(clear=True)
        root_joint = cmds.joint(name="root_motion")
        root_node = node_by_name(root_joint)

        # Connect root joint
        layer.connect_root_joint(root_node)

        # Verify connection
        connected_root = layer.root_joint()
        assert connected_root is not None
        assert connected_root.name() == root_joint

    def test_connect_bind_root(self, new_scene):
        """Test connecting a bind skeleton root joint."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        # Create bind skeleton root
        cmds.select(clear=True)
        bind_root = cmds.joint(name="root_drv")
        bind_node = node_by_name(bind_root)

        # Connect bind root
        layer.connect_bind_root(bind_node)

        # Verify connection
        connected_bind = layer.bind_root_joint()
        assert connected_bind is not None
        assert connected_bind.name() == bind_root


@pytest.mark.integration
class TestSkeletonLayerJointRegistration:
    """Test registering joints with the skeleton layer."""

    def test_add_single_joint(self, new_scene):
        """Test adding a single joint to the skeleton layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        # Create and add a joint
        cmds.select(clear=True)
        spine_joint = cmds.joint(name="spine_01_motion")
        spine_node = node_by_name(spine_joint)

        layer.add_joint(spine_node)

        # Verify joint count
        assert layer.joint_count() == 1

    def test_add_multiple_joints(self, new_scene):
        """Test adding multiple joints to the skeleton layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        # Create skeleton hierarchy
        cmds.select(clear=True)
        root = cmds.joint(name="root_motion")
        spine = cmds.joint(name="spine_01_motion")
        chest = cmds.joint(name="spine_02_motion")

        # Add all joints
        for joint_name in [root, spine, chest]:
            node = node_by_name(joint_name)
            layer.add_joint(node)

        # Verify joint count
        assert layer.joint_count() == 3

    def test_iterate_joints(self, new_scene):
        """Test iterating over registered joints."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        # Create and add joints
        cmds.select(clear=True)
        joint_names = ["root_motion", "spine_01_motion", "spine_02_motion"]
        created_joints = []
        for name in joint_names:
            joint = cmds.joint(name=name)
            created_joints.append(joint)
            layer.add_joint(node_by_name(joint))

        # Iterate and collect names
        iterated_names = [j.name() for j in layer.iterate_joints()]

        assert len(iterated_names) == 3
        for name in joint_names:
            assert name in iterated_names


@pytest.mark.integration
class TestSkeletonLayerSideFiltering:
    """Test filtering joints by side."""

    def test_left_joints(self, new_scene):
        """Test filtering left-side joints."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        # Create joints with different sides
        cmds.select(clear=True)
        root = cmds.joint(name="root_motion")
        cmds.select(clear=True)
        left_arm = cmds.joint(name="upperarm_l_motion")
        cmds.select(clear=True)
        right_arm = cmds.joint(name="upperarm_r_motion")

        for j in [root, left_arm, right_arm]:
            layer.add_joint(node_by_name(j))

        # Get left joints
        left_joints = layer.left_joints()
        left_names = [j.name() for j in left_joints]

        assert len(left_joints) == 1
        assert "upperarm_l_motion" in left_names

    def test_right_joints(self, new_scene):
        """Test filtering right-side joints."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        # Create joints
        cmds.select(clear=True)
        root = cmds.joint(name="root_motion")
        cmds.select(clear=True)
        left_arm = cmds.joint(name="upperarm_l_motion")
        cmds.select(clear=True)
        right_arm = cmds.joint(name="upperarm_r_motion")

        for j in [root, left_arm, right_arm]:
            layer.add_joint(node_by_name(j))

        # Get right joints
        right_joints = layer.right_joints()
        right_names = [j.name() for j in right_joints]

        assert len(right_joints) == 1
        assert "upperarm_r_motion" in right_names

    def test_center_joints(self, new_scene):
        """Test filtering center joints (no side suffix)."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        # Create joints
        cmds.select(clear=True)
        root = cmds.joint(name="root_motion")
        spine = cmds.joint(name="spine_01_motion")
        cmds.select(clear=True)
        left_arm = cmds.joint(name="upperarm_l_motion")

        for j in [root, spine, left_arm]:
            layer.add_joint(node_by_name(j))

        # Get center joints
        center_joints = layer.center_joints()
        center_names = [j.name() for j in center_joints]

        assert len(center_joints) == 2
        assert "root_motion" in center_names
        assert "spine_01_motion" in center_names


@pytest.mark.integration
class TestSkeletonLayerMotionFlag:
    """Test the motion skeleton flag."""

    def test_default_is_motion_skeleton(self, new_scene):
        """Test that default is_motion_skeleton is True."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        assert layer.is_motion_skeleton() is True

    def test_set_is_motion_skeleton_false(self, new_scene):
        """Test setting is_motion_skeleton to False."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")
        layer.set_is_motion_skeleton(False)

        assert layer.is_motion_skeleton() is False


@pytest.mark.integration
class TestBodyRigBuilderSkeletonLayer:
    """Test skeleton layer creation in body rig builder context."""

    def test_builder_creates_skeleton_layer_method(self, new_scene):
        """Test that builder has _create_skeleton_layer method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        # Verify the method exists
        assert hasattr(builder, "_create_skeleton_layer")
        assert callable(getattr(builder, "_create_skeleton_layer"))

    def test_builder_has_register_joints_method(self, new_scene):
        """Test that builder has _register_skeleton_joints method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_register_skeleton_joints")
        assert callable(getattr(builder, "_register_skeleton_joints"))

    def test_skeleton_layer_registers_joints(self, new_scene):
        """Test that _register_skeleton_joints registers all descendant joints."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)

        # Create a skeleton hierarchy
        cmds.select(clear=True)
        root = cmds.joint(name="root_motion")
        spine1 = cmds.joint(name="spine_01_motion")
        spine2 = cmds.joint(name="spine_02_motion")
        chest = cmds.joint(name="spine_03_motion")

        # Create skeleton layer
        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        # Create builder and use its method
        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)
        builder._register_skeleton_joints(layer, "root_motion")

        # Verify all joints were registered (root + 3 children = 4)
        assert layer.joint_count() == 4
