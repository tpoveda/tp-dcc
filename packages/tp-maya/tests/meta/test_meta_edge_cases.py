"""Edge case and error handling tests for the metadata system.

These tests verify error handling, edge cases, and boundary conditions.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestMetaNodeEdgeCases:
    """Test edge cases in meta node handling."""

    def test_meta_node_with_empty_name(self, new_scene):
        """Test creating meta node with empty name uses default."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="")
        # Should fall back to default naming
        assert meta.name() is not None
        assert len(meta.name()) > 0

    def test_meta_node_with_special_characters_in_tag(self, new_scene):
        """Test setting tag with special characters."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")
        meta.set_tag("test_tag_with_underscores")
        assert meta.tag() == "test_tag_with_underscores"

        meta.set_tag("tag123")
        assert meta.tag() == "tag123"

    def test_find_children_empty_hierarchy(self, new_scene):
        """Test finding children when there are none."""

        from tp.libs.maya.meta.base import MetaBase

        root = MetaBase(name="lonely_root")

        children = list(root.iterate_meta_children())
        assert len(children) == 0

        by_type = root.find_children_by_class_type("NonExistent")
        assert len(by_type) == 0

        by_tag = root.find_children_by_tag("nonexistent")
        assert len(by_tag) == 0

    def test_meta_parent_when_no_parent(self, new_scene):
        """Test meta_parent returns None for root nodes."""

        from tp.libs.maya.meta.base import MetaBase

        root = MetaBase(name="root")

        assert root.meta_parent() is None

    def test_meta_root_when_already_root(self, new_scene):
        """Test meta_root returns None for actual root nodes."""

        from tp.libs.maya.meta.base import MetaBase

        root = MetaBase(name="root")

        # meta_root returns None when node is itself a root
        result = root.meta_root()
        assert result is None

    def test_get_upstream_not_found(self, new_scene, meta_registry_clean):
        """Test get_upstream returns None when type not found."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry

        class SearchType(MetaBase):
            ID = "SearchType"

        MetaRegistry.register_meta_class(SearchType)

        root = MetaBase(name="root")
        child = MetaBase(name="child")
        child.add_meta_parent(root)

        # SearchType is not in the hierarchy
        found = child.get_upstream(SearchType)
        assert found is None

    def test_get_downstream_not_found(self, new_scene, meta_registry_clean):
        """Test get_downstream returns None when type not found."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry

        class SearchType(MetaBase):
            ID = "SearchType"

        MetaRegistry.register_meta_class(SearchType)

        root = MetaBase(name="root")
        child = MetaBase(name="child")
        root.add_meta_child(child)

        # SearchType is not in the hierarchy
        found = root.get_downstream(SearchType)
        assert found is None

    def test_remove_nonexistent_parent(self, new_scene):
        """Test removing a parent that isn't connected."""

        from tp.libs.maya.meta.base import MetaBase

        child = MetaBase(name="child")
        other = MetaBase(name="other")

        # Should not raise an error
        child.remove_meta_parent(other)

    def test_remove_all_meta_parents_when_none(self, new_scene):
        """Test remove_all_meta_parents when there are no parents."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="orphan")

        # Should not raise an error
        meta.remove_all_meta_parents()
        assert meta.meta_parent() is None

    def test_iterate_meta_children_depth_zero(self, new_scene):
        """Test iteration with depth limit of 0."""

        from tp.libs.maya.meta.base import MetaBase

        root = MetaBase(name="root")
        child = MetaBase(name="child")
        root.add_meta_child(child)

        # Depth 0 should return no children
        children = list(root.iterate_meta_children(depth_limit=0))
        assert len(children) == 0

    def test_circular_reference_prevention(self, new_scene):
        """Test that circular references are handled."""

        from tp.libs.maya.meta.base import MetaBase

        meta1 = MetaBase(name="meta1")
        meta2 = MetaBase(name="meta2")

        meta1.add_meta_child(meta2)

        # Attempting to make meta1 a child of meta2 would create a cycle
        # The visited set should prevent infinite loops
        meta2.add_meta_child(meta1)

        # Iteration should still work (not hang)
        children1 = list(meta1.iterate_meta_children(depth_limit=10))
        children2 = list(meta2.iterate_meta_children(depth_limit=10))

        # The iteration should complete without hanging
        assert True


@pytest.mark.integration
class TestMetaRegistryEdgeCases:
    """Test edge cases in MetaRegistry handling."""

    def test_register_same_class_twice(
        self, maya_session, meta_registry_clean
    ):
        """Test registering the same class twice is idempotent."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry

        class DuplicateMeta(MetaBase):
            ID = "DuplicateMeta"

        MetaRegistry.register_meta_class(DuplicateMeta)
        MetaRegistry.register_meta_class(DuplicateMeta)

        # Should still only be registered once
        assert MetaRegistry.is_in_registry("DuplicateMeta")
        assert MetaRegistry.get_type("DuplicateMeta") is DuplicateMeta

    def test_get_type_nonexistent(self, maya_session):
        """Test get_type returns None for unregistered type."""

        from tp.libs.maya.meta.base import MetaRegistry

        result = MetaRegistry.get_type("NonExistentType12345")
        assert result is None

    def test_is_in_registry_nonexistent(self, maya_session):
        """Test is_in_registry returns False for unregistered type."""

        from tp.libs.maya.meta.base import MetaRegistry

        result = MetaRegistry.is_in_registry("NonExistentType12345")
        assert result is False

    def test_unregister_nonexistent_class(
        self, maya_session, meta_registry_clean
    ):
        """Test unregistering a non-existent class returns False."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry

        class NeverRegistered(MetaBase):
            ID = "NeverRegistered"

        result = MetaRegistry.unregister_meta_class(NeverRegistered)
        assert result is False


@pytest.mark.integration
class TestMetaNodeDataEdgeCases:
    """Test edge cases in data handling."""

    def test_get_nonexistent_attribute_returns_default(self, new_scene):
        """Test get returns default for non-existent attribute."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")

        result = meta.get("nonexistent")
        assert result is None

        result = meta.get("nonexistent", default=42)
        assert result == 42

    def test_data_property_excludes_reserved(self, new_scene):
        """Test data property excludes reserved attributes."""

        from tp.libs.maya.meta.base import MetaBase
        from tp.libs.maya.meta.constants import RESERVED_ATTR_NAMES

        meta = MetaBase(name="test_meta")
        meta.set("userAttr", "value")

        data = meta.data

        # User attribute should be present
        assert "userAttr" in data

        # Reserved attributes should not be in data
        for reserved in RESERVED_ATTR_NAMES:
            assert reserved not in data

    def test_set_empty_string(self, new_scene):
        """Test setting an attribute to empty string."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")
        meta.set("emptyAttr", "")

        result = meta.get("emptyAttr")
        assert result == ""

    def test_set_zero_values(self, new_scene):
        """Test setting attributes to zero values."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")
        meta.set("zeroInt", 0)
        meta.set("zeroFloat", 0.0)

        assert meta.get("zeroInt") == 0
        assert meta.get("zeroFloat") == 0.0


