"""Integration tests for the property system.

These tests verify the functionality of the MetaProperty class and
related utility functions.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestPropertyRegistry:
    """Test the PropertyRegistry class."""

    def test_registry_is_singleton(self, maya_session):
        """Test that PropertyRegistry is a singleton."""

        from tp.libs.maya.meta.properties import PropertyRegistry

        reg1 = PropertyRegistry()
        reg2 = PropertyRegistry()

        assert reg1 is reg2

    def test_register_property_class(
        self, maya_session, property_registry_clean
    ):
        """Test registering a property class."""

        from tp.libs.maya.meta.properties import MetaProperty, PropertyRegistry

        class TestProperty(MetaProperty):
            ID = "TestProperty"
            _do_register = True

        PropertyRegistry.register_property_class(TestProperty)
        assert PropertyRegistry.is_in_registry("TestProperty")

    def test_hidden_property_class(
        self, maya_session, property_registry_clean
    ):
        """Test registering a hidden (non-public) property class."""

        from tp.libs.maya.meta.properties import MetaProperty, PropertyRegistry

        class HiddenProperty(MetaProperty):
            ID = "HiddenProperty"
            _do_register = False

        PropertyRegistry.register_property_class(HiddenProperty)

        assert not PropertyRegistry.is_in_registry("HiddenProperty")
        assert PropertyRegistry.get_hidden("HiddenProperty") is not None

    def test_get_type(self, maya_session, property_registry_clean):
        """Test getting a registered property type."""

        from tp.libs.maya.meta.properties import MetaProperty, PropertyRegistry

        class RetrievableProperty(MetaProperty):
            ID = "RetrievableProperty"
            _do_register = True

        PropertyRegistry.register_property_class(RetrievableProperty)

        retrieved = PropertyRegistry.get_type("RetrievableProperty")
        assert retrieved is RetrievableProperty


@pytest.mark.integration
class TestMetaPropertyCreation:
    """Test MetaProperty creation and basic functionality."""

    def test_create_property(self, new_scene, property_registry_clean):
        """Test creating a basic property node."""

        from tp.libs.maya.meta.properties import MetaProperty, PropertyRegistry

        class SimpleProperty(MetaProperty):
            ID = "SimpleProperty"
            _do_register = True

        PropertyRegistry.register_property_class(SimpleProperty)

        prop = SimpleProperty(name="test_property")
        assert prop is not None
        assert prop.metaclass_type() == "SimpleProperty"

    def test_property_has_priority_attribute(
        self, new_scene, property_registry_clean
    ):
        """Test that properties have priority attribute."""

        from tp.libs.maya.meta.properties import MetaProperty, PropertyRegistry

        class PriorityProperty(MetaProperty):
            ID = "PriorityProperty"
            _do_register = True
            priority = 5

        PropertyRegistry.register_property_class(PriorityProperty)

        prop = PriorityProperty(name="priority_prop")
        assert prop.hasAttribute("propertyPriority")
        assert prop.get_priority() == 5

    def test_property_has_auto_run_attribute(
        self, new_scene, property_registry_clean
    ):
        """Test that properties have auto_run attribute."""

        from tp.libs.maya.meta.properties import MetaProperty, PropertyRegistry

        class AutoRunProperty(MetaProperty):
            ID = "AutoRunProperty"
            _do_register = True
            auto_run = True

        PropertyRegistry.register_property_class(AutoRunProperty)

        prop = AutoRunProperty(name="autorun_prop")
        assert prop.hasAttribute("propertyAutoRun")
        assert prop.is_auto_run() is True

    def test_property_set_priority(self, new_scene, property_registry_clean):
        """Test setting property priority."""

        from tp.libs.maya.meta.properties import MetaProperty, PropertyRegistry

        class ModifiableProperty(MetaProperty):
            ID = "ModifiableProperty"
            _do_register = True

        PropertyRegistry.register_property_class(ModifiableProperty)

        prop = ModifiableProperty(name="mod_prop")
        prop.set_priority(10)
        assert prop.get_priority() == 10


@pytest.mark.integration
class TestPropertySceneConnection:
    """Test connecting properties to scene objects."""

    def test_connect_property_to_object(
        self, new_scene, property_registry_clean
    ):
        """Test connecting a property to a scene object."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.properties import MetaProperty, PropertyRegistry
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        class ConnectedProperty(MetaProperty):
            ID = "ConnectedProperty"
            _do_register = True

        PropertyRegistry.register_property_class(ConnectedProperty)

        # Create a joint
        cmds.select(clear=True)
        joint_name = cmds.joint(name="test_joint")
        joint = DagNode(mobject_by_name(joint_name))

        # Create property and connect
        prop = ConnectedProperty(name="connected_prop")
        prop.connect_to_object(joint)

        # Verify connection
        connected = prop.connected_object()
        assert connected is not None

    def test_add_property_utility(self, new_scene, property_registry_clean):
        """Test the add_property utility function."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.properties import (
            MetaProperty,
            PropertyRegistry,
            add_property,
        )
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        class AddableProperty(MetaProperty):
            ID = "AddableProperty"
            _do_register = True

        PropertyRegistry.register_property_class(AddableProperty)

        # Create a joint
        cmds.select(clear=True)
        joint_name = cmds.joint(name="test_joint")
        joint = DagNode(mobject_by_name(joint_name))

        # Add property
        prop = add_property(joint, AddableProperty)
        assert prop is not None
        assert isinstance(prop, AddableProperty)

    def test_get_properties(self, new_scene, property_registry_clean):
        """Test getting properties from a scene object."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.properties import (
            MetaProperty,
            PropertyRegistry,
            add_property,
            get_properties,
        )
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        class GettableProperty(MetaProperty):
            ID = "GettableProperty"
            _do_register = True
            multi_allowed = True

        PropertyRegistry.register_property_class(GettableProperty)

        cmds.select(clear=True)
        joint_name = cmds.joint(name="test_joint")
        joint = DagNode(mobject_by_name(joint_name))

        # Add multiple properties
        prop1 = add_property(joint, GettableProperty, name="prop1")
        prop2 = add_property(joint, GettableProperty, name="prop2")

        # Get properties
        props = get_properties(joint)
        assert len(props) >= 2


