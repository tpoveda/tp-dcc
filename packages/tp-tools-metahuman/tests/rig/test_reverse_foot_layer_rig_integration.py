"""Integration tests for Reverse Foot Layer integration with body rig builder.

These tests require Maya to be running (via mayapy with maya.standalone).
Run with: mayapy scripts/run_maya_tests.py tests/rig/test_reverse_foot_layer_rig_integration.py

These tests focus on Phase 5: Reverse Foot Layer integration with the body rig builder.
They test that reverse foot layers are created and components are properly registered.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestReverseFootLayerCreation:
    """Test that reverse foot layer is created during rig build."""

    def test_reverse_foot_layer_created_via_rig(self, new_scene):
        """Test creating a reverse foot layer through the rig metanode."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanReverseFootLayer)

        # Create rig metanode
        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        # Create reverse foot layer
        layer = meta_rig.create_layer(
            constants.METAHUMAN_REVERSE_FOOT_LAYER_TYPE,
            "reverse_foot_layer",
            "reverse_foot_layer_meta",
        )

        assert layer is not None
        assert cmds.objExists("reverse_foot_layer_meta")
        assert cmds.objExists("reverse_foot_layer")

    def test_reverse_foot_layer_has_correct_type(self, new_scene):
        """Test that reverse foot layer has the correct type ID."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanReverseFootLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_REVERSE_FOOT_LAYER_TYPE,
            "reverse_foot_layer",
            "reverse_foot_layer_meta",
        )

        assert (
            layer.metaclass_type()
            == constants.METAHUMAN_REVERSE_FOOT_LAYER_TYPE
        )


@pytest.mark.integration
class TestReverseFootLayerFootControlRegistration:
    """Test registering foot controls with the reverse foot layer."""

    def test_add_single_foot_control(self, new_scene):
        """Test adding a single foot control to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        MetaRegistry.register_meta_class(MetaHumanReverseFootLayer)

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        # Create a foot control
        ctrl = cmds.circle(name="foot_l_ik_ctrl")[0]
        ctrl_node = node_by_name(ctrl)

        layer.add_foot_control(ctrl_node)

        assert layer.foot_control_count() == 1

    def test_add_multiple_foot_controls(self, new_scene):
        """Test adding multiple foot controls to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        MetaRegistry.register_meta_class(MetaHumanReverseFootLayer)

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        # Create foot controls for both sides
        foot_names = ["foot_l_ik_ctrl", "foot_r_ik_ctrl"]
        for name in foot_names:
            ctrl = cmds.circle(name=name)[0]
            layer.add_foot_control(node_by_name(ctrl))

        assert layer.foot_control_count() == 2


@pytest.mark.integration
class TestReverseFootLayerPivotLocatorRegistration:
    """Test registering pivot locators with the reverse foot layer."""

    def test_add_single_pivot_locator(self, new_scene):
        """Test adding a single pivot locator to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        MetaRegistry.register_meta_class(MetaHumanReverseFootLayer)

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        # Create a pivot locator
        locator = cmds.spaceLocator(name="heel_pivot_l_loc")[0]
        locator_node = node_by_name(locator)

        layer.add_pivot_locator(locator_node)

        pivots = layer.pivot_locators()
        assert len(pivots) == 1

    def test_add_multiple_pivot_locators(self, new_scene):
        """Test adding multiple pivot locators to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        MetaRegistry.register_meta_class(MetaHumanReverseFootLayer)

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        # Create pivot locators
        pivot_names = [
            "heel_pivot_l_loc",
            "toe_pivot_l_loc",
            "ball_pivot_l_loc",
        ]
        for name in pivot_names:
            loc = cmds.spaceLocator(name=name)[0]
            layer.add_pivot_locator(node_by_name(loc))

        pivots = layer.pivot_locators()
        assert len(pivots) == 3


@pytest.mark.integration
class TestReverseFootLayerIKHandleRegistration:
    """Test registering IK handles with the reverse foot layer."""

    def test_add_single_ik_handle(self, new_scene):
        """Test adding a single IK handle to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )

        MetaRegistry.register_meta_class(MetaHumanReverseFootLayer)

        layer = MetaHumanReverseFootLayer(name="reverse_foot_layer_meta")

        # Create joints for IK handle
        cmds.select(clear=True)
        start = cmds.joint(name="foot_l")
        end = cmds.joint(name="ball_l")

        # Create IK handle
        ik_handle = cmds.ikHandle(
            name="foot_l_ikHandle",
            startJoint=start,
            endEffector=end,
            solver="ikSCsolver",
        )[0]

        handle_node = node_by_name(ik_handle)
        layer.add_ik_handle(handle_node)

        handles = layer.ik_handles()
        assert len(handles) == 1


