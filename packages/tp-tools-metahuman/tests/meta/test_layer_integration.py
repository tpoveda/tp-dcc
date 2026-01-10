"""Integration tests for MetaHumanLayer class.

These tests require Maya to be running (via mayapy with maya.standalone).
Run with: mayapy -m pytest tests/meta/test_layer_integration.py -m integration
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestMetaHumanLayerCreation:
    """Test MetaHumanLayer creation and initialization."""

    def test_create_layer(self, new_scene):
        """Test creating a MetaHumanLayer metanode."""

        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        assert layer is not None
        assert layer.exists()
        assert "test_layer_meta" in layer.name()

    def test_layer_has_correct_type(self, new_scene):
        """Test that the layer metanode has the correct type identifier."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        assert layer.metaclass_type() == constants.METAHUMAN_LAYER_TYPE

    def test_layer_has_required_attributes(self, new_scene):
        """Test that the layer metanode has all required attributes."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        required_attrs = [
            constants.LAYER_ROOT_TRANSFORM_ATTR,
            constants.LAYER_CONTROLS_ATTR,
            constants.LAYER_JOINTS_ATTR,
        ]

        for attr_name in required_attrs:
            assert layer.hasAttribute(attr_name), (
                f"Missing attribute: {attr_name}"
            )


@pytest.mark.integration
class TestMetaHumanLayerTransform:
    """Test MetaHumanLayer transform management."""

    def test_create_transform(self, new_scene):
        """Test creating the layer root transform."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")
        transform = layer.create_transform("layer_grp")

        assert transform is not None
        assert cmds.objExists("layer_grp")
        assert layer.root_transform() == transform

    def test_create_transform_with_parent(self, new_scene):
        """Test creating transform with a parent."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        # Create parent group
        parent_name = cmds.group(empty=True, name="parent_grp")
        parent = node_by_name(parent_name)

        layer = MetaHumanLayer(name="test_layer_meta")
        transform = layer.create_transform("layer_grp", parent=parent)

        # Check parent relationship
        actual_parent = cmds.listRelatives("layer_grp", parent=True)
        assert actual_parent is not None
        assert actual_parent[0] == "parent_grp"

    def test_transform_not_duplicated(self, new_scene):
        """Test that calling create_transform twice returns existing."""

        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        transform1 = layer.create_transform("layer_grp")
        transform2 = layer.create_transform("layer_grp")

        assert transform1 == transform2

    def test_root_transform_none_when_not_created(self, new_scene):
        """Test that root_transform returns None when not created."""

        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        assert layer.root_transform() is None


@pytest.mark.integration
class TestMetaHumanLayerControls:
    """Test MetaHumanLayer control management."""

    def test_add_control(self, new_scene):
        """Test adding a control to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        # Create a test control
        ctrl_name = cmds.circle(name="test_ctrl")[0]
        ctrl = node_by_name(ctrl_name)

        layer.add_control(ctrl)

        controls = layer.controls()
        assert len(controls) == 1
        assert controls[0].name() == ctrl_name

    def test_add_multiple_controls(self, new_scene):
        """Test adding multiple controls to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        # Create test controls
        ctrl_names = []
        for i in range(3):
            name = cmds.circle(name=f"test_ctrl_{i}")[0]
            ctrl_names.append(name)
            layer.add_control(node_by_name(name))

        controls = layer.controls()
        assert len(controls) == 3

    def test_iterate_controls(self, new_scene):
        """Test iterating over controls."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        # Create test controls
        for i in range(3):
            name = cmds.circle(name=f"test_ctrl_{i}")[0]
            layer.add_control(node_by_name(name))

        count = 0
        for ctrl in layer.iterate_controls():
            count += 1
            assert ctrl is not None

        assert count == 3

    def test_control_count(self, new_scene):
        """Test control count method."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        assert layer.control_count() == 0

        # Add controls
        for i in range(5):
            name = cmds.circle(name=f"test_ctrl_{i}")[0]
            layer.add_control(node_by_name(name))

        assert layer.control_count() == 5

    def test_controls_empty_initially(self, new_scene):
        """Test that controls list is empty initially."""

        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        assert layer.controls() == []
        assert layer.control_count() == 0


@pytest.mark.integration
class TestMetaHumanLayerJoints:
    """Test MetaHumanLayer joint management."""

    def test_add_joint(self, new_scene):
        """Test adding a joint to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        # Create a test joint
        cmds.select(clear=True)
        joint_name = cmds.joint(name="test_joint")
        joint = node_by_name(joint_name)

        layer.add_joint(joint)

        joints = layer.joints()
        assert len(joints) == 1
        assert joints[0].name() == joint_name

    def test_add_multiple_joints(self, new_scene):
        """Test adding multiple joints to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        # Create test joints
        cmds.select(clear=True)
        for i in range(3):
            name = cmds.joint(name=f"test_joint_{i}")
            cmds.select(clear=True)
            layer.add_joint(node_by_name(name))

        joints = layer.joints()
        assert len(joints) == 3

    def test_iterate_joints(self, new_scene):
        """Test iterating over joints."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        # Create test joints
        cmds.select(clear=True)
        for i in range(3):
            name = cmds.joint(name=f"test_joint_{i}")
            cmds.select(clear=True)
            layer.add_joint(node_by_name(name))

        count = 0
        for joint in layer.iterate_joints():
            count += 1
            assert joint is not None

        assert count == 3

    def test_joint_count(self, new_scene):
        """Test joint count method."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        assert layer.joint_count() == 0

        # Add joints
        cmds.select(clear=True)
        for i in range(5):
            name = cmds.joint(name=f"test_joint_{i}")
            cmds.select(clear=True)
            layer.add_joint(node_by_name(name))

        assert layer.joint_count() == 5

    def test_joints_empty_initially(self, new_scene):
        """Test that joints list is empty initially."""

        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        assert layer.joints() == []
        assert layer.joint_count() == 0


@pytest.mark.integration
class TestMetaHumanLayerDeletion:
    """Test MetaHumanLayer deletion."""

    def test_delete_layer(self, new_scene):
        """Test deleting the layer metanode."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")
        meta_name = layer.name()

        result = layer.delete()

        assert result is True
        assert not cmds.objExists(meta_name)

    def test_delete_layer_with_transform(self, new_scene):
        """Test deleting layer also deletes its root transform."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")
        layer.create_transform("layer_grp")

        layer.delete()

        assert not cmds.objExists("layer_grp")

    def test_delete_layer_preserves_controls(self, new_scene):
        """Test that deleting layer preserves connected controls."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        # Create and connect a control
        ctrl_name = cmds.circle(name="test_ctrl")[0]
        layer.add_control(node_by_name(ctrl_name))

        layer.delete()

        # Control should still exist
        assert cmds.objExists(ctrl_name)

    def test_delete_layer_preserves_joints(self, new_scene):
        """Test that deleting layer preserves connected joints."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer

        layer = MetaHumanLayer(name="test_layer_meta")

        # Create and connect a joint
        cmds.select(clear=True)
        joint_name = cmds.joint(name="test_joint")
        layer.add_joint(node_by_name(joint_name))

        layer.delete()

        # Joint should still exist
        assert cmds.objExists(joint_name)


@pytest.mark.integration
class TestMetaHumanLayerIntegrationWithRig:
    """Test MetaHumanLayer integration with MetaMetaHumanRig."""

    def test_layer_created_from_rig(self, new_scene):
        """Test creating a layer via rig.create_layer()."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaHumanLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_LAYER_TYPE,
            hierarchy_name="controls_grp",
            meta_name="controls_meta",
        )

        assert layer is not None
        assert layer.exists()

        # Layer should be retrievable from rig
        retrieved = meta_rig.layer(constants.METAHUMAN_LAYER_TYPE)
        assert retrieved == layer

    def test_layer_in_rig_layers_list(self, new_scene):
        """Test that created layer appears in rig.layers()."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaHumanLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_LAYER_TYPE,
            hierarchy_name="controls_grp",
            meta_name="controls_meta",
        )

        layers = meta_rig.layers()
        assert len(layers) == 1
        assert layers[0] == layer

    def test_rig_delete_cascades_to_layer(self, new_scene):
        """Test that deleting rig also deletes its layers."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaHumanLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_LAYER_TYPE,
            hierarchy_name="controls_grp",
            meta_name="controls_meta",
        )
        layer_name = layer.name()

        meta_rig.delete()

        assert not cmds.objExists(layer_name)
        assert not cmds.objExists("controls_grp")
