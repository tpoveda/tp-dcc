"""Integration tests for Space Switch Layer integration with body rig builder.

These tests require Maya to be running (via mayapy with maya.standalone).
Run with: mayapy scripts/run_maya_tests.py tests/rig/test_space_switch_layer_rig_integration.py

These tests focus on Phase 6: Space Switch Layer integration with the body rig builder.
They test that space switch layers are created and components are properly registered.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestSpaceSwitchLayerCreation:
    """Test that space switch layer is created during rig build."""

    def test_space_switch_layer_created_via_rig(self, new_scene):
        """Test creating a space switch layer through the rig metanode."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanSpaceSwitchLayer)

        # Create rig metanode
        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        # Create space switch layer
        layer = meta_rig.create_layer(
            constants.METAHUMAN_SPACE_SWITCH_LAYER_TYPE,
            "space_switch_layer",
            "space_switch_layer_meta",
        )

        assert layer is not None
        assert cmds.objExists("space_switch_layer_meta")
        assert cmds.objExists("space_switch_layer")

    def test_space_switch_layer_has_correct_type(self, new_scene):
        """Test that space switch layer has the correct type ID."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanSpaceSwitchLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_SPACE_SWITCH_LAYER_TYPE,
            "space_switch_layer",
            "space_switch_layer_meta",
        )

        assert (
            layer.metaclass_type()
            == constants.METAHUMAN_SPACE_SWITCH_LAYER_TYPE
        )


@pytest.mark.integration
class TestSpaceSwitchLayerControlRegistration:
    """Test registering space switch controls with the layer."""

    def test_add_single_space_switch_control(self, new_scene):
        """Test adding a single space switch control to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        MetaRegistry.register_meta_class(MetaHumanSpaceSwitchLayer)

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        # Create a space switch control
        ctrl = cmds.circle(name="hand_l_ik_ctrl")[0]
        ctrl_node = node_by_name(ctrl)

        layer.add_space_switch_control(ctrl_node)

        assert layer.space_switch_control_count() == 1

    def test_add_multiple_space_switch_controls(self, new_scene):
        """Test adding multiple space switch controls to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        MetaRegistry.register_meta_class(MetaHumanSpaceSwitchLayer)

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        # Create space switch controls
        ctrl_names = [
            "hand_l_ik_ctrl",
            "hand_r_ik_ctrl",
            "arm_pole_vector_l_ctrl",
        ]
        for name in ctrl_names:
            ctrl = cmds.circle(name=name)[0]
            layer.add_space_switch_control(node_by_name(ctrl))

        assert layer.space_switch_control_count() == 3


@pytest.mark.integration
class TestSpaceSwitchLayerConstraintRegistration:
    """Test registering space switch constraints with the layer."""

    def test_add_single_constraint(self, new_scene):
        """Test adding a single constraint to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        MetaRegistry.register_meta_class(MetaHumanSpaceSwitchLayer)

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        # Create objects for constraint
        driver = cmds.group(empty=True, name="driver_grp")
        driven = cmds.group(empty=True, name="driven_grp")

        # Create constraint
        constraint = cmds.parentConstraint(
            driver, driven, name="hand_l_ik_space_con"
        )[0]

        constraint_node = node_by_name(constraint)
        layer.add_constraint(constraint_node)

        constraints = layer.constraints()
        assert len(constraints) == 1

    def test_add_multiple_constraints(self, new_scene):
        """Test adding multiple constraints to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )

        MetaRegistry.register_meta_class(MetaHumanSpaceSwitchLayer)

        layer = MetaHumanSpaceSwitchLayer(name="space_switch_layer_meta")

        # Create multiple constraints
        for i in range(3):
            driver = cmds.group(empty=True, name=f"driver_{i}_grp")
            driven = cmds.group(empty=True, name=f"driven_{i}_grp")
            constraint = cmds.parentConstraint(
                driver, driven, name=f"space_con_{i}"
            )[0]
            layer.add_constraint(node_by_name(constraint))

        constraints = layer.constraints()
        assert len(constraints) == 3


@pytest.mark.integration
class TestBodyRigBuilderSpaceSwitchLayer:
    """Test space switch layer creation in body rig builder context."""

    def test_builder_has_space_switch_layer_variable(self, new_scene):
        """Test that builder has _space_switch_layer instance variable."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_space_switch_layer")
        assert builder._space_switch_layer is None

    def test_builder_has_create_space_switch_layer_method(self, new_scene):
        """Test that builder has _create_space_switch_layer method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_create_space_switch_layer")
        assert callable(getattr(builder, "_create_space_switch_layer"))

    def test_builder_has_register_control_method(self, new_scene):
        """Test that builder has _register_space_switch_control method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_register_space_switch_control")
        assert callable(getattr(builder, "_register_space_switch_control"))

    def test_builder_has_register_constraint_method(self, new_scene):
        """Test that builder has _register_space_switch_constraint method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_register_space_switch_constraint")
        assert callable(getattr(builder, "_register_space_switch_constraint"))

    def test_builder_has_register_components_method(self, new_scene):
        """Test that builder has _register_space_switch_components method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_register_space_switch_components")
        assert callable(getattr(builder, "_register_space_switch_components"))

    def test_register_control_method_works(self, new_scene):
        """Test that _register_space_switch_control works correctly."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanSpaceSwitchLayer)

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)
        builder._meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        from typing import cast

        layer = builder._meta_rig.create_layer(
            constants.METAHUMAN_SPACE_SWITCH_LAYER_TYPE,
            "space_switch_layer",
            "space_switch_layer_meta",
        )
        builder._space_switch_layer = cast(MetaHumanSpaceSwitchLayer, layer)

        # Create and register a control
        ctrl = cmds.circle(name="hand_l_ik_ctrl")[0]
        builder._register_space_switch_control(ctrl)

        assert builder._space_switch_layer.space_switch_control_count() == 1

    def test_register_constraint_method_works(self, new_scene):
        """Test that _register_space_switch_constraint works correctly."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanSpaceSwitchLayer)

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)
        builder._meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        from typing import cast

        layer = builder._meta_rig.create_layer(
            constants.METAHUMAN_SPACE_SWITCH_LAYER_TYPE,
            "space_switch_layer",
            "space_switch_layer_meta",
        )
        builder._space_switch_layer = cast(MetaHumanSpaceSwitchLayer, layer)

        # Create and register a constraint
        driver = cmds.group(empty=True, name="driver_grp")
        driven = cmds.group(empty=True, name="driven_grp")
        constraint = cmds.parentConstraint(
            driver, driven, name="hand_l_ik_space_con"
        )[0]

        builder._register_space_switch_constraint(constraint)

        assert len(builder._space_switch_layer.constraints()) == 1

    def test_register_methods_handle_none_layer(self, new_scene):
        """Test that register methods handle None layer gracefully."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert builder._space_switch_layer is None

        # Create components
        ctrl = cmds.circle(name="hand_l_ik_ctrl")[0]

        # These should not raise errors
        builder._register_space_switch_control(ctrl)

    def test_register_methods_handle_nonexistent_nodes(self, new_scene):
        """Test that register methods handle non-existent nodes gracefully."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import (
            MetaHumanSpaceSwitchLayer,
        )
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanSpaceSwitchLayer)

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)
        builder._meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        from typing import cast

        layer = builder._meta_rig.create_layer(
            constants.METAHUMAN_SPACE_SWITCH_LAYER_TYPE,
            "space_switch_layer",
            "space_switch_layer_meta",
        )
        builder._space_switch_layer = cast(MetaHumanSpaceSwitchLayer, layer)

        # Try to register non-existent nodes - should not raise
        builder._register_space_switch_control("nonexistent_ctrl")
        builder._register_space_switch_constraint("nonexistent_con")

        # Verify nothing was registered
        assert builder._space_switch_layer.space_switch_control_count() == 0
        assert len(builder._space_switch_layer.constraints()) == 0