@pytest.mark.integration
class TestBodyRigBuilderReverseFootLayer:
    """Test reverse foot layer creation in body rig builder context."""

    def test_builder_has_reverse_foot_layer_variable(self, new_scene):
        """Test that builder has _reverse_foot_layer instance variable."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_reverse_foot_layer")
        assert builder._reverse_foot_layer is None

    def test_builder_has_create_reverse_foot_layer_method(self, new_scene):
        """Test that builder has _create_reverse_foot_layer method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_create_reverse_foot_layer")
        assert callable(getattr(builder, "_create_reverse_foot_layer"))

    def test_builder_has_register_foot_control_method(self, new_scene):
        """Test that builder has _register_foot_control method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_register_foot_control")
        assert callable(getattr(builder, "_register_foot_control"))

    def test_builder_has_register_pivot_locator_method(self, new_scene):
        """Test that builder has _register_pivot_locator method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_register_pivot_locator")
        assert callable(getattr(builder, "_register_pivot_locator"))

    def test_builder_has_register_ik_handle_method(self, new_scene):
        """Test that builder has _register_ik_handle method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_register_ik_handle")
        assert callable(getattr(builder, "_register_ik_handle"))

    def test_builder_has_register_components_method(self, new_scene):
        """Test that builder has _register_reverse_foot_components method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_register_reverse_foot_components")
        assert callable(getattr(builder, "_register_reverse_foot_components"))

    def test_register_foot_control_method_works(self, new_scene):
        """Test that _register_foot_control registers controls correctly."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanReverseFootLayer)

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)
        builder._meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        from typing import cast

        layer = builder._meta_rig.create_layer(
            constants.METAHUMAN_REVERSE_FOOT_LAYER_TYPE,
            "reverse_foot_layer",
            "reverse_foot_layer_meta",
        )
        builder._reverse_foot_layer = cast(MetaHumanReverseFootLayer, layer)

        # Create and register a foot control
        ctrl = cmds.circle(name="foot_l_ik_ctrl")[0]
        builder._register_foot_control(ctrl)

        assert builder._reverse_foot_layer.foot_control_count() == 1

    def test_register_pivot_locator_method_works(self, new_scene):
        """Test that _register_pivot_locator registers locators correctly."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanReverseFootLayer)

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)
        builder._meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        from typing import cast

        layer = builder._meta_rig.create_layer(
            constants.METAHUMAN_REVERSE_FOOT_LAYER_TYPE,
            "reverse_foot_layer",
            "reverse_foot_layer_meta",
        )
        builder._reverse_foot_layer = cast(MetaHumanReverseFootLayer, layer)

        # Create and register a pivot locator
        loc = cmds.spaceLocator(name="heel_pivot_l_loc")[0]
        builder._register_pivot_locator(loc)

        assert len(builder._reverse_foot_layer.pivot_locators()) == 1

    def test_register_methods_handle_none_layer(self, new_scene):
        """Test that register methods handle None layer gracefully."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert builder._reverse_foot_layer is None

        # Create components
        ctrl = cmds.circle(name="foot_l_ik_ctrl")[0]
        loc = cmds.spaceLocator(name="heel_pivot_l_loc")[0]

        # These should not raise errors
        builder._register_foot_control(ctrl)
        builder._register_pivot_locator(loc)

    def test_register_methods_handle_nonexistent_nodes(self, new_scene):
        """Test that register methods handle non-existent nodes gracefully."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanReverseFootLayer,
        )
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanReverseFootLayer)

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)
        builder._meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        from typing import cast

        layer = builder._meta_rig.create_layer(
            constants.METAHUMAN_REVERSE_FOOT_LAYER_TYPE,
            "reverse_foot_layer",
            "reverse_foot_layer_meta",
        )
        builder._reverse_foot_layer = cast(MetaHumanReverseFootLayer, layer)

        # Try to register non-existent nodes - should not raise
        builder._register_foot_control("nonexistent_ctrl")
        builder._register_pivot_locator("nonexistent_loc")
        builder._register_ik_handle("nonexistent_handle")

        # Verify nothing was registered
        assert builder._reverse_foot_layer.foot_control_count() == 0
        assert len(builder._reverse_foot_layer.pivot_locators()) == 0
        assert len(builder._reverse_foot_layer.ik_handles()) == 0
