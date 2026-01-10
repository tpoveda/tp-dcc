"""Integration tests for serialization enhancements.

These tests verify the functionality of bake_to_object, bake_to_connected,
load_from_object, and data_equals methods.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestDataEquals:
    """Test the data_equals method."""

    def test_data_equals_matching(self, new_scene, meta_registry_clean):
        """Test data_equals returns True for matching data."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")
        meta.set("rigType", "FK")
        meta.set("side", "L")

        assert meta.data_equals({"rigType": "FK", "side": "L"}) is True

    def test_data_equals_partial_match(self, new_scene, meta_registry_clean):
        """Test data_equals with subset of attributes."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")
        meta.set("rigType", "FK")
        meta.set("side", "L")
        meta.set("index", 0)

        # Checking subset should still work
        assert meta.data_equals({"rigType": "FK"}) is True

    def test_data_equals_non_matching(self, new_scene, meta_registry_clean):
        """Test data_equals returns False for non-matching data."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")
        meta.set("rigType", "FK")

        assert meta.data_equals({"rigType": "IK"}) is False

    def test_data_equals_missing_attr(self, new_scene, meta_registry_clean):
        """Test data_equals returns False for missing attributes."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")
        meta.set("rigType", "FK")

        assert meta.data_equals({"nonExistent": "value"}) is False


@pytest.mark.integration
class TestBakeToObject:
    """Test the bake_to_object method."""

    def test_bake_basic_data(self, new_scene, meta_registry_clean):
        """Test baking basic data to an object."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint = DagNode(mobject_by_name(cmds.joint(name="test_joint")))

        meta = MetaBase(name="test_meta")
        meta.set("rigType", "FK")
        meta.set("side", "L")

        meta.bake_to_object(joint, prefix="meta_")

        # Verify attributes were created
        assert joint.hasAttribute("meta_class")
        assert joint.hasAttribute("meta_version")
        assert joint.hasAttribute("meta_rigType")
        assert joint.hasAttribute("meta_side")

        # Verify values
        assert joint.attribute("meta_rigType").value() == "FK"
        assert joint.attribute("meta_side").value() == "L"

    def test_bake_includes_class_info(self, new_scene, meta_registry_clean):
        """Test that class info is included by default."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint = DagNode(mobject_by_name(cmds.joint(name="test_joint")))

        meta = MetaBase(name="test_meta")
        meta.bake_to_object(joint)

        assert joint.hasAttribute("meta_class")
        assert joint.attribute("meta_class").value() == "MetaBase"

    def test_bake_without_class_info(self, new_scene, meta_registry_clean):
        """Test baking without class info."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint = DagNode(mobject_by_name(cmds.joint(name="test_joint")))

        meta = MetaBase(name="test_meta")
        meta.set("testAttr", "testValue")
        meta.bake_to_object(joint, include_class_info=False)

        assert not joint.hasAttribute("meta_class")
        assert joint.hasAttribute("meta_testAttr")

    def test_bake_with_custom_prefix(self, new_scene, meta_registry_clean):
        """Test baking with a custom prefix."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint = DagNode(mobject_by_name(cmds.joint(name="test_joint")))

        meta = MetaBase(name="test_meta")
        meta.set("testAttr", "testValue")
        meta.bake_to_object(joint, prefix="rig_")

        assert joint.hasAttribute("rig_class")
        assert joint.hasAttribute("rig_testAttr")


@pytest.mark.integration
class TestBakeToConnected:
    """Test the bake_to_connected method."""

    def test_bake_to_all_connected(self, new_scene, meta_registry_clean):
        """Test baking to all connected nodes."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint1 = DagNode(mobject_by_name(cmds.joint(name="joint1")))
        cmds.select(clear=True)
        joint2 = DagNode(mobject_by_name(cmds.joint(name="joint2")))

        meta = MetaBase(name="test_meta")
        meta.set("rigType", "FK")

        meta.connect_node(joint1, "startJoint")
        meta.connect_node(joint2, "endJoint")

        meta.bake_to_connected()

        # Both joints should have baked data
        assert joint1.hasAttribute("meta_rigType")
        assert joint2.hasAttribute("meta_rigType")
        assert joint1.attribute("meta_rigType").value() == "FK"
        assert joint2.attribute("meta_rigType").value() == "FK"


@pytest.mark.integration
class TestLoadFromObject:
    """Test the load_from_object class method."""

    def test_load_basic_data(self, new_scene, meta_registry_clean):
        """Test loading data from a baked object."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint = DagNode(mobject_by_name(cmds.joint(name="test_joint")))

        # Bake data
        original_meta = MetaBase(name="original_meta")
        original_meta.set("rigType", "FK")
        original_meta.set("side", "L")
        original_meta.bake_to_object(joint)

        # Load from object
        loaded_meta = MetaBase.load_from_object(joint)

        assert loaded_meta is not None
        assert loaded_meta.get("rigType") == "FK"
        assert loaded_meta.get("side") == "L"

    def test_load_uses_correct_class(self, new_scene, meta_registry_clean):
        """Test that loading uses the correct class type."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        class CustomMeta(MetaBase):
            ID = "CustomMeta"
            _do_register = True

        MetaRegistry.register_meta_class(CustomMeta)

        cmds.select(clear=True)
        joint = DagNode(mobject_by_name(cmds.joint(name="test_joint")))

        # Bake data from CustomMeta
        original = CustomMeta(name="original")
        original.set("customAttr", "customValue")
        original.bake_to_object(joint)

        # Load should return CustomMeta instance
        loaded = MetaBase.load_from_object(joint)

        assert loaded is not None
        assert loaded.metaclass_type() == "CustomMeta"
        assert loaded.get("customAttr") == "customValue"

    def test_load_no_baked_data_returns_none(
        self, new_scene, meta_registry_clean
    ):
        """Test loading from object without baked data."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint = DagNode(mobject_by_name(cmds.joint(name="test_joint")))

        loaded = MetaBase.load_from_object(joint, create_if_missing=False)

        assert loaded is None

    def test_load_with_custom_prefix(self, new_scene, meta_registry_clean):
        """Test loading with a custom prefix."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint = DagNode(mobject_by_name(cmds.joint(name="test_joint")))

        # Bake with custom prefix
        original = MetaBase(name="original")
        original.set("testAttr", "testValue")
        original.bake_to_object(joint, prefix="custom_")

        # Load with same prefix
        loaded = MetaBase.load_from_object(joint, prefix="custom_")

        assert loaded is not None
        assert loaded.get("testAttr") == "testValue"


@pytest.mark.integration
class TestRoundTrip:
    """Test full round-trip serialization."""

    def test_bake_and_load_roundtrip(self, new_scene, meta_registry_clean):
        """Test complete bake/load round trip."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        cmds.select(clear=True)
        joint = DagNode(mobject_by_name(cmds.joint(name="test_joint")))

        # Create and configure meta node
        original = MetaBase(name="original")
        original.set("stringAttr", "hello")
        original.set("intAttr", 42)
        original.set("floatAttr", 3.14)

        # Bake
        original.bake_to_object(joint)

        # Delete original
        original.delete()

        # Load
        loaded = MetaBase.load_from_object(joint)

        assert loaded is not None
        assert loaded.get("stringAttr") == "hello"
        assert loaded.get("intAttr") == 42
        # Float comparison with tolerance
        assert abs(loaded.get("floatAttr") - 3.14) < 0.001
