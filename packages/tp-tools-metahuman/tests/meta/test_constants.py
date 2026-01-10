"""Unit tests for meta constants module.

These tests verify that constants are properly defined and have the
expected values. They do not require Maya.

We import the constants module directly to avoid triggering Maya-dependent
imports from the parent rig package.
"""

from __future__ import annotations

import importlib.util
import os

import pytest

# Path to the constants module
CONSTANTS_MODULE_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "src",
    "tp",
    "tools",
    "metahuman",
    "rig",
    "meta",
    "constants.py",
)


def _import_constants_directly():
    """Import constants module directly without going through package chain.

    This avoids triggering Maya-dependent imports from the parent rig package.
    """

    spec = importlib.util.spec_from_file_location(
        "meta_constants",
        os.path.abspath(CONSTANTS_MODULE_PATH),
    )
    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not load constants from {CONSTANTS_MODULE_PATH}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
class TestMetaConstants:
    """Test meta constants definitions."""

    def test_metanode_type_constants_are_strings(self):
        """Test that all metanode type constants are non-empty strings."""

        constants = _import_constants_directly()

        type_constants = [
            constants.METAHUMAN_RIG_TYPE,
            constants.METAHUMAN_LAYER_TYPE,
            constants.METAHUMAN_CONTROLS_LAYER_TYPE,
            constants.METAHUMAN_SKELETON_LAYER_TYPE,
            constants.METAHUMAN_FKIK_LAYER_TYPE,
            constants.METAHUMAN_SPACE_SWITCH_LAYER_TYPE,
            constants.METAHUMAN_REVERSE_FOOT_LAYER_TYPE,
        ]

        for const in type_constants:
            assert isinstance(const, str)
            assert len(const) > 0

    def test_metanode_types_are_unique(self):
        """Test that all metanode type identifiers are unique."""

        constants = _import_constants_directly()

        type_constants = [
            constants.METAHUMAN_RIG_TYPE,
            constants.METAHUMAN_LAYER_TYPE,
            constants.METAHUMAN_CONTROLS_LAYER_TYPE,
            constants.METAHUMAN_SKELETON_LAYER_TYPE,
            constants.METAHUMAN_FKIK_LAYER_TYPE,
            constants.METAHUMAN_SPACE_SWITCH_LAYER_TYPE,
            constants.METAHUMAN_REVERSE_FOOT_LAYER_TYPE,
        ]

        # All types should be unique
        assert len(type_constants) == len(set(type_constants))

    def test_attribute_name_constants_are_strings(self):
        """Test that all attribute name constants are non-empty strings."""

        constants = _import_constants_directly()

        attr_constants = [
            constants.ID_ATTR,
            constants.NAME_ATTR,
            constants.IS_METAHUMAN_RIG_ATTR,
            constants.IS_ROOT_ATTR,
            constants.RIG_VERSION_ATTR,
            constants.RIG_ROOT_TRANSFORM_ATTR,
            constants.RIG_CONTROLS_GROUP_ATTR,
            constants.RIG_SETUP_GROUP_ATTR,
            constants.RIG_MOTION_SKELETON_ATTR,
            constants.RIG_CONTROL_DISPLAY_LAYER_ATTR,
            constants.RIG_IS_MOTION_MODE_ATTR,
            constants.LAYER_ROOT_TRANSFORM_ATTR,
            constants.LAYER_CONTROLS_ATTR,
            constants.LAYER_JOINTS_ATTR,
            constants.CONTROL_ID_ATTR,
            constants.CONTROL_SIDE_ATTR,
            constants.CONTROL_TYPE_ATTR,
        ]

        for const in attr_constants:
            assert isinstance(const, str)
            assert len(const) > 0

    def test_controls_layer_constants_exist(self):
        """Test that controls layer attribute constants exist."""

        constants = _import_constants_directly()

        assert hasattr(constants, "CONTROLS_LAYER_SETTINGS_NODE_ATTR")
        assert hasattr(constants, "CONTROLS_LAYER_VISIBILITY_ATTR")
        assert isinstance(constants.CONTROLS_LAYER_SETTINGS_NODE_ATTR, str)
        assert isinstance(constants.CONTROLS_LAYER_VISIBILITY_ATTR, str)

    def test_skeleton_layer_constants_exist(self):
        """Test that skeleton layer attribute constants exist."""

        constants = _import_constants_directly()

        assert hasattr(constants, "SKELETON_LAYER_ROOT_JOINT_ATTR")
        assert hasattr(constants, "SKELETON_LAYER_BIND_ROOT_ATTR")
        assert hasattr(constants, "SKELETON_LAYER_IS_MOTION_SKELETON_ATTR")
        assert isinstance(constants.SKELETON_LAYER_ROOT_JOINT_ATTR, str)
        assert isinstance(constants.SKELETON_LAYER_BIND_ROOT_ATTR, str)
        assert isinstance(
            constants.SKELETON_LAYER_IS_MOTION_SKELETON_ATTR, str
        )

    def test_fkik_layer_constants_exist(self):
        """Test that FK/IK layer attribute constants exist."""

        constants = _import_constants_directly()

        assert hasattr(constants, "FKIK_LAYER_FK_CONTROLS_ATTR")
        assert hasattr(constants, "FKIK_LAYER_IK_CONTROLS_ATTR")
        assert hasattr(constants, "FKIK_LAYER_POLE_VECTORS_ATTR")
        assert hasattr(constants, "FKIK_LAYER_BLEND_NODES_ATTR")
        assert hasattr(constants, "FKIK_LAYER_SETTINGS_NODE_ATTR")

    def test_space_switch_layer_constants_exist(self):
        """Test that space switch layer attribute constants exist."""

        constants = _import_constants_directly()

        assert hasattr(constants, "SPACE_SWITCH_LAYER_CONTROLS_ATTR")
        assert hasattr(constants, "SPACE_SWITCH_LAYER_CONSTRAINTS_ATTR")
        assert hasattr(constants, "SPACE_SWITCH_LAYER_DRIVER_NODES_ATTR")

    def test_reverse_foot_layer_constants_exist(self):
        """Test that reverse foot layer attribute constants exist."""

        constants = _import_constants_directly()

        assert hasattr(constants, "REVERSE_FOOT_LAYER_FOOT_CONTROLS_ATTR")
        assert hasattr(constants, "REVERSE_FOOT_LAYER_PIVOT_LOCATORS_ATTR")
        assert hasattr(constants, "REVERSE_FOOT_LAYER_IK_HANDLES_ATTR")
        assert hasattr(constants, "REVERSE_FOOT_LAYER_SETTINGS_NODE_ATTR")

    def test_transform_attrs_is_tuple(self):
        """Test that TRANSFORM_ATTRS is a tuple of strings."""

        constants = _import_constants_directly()

        assert isinstance(constants.TRANSFORM_ATTRS, tuple)
        assert len(constants.TRANSFORM_ATTRS) > 0
        for attr in constants.TRANSFORM_ATTRS:
            assert isinstance(attr, str)

    def test_local_transform_attrs_is_tuple(self):
        """Test that LOCAL_TRANSFORM_ATTRS is a tuple of strings."""

        constants = _import_constants_directly()

        assert isinstance(constants.LOCAL_TRANSFORM_ATTRS, tuple)
        assert len(constants.LOCAL_TRANSFORM_ATTRS) == 9  # 3x3 for XYZ
        for attr in constants.LOCAL_TRANSFORM_ATTRS:
            assert isinstance(attr, str)

    def test_default_values_exist(self):
        """Test that default value constants exist and are valid."""

        constants = _import_constants_directly()

        assert isinstance(constants.DEFAULT_RIG_VERSION, str)
        assert len(constants.DEFAULT_RIG_VERSION) > 0

        assert isinstance(constants.DEFAULT_RIG_NAME, str)
        assert len(constants.DEFAULT_RIG_NAME) > 0

    def test_rig_type_follows_naming_convention(self):
        """Test that rig type uses expected naming pattern."""

        constants = _import_constants_directly()

        # Should use camelCase starting with 'metaHuman'
        assert constants.METAHUMAN_RIG_TYPE.startswith("metaHuman")

    def test_layer_types_follow_naming_convention(self):
        """Test that layer types use expected naming pattern."""

        constants = _import_constants_directly()

        layer_types = [
            constants.METAHUMAN_LAYER_TYPE,
            constants.METAHUMAN_CONTROLS_LAYER_TYPE,
            constants.METAHUMAN_SKELETON_LAYER_TYPE,
            constants.METAHUMAN_FKIK_LAYER_TYPE,
            constants.METAHUMAN_SPACE_SWITCH_LAYER_TYPE,
            constants.METAHUMAN_REVERSE_FOOT_LAYER_TYPE,
        ]

        for layer_type in layer_types:
            # Should use camelCase starting with 'metaHuman'
            assert layer_type.startswith("metaHuman")
            # Should end with 'Layer'
            assert "Layer" in layer_type


@pytest.mark.unit
class TestModuleImports:
    """Test that the meta module can be imported correctly."""

    def test_import_constants_directly(self):
        """Test importing constants module directly."""

        constants = _import_constants_directly()

        assert constants is not None
        assert hasattr(constants, "METAHUMAN_RIG_TYPE")

    def test_constants_module_has_expected_attributes(self):
        """Test that constants module has all expected type constants."""

        constants = _import_constants_directly()

        expected_attrs = [
            "METAHUMAN_RIG_TYPE",
            "METAHUMAN_LAYER_TYPE",
            "METAHUMAN_CONTROLS_LAYER_TYPE",
            "METAHUMAN_SKELETON_LAYER_TYPE",
            "METAHUMAN_FKIK_LAYER_TYPE",
            "METAHUMAN_SPACE_SWITCH_LAYER_TYPE",
            "METAHUMAN_REVERSE_FOOT_LAYER_TYPE",
            "ID_ATTR",
            "NAME_ATTR",
            "DEFAULT_RIG_VERSION",
            "DEFAULT_RIG_NAME",
        ]

        for attr in expected_attrs:
            assert hasattr(constants, attr), f"Missing attribute: {attr}"
