"""Tests for tp.libs.templating.context module."""

from __future__ import annotations

import pytest

from tp.libs.templating.context import ContextStack, TemplateContext


class TestTemplateContextBasic:
    """Basic tests for TemplateContext class."""

    def test_initialization(self):
        """Test context initialization."""
        ctx = TemplateContext(name="test")
        assert ctx.name == "test"
        assert ctx.parent is None
        assert ctx.depth == 0

    def test_set_get(self):
        """Test setting and getting values."""
        ctx = TemplateContext()
        ctx.set("key", "value")
        assert ctx.get("key") == "value"

    def test_get_default(self):
        """Test getting with default."""
        ctx = TemplateContext()
        assert ctx.get("missing", "default") == "default"

    def test_has(self):
        """Test checking for key existence."""
        ctx = TemplateContext()
        ctx.set("key", "value")
        assert ctx.has("key") is True
        assert ctx.has("missing") is False

    def test_delete(self):
        """Test deleting values."""
        ctx = TemplateContext()
        ctx.set("key", "value")
        assert ctx.delete("key") is True
        assert ctx.has("key") is False
        assert ctx.delete("key") is False

    def test_keys(self):
        """Test getting all keys."""
        ctx = TemplateContext()
        ctx.set("a", 1)
        ctx.set("b", 2)
        keys = ctx.keys(include_parents=False)
        assert "a" in keys
        assert "b" in keys

    def test_to_dict(self):
        """Test converting to dictionary."""
        ctx = TemplateContext()
        ctx.set("a", 1)
        ctx.set("b", 2)
        data = ctx.to_dict()
        assert data == {"a": 1, "b": 2}

    def test_clear(self):
        """Test clearing values."""
        ctx = TemplateContext()
        ctx.set("key", "value")
        ctx.clear()
        assert ctx.has("key") is False


class TestTemplateContextInheritance:
    """Tests for context inheritance."""

    def test_parent_child(self):
        """Test parent-child relationship."""
        parent = TemplateContext(name="parent")
        child = TemplateContext(name="child", parent=parent)
        assert child.parent is parent
        assert child.depth == 1

    def test_inherit_values(self):
        """Test that values inherit from parent."""
        parent = TemplateContext(name="parent")
        parent.set("inherited", "from_parent")

        child = TemplateContext(name="child", parent=parent)
        assert child.get("inherited") == "from_parent"

    def test_override_values(self):
        """Test that child can override parent values."""
        parent = TemplateContext(name="parent")
        parent.set("key", "parent_value")

        child = TemplateContext(name="child", parent=parent)
        child.set("key", "child_value")

        assert parent.get("key") == "parent_value"
        assert child.get("key") == "child_value"

    def test_with_override(self):
        """Test creating child with overrides."""
        parent = TemplateContext(name="parent")
        parent.set("a", 1)

        child = parent.with_override(name="child", b=2, c=3)

        assert child.parent is parent
        assert child.get("a") == 1  # Inherited
        assert child.get("b") == 2  # Override
        assert child.get("c") == 3  # Override

    def test_root(self):
        """Test getting root context."""
        root = TemplateContext(name="root")
        child1 = TemplateContext(name="child1", parent=root)
        child2 = TemplateContext(name="child2", parent=child1)

        assert root.root is root
        assert child1.root is root
        assert child2.root is root

    def test_keys_with_parents(self):
        """Test getting keys including parents."""
        parent = TemplateContext(name="parent")
        parent.set("a", 1)

        child = TemplateContext(name="child", parent=parent)
        child.set("b", 2)

        keys = child.keys(include_parents=True)
        assert "a" in keys
        assert "b" in keys

        keys_no_parent = child.keys(include_parents=False)
        assert "a" not in keys_no_parent
        assert "b" in keys_no_parent

    def test_to_dict_with_parents(self):
        """Test converting to dict including parents."""
        parent = TemplateContext(name="parent")
        parent.set("a", 1)

        child = TemplateContext(name="child", parent=parent)
        child.set("b", 2)

        data = child.to_dict(include_parents=True)
        assert data == {"a": 1, "b": 2}

        data_no_parent = child.to_dict(include_parents=False)
        assert data_no_parent == {"b": 2}

    def test_get_local(self):
        """Test getting local values only."""
        parent = TemplateContext(name="parent")
        parent.set("inherited", "value")

        child = TemplateContext(name="child", parent=parent)
        child.set("local", "value")

        assert child.get_local("local") == "value"
        assert child.get_local("inherited") is None


