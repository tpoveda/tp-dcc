"""Integration tests for MetaHumanSkeletonLayer class.

These tests require Maya to be running (via mayapy with maya.standalone).
Run with: mayapy scripts/run_maya_tests.py tests/meta/layers/test_skeleton_layer_integration.py
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestMetaHumanSkeletonLayerCreation:
    """Test MetaHumanSkeletonLayer creation and initialization."""

    def test_create_skeleton_layer(self, new_scene):
        """Test creating a MetaHumanSkeletonLayer metanode."""

        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        assert layer is not None
        assert layer.exists()
        assert "skeleton_layer_meta" in layer.name()

    def test_skeleton_layer_has_correct_type(self, new_scene):
        """Test that the skeleton layer metanode has the correct type."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        assert (
            layer.metaclass_type() == constants.METAHUMAN_SKELETON_LAYER_TYPE
        )

    def test_skeleton_layer_has_required_attributes(self, new_scene):
        """Test that the skeleton layer has all required attributes."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        required_attrs = [
            constants.LAYER_ROOT_TRANSFORM_ATTR,
            constants.LAYER_CONTROLS_ATTR,
            constants.LAYER_JOINTS_ATTR,
            constants.SKELETON_LAYER_ROOT_JOINT_ATTR,
            constants.SKELETON_LAYER_BIND_ROOT_ATTR,
            constants.SKELETON_LAYER_IS_MOTION_SKELETON_ATTR,
        ]

        for attr_name in required_attrs:
            assert layer.hasAttribute(attr_name), (
                f"Missing attribute: {attr_name}"
            )


@pytest.mark.integration
class TestMetaHumanSkeletonLayerRootJoint:
    """Test MetaHumanSkeletonLayer root joint management."""

    def test_root_joint_none_initially(self, new_scene):
        """Test that root joint is None initially."""

        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        assert layer.root_joint() is None

    def test_connect_root_joint(self, new_scene):
        """Test connecting a root joint."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        # Create root joint
        cmds.select(clear=True)
        joint_name = cmds.joint(name="root_joint")
        joint = node_by_name(joint_name)

        layer.connect_root_joint(joint)

        assert layer.root_joint() is not None
        assert layer.root_joint().name() == joint_name


@pytest.mark.integration
class TestMetaHumanSkeletonLayerBindRoot:
    """Test MetaHumanSkeletonLayer bind root management."""

    def test_bind_root_none_initially(self, new_scene):
        """Test that bind root is None initially."""

        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        assert layer.bind_root_joint() is None

    def test_connect_bind_root(self, new_scene):
        """Test connecting a bind root joint."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        # Create bind root joint
        cmds.select(clear=True)
        joint_name = cmds.joint(name="bind_root_joint")
        joint = node_by_name(joint_name)

        layer.connect_bind_root(joint)

        assert layer.bind_root_joint() is not None
        assert layer.bind_root_joint().name() == joint_name


@pytest.mark.integration
class TestMetaHumanSkeletonLayerMotionFlag:
    """Test MetaHumanSkeletonLayer motion skeleton flag."""

    def test_default_is_motion_skeleton(self, new_scene):
        """Test that is_motion_skeleton defaults to True."""

        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        assert layer.is_motion_skeleton() is True

    def test_set_is_motion_skeleton(self, new_scene):
        """Test setting is_motion_skeleton flag."""

        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")
        layer.set_is_motion_skeleton(False)

        assert layer.is_motion_skeleton() is False


@pytest.mark.integration
class TestMetaHumanSkeletonLayerSideFiltering:
    """Test MetaHumanSkeletonLayer side-based joint filtering."""

    def test_left_joints(self, new_scene):
        """Test filtering left-side joints."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        # Create joints with side naming
        cmds.select(clear=True)
        for name in ["arm_l", "arm_r", "spine"]:
            cmds.select(clear=True)
            joint_name = cmds.joint(name=name)
            layer.add_joint(node_by_name(joint_name))

        left_joints = layer.left_joints()
        assert len(left_joints) == 1
        assert "arm_l" in left_joints[0].name()

    def test_right_joints(self, new_scene):
        """Test filtering right-side joints."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        cmds.select(clear=True)
        for name in ["arm_l", "arm_r", "spine"]:
            cmds.select(clear=True)
            joint_name = cmds.joint(name=name)
            layer.add_joint(node_by_name(joint_name))

        right_joints = layer.right_joints()
        assert len(right_joints) == 1
        assert "arm_r" in right_joints[0].name()

    def test_center_joints(self, new_scene):
        """Test filtering center joints."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        cmds.select(clear=True)
        for name in ["arm_l", "arm_r", "spine"]:
            cmds.select(clear=True)
            joint_name = cmds.joint(name=name)
            layer.add_joint(node_by_name(joint_name))

        center_joints = layer.center_joints()
        assert len(center_joints) == 1
        assert "spine" in center_joints[0].name()


@pytest.mark.integration
class TestMetaHumanSkeletonLayerFromRig:
    """Test creating skeleton layer via MetaMetaHumanRig."""

    def test_create_skeleton_layer_from_rig(self, new_scene):
        """Test creating skeleton layer via rig.create_layer()."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_SKELETON_LAYER_TYPE,
            hierarchy_name="skeleton_grp",
            meta_name="skeleton_meta",
        )

        assert layer is not None
        assert layer.exists()
        assert isinstance(layer, MetaHumanSkeletonLayer)

    def test_skeleton_layer_retrievable_from_rig(self, new_scene):
        """Test that skeleton layer is retrievable from rig."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_SKELETON_LAYER_TYPE,
            hierarchy_name="skeleton_grp",
            meta_name="skeleton_meta",
        )

        retrieved = meta_rig.skeleton_layer()
        assert retrieved is not None
        assert retrieved == layer


@pytest.mark.integration
class TestMetaHumanSkeletonLayerDeletion:
    """Test MetaHumanSkeletonLayer deletion."""

    def test_delete_layer(self, new_scene):
        """Test deleting the skeleton layer."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")
        meta_name = layer.name()

        result = layer.delete()

        assert result is True
        assert not cmds.objExists(meta_name)

    def test_delete_layer_preserves_joints(self, new_scene):
        """Test that deleting layer preserves connected joints."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        layer = MetaHumanSkeletonLayer(name="skeleton_layer_meta")

        # Create and connect a joint
        cmds.select(clear=True)
        joint_name = cmds.joint(name="test_joint")
        layer.add_joint(node_by_name(joint_name))

        layer.delete()

        # Joint should still exist
        assert cmds.objExists(joint_name)
