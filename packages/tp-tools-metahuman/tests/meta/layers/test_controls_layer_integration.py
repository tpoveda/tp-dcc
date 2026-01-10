"""Integration tests for MetaHumanControlsLayer class.

These tests require Maya to be running (via mayapy with maya.standalone).
Run with: mayapy scripts/run_maya_tests.py tests/meta/layers/test_controls_layer_integration.py
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestMetaHumanControlsLayerCreation:
    """Test MetaHumanControlsLayer creation and initialization."""

    def test_create_controls_layer(self, new_scene):
        """Test creating a MetaHumanControlsLayer metanode."""

        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        layer = MetaHumanControlsLayer(name="controls_layer_meta")

        assert layer is not None
        assert layer.exists()
        assert "controls_layer_meta" in layer.name()

    def test_controls_layer_has_correct_type(self, new_scene):
        """Test that the controls layer metanode has the correct type."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        layer = MetaHumanControlsLayer(name="controls_layer_meta")

        assert (
            layer.metaclass_type() == constants.METAHUMAN_CONTROLS_LAYER_TYPE
        )

    def test_controls_layer_has_required_attributes(self, new_scene):
        """Test that the controls layer has all required attributes."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        layer = MetaHumanControlsLayer(name="controls_layer_meta")

        required_attrs = [
            constants.LAYER_ROOT_TRANSFORM_ATTR,
            constants.LAYER_CONTROLS_ATTR,
            constants.LAYER_JOINTS_ATTR,
            constants.CONTROLS_LAYER_SETTINGS_NODE_ATTR,
            constants.CONTROLS_LAYER_VISIBILITY_ATTR,
        ]

        for attr_name in required_attrs:
            assert layer.hasAttribute(attr_name), (
                f"Missing attribute: {attr_name}"
            )


@pytest.mark.integration
class TestMetaHumanControlsLayerVisibility:
    """Test MetaHumanControlsLayer visibility management."""

    def test_default_visibility(self, new_scene):
        """Test that default visibility is True."""

        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        layer = MetaHumanControlsLayer(name="controls_layer_meta")

        assert layer.controls_visibility() is True

    def test_set_visibility(self, new_scene):
        """Test setting visibility."""

        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        layer = MetaHumanControlsLayer(name="controls_layer_meta")
        layer.set_controls_visibility(False)

        assert layer.controls_visibility() is False

    def test_toggle_visibility(self, new_scene):
        """Test toggling visibility."""

        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        layer = MetaHumanControlsLayer(name="controls_layer_meta")

        layer.set_controls_visibility(False)
        assert layer.controls_visibility() is False

        layer.set_controls_visibility(True)
        assert layer.controls_visibility() is True


@pytest.mark.integration
class TestMetaHumanControlsLayerSettingsNode:
    """Test MetaHumanControlsLayer settings node management."""

    def test_settings_node_none_initially(self, new_scene):
        """Test that settings node is None initially."""

        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        layer = MetaHumanControlsLayer(name="controls_layer_meta")

        assert layer.settings_node() is None

    def test_connect_settings_node(self, new_scene):
        """Test connecting a settings node."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        layer = MetaHumanControlsLayer(name="controls_layer_meta")

        # Create a settings node (locator for test)
        settings_name = cmds.spaceLocator(name="controls_settings")[0]
        settings_node = node_by_name(settings_name)

        layer.connect_settings_node(settings_node)

        assert layer.settings_node() is not None
        assert layer.settings_node().name() == settings_name


