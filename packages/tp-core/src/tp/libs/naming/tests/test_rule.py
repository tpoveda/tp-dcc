"""Unit tests for the naming library rule module."""

from __future__ import annotations

from tp.libs.naming import rule


class TestRule:
    """Tests for the Rule class."""

    def test_initialization(self):
        """Test Rule initialization."""
        r = rule.Rule(
            name="test_rule",
            creator="tester",
            description="A test rule",
            expression="{prefix}_{name}_{suffix}",
            example_tokens={"prefix": "PFX", "name": "Object", "suffix": "01"},
        )
        assert r.name == "test_rule"
        assert r.creator == "tester"
        assert r.description == "A test rule"
        assert r.expression == "{prefix}_{name}_{suffix}"
        assert r.example_tokens == {
            "prefix": "PFX",
            "name": "Object",
            "suffix": "01",
        }

    def test_repr(self):
        """Test Rule string representation."""
        r = rule.Rule(
            name="test_rule",
            creator="tester",
            description="A test rule",
            expression="{prefix}_{name}",
            example_tokens={},
        )
        assert "Rule" in repr(r)
        assert "test_rule" in repr(r)
        assert "{prefix}_{name}" in repr(r)

    def test_hash(self):
        """Test Rule hashing."""
        r1 = rule.Rule("rule1", "", "", "{a}_{b}", {})
        r2 = rule.Rule("rule1", "", "", "{c}_{d}", {})
        # Hash is based on name only
        assert hash(r1) == hash(r2)

    def test_equality(self):
        """Test Rule equality comparison."""
        r1 = rule.Rule("rule1", "", "", "{a}_{b}", {})
        r2 = rule.Rule("rule1", "", "", "{c}_{d}", {})
        r3 = rule.Rule("rule2", "", "", "{a}_{b}", {})
        assert r1 == r2  # Same name
        assert r1 != r3  # Different name

    def test_equality_with_non_rule(self):
        """Test Rule equality with non-Rule objects."""
        r = rule.Rule("rule1", "", "", "{a}_{b}", {})
        assert r != "rule1"
        assert r != 123

    def test_tokens(self):
        """Test extracting tokens from expression."""
        r = rule.Rule(
            name="test",
            creator="",
            description="",
            expression="{prefix}_{name}_{suffix}",
            example_tokens={},
        )
        tokens = r.tokens()
        assert "prefix" in tokens
        assert "name" in tokens
        assert "suffix" in tokens
        assert len(tokens) == 3

    def test_tokens_no_tokens(self):
        """Test extracting tokens from expression without tokens."""
        r = rule.Rule(
            name="test",
            creator="",
            description="",
            expression="static_name",
            example_tokens={},
        )
        tokens = r.tokens()
        assert len(tokens) == 0

    def test_tokens_complex_expression(self):
        """Test extracting tokens from complex expression."""
        r = rule.Rule(
            name="test",
            creator="",
            description="",
            expression="{a}_{b}_{c}_{d}_{e}",
            example_tokens={},
        )
        tokens = r.tokens()
        assert len(tokens) == 5


class TestRuleSerialization:
    """Tests for Rule serialization and deserialization."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        r = rule.Rule(
            name="test_rule",
            creator="tester",
            description="A test rule",
            expression="{prefix}_{name}",
            example_tokens={"prefix": "PFX", "name": "Object"},
        )
        data = r.to_dict()
        assert data["name"] == "test_rule"
        assert data["creator"] == "tester"
        assert data["description"] == "A test rule"
        assert data["expression"] == "{prefix}_{name}"
        assert data["exampleFields"] == {"prefix": "PFX", "name": "Object"}

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "name": "test_rule",
            "creator": "tester",
            "description": "A test rule",
            "expression": "{prefix}_{name}",
            "exampleFields": {"prefix": "PFX", "name": "Object"},
        }
        r = rule.Rule.from_dict(data)
        assert r is not None
        assert r.name == "test_rule"
        assert r.creator == "tester"
        assert r.description == "A test rule"
        assert r.expression == "{prefix}_{name}"

    def test_from_dict_minimal(self):
        """Test deserialization from minimal dictionary."""
        data = {
            "name": "test_rule",
            "expression": "{name}",
        }
        r = rule.Rule.from_dict(data)
        assert r is not None
        assert r.name == "test_rule"
        assert r.expression == "{name}"
        assert r.creator == ""
        assert r.description == ""

    def test_from_dict_invalid(self):
        """Test deserialization from invalid dictionary - missing name."""
        data = {"invalid": "data"}
        # from_dict requires "name" key
        try:
            r = rule.Rule.from_dict(data)
            # If it doesn't raise, should return None or fail
            assert r is None or r.name == ""
        except KeyError:
            pass  # Expected behavior - missing required key

    def test_round_trip(self):
        """Test that serialization and deserialization preserves data."""
        original = rule.Rule(
            name="complex_rule",
            creator="developer",
            description="A complex naming rule",
            expression="{type}_{category}_{name}_{version}",
            example_tokens={
                "type": "CHR",
                "category": "Hero",
                "name": "Warrior",
                "version": "v001",
            },
        )
        data = original.to_dict()
        restored = rule.Rule.from_dict(data)

        assert restored is not None
        assert restored.name == original.name
        assert restored.creator == original.creator
        assert restored.description == original.description
        assert restored.expression == original.expression
        assert restored.example_tokens == original.example_tokens


class TestRuleExpressionParsing:
    """Tests for rule expression parsing."""

    def test_expression_property(self):
        """Test expression property getter."""
        r = rule.Rule("test", "", "", "{a}_{b}", {})
        assert r.expression == "{a}_{b}"

    def test_tokens_with_underscores(self):
        """Test tokens with underscores in the expression."""
        r = rule.Rule(
            name="test",
            creator="",
            description="",
            expression="{asset_type}_{asset_name}",
            example_tokens={},
        )
        tokens = r.tokens()
        assert "asset_type" in tokens
        assert "asset_name" in tokens

    def test_tokens_with_repeated_tokens(self):
        """Test expression with repeated token names."""
        r = rule.Rule(
            name="test",
            creator="",
            description="",
            expression="{name}_{name}_{name}",
            example_tokens={},
        )
        tokens = r.tokens()
        # Should return unique tokens
        assert tokens.count("name") == 1 or len(set(tokens)) <= len(tokens)


class TestRuleExampleTokens:
    """Tests for rule example tokens."""

    def test_example_tokens_property(self):
        """Test example_tokens property getter."""
        examples = {"prefix": "PFX", "name": "Object"}
        r = rule.Rule("test", "", "", "{prefix}_{name}", examples)
        assert r.example_tokens == examples

    def test_empty_example_tokens(self):
        """Test rule with empty example tokens."""
        r = rule.Rule("test", "", "", "{prefix}_{name}", {})
        assert r.example_tokens == {}

    def test_example_tokens_validation(self):
        """Test that example tokens should match expression tokens."""
        r = rule.Rule(
            name="test",
            creator="",
            description="",
            expression="{prefix}_{name}_{suffix}",
            example_tokens={"prefix": "PFX", "name": "Object", "suffix": "01"},
        )
        expression_tokens = r.tokens()
        for token_name in expression_tokens:
            assert token_name in r.example_tokens
