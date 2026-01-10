"""Unit tests for the naming library convention module."""

from __future__ import annotations

import os
import tempfile

from tp.libs.templating.naming import convention


class TestNamingConventionInitialization:
    """Tests for NamingConvention initialization."""

    def test_default_initialization(self):
        """Test NamingConvention default initialization."""
        nc = convention.NamingConvention()
        assert nc.name == ""
        assert nc.description == ""
        assert nc.parent is None
        assert nc.token_count() == 0
        assert nc.rule_count() == 0

    def test_initialization_with_naming_data(self):
        """Test NamingConvention with naming data."""
        naming_data = {"name": "test_convention", "description": "Test"}
        nc = convention.NamingConvention(naming_data=naming_data)
        assert nc.name == "test_convention"
        assert nc.description == "Test"

    def test_initialization_with_parent(self):
        """Test NamingConvention with parent."""
        parent = convention.NamingConvention(naming_data={"name": "parent"})
        child = convention.NamingConvention(
            naming_data={"name": "child"}, parent=parent
        )
        assert child.parent is parent


class TestNamingConventionTokens:
    """Tests for NamingConvention token management."""

    def test_add_token(self, empty_naming_convention):
        """Test adding a token."""
        t = empty_naming_convention.add_token("side")
        assert t is not None
        assert empty_naming_convention.has_token("side")

    def test_add_token_with_values(self, empty_naming_convention):
        """Test adding a token with key-value pairs."""
        t = empty_naming_convention.add_token("side", left="L", right="R")
        assert t.solve("left") == "L"
        assert t.solve("right") == "R"

    def test_add_token_with_default(self, empty_naming_convention):
        """Test adding a token with default value."""
        t = empty_naming_convention.add_token(
            "side", left="L", right="R", default="M"
        )
        assert t.default is not None
        assert t.default.value == "M"

    def test_add_token_with_padding(self, empty_naming_convention):
        """Test adding a token with padding for numeric values."""
        t = empty_naming_convention.add_token("index", padding=3)
        assert t is not None
        assert t.padding == 3
        # Test that solve applies padding
        assert t.solve("1") == "001"
        assert t.solve("42") == "042"
        assert t.solve("123") == "123"  # Doesn't truncate

    def test_delete_token(self, empty_naming_convention):
        """Test deleting a token."""
        t = empty_naming_convention.add_token("side")
        result = empty_naming_convention.delete_token(t)
        assert result is True
        assert not empty_naming_convention.has_token("side")

    def test_delete_token_by_name(self, empty_naming_convention):
        """Test deleting a token by name."""
        empty_naming_convention.add_token("side")
        result = empty_naming_convention.delete_token_by_name("side")
        assert result is True
        assert not empty_naming_convention.has_token("side")

    def test_delete_nonexistent_token(self, empty_naming_convention):
        """Test deleting a non-existent token."""
        result = empty_naming_convention.delete_token_by_name("nonexistent")
        assert result is False

    def test_has_token(self, empty_naming_convention):
        """Test checking if token exists."""
        empty_naming_convention.add_token("side")
        assert empty_naming_convention.has_token("side") is True
        assert empty_naming_convention.has_token("nonexistent") is False

    def test_token(self, empty_naming_convention):
        """Test getting a token by name."""
        empty_naming_convention.add_token("side", left="L")
        t = empty_naming_convention.token("side")
        assert t is not None
        assert t.name == "side"

    def test_token_nonexistent(self, empty_naming_convention):
        """Test getting a non-existent token."""
        t = empty_naming_convention.token("nonexistent")
        assert t is None

    def test_token_count(self, empty_naming_convention):
        """Test counting tokens."""
        assert empty_naming_convention.token_count() == 0
        empty_naming_convention.add_token("side")
        assert empty_naming_convention.token_count() == 1
        empty_naming_convention.add_token("type")
        assert empty_naming_convention.token_count() == 2

    def test_clear_tokens(self, empty_naming_convention):
        """Test clearing all tokens."""
        empty_naming_convention.add_token("side")
        empty_naming_convention.add_token("type")
        empty_naming_convention.clear_tokens()
        assert empty_naming_convention.token_count() == 0

    def test_tokens_list(self, empty_naming_convention):
        """Test getting list of tokens."""
        empty_naming_convention.add_token("side")
        empty_naming_convention.add_token("type")
        tokens = empty_naming_convention.tokens()
        assert len(tokens) == 2