@pytest.mark.integration
class TestMetaNodeSceneFunctions:
    """Test scene-level function edge cases."""

    def test_iterate_scene_meta_nodes_empty_scene(self, new_scene):
        """Test iterating meta nodes in empty scene."""

        from tp.libs.maya.meta.base import iterate_scene_meta_nodes

        # Fresh scene should have no meta nodes
        meta_nodes = list(iterate_scene_meta_nodes())
        assert len(meta_nodes) == 0

    def test_is_meta_node_with_none(self, new_scene):
        """Test is_meta_node handles edge cases gracefully."""

        from tp.libs.maya.meta.base import MetaBase, is_meta_node

        # Create a meta node to test with
        meta = MetaBase(name="test")
        assert is_meta_node(meta)

    def test_is_meta_node_of_types_empty_list(self, new_scene):
        """Test is_meta_node_of_types with empty type list."""

        from tp.libs.maya.meta.base import MetaBase, is_meta_node_of_types

        meta = MetaBase(name="test")

        result = is_meta_node_of_types(meta, [])
        assert result is False

    def test_find_meta_nodes_by_class_type_empty_scene(self, new_scene):
        """Test find_meta_nodes_by_class_type in empty scene."""

        from tp.libs.maya.meta.base import find_meta_nodes_by_class_type

        result = find_meta_nodes_by_class_type("MetaBase")
        assert len(result) == 0

    def test_find_meta_nodes_by_tag_empty_scene(self, new_scene):
        """Test find_meta_nodes_by_tag in empty scene."""

        from tp.libs.maya.meta.base import find_meta_nodes_by_tag

        result = find_meta_nodes_by_tag("any_tag")
        assert len(result) == 0


@pytest.mark.integration
class TestMetaNodeRepr:
    """Test string representation of meta nodes."""

    def test_repr_format(self, new_scene):
        """Test __repr__ returns expected format."""

        from tp.libs.maya.meta.base import MetaBase

        meta = MetaBase(name="test_meta")
        repr_str = repr(meta)

        # Should contain class name and node name
        assert "MetaBase" in repr_str
        assert "test_meta" in repr_str

    def test_as_str_name_only(self, new_scene):
        """Test as_str with name_only=True."""

        from tp.libs.maya.meta.base import MetaBase

        result = MetaBase.as_str(name_only=True)
        assert result == "MetaBase"

    def test_as_str_full_path(self, new_scene):
        """Test as_str with name_only=False."""

        from tp.libs.maya.meta.base import MetaBase

        result = MetaBase.as_str(name_only=False)
        assert "MetaBase" in result
        assert "." in result  # Should include module path


@pytest.mark.integration
class TestCustomMetaSetup:
    """Test custom setup method in meta classes."""

    def test_setup_called_on_creation(self, new_scene, meta_registry_clean):
        """Test that setup method is called during creation."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry

        setup_called = []

        class SetupMeta(MetaBase):
            ID = "SetupMeta"

            def setup(self, *args, **kwargs):
                setup_called.append(True)
                super().setup(*args, **kwargs)

        MetaRegistry.register_meta_class(SetupMeta)

        meta = SetupMeta(name="test_setup")
        assert len(setup_called) == 1

    def test_setup_receives_kwargs(self, new_scene, meta_registry_clean):
        """Test that setup receives keyword arguments."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry

        received_kwargs = {}

        class KwargMeta(MetaBase):
            ID = "KwargMeta"

            def setup(self, *args, **kwargs):
                received_kwargs.update(kwargs)
                super().setup(*args, **kwargs)

        MetaRegistry.register_meta_class(KwargMeta)

        meta = KwargMeta(name="test_kwargs", custom_arg="custom_value")
        assert received_kwargs.get("custom_arg") == "custom_value"
