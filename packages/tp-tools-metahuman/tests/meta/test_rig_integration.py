"""Integration tests for MetaMetaHumanRig class.

These tests require Maya to be running (via mayapy with maya.standalone).
Run with: mayapy -m pytest tests/meta/test_rig_integration.py -m integration

Or run all integration tests:
    mayapy -m pytest tests/ -m integration
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestMetaMetaHumanRigCreation:
    """Test MetaMetaHumanRig creation and initialization."""

    def test_create_meta_rig(self, new_scene):
        """Test creating a MetaMetaHumanRig metanode."""

        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        assert meta_rig is not None
        assert meta_rig.exists()
        assert "test_rig_meta" in meta_rig.name()

    def test_meta_rig_has_correct_type(self, new_scene):
        """Test that the rig metanode has the correct type identifier."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        assert meta_rig.metaclass_type() == constants.METAHUMAN_RIG_TYPE

    def test_meta_rig_has_required_attributes(self, new_scene):
        """Test that the rig metanode has all required attributes."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        # Check all required attributes exist
        required_attrs = [
            constants.RIG_VERSION_ATTR,
            constants.NAME_ATTR,
            constants.ID_ATTR,
            constants.IS_METAHUMAN_RIG_ATTR,
            constants.IS_ROOT_ATTR,
            constants.RIG_IS_MOTION_MODE_ATTR,
            constants.RIG_ROOT_TRANSFORM_ATTR,
            constants.RIG_CONTROLS_GROUP_ATTR,
            constants.RIG_SETUP_GROUP_ATTR,
            constants.RIG_MOTION_SKELETON_ATTR,
            constants.RIG_CONTROL_DISPLAY_LAYER_ATTR,
        ]

        for attr_name in required_attrs:
            assert meta_rig.hasAttribute(attr_name), (
                f"Missing attribute: {attr_name}"
            )

    def test_meta_rig_default_values(self, new_scene):
        """Test that default attribute values are set correctly."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        # Check default values
        assert meta_rig.rig_version() == constants.DEFAULT_RIG_VERSION
        assert meta_rig.is_motion_mode() is True
        assert (
            meta_rig.attribute(constants.IS_METAHUMAN_RIG_ATTR).value() is True
        )
        assert meta_rig.attribute(constants.IS_ROOT_ATTR).value() is True

    def test_meta_rig_set_name(self, new_scene):
        """Test setting the rig name attribute."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        meta_rig.attribute(constants.NAME_ATTR).set("my_character")

        assert meta_rig.rig_name() == "my_character"


@pytest.mark.integration
class TestMetaMetaHumanRigGroups:
    """Test MetaMetaHumanRig group creation and management."""

    def test_create_controls_group(self, new_scene):
        """Test creating the controls group."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        controls_grp = meta_rig.create_controls_group("rig_ctrls")

        assert controls_grp is not None
        assert cmds.objExists("rig_ctrls")
        assert meta_rig.controls_group() == controls_grp

    def test_create_setup_group(self, new_scene):
        """Test creating the setup group."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        setup_grp = meta_rig.create_setup_group("rig_setup")

        assert setup_grp is not None
        assert cmds.objExists("rig_setup")
        assert meta_rig.setup_group() == setup_grp

    def test_create_root_transform(self, new_scene):
        """Test creating the root transform."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        root = meta_rig.create_transform("rig_root")

        assert root is not None
        assert cmds.objExists("rig_root")
        assert meta_rig.root_transform() == root

    def test_create_controls_group_with_parent(self, new_scene):
        """Test creating groups with parent hierarchy."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        root = meta_rig.create_transform("rig_root")
        controls_grp = meta_rig.create_controls_group("rig_ctrls", parent=root)

        # Check parent-child relationship
        parent = cmds.listRelatives("rig_ctrls", parent=True)
        assert parent is not None
        assert parent[0] == "rig_root"

    def test_groups_not_duplicated(self, new_scene):
        """Test that calling create group twice returns existing group."""

        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        grp1 = meta_rig.create_controls_group("rig_ctrls")
        grp2 = meta_rig.create_controls_group("rig_ctrls")

        assert grp1 == grp2

    def test_groups_none_when_not_created(self, new_scene):
        """Test that group getters return None when groups don't exist."""

        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        assert meta_rig.root_transform() is None
        assert meta_rig.controls_group() is None
        assert meta_rig.setup_group() is None
        assert meta_rig.motion_skeleton() is None