class TestNamingConventionRules:
    """Tests for NamingConvention rule management."""

    def test_add_rule(self, empty_naming_convention):
        """Test adding a rule."""
        r = empty_naming_convention.add_rule(
            "test_rule",
            "{prefix}_{name}",
            {"prefix": "PFX", "name": "Object"},
        )
        assert r is not None
        assert empty_naming_convention.has_rule("test_rule")

    def test_add_rule_from_tokens(self, simple_naming_convention):
        """Test adding a rule from token names."""
        r = simple_naming_convention.add_rule_from_tokens(
            "new_rule", "description", "side"
        )
        assert r is not None
        assert "{description}" in r.expression
        assert "{side}" in r.expression

    def test_delete_rule(self, empty_naming_convention):
        """Test deleting a rule."""
        r = empty_naming_convention.add_rule("test", "{a}", {})
        result = empty_naming_convention.delete_rule(r)
        assert result is True
        assert not empty_naming_convention.has_rule("test")

    def test_delete_rule_by_name(self, empty_naming_convention):
        """Test deleting a rule by name."""
        empty_naming_convention.add_rule("test", "{a}", {})
        result = empty_naming_convention.delete_rule_by_name("test")
        assert result is True
        assert not empty_naming_convention.has_rule("test")

    def test_delete_nonexistent_rule(self, empty_naming_convention):
        """Test deleting a non-existent rule."""
        result = empty_naming_convention.delete_rule_by_name("nonexistent")
        assert result is False

    def test_has_rule(self, empty_naming_convention):
        """Test checking if rule exists."""
        empty_naming_convention.add_rule("test", "{a}", {})
        assert empty_naming_convention.has_rule("test") is True
        assert empty_naming_convention.has_rule("nonexistent") is False

    def test_rule(self, empty_naming_convention):
        """Test getting a rule by name."""
        empty_naming_convention.add_rule("test", "{a}_{b}", {})
        r = empty_naming_convention.rule("test")
        assert r is not None
        assert r.name == "test"

    def test_rule_nonexistent(self, empty_naming_convention):
        """Test getting a non-existent rule."""
        r = empty_naming_convention.rule("nonexistent")
        assert r is None

    def test_rule_count(self, empty_naming_convention):
        """Test counting rules."""
        assert empty_naming_convention.rule_count() == 0
        empty_naming_convention.add_rule("rule1", "{a}", {})
        assert empty_naming_convention.rule_count() == 1
        empty_naming_convention.add_rule("rule2", "{b}", {})
        assert empty_naming_convention.rule_count() == 2

    def test_clear_rules(self, empty_naming_convention):
        """Test clearing all rules."""
        empty_naming_convention.add_rule("rule1", "{a}", {})
        empty_naming_convention.add_rule("rule2", "{b}", {})
        empty_naming_convention.clear_rules()
        assert empty_naming_convention.rule_count() == 0

    def test_rules_list(self, empty_naming_convention):
        """Test getting list of rules."""
        empty_naming_convention.add_rule("rule1", "{a}", {})
        empty_naming_convention.add_rule("rule2", "{b}", {})
        rules = empty_naming_convention.rules()
        assert len(rules) == 2


class TestNamingConventionActiveRule:
    """Tests for NamingConvention active rule."""

    def test_set_active_rule(self, simple_naming_convention):
        """Test setting active rule."""
        r = simple_naming_convention.rule("default")
        simple_naming_convention.set_active_rule(r)
        assert simple_naming_convention.active_rule() == r

    def test_set_active_rule_by_name(self, simple_naming_convention):
        """Test setting active rule by name."""
        result = simple_naming_convention.set_active_rule_by_name("default")
        assert result is True
        assert simple_naming_convention.active_rule().name == "default"

    def test_set_active_rule_by_name_nonexistent(
        self, simple_naming_convention
    ):
        """Test setting non-existent active rule by name."""
        result = simple_naming_convention.set_active_rule_by_name(
            "nonexistent"
        )
        assert result is False

    def test_clear_active_rule(self, simple_naming_convention):
        """Test clearing active rule."""
        simple_naming_convention.set_active_rule_by_name("default")
        simple_naming_convention.set_active_rule(None)
        assert simple_naming_convention.active_rule() is None


class TestNamingConventionSolve:
    """Tests for NamingConvention name solving."""

    def test_solve_explicit(self, simple_naming_convention):
        """Test solving with explicit values."""
        simple_naming_convention.set_active_rule_by_name("default")
        result = simple_naming_convention.solve(
            description="foo", side="left", type="joint"
        )
        assert result == "foo_L_jnt"

    def test_solve_with_defaults(self, simple_naming_convention):
        """Test solving with default token values."""
        simple_naming_convention.set_active_rule_by_name("default")
        result = simple_naming_convention.solve(description="foo")
        assert result == "foo_M_ctrl"  # Uses defaults for side and type

    def test_solve_implicit(self, simple_naming_convention):
        """Test solving with implicit first argument."""
        simple_naming_convention.set_active_rule_by_name("default")
        result = simple_naming_convention.solve(
            "foo", side="left", type="joint"
        )
        assert result == "foo_L_jnt"

    def test_solve_with_rule_name(self, simple_naming_convention):
        """Test solving with specific rule name."""
        simple_naming_convention.add_rule(
            "alternate",
            "{type}_{description}",
            {"type": "joint", "description": "test"},
        )
        result = simple_naming_convention.solve(
            rule_name="alternate", description="bar", type="joint"
        )
        assert result == "jnt_bar"

    def test_solve_nonexistent_token_value(self, simple_naming_convention):
        """Test solving with non-existent token value uses value directly."""
        simple_naming_convention.set_active_rule_by_name("default")
        result = simple_naming_convention.solve(
            description="custom_desc", side="custom_side", type="custom_type"
        )
        # Non-table values are used directly
        assert "custom_desc" in result

    def test_solve_with_index_padding(self, empty_naming_convention):
        """Test solving with index token that has padding."""
        # Add tokens
        empty_naming_convention.add_token("description")
        empty_naming_convention.add_token(
            "side", left="L", right="R", center="C"
        )
        empty_naming_convention.add_token("type", joint="jnt", control="ctrl")
        empty_naming_convention.add_token("index", padding=2)

        # Add rule with index
        empty_naming_convention.add_rule(
            "indexed",
            "{description}_{side}_{type}_{index}",
            {
                "description": "arm",
                "side": "left",
                "type": "joint",
                "index": "01",
            },
        )

        # Solve with single digit - should be padded to 2 digits
        result = empty_naming_convention.solve(
            rule_name="indexed",
            description="arm",
            side="left",
            type="joint",
            index="1",
        )
        assert result == "arm_L_jnt_01"

        # Solve with two digits - should remain as-is
        result2 = empty_naming_convention.solve(
            rule_name="indexed",
            description="leg",
            side="right",
            type="control",
            index="12",
        )
        assert result2 == "leg_R_ctrl_12"