@pytest.mark.integration
class TestMetaHumanControlsLayerSideFiltering:
    """Test MetaHumanControlsLayer side-based control filtering."""

    def test_left_controls(self, new_scene):
        """Test filtering left-side controls."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        layer = MetaHumanControlsLayer(name="controls_layer_meta")

        # Create controls with side attributes
        for side, name in [
            ("l", "arm_l_ctrl"),
            ("r", "arm_r_ctrl"),
            ("c", "spine_ctrl"),
        ]:
            ctrl_name = cmds.circle(name=name)[0]
            ctrl = node_by_name(ctrl_name)
            cmds.addAttr(
                ctrl_name,
                longName=constants.CONTROL_SIDE_ATTR,
                dataType="string",
            )
            cmds.setAttr(
                f"{ctrl_name}.{constants.CONTROL_SIDE_ATTR}",
                side,
                type="string",
            )
            layer.add_control(ctrl)

        left_ctrls = layer.left_controls()
        assert len(left_ctrls) == 1
        assert "arm_l_ctrl" in left_ctrls[0].name()

    def test_right_controls(self, new_scene):
        """Test filtering right-side controls."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        layer = MetaHumanControlsLayer(name="controls_layer_meta")

        for side, name in [
            ("l", "arm_l_ctrl"),
            ("r", "arm_r_ctrl"),
            ("c", "spine_ctrl"),
        ]:
            ctrl_name = cmds.circle(name=name)[0]
            ctrl = node_by_name(ctrl_name)
            cmds.addAttr(
                ctrl_name,
                longName=constants.CONTROL_SIDE_ATTR,
                dataType="string",
            )
            cmds.setAttr(
                f"{ctrl_name}.{constants.CONTROL_SIDE_ATTR}",
                side,
                type="string",
            )
            layer.add_control(ctrl)

        right_ctrls = layer.right_controls()
        assert len(right_ctrls) == 1
        assert "arm_r_ctrl" in right_ctrls[0].name()

    def test_center_controls(self, new_scene):
        """Test filtering center controls."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        layer = MetaHumanControlsLayer(name="controls_layer_meta")

        for side, name in [
            ("l", "arm_l_ctrl"),
            ("r", "arm_r_ctrl"),
            ("c", "spine_ctrl"),
        ]:
            ctrl_name = cmds.circle(name=name)[0]
            ctrl = node_by_name(ctrl_name)
            cmds.addAttr(
                ctrl_name,
                longName=constants.CONTROL_SIDE_ATTR,
                dataType="string",
            )
            cmds.setAttr(
                f"{ctrl_name}.{constants.CONTROL_SIDE_ATTR}",
                side,
                type="string",
            )
            layer.add_control(ctrl)

        center_ctrls = layer.center_controls()
        assert len(center_ctrls) == 1
        assert "spine_ctrl" in center_ctrls[0].name()


@pytest.mark.integration
class TestMetaHumanControlsLayerFromRig:
    """Test creating controls layer via MetaMetaHumanRig."""

    def test_create_controls_layer_from_rig(self, new_scene):
        """Test creating controls layer via rig.create_layer()."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaHumanControlsLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_CONTROLS_LAYER_TYPE,
            hierarchy_name="controls_grp",
            meta_name="controls_meta",
        )

        assert layer is not None
        assert layer.exists()
        assert isinstance(layer, MetaHumanControlsLayer)

    def test_controls_layer_retrievable_from_rig(self, new_scene):
        """Test that controls layer is retrievable from rig."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaHumanControlsLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_CONTROLS_LAYER_TYPE,
            hierarchy_name="controls_grp",
            meta_name="controls_meta",
        )

        retrieved = meta_rig.controls_layer()
        assert retrieved is not None
        assert retrieved == layer


@pytest.mark.integration
class TestMetaHumanControlsLayerDeletion:
    """Test MetaHumanControlsLayer deletion."""

    def test_delete_layer(self, new_scene):
        """Test deleting the controls layer."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        layer = MetaHumanControlsLayer(name="controls_layer_meta")
        meta_name = layer.name()

        result = layer.delete()

        assert result is True
        assert not cmds.objExists(meta_name)

    def test_delete_layer_with_settings_node(self, new_scene):
        """Test that deleting layer also deletes settings node."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        layer = MetaHumanControlsLayer(name="controls_layer_meta")

        # Create and connect settings node
        settings_name = cmds.spaceLocator(name="controls_settings")[0]
        layer.connect_settings_node(node_by_name(settings_name))

        layer.delete()

        assert not cmds.objExists(settings_name)