class TestTemplateContextDunderMethods:
    """Tests for dunder methods."""

    def test_contains(self):
        """Test 'in' operator."""
        ctx = TemplateContext()
        ctx.set("key", "value")
        assert "key" in ctx
        assert "missing" not in ctx

    def test_getitem(self):
        """Test bracket access."""
        ctx = TemplateContext()
        ctx.set("key", "value")
        assert ctx["key"] == "value"

    def test_getitem_missing(self):
        """Test bracket access with missing key."""
        ctx = TemplateContext()
        with pytest.raises(KeyError):
            _ = ctx["missing"]

    def test_setitem(self):
        """Test bracket assignment."""
        ctx = TemplateContext()
        ctx["key"] = "value"
        assert ctx.get("key") == "value"

    def test_delitem(self):
        """Test bracket deletion."""
        ctx = TemplateContext()
        ctx["key"] = "value"
        del ctx["key"]
        assert "key" not in ctx

    def test_delitem_missing(self):
        """Test bracket deletion with missing key."""
        ctx = TemplateContext()
        with pytest.raises(KeyError):
            del ctx["missing"]

    def test_repr(self):
        """Test string representation."""
        ctx = TemplateContext(name="test")
        ctx.set("a", 1)
        repr_str = repr(ctx)
        assert "test" in repr_str
        assert "TemplateContext" in repr_str


class TestContextStack:
    """Tests for ContextStack class."""

    def test_initialization(self):
        """Test stack initialization."""
        stack = ContextStack()
        assert stack.depth == 1  # Root context
        assert stack.current is not None

    def test_push_pop(self):
        """Test pushing and popping contexts."""
        stack = ContextStack()
        initial_depth = stack.depth

        stack.push(a=1)
        assert stack.depth == initial_depth + 1
        assert stack.get("a") == 1

        stack.pop()
        assert stack.depth == initial_depth
        assert stack.get("a") is None

    def test_inheritance(self):
        """Test value inheritance through stack."""
        stack = ContextStack()
        stack.push(project="MyGame")
        stack.push(shot="010")

        assert stack.get("project") == "MyGame"
        assert stack.get("shot") == "010"

    def test_pop_at_root(self):
        """Test popping at root returns None."""
        stack = ContextStack()
        assert stack.pop() is None

    def test_set_in_current(self):
        """Test setting values in current context."""
        stack = ContextStack()
        stack.set("key", "value")
        assert stack.get("key") == "value"

    def test_clear_to_root(self):
        """Test clearing back to root."""
        stack = ContextStack()
        stack.push(a=1)
        stack.push(b=2)
        stack.push(c=3)

        stack.clear_to_root()
        assert stack.depth == 1


class TestTemplateContextIntegration:
    """Integration tests for TemplateContext."""

    def test_project_shot_asset_hierarchy(self):
        """Test typical project/shot/asset context hierarchy."""
        # Project level
        project_ctx = TemplateContext(name="project")
        project_ctx.set("project", "MyGame")
        project_ctx.set("root", "/content")

        # Shot level
        shot_ctx = project_ctx.with_override(
            name="shot_010",
            shot="010",
            episode="ep01",
        )

        # Asset level
        asset_ctx = shot_ctx.with_override(
            name="hero_asset",
            asset="hero",
            version="001",
        )

        # All values should be accessible
        assert asset_ctx.get("project") == "MyGame"
        assert asset_ctx.get("shot") == "010"
        assert asset_ctx.get("asset") == "hero"
        assert asset_ctx.get("version") == "001"

        # Full dict should have all values
        full_dict = asset_ctx.to_dict()
        assert full_dict["project"] == "MyGame"
        assert full_dict["asset"] == "hero"