@pytest.mark.integration
class TestPropertyMultiAllowed:
    """Test the multi_allowed functionality."""

    def test_multi_allowed_false_returns_existing(
        self, new_scene, property_registry_clean
    ):
        """Test that adding same property type returns existing when multi_allowed=False."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.properties import (
            MetaProperty,
            PropertyRegistry,
            add_property,
        )
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        class SingleProperty(MetaProperty):
            ID = "SingleProperty"
            _do_register = True
            multi_allowed = False

        PropertyRegistry.register_property_class(SingleProperty)

        cmds.select(clear=True)
        joint_name = cmds.joint(name="test_joint")
        joint = DagNode(mobject_by_name(joint_name))

        # Add first property
        prop1 = add_property(joint, SingleProperty)

        # Try to add second - should return first
        prop2 = add_property(joint, SingleProperty)

        assert prop1 == prop2

    def test_multi_allowed_true_creates_multiple(
        self, new_scene, property_registry_clean
    ):
        """Test that multi_allowed=True allows multiple properties."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.properties import (
            MetaProperty,
            PropertyRegistry,
            add_property,
            get_properties,
        )
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        class MultiProperty(MetaProperty):
            ID = "MultiProperty"
            _do_register = True
            multi_allowed = True

        PropertyRegistry.register_property_class(MultiProperty)

        cmds.select(clear=True)
        joint_name = cmds.joint(name="test_joint")
        joint = DagNode(mobject_by_name(joint_name))

        # Add multiple properties
        prop1 = add_property(joint, MultiProperty, name="multi1")
        prop2 = add_property(joint, MultiProperty, name="multi2")

        assert prop1 != prop2

        props = get_properties(joint)
        assert len(props) >= 2


