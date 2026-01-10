"""Integration tests for MetaHumanReverseFootLayer class.

These tests require Maya to be running (via mayapy with maya.standalone).
Run with: mayapy scripts/run_maya_tests.py tests/meta/layers/test_reverse_foot_layer_integration.py
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestMetaHumanReverseFootLayerCreation:
    """Test MetaHumanReverseFootLayer creation and initialization."""

    def test_create_reverse_foot_layer(self, new_scene):
        """Test creating a MetaHumanReverseFootLayer metanode."""

        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        assert layer is not None
        assert layer.exists()
        assert "reverse_foot_layer_meta" in layer.name()

    def test_reverse_foot_layer_has_correct_type(self, new_scene):
        """Test that the reverse foot layer has the correct type."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        assert (
            layer.metaclass_type()
            == constants.METAHUMAN_REVERSE_FOOT_LAYER_TYPE
        )

    def test_reverse_foot_layer_has_required_attributes(self, new_scene):
        """Test that the reverse foot layer has all required attributes."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        required_attrs = [
            constants.LAYER_ROOT_TRANSFORM_ATTR,
            constants.REVERSE_FOOT_LAYER_FOOT_CONTROLS_ATTR,
            constants.REVERSE_FOOT_LAYER_PIVOT_LOCATORS_ATTR,
            constants.REVERSE_FOOT_LAYER_IK_HANDLES_ATTR,
            constants.REVERSE_FOOT_LAYER_SETTINGS_NODE_ATTR,
        ]

        for attr_name in required_attrs:
            assert layer.hasAttribute(attr_name), (
                f"Missing attribute: {attr_name}"
            )


@pytest.mark.integration
class TestMetaHumanReverseFootLayerFootControls:
    """Test MetaHumanReverseFootLayer foot control management."""

    def test_foot_controls_empty_initially(self, new_scene):
        """Test that foot controls are empty initially."""

        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        assert layer.foot_controls() == []
        assert layer.foot_control_count() == 0

    def test_add_foot_control(self, new_scene):
        """Test adding a foot control."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        ctrl_name = cmds.circle(name="foot_ik_l_ctrl")[0]
        layer.add_foot_control(node_by_name(ctrl_name))

        assert layer.foot_control_count() == 1
        assert "foot_ik_l_ctrl" in layer.foot_controls()[0].name()

    def test_add_multiple_foot_controls(self, new_scene):
        """Test adding multiple foot controls (left and right)."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        for side in ["l", "r"]:
            ctrl_name = cmds.circle(name=f"foot_ik_{side}_ctrl")[0]
            layer.add_foot_control(node_by_name(ctrl_name))

        assert layer.foot_control_count() == 2

    def test_iterate_foot_controls(self, new_scene):
        """Test iterating over foot controls."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        for side in ["l", "r"]:
            ctrl_name = cmds.circle(name=f"foot_ik_{side}_ctrl")[0]
            layer.add_foot_control(node_by_name(ctrl_name))

        count = 0
        for ctrl in layer.iterate_foot_controls():
            count += 1
            assert ctrl is not None

        assert count == 2


