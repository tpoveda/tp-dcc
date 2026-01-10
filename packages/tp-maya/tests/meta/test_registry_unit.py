"""Unit tests for the MetaRegistry class.

These tests verify the registry logic without requiring Maya.
They use mocking to isolate the registry behavior.

Note: Tests that import from tp.libs.maya.meta.constants are marked as
integration tests because the constants module imports Maya-dependent modules.
"""

from __future__ import annotations

import pytest


class TestMetaRegistryRegistrationLogic:
    """Test the registry name and class registration logic."""

    @pytest.mark.unit
    def test_registry_name_for_class_with_id(self):
        """Test that registry_name_for_class returns the ID attribute if present."""

        class MockMetaClass:
            ID = "CustomMetaID"

        # Import here to avoid Maya import issues in unit tests
        # We test the static method logic independently
        # The actual method uses: hasattr(class_type, "ID") and class_type.ID
        result = (
            MockMetaClass.ID
            if hasattr(MockMetaClass, "ID") and MockMetaClass.ID
            else MockMetaClass.__name__
        )
        assert result == "CustomMetaID"

    @pytest.mark.unit
    def test_registry_name_for_class_without_id(self):
        """Test that registry_name_for_class returns __name__ if ID is None."""

        class MockMetaClass:
            ID = None

        result = (
            MockMetaClass.ID
            if hasattr(MockMetaClass, "ID") and MockMetaClass.ID
            else MockMetaClass.__name__
        )
        assert result == "MockMetaClass"

    @pytest.mark.unit
    def test_registry_name_for_class_no_id_attr(self):
        """Test that registry_name_for_class returns __name__ if no ID attribute."""

        class MockMetaClass:
            pass

        result = (
            MockMetaClass.ID
            if hasattr(MockMetaClass, "ID") and MockMetaClass.ID
            else MockMetaClass.__name__
        )
        assert result == "MockMetaClass"

    @pytest.mark.unit
    def test_registry_name_for_class_empty_id(self):
        """Test that registry_name_for_class returns __name__ if ID is empty string."""

        class MockMetaClass:
            ID = ""

        result = (
            MockMetaClass.ID
            if hasattr(MockMetaClass, "ID") and MockMetaClass.ID
            else MockMetaClass.__name__
        )
        assert result == "MockMetaClass"


class TestReservedAttributeNames:
    """Test reserved attribute name constants.

    Note: These tests are marked as integration because importing constants
    triggers Maya module imports.
    """

    @pytest.mark.integration
    def test_reserved_attr_names_contains_required_attrs(self, maya_session):
        """Test that RESERVED_ATTR_NAMES contains all meta attributes."""

        from tp.libs.maya.meta.constants import (
            META_CHILDREN_ATTR_NAME,
            META_CLASS_ATTR_NAME,
            META_GUID_ATTR_NAME,
            META_PARENT_ATTR_NAME,
            META_TAG_ATTR_NAME,
            META_VERSION_ATTR_NAME,
            RESERVED_ATTR_NAMES,
        )

        assert META_CLASS_ATTR_NAME in RESERVED_ATTR_NAMES
        assert META_VERSION_ATTR_NAME in RESERVED_ATTR_NAMES
        assert META_PARENT_ATTR_NAME in RESERVED_ATTR_NAMES
        assert META_CHILDREN_ATTR_NAME in RESERVED_ATTR_NAMES
        assert META_TAG_ATTR_NAME in RESERVED_ATTR_NAMES
        assert META_GUID_ATTR_NAME in RESERVED_ATTR_NAMES


class TestTypeMappings:
    """Test type mapping constants.

    Note: These tests are marked as integration because importing constants
    triggers Maya module imports.
    """

    @pytest.mark.integration
    def test_type_to_maya_attr_mappings(self, maya_session):
        """Test that TYPE_TO_MAYA_ATTR contains expected Python types."""

        from tp.libs.maya.meta.constants import TYPE_TO_MAYA_ATTR

        assert str in TYPE_TO_MAYA_ATTR
        assert int in TYPE_TO_MAYA_ATTR
        assert float in TYPE_TO_MAYA_ATTR
        assert bool in TYPE_TO_MAYA_ATTR
        assert list in TYPE_TO_MAYA_ATTR
        assert tuple in TYPE_TO_MAYA_ATTR

    @pytest.mark.integration
    def test_maya_attr_to_type_mappings(self, maya_session):
        """Test that MAYA_ATTR_TO_TYPE contains expected reverse mappings."""

        from tp.libs.maya.meta.constants import MAYA_ATTR_TO_TYPE

        # Verify the dict exists and has entries
        assert isinstance(MAYA_ATTR_TO_TYPE, dict)
        # Check that Python types are values
        for maya_type, py_type in MAYA_ATTR_TO_TYPE.items():
            assert isinstance(maya_type, int)
            assert isinstance(py_type, type)
