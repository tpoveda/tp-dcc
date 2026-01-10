"""Integration tests for MetaHumanFKIKLayer class.

These tests require Maya to be running (via mayapy with maya.standalone).
Run with: mayapy scripts/run_maya_tests.py tests/meta/layers/test_fkik_layer_integration.py
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestMetaHumanFKIKLayerCreation:
    """Test MetaHumanFKIKLayer creation and initialization."""

    def test_create_fkik_layer(self, new_scene):
        """Test creating a MetaHumanFKIKLayer metanode."""

        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        assert layer is not None
        assert layer.exists()
        assert "fkik_layer_meta" in layer.name()

    def test_fkik_layer_has_correct_type(self, new_scene):
        """Test that the FK/IK layer metanode has the correct type."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        assert layer.metaclass_type() == constants.METAHUMAN_FKIK_LAYER_TYPE

    def test_fkik_layer_has_required_attributes(self, new_scene):
        """Test that the FK/IK layer has all required attributes."""

        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        required_attrs = [
            constants.LAYER_ROOT_TRANSFORM_ATTR,
            constants.FKIK_LAYER_FK_CONTROLS_ATTR,
            constants.FKIK_LAYER_IK_CONTROLS_ATTR,
            constants.FKIK_LAYER_POLE_VECTORS_ATTR,
            constants.FKIK_LAYER_BLEND_NODES_ATTR,
            constants.FKIK_LAYER_SETTINGS_NODE_ATTR,
        ]

        for attr_name in required_attrs:
            assert layer.hasAttribute(attr_name), (
                f"Missing attribute: {attr_name}"
            )


@pytest.mark.integration
class TestMetaHumanFKIKLayerFKControls:
    """Test MetaHumanFKIKLayer FK control management."""

    def test_fk_controls_empty_initially(self, new_scene):
        """Test that FK controls are empty initially."""

        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        assert layer.fk_controls() == []
        assert layer.fk_control_count() == 0

    def test_add_fk_control(self, new_scene):
        """Test adding an FK control."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        ctrl_name = cmds.circle(name="fk_shoulder_ctrl")[0]
        layer.add_fk_control(node_by_name(ctrl_name))

        assert layer.fk_control_count() == 1
        assert "fk_shoulder_ctrl" in layer.fk_controls()[0].name()

    def test_add_multiple_fk_controls(self, new_scene):
        """Test adding multiple FK controls."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        for i in range(3):
            ctrl_name = cmds.circle(name=f"fk_ctrl_{i}")[0]
            layer.add_fk_control(node_by_name(ctrl_name))

        assert layer.fk_control_count() == 3

    def test_iterate_fk_controls(self, new_scene):
        """Test iterating over FK controls."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        for i in range(3):
            ctrl_name = cmds.circle(name=f"fk_ctrl_{i}")[0]
            layer.add_fk_control(node_by_name(ctrl_name))

        count = 0
        for ctrl in layer.iterate_fk_controls():
            count += 1
            assert ctrl is not None

        assert count == 3


@pytest.mark.integration
class TestMetaHumanFKIKLayerIKControls:
    """Test MetaHumanFKIKLayer IK control management."""

    def test_ik_controls_empty_initially(self, new_scene):
        """Test that IK controls are empty initially."""

        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        assert layer.ik_controls() == []
        assert layer.ik_control_count() == 0

    def test_add_ik_control(self, new_scene):
        """Test adding an IK control."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        ctrl_name = cmds.circle(name="ik_hand_ctrl")[0]
        layer.add_ik_control(node_by_name(ctrl_name))

        assert layer.ik_control_count() == 1
        assert "ik_hand_ctrl" in layer.ik_controls()[0].name()

    def test_iterate_ik_controls(self, new_scene):
        """Test iterating over IK controls."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        for i in range(2):
            ctrl_name = cmds.circle(name=f"ik_ctrl_{i}")[0]
            layer.add_ik_control(node_by_name(ctrl_name))

        count = 0
        for ctrl in layer.iterate_ik_controls():
            count += 1
            assert ctrl is not None

        assert count == 2


@pytest.mark.integration
class TestMetaHumanFKIKLayerPoleVectors:
    """Test MetaHumanFKIKLayer pole vector management."""

    def test_pole_vectors_empty_initially(self, new_scene):
        """Test that pole vectors are empty initially."""

        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        assert layer.pole_vectors() == []

    def test_add_pole_vector(self, new_scene):
        """Test adding a pole vector."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        pv_name = cmds.spaceLocator(name="arm_pv")[0]
        layer.add_pole_vector(node_by_name(pv_name))

        assert len(layer.pole_vectors()) == 1
        assert "arm_pv" in layer.pole_vectors()[0].name()

    def test_iterate_pole_vectors(self, new_scene):
        """Test iterating over pole vectors."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        for side in ["l", "r"]:
            pv_name = cmds.spaceLocator(name=f"arm_pv_{side}")[0]
            layer.add_pole_vector(node_by_name(pv_name))

        count = 0
        for pv in layer.iterate_pole_vectors():
            count += 1
            assert pv is not None

        assert count == 2


@pytest.mark.integration
class TestMetaHumanFKIKLayerBlendNodes:
    """Test MetaHumanFKIKLayer blend node management."""

    def test_blend_nodes_empty_initially(self, new_scene):
        """Test that blend nodes are empty initially."""

        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        assert layer.blend_nodes() == []

    def test_add_blend_node(self, new_scene):
        """Test adding a blend node."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        # Create a blend node (using a blendColors node for test)
        blend_name = cmds.createNode("blendColors", name="arm_fkik_blend")
        layer.add_blend_node(node_by_name(blend_name))

        assert len(layer.blend_nodes()) == 1


