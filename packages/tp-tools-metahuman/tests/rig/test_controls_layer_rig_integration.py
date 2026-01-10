"""Integration tests for Controls Layer integration with body rig builder.

These tests require Maya to be running (via mayapy with maya.standalone).
Run with: mayapy scripts/run_maya_tests.py tests/rig/test_controls_layer_integration.py

These tests focus on Phase 3: Controls Layer integration with the body rig builder.
They test that controls layers are created and controls are properly registered.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestControlsLayerCreation:
    """Test that controls layer is created during rig build."""

    def test_controls_layer_created_via_rig(self, new_scene):
        """Test creating a controls layer through the rig metanode."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanControlsLayer)

        # Create rig metanode
        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        # Create controls layer
        layer = meta_rig.create_layer(
            constants.METAHUMAN_CONTROLS_LAYER_TYPE,
            "controls_layer",
            "controls_layer_meta",
        )

        assert layer is not None
        assert cmds.objExists("controls_layer_meta")
        assert cmds.objExists("controls_layer")

    def test_controls_layer_has_correct_type(self, new_scene):
        """Test that controls layer has the correct type ID."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanControlsLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_CONTROLS_LAYER_TYPE,
            "controls_layer",
            "controls_layer_meta",
        )

        assert (
            layer.metaclass_type() == constants.METAHUMAN_CONTROLS_LAYER_TYPE
        )


@pytest.mark.integration
class TestControlsLayerControlRegistration:
    """Test registering controls with the controls layer."""

    def test_add_single_control(self, new_scene):
        """Test adding a single control to the controls layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        MetaRegistry.register_meta_class(MetaHumanControlsLayer)

        layer = MetaHumanControlsLayer(name="controls_layer_meta")

        # Create a control (nurbsCircle)
        ctrl = cmds.circle(name="spine_01_ctrl")[0]
        ctrl_node = node_by_name(ctrl)

        layer.add_control(ctrl_node)

        # Verify control count
        assert layer.control_count() == 1

    def test_add_multiple_controls(self, new_scene):
        """Test adding multiple controls to the controls layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        MetaRegistry.register_meta_class(MetaHumanControlsLayer)

        layer = MetaHumanControlsLayer(name="controls_layer_meta")

        # Create controls
        ctrl_names = ["global_ctrl", "body_ctrl", "root_ctrl"]
        for name in ctrl_names:
            ctrl = cmds.circle(name=name)[0]
            layer.add_control(node_by_name(ctrl))

        # Verify control count
        assert layer.control_count() == 3

    def test_iterate_controls(self, new_scene):
        """Test iterating over registered controls."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        MetaRegistry.register_meta_class(MetaHumanControlsLayer)

        layer = MetaHumanControlsLayer(name="controls_layer_meta")

        # Create and add controls
        ctrl_names = ["global_ctrl", "body_ctrl", "root_ctrl"]
        for name in ctrl_names:
            ctrl = cmds.circle(name=name)[0]
            layer.add_control(node_by_name(ctrl))

        # Iterate and collect names
        iterated_names = [c.name() for c in layer.iterate_controls()]

        assert len(iterated_names) == 3
        for name in ctrl_names:
            assert name in iterated_names


@pytest.mark.integration
class TestControlsLayerVisibility:
    """Test controls layer visibility management."""

    def test_default_visibility_true(self, new_scene):
        """Test that default visibility is True."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        MetaRegistry.register_meta_class(MetaHumanControlsLayer)

        layer = MetaHumanControlsLayer(name="controls_layer_meta")

        assert layer.controls_visibility() is True

    def test_set_visibility_false(self, new_scene):
        """Test setting visibility to False."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer

        MetaRegistry.register_meta_class(MetaHumanControlsLayer)

        layer = MetaHumanControlsLayer(name="controls_layer_meta")
        layer.set_controls_visibility(False)

        assert layer.controls_visibility() is False


@pytest.mark.integration
class TestBodyRigBuilderControlsLayer:
    """Test controls layer creation in body rig builder context."""

    def test_builder_has_controls_layer_variable(self, new_scene):
        """Test that builder has _controls_layer instance variable."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        # Verify the variable exists and is initially None
        assert hasattr(builder, "_controls_layer")
        assert builder._controls_layer is None

    def test_builder_has_create_controls_layer_method(self, new_scene):
        """Test that builder has _create_controls_layer method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_create_controls_layer")
        assert callable(getattr(builder, "_create_controls_layer"))

    def test_builder_has_register_control_method(self, new_scene):
        """Test that builder has _register_control method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_register_control")
        assert callable(getattr(builder, "_register_control"))

    def test_register_control_method_works(self, new_scene):
        """Test that _register_control registers controls correctly."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanControlsLayer)

        # Create builder and manually set up meta rig and controls layer
        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)
        builder._meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        # Manually create controls layer
        from typing import cast

        layer = builder._meta_rig.create_layer(
            constants.METAHUMAN_CONTROLS_LAYER_TYPE,
            "controls_layer",
            "controls_layer_meta",
        )
        builder._controls_layer = cast(MetaHumanControlsLayer, layer)

        # Create a control
        ctrl = cmds.circle(name="test_ctrl")[0]

        # Register it
        builder._register_control(ctrl)

        # Verify it was registered
        assert builder._controls_layer.control_count() == 1

    def test_register_control_handles_none_layer(self, new_scene):
        """Test that _register_control handles None controls_layer gracefully."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        # Ensure controls_layer is None
        assert builder._controls_layer is None

        # Create a control
        ctrl = cmds.circle(name="test_ctrl")[0]

        # This should not raise an error
        builder._register_control(ctrl)

    def test_register_control_handles_nonexistent_control(self, new_scene):
        """Test that _register_control handles non-existent controls gracefully."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanControlsLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanControlsLayer)

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)
        builder._meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        from typing import cast

        layer = builder._meta_rig.create_layer(
            constants.METAHUMAN_CONTROLS_LAYER_TYPE,
            "controls_layer",
            "controls_layer_meta",
        )
        builder._controls_layer = cast(MetaHumanControlsLayer, layer)

        # Try to register a non-existent control - should not raise
        builder._register_control("nonexistent_ctrl")

        # Verify nothing was registered
        assert builder._controls_layer.control_count() == 0