@pytest.mark.integration
class TestPropertyAct:
    """Test the property act() method."""

    def test_act_method_called(self, new_scene, property_registry_clean):
        """Test that act() method is called correctly."""

        from tp.libs.maya.meta.properties import MetaProperty, PropertyRegistry

        class ActionProperty(MetaProperty):
            ID = "ActionProperty"
            _do_register = True

            def act(self, *args, **kwargs):
                return "action_result"

        PropertyRegistry.register_property_class(ActionProperty)

        prop = ActionProperty(name="action_prop")
        result = prop.act()
        assert result == "action_result"

    def test_run_properties(self, new_scene, property_registry_clean):
        """Test run_properties utility function."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.properties import (
            MetaProperty,
            PropertyRegistry,
            add_property,
            run_properties,
        )
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        class RunProperty(MetaProperty):
            ID = "RunProperty"
            _do_register = True
            multi_allowed = True

            def act(self, *args, **kwargs):
                return self.name()

        PropertyRegistry.register_property_class(RunProperty)

        cmds.select(clear=True)
        joint_name = cmds.joint(name="test_joint")
        joint = DagNode(mobject_by_name(joint_name))

        add_property(joint, RunProperty, name="run1")
        add_property(joint, RunProperty, name="run2")

        results = run_properties(joint)
        assert len(results) >= 2


@pytest.mark.integration
class TestPropertyOnAdd:
    """Test the on_add hook."""

    def test_on_add_called(self, new_scene, property_registry_clean):
        """Test that on_add is called when property is added."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.properties import (
            MetaProperty,
            PropertyRegistry,
            add_property,
        )
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        on_add_called = []

        class OnAddProperty(MetaProperty):
            ID = "OnAddProperty"
            _do_register = True

            def on_add(self, obj, **kwargs):
                on_add_called.append(True)

        PropertyRegistry.register_property_class(OnAddProperty)

        cmds.select(clear=True)
        joint_name = cmds.joint(name="test_joint")
        joint = DagNode(mobject_by_name(joint_name))

        add_property(joint, OnAddProperty)

        assert len(on_add_called) == 1


@pytest.mark.integration
class TestPropertyCompare:
    """Test property data comparison."""

    def test_compare_matching_data(self, new_scene, property_registry_clean):
        """Test compare returns True for matching data."""

        from tp.libs.maya.meta.properties import MetaProperty, PropertyRegistry

        class CompareProperty(MetaProperty):
            ID = "CompareProperty"
            _do_register = True

        PropertyRegistry.register_property_class(CompareProperty)

        prop = CompareProperty(name="compare_prop")
        prop.set("testAttr", "testValue")

        assert prop.compare({"testAttr": "testValue"}) is True

    def test_compare_non_matching_data(
        self, new_scene, property_registry_clean
    ):
        """Test compare returns False for non-matching data."""

        from tp.libs.maya.meta.properties import MetaProperty, PropertyRegistry

        class CompareProperty2(MetaProperty):
            ID = "CompareProperty2"
            _do_register = True

        PropertyRegistry.register_property_class(CompareProperty2)

        prop = CompareProperty2(name="compare_prop2")
        prop.set("testAttr", "testValue")

        assert prop.compare({"testAttr": "wrongValue"}) is False


@pytest.mark.integration
class TestRemoveProperty:
    """Test property removal."""

    def test_remove_property(self, new_scene, property_registry_clean):
        """Test removing a property from an object."""

        import maya.cmds as cmds

        from tp.libs.maya.meta.properties import (
            MetaProperty,
            PropertyRegistry,
            add_property,
            get_properties,
            remove_property,
        )
        from tp.libs.maya.om.nodes import mobject_by_name
        from tp.libs.maya.wrapper import DagNode

        class RemovableProperty(MetaProperty):
            ID = "RemovableProperty"
            _do_register = True

        PropertyRegistry.register_property_class(RemovableProperty)

        cmds.select(clear=True)
        joint_name = cmds.joint(name="test_joint")
        joint = DagNode(mobject_by_name(joint_name))

        add_property(joint, RemovableProperty)
        props_before = get_properties(joint)
        assert len(props_before) >= 1

        remove_property(joint, RemovableProperty)
        props_after = get_properties(joint)
        assert len(props_after) < len(props_before)
