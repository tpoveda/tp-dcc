"""Integration tests for MetaHumanSpaceSwitchLayer class.

These tests require Maya to be running (via mayapy with maya.standalone).
Run with: mayapy scripts/run_maya_tests.py tests/meta/layers/test_space_switch_layer_integration.py
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestMetaHumanSpaceSwitchLayerCreation:
    """Test MetaHumanSpaceSwitchLayer creation and initialization."""

    def test_create_space_switch_layer(self, new_scene):
        """Test creating a MetaHumanSpaceSwitchLayer metanode."""

        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        assert layer is not None
        assert layer.exists()
        assert "space_switch_layer_meta" in layer.name()

    def test_space_switch_layer_has_correct_type(self, new_scene):
        """Test that the space switch layer has the correct type."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        assert (
            layer.metaclass_type()
            == constants.METAHUMAN_SPACE_SWITCH_LAYER_TYPE
        )

    def test_space_switch_layer_has_required_attributes(self, new_scene):
        """Test that the space switch layer has all required attributes."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        required_attrs = [
            constants.LAYER_ROOT_TRANSFORM_ATTR,
            constants.SPACE_SWITCH_LAYER_CONTROLS_ATTR,
            constants.SPACE_SWITCH_LAYER_CONSTRAINTS_ATTR,
            constants.SPACE_SWITCH_LAYER_DRIVER_NODES_ATTR,
        ]

        for attr_name in required_attrs:
            assert layer.hasAttribute(attr_name), (
                f"Missing attribute: {attr_name}"
            )


@pytest.mark.integration
class TestMetaHumanSpaceSwitchLayerControls:
    """Test MetaHumanSpaceSwitchLayer space switch control management."""

    def test_space_switch_controls_empty_initially(self, new_scene):
        """Test that space switch controls are empty initially."""

        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        assert layer.space_switch_controls() == []
        assert layer.space_switch_control_count() == 0

    def test_add_space_switch_control(self, new_scene):
        """Test adding a space switch control."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        ctrl_name = cmds.circle(name="hand_ctrl")[0]
        layer.add_space_switch_control(node_by_name(ctrl_name))

        assert layer.space_switch_control_count() == 1
        assert "hand_ctrl" in layer.space_switch_controls()[0].name()

    def test_add_multiple_space_switch_controls(self, new_scene):
        """Test adding multiple space switch controls."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        for name in ["hand_l_ctrl", "hand_r_ctrl", "head_ctrl"]:
            ctrl_name = cmds.circle(name=name)[0]
            layer.add_space_switch_control(node_by_name(ctrl_name))

        assert layer.space_switch_control_count() == 3

    def test_iterate_space_switch_controls(self, new_scene):
        """Test iterating over space switch controls."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        for i in range(3):
            ctrl_name = cmds.circle(name=f"ctrl_{i}")[0]
            layer.add_space_switch_control(node_by_name(ctrl_name))

        count = 0
        for ctrl in layer.iterate_space_switch_controls():
            count += 1
            assert ctrl is not None

        assert count == 3


@pytest.mark.integration
class TestMetaHumanSpaceSwitchLayerConstraints:
    """Test MetaHumanSpaceSwitchLayer constraint management."""

    def test_constraints_empty_initially(self, new_scene):
        """Test that constraints are empty initially."""

        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        assert layer.constraints() == []

    def test_add_constraint(self, new_scene):
        """Test adding a constraint."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        # Create a parent constraint
        src = cmds.spaceLocator(name="source")[0]
        tgt = cmds.spaceLocator(name="target")[0]
        con = cmds.parentConstraint(src, tgt, name="space_con")[0]

        layer.add_constraint(node_by_name(con))

        assert len(layer.constraints()) == 1

    def test_iterate_constraints(self, new_scene):
        """Test iterating over constraints."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        # Create multiple constraints
        for i in range(2):
            src = cmds.spaceLocator(name=f"source_{i}")[0]
            tgt = cmds.spaceLocator(name=f"target_{i}")[0]
            con = cmds.parentConstraint(src, tgt, name=f"space_con_{i}")[0]
            layer.add_constraint(node_by_name(con))

        count = 0
        for con in layer.iterate_constraints():
            count += 1
            assert con is not None

        assert count == 2


@pytest.mark.integration
class TestMetaHumanSpaceSwitchLayerDriverNodes:
    """Test MetaHumanSpaceSwitchLayer driver node management."""

    def test_driver_nodes_empty_initially(self, new_scene):
        """Test that driver nodes are empty initially."""

        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        assert layer.driver_nodes() == []

    def test_add_driver_node(self, new_scene):
        """Test adding a driver node."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        driver_name = cmds.spaceLocator(name="world_space_driver")[0]
        layer.add_driver_node(node_by_name(driver_name))

        assert len(layer.driver_nodes()) == 1
        assert "world_space_driver" in layer.driver_nodes()[0].name()

    def test_iterate_driver_nodes(self, new_scene):
        """Test iterating over driver nodes."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        for space in ["world", "local", "parent"]:
            driver_name = cmds.spaceLocator(name=f"{space}_driver")[0]
            layer.add_driver_node(node_by_name(driver_name))

        count = 0
        for driver in layer.iterate_driver_nodes():
            count += 1
            assert driver is not None

        assert count == 3


@pytest.mark.integration
class TestMetaHumanSpaceSwitchLayerFromRig:
    """Test creating space switch layer via MetaMetaHumanRig."""

    def test_create_space_switch_layer_from_rig(self, new_scene):
        """Test creating space switch layer via rig.create_layer()."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaHumanSpaceSwitchLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_SPACE_SWITCH_LAYER_TYPE,
            hierarchy_name="space_switch_grp",
            meta_name="space_switch_meta",
        )

        assert layer is not None
        assert layer.exists()
        assert isinstance(layer, MetaHumanSpaceSwitchLayer)


@pytest.mark.integration
class TestMetaHumanSpaceSwitchLayerDeletion:
    """Test MetaHumanSpaceSwitchLayer deletion."""

    def test_delete_layer(self, new_scene):
        """Test deleting the space switch layer."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")
        meta_name = layer.name()

        result = layer.delete()

        assert result is True
        assert not cmds.objExists(meta_name)

    def test_delete_layer_with_constraints(self, new_scene):
        """Test that deleting layer also deletes constraints."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        # Create a constraint
        src = cmds.spaceLocator(name="source")[0]
        tgt = cmds.spaceLocator(name="target")[0]
        con = cmds.parentConstraint(src, tgt, name="space_con")[0]
        layer.add_constraint(node_by_name(con))

        layer.delete()

        assert not cmds.objExists(con)

    def test_delete_layer_with_driver_nodes(self, new_scene):
        """Test that deleting layer also deletes driver nodes."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        driver_name = cmds.spaceLocator(name="space_driver")[0]
        layer.add_driver_node(node_by_name(driver_name))

        layer.delete()

        assert not cmds.objExists(driver_name)

    def test_delete_layer_preserves_controls(self, new_scene):
        """Test that deleting layer preserves space switch controls."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        ctrl_name = cmds.circle(name="hand_ctrl")[0]
        layer.add_space_switch_control(node_by_name(ctrl_name))

        layer.delete()

        # Control should still exist
        assert cmds.objExists(ctrl_name)