class TestNamingConventionParse:
    """Tests for NamingConvention name parsing."""

    def test_parse(self, simple_naming_convention):
        """Test parsing a solved name."""
        parsed = simple_naming_convention.parse("foo_M_ctrl")
        assert parsed["description"] == "foo"
        assert parsed["side"] == "middle"
        assert parsed["type"] == "control"

    def test_parse_by_active_rule(self, simple_naming_convention):
        """Test parsing by active rule."""
        simple_naming_convention.set_active_rule_by_name("default")
        parsed = simple_naming_convention.parse_by_active_rule("bar_L_jnt")
        assert parsed["description"] == "bar"
        assert parsed["side"] == "left"
        assert parsed["type"] == "joint"

    def test_parse_by_rule(self, simple_naming_convention):
        """Test parsing by specific rule."""
        r = simple_naming_convention.rule("default")
        parsed = simple_naming_convention.parse_by_rule(r, "baz_R_anim")
        assert parsed["description"] == "baz"
        assert parsed["side"] == "right"
        assert parsed["type"] == "animation"


class TestNamingConventionParentInheritance:
    """Tests for NamingConvention parent inheritance."""

    def test_inherit_tokens_from_parent(self, naming_convention_with_parent):
        """Test that tokens are inherited from parent."""
        # Child should have access to parent's tokens
        parent_token = naming_convention_with_parent.token(
            "myToken", recursive=True
        )
        assert parent_token is not None

    def test_inherit_rules_from_parent(self, naming_convention_with_parent):
        """Test that rules are inherited from parent."""
        # Child should have access to parent's rules
        parent_rule = naming_convention_with_parent.rule(
            "parentRule", recursive=True
        )
        assert parent_rule is not None

    def test_child_overrides_parent_rule(self, naming_convention_with_parent):
        """Test that child rules override parent rules with same name."""
        # Both base and parent have "object" rule
        object_rule = naming_convention_with_parent.rule("object")
        # Should get the child's rule (base.json version)
        assert object_rule is not None


class TestNamingConventionSerialization:
    """Tests for NamingConvention serialization."""

    def test_save_and_load(self, simple_naming_convention):
        """Test saving and loading a naming convention."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            result = simple_naming_convention.save_to_file(temp_path)
            assert result is True
            assert os.path.isfile(temp_path)

            loaded = convention.NamingConvention.from_path(temp_path)
            assert loaded is not None
            assert loaded.has_token("description")
            assert loaded.has_token("side")
            assert loaded.has_token("type")
            assert loaded.has_rule("default")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_from_path_json(self, base_naming_convention):
        """Test loading from JSON file."""
        assert base_naming_convention is not None
        assert base_naming_convention.name == "base"
        assert base_naming_convention.has_rule("object")

    def test_save_to_file(self, simple_naming_convention, temp_dir):
        """Test saving naming convention to file."""
        temp_path = os.path.join(temp_dir, "test_convention.yaml")

        result = simple_naming_convention.save_to_file(temp_path)
        assert result is True
        assert os.path.isfile(temp_path)


class TestNamingConventionExpressionFromString:
    """Tests for NamingConvention expression matching."""

    def test_expression_from_string(self, base_naming_convention):
        """Test getting expression from solved string."""
        expression = base_naming_convention.expression_from_string(
            "head_l_jnt"
        )
        assert expression == "{area}_{section}_{side}_{type}"

    def test_rule_from_expression(self, base_naming_convention):
        """Test finding rule from expression."""
        r = base_naming_convention.rule_from_expression(
            "{area}_{section}_{side}_{type}"
        )
        assert r is not None
        assert r.name == "object"

    def test_rule_from_expression_not_found(self, base_naming_convention):
        """Test finding rule from non-existent expression."""
        r = base_naming_convention.rule_from_expression(
            "{nonexistent}_{expression}"
        )
        assert r is None