@pytest.mark.integration
class TestMetaHumanReverseFootLayerPivotLocators:
    """Test MetaHumanReverseFootLayer pivot locator management."""

    def test_pivot_locators_empty_initially(self, new_scene):
        """Test that pivot locators are empty initially."""

        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        assert layer.pivot_locators() == []

    def test_add_pivot_locator(self, new_scene):
        """Test adding a pivot locator."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        pivot_name = cmds.spaceLocator(name="heel_pivot_l")[0]
        layer.add_pivot_locator(node_by_name(pivot_name))

        assert len(layer.pivot_locators()) == 1
        assert "heel_pivot_l" in layer.pivot_locators()[0].name()

    def test_add_multiple_pivot_locators(self, new_scene):
        """Test adding multiple pivot locators."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        for pivot in ["heel", "toe", "ball", "bank_in", "bank_out"]:
            pivot_name = cmds.spaceLocator(name=f"{pivot}_pivot_l")[0]
            layer.add_pivot_locator(node_by_name(pivot_name))

        assert len(layer.pivot_locators()) == 5

    def test_iterate_pivot_locators(self, new_scene):
        """Test iterating over pivot locators."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        for pivot in ["heel", "toe", "ball"]:
            pivot_name = cmds.spaceLocator(name=f"{pivot}_pivot")[0]
            layer.add_pivot_locator(node_by_name(pivot_name))

        count = 0
        for locator in layer.iterate_pivot_locators():
            count += 1
            assert locator is not None

        assert count == 3


@pytest.mark.integration
class TestMetaHumanReverseFootLayerIKHandles:
    """Test MetaHumanReverseFootLayer IK handle management."""

    def test_ik_handles_empty_initially(self, new_scene):
        """Test that IK handles are empty initially."""

        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        assert layer.ik_handles() == []

    def test_add_ik_handle(self, new_scene):
        """Test adding an IK handle."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        # Create a simple joint chain for IK
        cmds.select(clear=True)
        cmds.joint(name="start_jnt", position=(0, 2, 0))
        cmds.joint(name="mid_jnt", position=(0, 1, 0))
        cmds.joint(name="end_jnt", position=(0, 0, 0))

        ik_handle = cmds.ikHandle(
            name="leg_ik",
            startJoint="start_jnt",
            endEffector="end_jnt",
            solver="ikRPsolver",
        )[0]

        layer.add_ik_handle(node_by_name(ik_handle))

        assert len(layer.ik_handles()) == 1

    def test_iterate_ik_handles(self, new_scene):
        """Test iterating over IK handles."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        # Create leg IK and ball IK
        for prefix in ["leg", "ball"]:
            cmds.select(clear=True)
            cmds.joint(name=f"{prefix}_start_jnt", position=(0, 2, 0))
            cmds.joint(name=f"{prefix}_end_jnt", position=(0, 0, 0))

            ik_handle = cmds.ikHandle(
                name=f"{prefix}_ik",
                startJoint=f"{prefix}_start_jnt",
                endEffector=f"{prefix}_end_jnt",
                solver="ikSCsolver",
            )[0]
            layer.add_ik_handle(node_by_name(ik_handle))

        count = 0
        for ik in layer.iterate_ik_handles():
            count += 1
            assert ik is not None

        assert count == 2


@pytest.mark.integration
class TestMetaHumanReverseFootLayerSettingsNode:
    """Test MetaHumanReverseFootLayer settings node management."""

    def test_settings_node_none_initially(self, new_scene):
        """Test that settings node is None initially."""

        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        assert layer.settings_node() is None

    def test_connect_settings_node(self, new_scene):
        """Test connecting a settings node."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        settings_name = cmds.spaceLocator(name="reverse_foot_settings")[0]
        layer.connect_settings_node(node_by_name(settings_name))

        assert layer.settings_node() is not None
        assert layer.settings_node().name() == settings_name


@pytest.mark.integration
class TestMetaHumanReverseFootLayerFromRig:
    """Test creating reverse foot layer via MetaMetaHumanRig."""

    def test_create_reverse_foot_layer_from_rig(self, new_scene):
        """Test creating reverse foot layer via rig.create_layer()."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaHumanReverseFootLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_REVERSE_FOOT_LAYER_TYPE,
            hierarchy_name="reverse_foot_grp",
            meta_name="reverse_foot_meta",
        )

        assert layer is not None
        assert layer.exists()
        assert isinstance(layer, MetaHumanReverseFootLayer)


@pytest.mark.integration
class TestMetaHumanReverseFootLayerDeletion:
    """Test MetaHumanReverseFootLayer deletion."""

    def test_delete_layer(self, new_scene):
        """Test deleting the reverse foot layer."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")
        meta_name = layer.name()

        result = layer.delete()

        assert result is True
        assert not cmds.objExists(meta_name)

    def test_delete_layer_with_settings_node(self, new_scene):
        """Test that deleting layer also deletes settings node."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        settings_name = cmds.spaceLocator(name="reverse_foot_settings")[0]
        layer.connect_settings_node(node_by_name(settings_name))

        layer.delete()

        assert not cmds.objExists(settings_name)

    def test_delete_layer_with_pivot_locators(self, new_scene):
        """Test that deleting layer also deletes pivot locators."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        pivot_name = cmds.spaceLocator(name="heel_pivot")[0]
        layer.add_pivot_locator(node_by_name(pivot_name))

        layer.delete()

        assert not cmds.objExists(pivot_name)

    def test_delete_layer_with_ik_handles(self, new_scene):
        """Test that deleting layer also deletes IK handles."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        # Create a simple IK handle
        cmds.select(clear=True)
        cmds.joint(name="start_jnt", position=(0, 2, 0))
        cmds.joint(name="end_jnt", position=(0, 0, 0))
        ik_handle = cmds.ikHandle(
            name="test_ik",
            startJoint="start_jnt",
            endEffector="end_jnt",
            solver="ikSCsolver",
        )[0]

        layer.add_ik_handle(node_by_name(ik_handle))

        layer.delete()

        assert not cmds.objExists(ik_handle)

    def test_delete_layer_preserves_foot_controls(self, new_scene):
        """Test that deleting layer preserves foot controls."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        ctrl_name = cmds.circle(name="foot_ctrl")[0]
        layer.add_foot_control(node_by_name(ctrl_name))

        layer.delete()

        # Control should still exist
        assert cmds.objExists(ctrl_name)
