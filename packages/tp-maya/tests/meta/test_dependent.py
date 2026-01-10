"""Integration tests for the dependent node pattern.

These tests verify the functionality of the DependentMeta class and
related utility functions.
"""

from __future__ import annotations

import pytest


@pytest.mark.integration
class TestDependentMetaCreation:
    """Test DependentMeta creation and basic functionality."""

    def test_create_dependent_without_dependency(
        self, new_scene, meta_registry_clean
    ):
        """Test creating a DependentMeta without dependent_node set."""

        from tp.libs.maya.meta.base import MetaRegistry
        from tp.libs.maya.meta.dependent import DependentMeta

        class SimpleDependentMeta(DependentMeta):
            ID = "SimpleDependentMeta"
            _do_register = True
            dependent_node = None  # No dependency

        MetaRegistry.register_meta_class(SimpleDependentMeta)

        node = SimpleDependentMeta(name="test_dependent")
        assert node is not None
        assert node.meta_parent() is None  # No parent expected

    def test_create_dependent_auto_creates_parent(
        self, new_scene, meta_registry_clean
    ):
        """Test that creating a DependentMeta auto-creates parent."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry
        from tp.libs.maya.meta.dependent import DependentMeta

        class ParentMeta(MetaBase):
            ID = "ParentMeta"
            _do_register = True

        class ChildDependentMeta(DependentMeta):
            ID = "ChildDependentMeta"
            _do_register = True
            dependent_node = ParentMeta

        MetaRegistry.register_meta_class(ParentMeta)
        MetaRegistry.register_meta_class(ChildDependentMeta)

        child = ChildDependentMeta(name="test_child")
        assert child is not None

        parent = child.meta_parent()
        assert parent is not None
        assert isinstance(parent, ParentMeta)

    def test_create_dependent_uses_existing_parent(
        self, new_scene, meta_registry_clean
    ):
        """Test that creating a DependentMeta uses existing parent."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry
        from tp.libs.maya.meta.dependent import DependentMeta

        class ExistingParentMeta(MetaBase):
            ID = "ExistingParentMeta"
            _do_register = True

        class ChildOfExistingMeta(DependentMeta):
            ID = "ChildOfExistingMeta"
            _do_register = True
            dependent_node = ExistingParentMeta

        MetaRegistry.register_meta_class(ExistingParentMeta)
        MetaRegistry.register_meta_class(ChildOfExistingMeta)

        # Create parent first
        parent = ExistingParentMeta(name="existing_parent")

        # Create child - should connect to existing parent
        child = ChildOfExistingMeta(name="test_child")

        child_parent = child.meta_parent()
        assert child_parent is not None
        assert child_parent.name() == parent.name()

    def test_create_dependent_with_explicit_parent(
        self, new_scene, meta_registry_clean
    ):
        """Test creating a DependentMeta with explicit parent parameter."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry
        from tp.libs.maya.meta.dependent import DependentMeta

        class ExplicitParentMeta(MetaBase):
            ID = "ExplicitParentMeta"
            _do_register = True

        class ExplicitChildMeta(DependentMeta):
            ID = "ExplicitChildMeta"
            _do_register = True
            dependent_node = ExplicitParentMeta

        MetaRegistry.register_meta_class(ExplicitParentMeta)
        MetaRegistry.register_meta_class(ExplicitChildMeta)

        # Create a specific parent
        parent = ExplicitParentMeta(name="explicit_parent")

        # Create child with explicit parent
        child = ExplicitChildMeta(name="test_child", parent=parent)

        child_parent = child.meta_parent()
        assert child_parent is not None
        assert child_parent.name() == parent.name()


@pytest.mark.integration
class TestDependentMetaChain:
    """Test dependency chain functionality."""

    def test_dependency_chain_auto_creation(
        self, new_scene, meta_registry_clean
    ):
        """Test auto-creation of multi-level dependency chain."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry
        from tp.libs.maya.meta.dependent import DependentMeta

        class RootMeta(MetaBase):
            ID = "RootMeta"
            _do_register = True

        class MiddleMeta(DependentMeta):
            ID = "MiddleMeta"
            _do_register = True
            dependent_node = RootMeta

        class LeafMeta(DependentMeta):
            ID = "LeafMeta"
            _do_register = True
            dependent_node = MiddleMeta

        MetaRegistry.register_meta_class(RootMeta)
        MetaRegistry.register_meta_class(MiddleMeta)
        MetaRegistry.register_meta_class(LeafMeta)

        # Creating leaf should create entire chain
        leaf = LeafMeta(name="leaf_node")

        # Verify chain
        middle = leaf.meta_parent()
        assert middle is not None
        assert isinstance(middle, MiddleMeta)

        root = middle.meta_parent()
        assert root is not None
        assert isinstance(root, RootMeta)

    def test_get_dependency_chain(self, new_scene, meta_registry_clean):
        """Test get_dependency_chain class method."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry
        from tp.libs.maya.meta.dependent import DependentMeta

        class ChainRoot(MetaBase):
            ID = "ChainRoot"
            _do_register = True

        class ChainMiddle(DependentMeta):
            ID = "ChainMiddle"
            _do_register = True
            dependent_node = ChainRoot

        class ChainLeaf(DependentMeta):
            ID = "ChainLeaf"
            _do_register = True
            dependent_node = ChainMiddle

        MetaRegistry.register_meta_class(ChainRoot)
        MetaRegistry.register_meta_class(ChainMiddle)
        MetaRegistry.register_meta_class(ChainLeaf)

        chain = ChainLeaf.get_dependency_chain()

        assert len(chain) == 3
        assert chain[0] == ChainRoot
        assert chain[1] == ChainMiddle
        assert chain[2] == ChainLeaf

    def test_ensure_dependency_chain(self, new_scene, meta_registry_clean):
        """Test ensure_dependency_chain method."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry
        from tp.libs.maya.meta.dependent import DependentMeta

        class EnsureRoot(MetaBase):
            ID = "EnsureRoot"
            _do_register = True

        class EnsureChild(DependentMeta):
            ID = "EnsureChild"
            _do_register = True
            dependent_node = EnsureRoot

        MetaRegistry.register_meta_class(EnsureRoot)
        MetaRegistry.register_meta_class(EnsureChild)

        child = EnsureChild(name="ensure_child")

        result = child.ensure_dependency_chain()
        assert result is True
        assert child.meta_parent() is not None


