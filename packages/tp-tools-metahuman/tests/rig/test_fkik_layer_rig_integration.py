"""Integration tests for FK/IK Layer integration with body rig builder.

These tests require Maya to be running (via mayapy with maya.standalone).
Run with: mayapy scripts/run_maya_tests.py tests/rig/test_fkik_layer_rig_integration.py

These tests focus on Phase 4: FK/IK Layer integration with the body rig builder.
They test that FK/IK layers are created and FK/IK controls are properly registered.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestFKIKLayerCreation:
    """Test that FK/IK layer is created during rig build."""

    def test_fkik_layer_created_via_rig(self, new_scene):
        """Test creating an FK/IK layer through the rig metanode."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanFKIKLayer)

        # Create rig metanode
        meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        # Create FK/IK layer
        layer = meta_rig.create_layer(
            constants.METAHUMAN_FKIK_LAYER_TYPE,
            "fkik_layer",
            "fkik_layer_meta",
        )

        assert layer is not None
        assert cmds.objExists("fkik_layer_meta")
        assert cmds.objExists("fkik_layer")

    def test_fkik_layer_has_correct_type(self, new_scene):
        """Test that FK/IK layer has the correct type ID."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanFKIKLayer)

        meta_rig = MetaMetaHumanRig(name="test_rig_meta")
        layer = meta_rig.create_layer(
            constants.METAHUMAN_FKIK_LAYER_TYPE,
            "fkik_layer",
            "fkik_layer_meta",
        )

        assert layer.metaclass_type() == constants.METAHUMAN_FKIK_LAYER_TYPE


@pytest.mark.integration
class TestFKIKLayerFKControlRegistration:
    """Test registering FK controls with the FK/IK layer."""

    def test_add_single_fk_control(self, new_scene):
        """Test adding a single FK control to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        MetaRegistry.register_meta_class(MetaHumanFKIKLayer)

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        # Create an FK control
        ctrl = cmds.circle(name="upperarm_l_fk_ctrl")[0]
        ctrl_node = node_by_name(ctrl)

        layer.add_fk_control(ctrl_node)

        assert layer.fk_control_count() == 1

    def test_add_multiple_fk_controls(self, new_scene):
        """Test adding multiple FK controls to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        MetaRegistry.register_meta_class(MetaHumanFKIKLayer)

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        # Create FK controls
        fk_names = [
            "upperarm_l_fk_ctrl",
            "lowerarm_l_fk_ctrl",
            "hand_l_fk_ctrl",
        ]
        for name in fk_names:
            ctrl = cmds.circle(name=name)[0]
            layer.add_fk_control(node_by_name(ctrl))

        assert layer.fk_control_count() == 3


@pytest.mark.integration
class TestFKIKLayerIKControlRegistration:
    """Test registering IK controls with the FK/IK layer."""

    def test_add_single_ik_control(self, new_scene):
        """Test adding a single IK control to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        MetaRegistry.register_meta_class(MetaHumanFKIKLayer)

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        # Create an IK control
        ctrl = cmds.circle(name="hand_l_ik_ctrl")[0]
        ctrl_node = node_by_name(ctrl)

        layer.add_ik_control(ctrl_node)

        assert layer.ik_control_count() == 1

    def test_add_multiple_ik_controls(self, new_scene):
        """Test adding multiple IK controls to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        MetaRegistry.register_meta_class(MetaHumanFKIKLayer)

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        # Create IK controls
        ik_names = ["hand_l_ik_ctrl", "hand_r_ik_ctrl", "foot_l_ik_ctrl"]
        for name in ik_names:
            ctrl = cmds.circle(name=name)[0]
            layer.add_ik_control(node_by_name(ctrl))

        assert layer.ik_control_count() == 3


@pytest.mark.integration
class TestFKIKLayerPoleVectorRegistration:
    """Test registering pole vector controls with the FK/IK layer."""

    def test_add_single_pole_vector(self, new_scene):
        """Test adding a single pole vector to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        MetaRegistry.register_meta_class(MetaHumanFKIKLayer)

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        # Create a pole vector control
        ctrl = cmds.circle(name="arm_pole_vector_l_ctrl")[0]
        ctrl_node = node_by_name(ctrl)

        layer.add_pole_vector(ctrl_node)

        pv_list = layer.pole_vectors()
        assert len(pv_list) == 1

    def test_add_multiple_pole_vectors(self, new_scene):
        """Test adding multiple pole vectors to the layer."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.wrapper import node_by_name
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer

        MetaRegistry.register_meta_class(MetaHumanFKIKLayer)

        layer = MetaHumanFKIKLayer(name="fkik_layer_meta")

        # Create pole vector controls
        pv_names = [
            "arm_pole_vector_l_ctrl",
            "arm_pole_vector_r_ctrl",
            "leg_pole_vector_l_ctrl",
            "leg_pole_vector_r_ctrl",
        ]
        for name in pv_names:
            ctrl = cmds.circle(name=name)[0]
            layer.add_pole_vector(node_by_name(ctrl))

        pv_list = layer.pole_vectors()
        assert len(pv_list) == 4


@pytest.mark.integration
class TestBodyRigBuilderFKIKLayer:
    """Test FK/IK layer creation in body rig builder context."""

    def test_builder_has_fkik_layer_variable(self, new_scene):
        """Test that builder has _fkik_layer instance variable."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_fkik_layer")
        assert builder._fkik_layer is None

    def test_builder_has_create_fkik_layer_method(self, new_scene):
        """Test that builder has _create_fkik_layer method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_create_fkik_layer")
        assert callable(getattr(builder, "_create_fkik_layer"))

    def test_builder_has_register_fk_control_method(self, new_scene):
        """Test that builder has _register_fk_control method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_register_fk_control")
        assert callable(getattr(builder, "_register_fk_control"))

    def test_builder_has_register_ik_control_method(self, new_scene):
        """Test that builder has _register_ik_control method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_register_ik_control")
        assert callable(getattr(builder, "_register_ik_control"))

    def test_builder_has_register_pole_vector_method(self, new_scene):
        """Test that builder has _register_pole_vector method."""

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert hasattr(builder, "_register_pole_vector")
        assert callable(getattr(builder, "_register_pole_vector"))

    def test_register_fk_control_method_works(self, new_scene):
        """Test that _register_fk_control registers controls correctly."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanFKIKLayer)

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)
        builder._meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        from typing import cast

        layer = builder._meta_rig.create_layer(
            constants.METAHUMAN_FKIK_LAYER_TYPE,
            "fkik_layer",
            "fkik_layer_meta",
        )
        builder._fkik_layer = cast(MetaHumanFKIKLayer, layer)

        # Create and register an FK control
        ctrl = cmds.circle(name="test_fk_ctrl")[0]
        builder._register_fk_control(ctrl)

        assert builder._fkik_layer.fk_control_count() == 1

    def test_register_ik_control_method_works(self, new_scene):
        """Test that _register_ik_control registers controls correctly."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanFKIKLayer)

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)
        builder._meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        from typing import cast

        layer = builder._meta_rig.create_layer(
            constants.METAHUMAN_FKIK_LAYER_TYPE,
            "fkik_layer",
            "fkik_layer_meta",
        )
        builder._fkik_layer = cast(MetaHumanFKIKLayer, layer)

        # Create and register an IK control
        ctrl = cmds.circle(name="test_ik_ctrl")[0]
        builder._register_ik_control(ctrl)

        assert builder._fkik_layer.ik_control_count() == 1

    def test_register_pole_vector_method_works(self, new_scene):
        """Test that _register_pole_vector registers controls correctly."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanFKIKLayer)

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)
        builder._meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        from typing import cast

        layer = builder._meta_rig.create_layer(
            constants.METAHUMAN_FKIK_LAYER_TYPE,
            "fkik_layer",
            "fkik_layer_meta",
        )
        builder._fkik_layer = cast(MetaHumanFKIKLayer, layer)

        # Create and register a pole vector control
        ctrl = cmds.circle(name="test_pv_ctrl")[0]
        builder._register_pole_vector(ctrl)

        assert len(builder._fkik_layer.pole_vectors()) == 1

    def test_register_methods_handle_none_layer(self, new_scene):
        """Test that register methods handle None fkik_layer gracefully."""

        import maya.cmds as cmds

        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)

        assert builder._fkik_layer is None

        # Create controls
        fk_ctrl = cmds.circle(name="test_fk_ctrl")[0]
        ik_ctrl = cmds.circle(name="test_ik_ctrl")[0]
        pv_ctrl = cmds.circle(name="test_pv_ctrl")[0]

        # These should not raise errors
        builder._register_fk_control(fk_ctrl)
        builder._register_ik_control(ik_ctrl)
        builder._register_pole_vector(pv_ctrl)

    def test_register_methods_handle_nonexistent_controls(self, new_scene):
        """Test that register methods handle non-existent controls gracefully."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.tools.metahuman.rig.body_rig_builder import (
            MetaHumanBodyRigBuilder,
        )
        from tp.tools.metahuman.rig.meta import constants
        from tp.tools.metahuman.rig.meta.layers import MetaHumanFKIKLayer
        from tp.tools.metahuman.rig.meta.rig import MetaMetaHumanRig

        MetaRegistry.register_meta_class(MetaMetaHumanRig)
        MetaRegistry.register_meta_class(MetaHumanFKIKLayer)

        builder = MetaHumanBodyRigBuilder(motion=True, show_dialogs=False)
        builder._meta_rig = MetaMetaHumanRig(name="test_rig_meta")

        from typing import cast

        layer = builder._meta_rig.create_layer(
            constants.METAHUMAN_FKIK_LAYER_TYPE,
            "fkik_layer",
            "fkik_layer_meta",
        )
        builder._fkik_layer = cast(MetaHumanFKIKLayer, layer)

        # Try to register non-existent controls - should not raise
        builder._register_fk_control("nonexistent_fk_ctrl")
        builder._register_ik_control("nonexistent_ik_ctrl")
        builder._register_pole_vector("nonexistent_pv_ctrl")

        # Verify nothing was registered
        assert builder._fkik_layer.fk_control_count() == 0
        assert builder._fkik_layer.ik_control_count() == 0
        assert len(builder._fkik_layer.pole_vectors()) == 0