@pytest.mark.integration
class TestMetaMetaHumanRigDisplayLayer:
    """Test MetaMetaHumanRig display layer management."""

    def test_create_display_layer(self, new_scene):
        """Test creating a display layer."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_display_layer("test_display_layer")

        assert layer is not None
        assert cmds.objExists("test_display_layer")
        assert meta_rig.display_layer() == layer

    def test_display_layer_not_duplicated(self, new_scene):
        """Test that calling create display layer twice returns existing."""

        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        layer1 = meta_rig.create_display_layer("test_layer")
        layer2 = meta_rig.create_display_layer("another_name")

        assert layer1 == layer2

    def test_delete_display_layer(self, new_scene):
        """Test deleting the display layer."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        meta_rig.create_display_layer("test_layer")

        result = meta_rig.delete_display_layer()

        assert result is True
        assert not cmds.objExists("test_layer")
        assert meta_rig.display_layer() is None

    def test_display_layer_none_when_not_created(self, new_scene):
        """Test that display layer getter returns None when not created."""

        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        assert meta_rig.display_layer() is None


@pytest.mark.integration
class TestMetaMetaHumanRigLayers:
    """Test MetaMetaHumanRig layer management."""

    def test_create_layer(self, new_scene):
        """Test creating a layer."""

        # Register the layer class
        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaHumanLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_LAYER_TYPE,
            hierarchy_name="controls_grp",
            meta_name="controls_layer_meta",
        )

        assert layer is not None
        assert layer.exists()
        assert meta_rig.layer(constants.METAHUMAN_LAYER_TYPE) == layer

    def test_layer_returns_none_when_not_exists(self, new_scene):
        """Test that layer getter returns None when layer doesn't exist."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        assert meta_rig.layer(constants.METAHUMAN_LAYER_TYPE) is None
        assert meta_rig.controls_layer() is None
        assert meta_rig.skeleton_layer() is None
        assert meta_rig.fkik_layer() is None

    def test_layers_returns_empty_list_initially(self, new_scene):
        """Test that layers() returns empty list when no layers exist."""

        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        assert meta_rig.layers() == []

    def test_create_layer_with_parent(self, new_scene):
        """Test creating a layer with a parent transform."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaHumanLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        root = meta_rig.create_transform("rig_root")

        layer = meta_rig.create_layer(
            constants.METAHUMAN_LAYER_TYPE,
            hierarchy_name="layer_grp",
            meta_name="layer_meta",
            parent=root,
        )

        # Check parent relationship
        parent = cmds.listRelatives("layer_grp", parent=True)
        assert parent is not None
        assert parent[0] == "rig_root"


@pytest.mark.integration
class TestMetaMetaHumanRigDeletion:
    """Test MetaMetaHumanRig deletion."""

    def test_delete_rig(self, new_scene):
        """Test deleting the rig metanode."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        meta_name = meta_rig.name()

        result = meta_rig.delete()

        assert result is True
        assert not cmds.objExists(meta_name)

    def test_delete_rig_with_groups(self, new_scene):
        """Test deleting rig also deletes connected groups."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        meta_rig.create_controls_group("rig_ctrls")
        meta_rig.create_setup_group("rig_setup")

        meta_rig.delete()

        assert not cmds.objExists("rig_ctrls")
        assert not cmds.objExists("rig_setup")

    def test_delete_rig_with_display_layer(self, new_scene):
        """Test deleting rig also deletes display layer."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        meta_rig.create_display_layer("test_layer")

        meta_rig.delete()

        assert not cmds.objExists("test_layer")

    def test_delete_rig_with_layers(self, new_scene):
        """Test deleting rig also deletes child layers."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layer import MetaHumanLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaHumanLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_LAYER_TYPE,
            hierarchy_name="layer_grp",
            meta_name="layer_meta",
        )
        layer_meta_name = layer.name()

        meta_rig.delete()

        assert not cmds.objExists(layer_meta_name)
        assert not cmds.objExists("layer_grp")


@pytest.mark.integration
class TestMetaMetaHumanRigMotionSkeleton:
    """Test MetaMetaHumanRig motion skeleton connection."""

    def test_connect_motion_skeleton(self, new_scene):
        """Test connecting a motion skeleton root joint."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        # Create a test joint
        cmds.select(clear=True)
        joint_name = cmds.joint(name="root_motion")
        joint_node = node_by_name(joint_name)

        meta_rig.connect_motion_skeleton(joint_node)

        assert meta_rig.motion_skeleton() is not None
        assert meta_rig.motion_skeleton().name() == joint_name