@pytest.mark.integration
class TestDependentMetaAutoCreate:
    """Test auto_create_parent flag functionality."""

    def test_auto_create_disabled(self, new_scene, meta_registry_clean):
        """Test that auto_create_parent=False prevents parent creation."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry
        from tp.libs.maya.meta.dependent import DependentMeta

        class NoAutoParent(MetaBase):
            ID = "NoAutoParent"
            _do_register = True

        class NoAutoChild(DependentMeta):
            ID = "NoAutoChild"
            _do_register = True
            dependent_node = NoAutoParent
            auto_create_parent = False

        MetaRegistry.register_meta_class(NoAutoParent)
        MetaRegistry.register_meta_class(NoAutoChild)

        child = NoAutoChild(name="no_auto_child")

        # Parent should not be auto-created
        assert child.meta_parent() is None


@pytest.mark.integration
class TestDependentMetaUtilities:
    """Test utility functions for dependent nodes."""

    def test_create_dependency_chain_utility(
        self, new_scene, meta_registry_clean
    ):
        """Test create_dependency_chain utility function."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry
        from tp.libs.maya.meta.dependent import (
            DependentMeta,
            create_dependency_chain,
        )

        class UtilRoot(MetaBase):
            ID = "UtilRoot"
            _do_register = True

        class UtilChild(DependentMeta):
            ID = "UtilChild"
            _do_register = True
            dependent_node = UtilRoot

        MetaRegistry.register_meta_class(UtilRoot)
        MetaRegistry.register_meta_class(UtilChild)

        leaf = create_dependency_chain(UtilChild, name="util_child")

        assert leaf is not None
        assert isinstance(leaf, UtilChild)
        assert leaf.meta_parent() is not None

    def test_get_or_create_parent_utility(
        self, new_scene, meta_registry_clean
    ):
        """Test get_or_create_parent utility function."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry
        from tp.libs.maya.meta.dependent import (
            DependentMeta,
            get_or_create_parent,
        )

        class GetCreateRoot(MetaBase):
            ID = "GetCreateRoot"
            _do_register = True

        class GetCreateChild(DependentMeta):
            ID = "GetCreateChild"
            _do_register = True
            dependent_node = GetCreateRoot
            auto_create_parent = False  # Disable auto-create for manual test

        MetaRegistry.register_meta_class(GetCreateRoot)
        MetaRegistry.register_meta_class(GetCreateChild)

        child = GetCreateChild(name="get_create_child")

        # Initially no parent
        assert child.meta_parent() is None

        # Get or create parent
        parent = get_or_create_parent(child)
        assert parent is not None
        assert isinstance(parent, GetCreateRoot)

    def test_get_dependency_parent(self, new_scene, meta_registry_clean):
        """Test get_dependency_parent method."""

        from tp.libs.maya.meta.base import MetaBase, MetaRegistry
        from tp.libs.maya.meta.dependent import DependentMeta

        class DepParent(MetaBase):
            ID = "DepParent"
            _do_register = True

        class DepChild(DependentMeta):
            ID = "DepChild"
            _do_register = True
            dependent_node = DepParent

        MetaRegistry.register_meta_class(DepParent)
        MetaRegistry.register_meta_class(DepChild)

        child = DepChild(name="dep_child")

        dep_parent = child.get_dependency_parent()
        assert dep_parent is not None
        assert isinstance(dep_parent, DepParent)


@pytest.mark.integration
class TestDependentMetaWithExistingNode:
    """Test DependentMeta behavior when wrapping existing nodes."""

    def test_wrap_existing_node(self, new_scene, meta_registry_clean):
        """Test wrapping an existing node doesn't create new parent."""

        from tp.libs.maya.meta.base import (
            MetaBase,
            MetaRegistry,
            find_meta_nodes_by_class_type,
        )
        from tp.libs.maya.meta.dependent import DependentMeta

        class WrapParent(MetaBase):
            ID = "WrapParent"
            _do_register = True

        class WrapChild(DependentMeta):
            ID = "WrapChild"
            _do_register = True
            dependent_node = WrapParent

        MetaRegistry.register_meta_class(WrapParent)
        MetaRegistry.register_meta_class(WrapChild)

        # Create child (this creates parent too)
        child = WrapChild(name="wrap_child")
        original_parent = child.meta_parent()

        # Count parents before wrap
        parents_before = find_meta_nodes_by_class_type(WrapParent)

        # Wrap the existing child node
        wrapped = WrapChild(node=child.object(), init_defaults=False)

        # Count parents after wrap
        parents_after = find_meta_nodes_by_class_type(WrapParent)

        # Should not create new parent
        assert len(parents_after) == len(parents_before)
        assert wrapped.meta_parent().name() == original_parent.name()
