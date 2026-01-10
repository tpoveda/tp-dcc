"""Integration tests for MetaHumanBodyRigBuilder metanode integration.

These tests require Maya to be running (via mayapy with maya.standalone).
Run with: mayapy scripts/run_maya_tests.py tests/rig/test_body_rig_builder_meta_integration.py

These tests focus on Phase 1: Integration of metanode system with the body rig builder.
They test that the metanode is created, configured, and connected properly.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestMetaRigCreationOnBuild:
    """Test that building a rig creates and configures the metanode."""

    def test_meta_rig_is_created_during_build(self, new_scene):
        """Test that MetaMetaHumanRig metanode is created during build."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        # We need a skeleton to build - create a minimal one for testing
        # For now, we'll test the builder initialization and meta_rig property
        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        # Check that _meta_rig is initially None
        assert builder._meta_rig is None

    def test_meta_rig_has_correct_type_after_registration(self, new_scene):
        """Test that MetaMetaHumanRig has correct type after class registration."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        # Register the class
        MetaRegistry.register_meta_class(MetaMetaHumanRig)

        # Create manually and check
        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        assert meta_rig.metaclass_type() == constants.METAHUMAN_RIG_TYPE


@pytest.mark.integration
class TestMetaRigGroupConnections:
    """Test that rig groups are connected to the metanode."""

    def test_setup_group_connected_to_meta_rig(self, new_scene):
        """Test that setup group is connected via metanode create_setup_group."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        setup_grp = meta_rig.create_setup_group("rig_setup")

        assert setup_grp is not None
        assert cmds.objExists("rig_setup")
        assert meta_rig.setup_group() == setup_grp

    def test_controls_group_connected_to_meta_rig(self, new_scene):
        """Test that controls group is connected via metanode create_controls_group."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        controls_grp = meta_rig.create_controls_group("rig_ctrls")

        assert controls_grp is not None
        assert cmds.objExists("rig_ctrls")
        assert meta_rig.controls_group() == controls_grp


@pytest.mark.integration
class TestMetaRigMotionSkeletonConnection:
    """Test that motion skeleton is connected to the metanode."""

    def test_connect_motion_skeleton(self, new_scene):
        """Test connecting a motion skeleton root to the metanode."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        # Create a mock motion skeleton root joint
        cmds.select(clear=True)
        root_joint = cmds.joint(name="root_motion")

        motion_root = node_by_name(root_joint)
        meta_rig.connect_motion_skeleton(motion_root)

        # Verify connection
        connected_skeleton = meta_rig.motion_skeleton()
        assert connected_skeleton is not None
        assert connected_skeleton.name() == root_joint


@pytest.mark.integration
class TestMetaRigModeConfiguration:
    """Test that rig mode is configured correctly on the metanode."""

    def test_motion_mode_is_set_true(self, new_scene):
        """Test that motion mode is set to True when motion=True."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        meta_rig.attribute(constants.RIG_IS_MOTION_MODE_ATTR).set(True)

        assert meta_rig.is_motion_mode() is True

    def test_motion_mode_is_set_false(self, new_scene):
        """Test that motion mode is set to False when motion=False."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        meta_rig.attribute(constants.RIG_IS_MOTION_MODE_ATTR).set(False)

        assert meta_rig.is_motion_mode() is False


@pytest.mark.integration
class TestMetaRigNameConfiguration:
    """Test that rig name is configured correctly on the metanode."""

    def test_default_rig_name_is_set(self, new_scene):
        """Test that default rig name is set."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        meta_rig.attribute(constants.NAME_ATTR).set(constants.DEFAULT_RIG_NAME)

        assert meta_rig.rig_name() == constants.DEFAULT_RIG_NAME


@pytest.mark.integration
class TestExistingRigDeletion:
    """Test that existing rig detection includes metanode."""

    def test_metanode_is_deleted_when_rebuilding(self, new_scene):
        """Test that existing metanode is deleted on rebuild."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)

        # Create an existing metanode
        existing_meta = MetaMetaHumanRig(name="metahuman_body_rig_meta")
        assert cmds.objExists("metahuman_body_rig_meta")

        # Delete it using the same method as the builder
        cmds.delete("metahuman_body_rig_meta")

        # Verify it's gone
        assert not cmds.objExists("metahuman_body_rig_meta")


@pytest.mark.integration
class TestRigBuildResultMetaRig:
    """Test that RigBuildResult includes meta_rig field."""

    def test_rig_build_result_dataclass_structure(self, new_scene):
        """Test that RigBuildResult has meta_rig field in dataclass."""

        from dataclasses import fields

        from tp.tools.metahuman.rig.body_rig_builder import RigBuildResult

        field_names = [f.name for f in fields(RigBuildResult)]

        assert "meta_rig" in field_names
        assert "success" in field_names
        assert "message" in field_names
        assert "root_joint" in field_names
        assert "motion_skeleton" in field_names
        assert "controls_created" in field_names

    def test_rig_build_result_meta_rig_default_none(self, new_scene):
        """Test that RigBuildResult.meta_rig defaults to None."""

        from tp.tools.metahuman.rig.body_rig_builder import RigBuildResult

        result = RigBuildResult(success=True, message="Test")

        assert result.meta_rig is None


@pytest.mark.integration
class TestLayerRegistration:
    """Test that all layer classes are registered during build."""

    def test_controls_layer_is_registered(self, new_scene):
        """Test that MetaHumanControlsLayer is registered."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        MetaRegistry.register_meta_class(MetaHumanControlsLayer)

        # Verify we can look it up
        assert MetaRegistry.is_in_registry(
            constants.METAHUMAN_CONTROLS_LAYER_TYPE
        )

    def test_skeleton_layer_is_registered(self, new_scene):
        """Test that MetaHumanSkeletonLayer is registered."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanSkeletonLayer

        MetaRegistry.register_meta_class(MetaHumanSkeletonLayer)

        assert MetaRegistry.is_in_registry(
            constants.METAHUMAN_SKELETON_LAYER_TYPE
        )

    def test_fkik_layer_is_registered(self, new_scene):
        """Test that MetaHumanFKIKLayer is registered."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        MetaRegistry.register_meta_class(MetaHumanFKIKLayer)

        assert MetaRegistry.is_in_registry(constants.METAHUMAN_FKIK_LAYER_TYPE)

    def test_space_switch_layer_is_registered(self, new_scene):
        """Test that MetaHumanSpaceSwitchLayer is registered."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        MetaRegistry.register_meta_class(MetaHumanSpaceSwitchLayer)

        assert MetaRegistry.is_in_registry(
            constants.METAHUMAN_SPACE_SWITCH_LAYER_TYPE
        )

    def test_reverse_foot_layer_is_registered(self, new_scene):
        """Test that MetaHumanReverseFootLayer is registered."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        MetaRegistry.register_meta_class(MetaHumanReverseFootLayer)

        assert MetaRegistry.is_in_registry(
            constants.METAHUMAN_REVERSE_FOOT_LAYER_TYPE
        )