@pytest.mark.integration
class TestMetaHumanFKIKLayerSettingsNode:
    """Test MetaHumanFKIKLayer settings node management."""

    def test_settings_node_none_initially(self, new_scene):
        """Test that settings node is None initially."""

        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        assert layer.settings_node() is None

    def test_connect_settings_node(self, new_scene):
        """Test connecting a settings node."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        settings_name = cmds.spaceLocator(name="fkik_settings")[0]
        layer.connect_settings_node(node_by_name(settings_name))

        assert layer.settings_node() is not None
        assert layer.settings_node().name() == settings_name


@pytest.mark.integration
class TestMetaHumanFKIKLayerFromRig:
    """Test creating FK/IK layer via MetaMetaHumanRig."""

    def test_create_fkik_layer_from_rig(self, new_scene):
        """Test creating FK/IK layer via rig.create_layer()."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaHumanFKIKLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_FKIK_LAYER_TYPE,
            hierarchy_name="fkik_grp",
            meta_name="fkik_meta",
        )

        assert layer is not None
        assert layer.exists()
        assert isinstance(layer, MetaHumanFKIKLayer)

    def test_fkik_layer_retrievable_from_rig(self, new_scene):
        """Test that FK/IK layer is retrievable from rig."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaHumanFKIKLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_FKIK_LAYER_TYPE,
            hierarchy_name="fkik_grp",
            meta_name="fkik_meta",
        )

        retrieved = meta_rig.fkik_layer()
        assert retrieved is not None
        assert retrieved == layer


@pytest.mark.integration
class TestMetaHumanFKIKLayerDeletion:
    """Test MetaHumanFKIKLayer deletion."""

    def test_delete_layer(self, new_scene):
        """Test deleting the FK/IK layer."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")
        meta_name = layer.name()

        result = layer.delete()

        assert result is True
        assert not cmds.objExists(meta_name)

    def test_delete_layer_with_settings_node(self, new_scene):
        """Test that deleting layer also deletes settings node."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        settings_name = cmds.spaceLocator(name="fkik_settings")[0]
        layer.connect_settings_node(node_by_name(settings_name))

        layer.delete()

        assert not cmds.objExists(settings_name)

    def test_delete_layer_with_blend_nodes(self, new_scene):
        """Test that deleting layer also deletes blend nodes."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        blend_name = cmds.createNode("blendColors", name="arm_fkik_blend")
        layer.add_blend_node(node_by_name(blend_name))

        layer.delete()

        assert not cmds.objExists(blend_name)

    def test_delete_layer_preserves_controls(self, new_scene):
        """Test that deleting layer preserves FK and IK controls."""

        import maya.cmds as cmds

        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        fk_ctrl_name = cmds.circle(name="fk_ctrl")[0]
        ik_ctrl_name = cmds.circle(name="ik_ctrl")[0]
        layer.add_fk_control(node_by_name(fk_ctrl_name))
        layer.add_ik_control(node_by_name(ik_ctrl_name))

        layer.delete()

        # Controls should still exist
        assert cmds.objExists(fk_ctrl_name)
        assert cmds.objExists(ik_ctrl_name)
