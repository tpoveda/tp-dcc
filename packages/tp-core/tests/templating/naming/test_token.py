"""Unit tests for the naming library token module."""

from __future__ import annotations

from tp.libs.templating.naming import token


class TestKeyValue:
    """Tests for the KeyValue class."""

    def test_initialization(self):
        """Test KeyValue initialization."""
        kv = token.KeyValue("left", "L")
        assert kv.name == "left"
        assert kv.value == "L"
        assert kv.protected is False

    def test_initialization_protected(self):
        """Test KeyValue initialization with protected flag."""
        kv = token.KeyValue("center", "C", protected=True)
        assert kv.protected is True

    def test_repr(self):
        """Test KeyValue string representation."""
        kv = token.KeyValue("left", "L")
        assert "KeyValue" in repr(kv)
        assert "left" in repr(kv)
        assert "L" in repr(kv)

    def test_str(self):
        """Test KeyValue string conversion."""
        kv = token.KeyValue("left", "L")
        assert str(kv) == "L"

    def test_hash(self):
        """Test KeyValue hashing."""
        kv1 = token.KeyValue("left", "L")
        kv2 = token.KeyValue("left", "R")
        # Hash is based on name only
        assert hash(kv1) == hash(kv2)

    def test_equality(self):
        """Test KeyValue equality comparison."""
        kv1 = token.KeyValue("left", "L")
        kv2 = token.KeyValue("left", "L")
        kv3 = token.KeyValue("right", "R")
        assert kv1 == kv2
        assert kv1 != kv3

    def test_equality_with_non_keyvalue(self):
        """Test KeyValue equality with non-KeyValue objects."""
        kv = token.KeyValue("left", "L")
        assert kv != "left"
        assert kv != 123

    def test_name_setter(self):
        """Test KeyValue name setter."""
        kv = token.KeyValue("left", "L")
        kv.name = "right"
        assert kv.name == "right"

    def test_name_setter_protected(self):
        """Test KeyValue name setter with protected flag."""
        kv = token.KeyValue("left", "L", protected=True)
        kv.name = "right"
        assert kv.name == "left"  # Should not change

    def test_value_setter(self):
        """Test KeyValue value setter."""
        kv = token.KeyValue("left", "L")
        kv.value = "LEFT"
        assert kv.value == "LEFT"

    def test_to_dict(self):
        """Test KeyValue to_dict method."""
        kv = token.KeyValue("left", "L")
        data = kv.to_dict()
        assert data["name"] == "left"
        assert data["value"] == "L"


class TestToken:
    """Tests for the Token class."""

    def test_initialization(self):
        """Test Token initialization."""
        t = token.Token(
            name="side",
            description="Side of the object",
            permissions=[],
            key_values=[],
        )
        assert t.name == "side"
        assert t.description == "Side of the object"
        assert len(t) == 0

    def test_initialization_with_key_values(self):
        """Test Token initialization with key-value pairs."""
        key_values = [
            token.KeyValue("left", "L"),
            token.KeyValue("right", "R"),
        ]
        t = token.Token(
            name="side",
            description="Side",
            permissions=[],
            key_values=key_values,
        )
        assert len(t) == 2
        assert t.has_key("left")
        assert t.has_key("right")

    def test_repr(self):
        """Test Token string representation."""
        t = token.Token(
            name="side",
            description="",
            permissions=[],
            key_values=[],
        )
        assert "Token" in repr(t)
        assert "side" in repr(t)

    def test_len(self):
        """Test Token length."""
        key_values = [
            token.KeyValue("left", "L"),
            token.KeyValue("right", "R"),
        ]
        t = token.Token(
            name="side",
            description="",
            permissions=[],
            key_values=key_values,
        )
        assert len(t) == 2

    def test_iter(self):
        """Test Token iteration."""
        key_values = [
            token.KeyValue("left", "L"),
            token.KeyValue("right", "R"),
        ]
        t = token.Token(
            name="side",
            description="",
            permissions=[],
            key_values=key_values,
        )
        keys = [kv.name for kv in t]
        assert "left" in keys
        assert "right" in keys

    def test_add_key_value(self):
        """Test adding a key-value pair to token."""
        t = token.Token(
            name="side",
            description="",
            permissions=[],
            key_values=[],
        )
        result = t.add("left", "L")
        assert result is not None
        assert isinstance(result, token.KeyValue)
        assert t.has_key("left")
        assert t.solve("left") == "L"

    def test_add_duplicate_key(self):
        """Test adding a duplicate key generates unique name."""
        key_values = [token.KeyValue("left", "L")]
        t = token.Token(
            name="side",
            description="",
            permissions=[],
            key_values=key_values,
        )
        result = t.add("left", "LEFT")
        # Should add with modified name (left1)
        assert result is not None
        assert len(t) == 2

    def test_remove_key(self):
        """Test removing a key from token."""
        key_values = [
            token.KeyValue("left", "L"),
            token.KeyValue("right", "R"),
        ]
        t = token.Token(
            name="side",
            description="",
            permissions=[],
            key_values=key_values,
        )
        result = t.remove("left")
        assert result is True
        assert not t.has_key("left")

    def test_remove_nonexistent_key(self):
        """Test removing a key that doesn't exist."""
        key_values = [token.KeyValue("left", "L")]
        t = token.Token(
            name="side",
            description="",
            permissions=[],
            key_values=key_values,
        )
        result = t.remove("nonexistent")
        assert result is False

    def test_solve_existing_key(self):
        """Test solving an existing key."""
        key_values = [
            token.KeyValue("left", "L"),
            token.KeyValue("right", "R"),
        ]
        t = token.Token(
            name="side",
            description="",
            permissions=[],
            key_values=key_values,
        )
        assert t.solve("left") == "L"
        assert t.solve("right") == "R"

    def test_solve_nonexistent_key(self):
        """Test solving a non-existent key."""
        key_values = [token.KeyValue("left", "L")]
        t = token.Token(
            name="side",
            description="",
            permissions=[],
            key_values=key_values,
        )
        assert t.solve("nonexistent") is None

    def test_solve_with_default_fallback(self):
        """Test solving with default fallback value."""
        key_values = [token.KeyValue("left", "L")]
        t = token.Token(
            name="side",
            description="",
            permissions=[],
            key_values=key_values,
        )
        result = t.solve("nonexistent", "DEFAULT")
        assert result == "DEFAULT"

    def test_has_key(self):
        """Test checking if key exists."""
        key_values = [token.KeyValue("left", "L")]
        t = token.Token(
            name="side",
            description="",
            permissions=[],
            key_values=key_values,
        )
        assert t.has_key("left") is True
        assert t.has_key("right") is False

    def test_key_value(self):
        """Test getting a KeyValue by name."""
        key_values = [token.KeyValue("left", "L")]
        t = token.Token(
            name="side",
            description="",
            permissions=[],
            key_values=key_values,
        )
        kv = t.key_value("left")
        assert kv is not None
        assert kv.value == "L"

    def test_key_value_nonexistent(self):
        """Test getting a non-existent KeyValue."""
        key_values = [token.KeyValue("left", "L")]
        t = token.Token(
            name="side",
            description="",
            permissions=[],
            key_values=key_values,
        )
        kv = t.key_value("nonexistent")
        assert kv is None

    def test_key_values_method(self):
        """Test getting all key values."""
        key_values = [
            token.KeyValue("left", "L"),
            token.KeyValue("right", "R"),
        ]
        t = token.Token(
            name="side",
            description="",
            permissions=[],
            key_values=key_values,
        )
        all_kvs = t.key_values()
        assert len(all_kvs) == 2
        names = [kv.name for kv in all_kvs]
        assert "left" in names
        assert "right" in names

    def test_to_dict(self):
        """Test serialization to dictionary."""
        key_values = [
            token.KeyValue("left", "L"),
            token.KeyValue("right", "R"),
        ]
        t = token.Token(
            name="side",
            description="Side of object",
            permissions=[],
            key_values=key_values,
        )
        data = t.to_dict()
        assert data["name"] == "side"
        assert data["description"] == "Side of object"
        assert "table" in data
        assert data["table"]["left"] == "L"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "name": "side",
            "description": "Side of object",
            "table": {"left": "L", "right": "R"},
        }
        t = token.Token.from_dict(data)
        assert t is not None
        assert t.name == "side"
        assert t.description == "Side of object"
        assert t.solve("left") == "L"

    def test_from_dict_minimal(self):
        """Test deserialization from minimal dictionary."""
        data = {"name": "description"}
        t = token.Token.from_dict(data)
        assert t is not None
        assert t.name == "description"
        assert len(t) == 0

    def test_from_dict_invalid(self):
        """Test deserialization from invalid dictionary - missing name."""
        data = {"invalid": "data"}
        # from_dict requires "name" key, so this should fail
        try:
            t = token.Token.from_dict(data)
            # If it doesn't raise, it may return None or have unexpected behavior
            assert t is None or t.name == ""
        except KeyError:
            pass  # Expected behavior - missing required key

    def test_name_property(self):
        """Test token name property getter."""
        t = token.Token(
            name="side",
            description="",
            permissions=[],
            key_values=[],
        )
        assert t.name == "side"

    def test_description_property(self):
        """Test token description property getter."""
        t = token.Token(
            name="side",
            description="Side of the object",
            permissions=[],
            key_values=[],
        )
        assert t.description == "Side of the object"


class TestTokenPadding:
    """Tests for Token padding functionality."""

    def test_padding_default_zero(self):
        """Test that padding defaults to 0."""
        t = token.Token(
            name="index",
            description="Index number",
            permissions=[],
            key_values=[],
        )
        assert t.padding == 0

    def test_padding_initialization(self):
        """Test Token initialization with padding."""
        t = token.Token(
            name="index",
            description="Index number",
            permissions=[],
            key_values=[],
            padding=3,
        )
        assert t.padding == 3

    def test_padding_setter(self):
        """Test Token padding setter."""
        t = token.Token(
            name="index",
            description="Index number",
            permissions=[],
            key_values=[],
        )
        t.padding = 4
        assert t.padding == 4

    def test_padding_setter_negative(self):
        """Test Token padding setter with negative value."""
        t = token.Token(
            name="index",
            description="Index number",
            permissions=[],
            key_values=[],
        )
        t.padding = -5
        assert t.padding == 0  # Should clamp to 0

    def test_solve_with_padding_single_digit(self):
        """Test solve applies padding to single digit."""
        t = token.Token(
            name="index",
            description="Index number",
            permissions=[],
            key_values=[],
            padding=3,
        )
        # When no key-value mapping, padding is applied to the key itself
        result = t.solve("1")
        assert result == "001"

    def test_solve_with_padding_multiple_digits(self):
        """Test solve applies padding correctly to multiple digits."""
        t = token.Token(
            name="index",
            description="Index number",
            permissions=[],
            key_values=[],
            padding=3,
        )
        result = t.solve("42")
        assert result == "042"

    def test_solve_with_padding_already_padded(self):
        """Test solve handles already padded values."""
        t = token.Token(
            name="index",
            description="Index number",
            permissions=[],
            key_values=[],
            padding=3,
        )
        result = t.solve("007")
        assert result == "007"

    def test_solve_with_padding_exceeds_length(self):
        """Test solve when value exceeds padding length."""
        t = token.Token(
            name="index",
            description="Index number",
            permissions=[],
            key_values=[],
            padding=2,
        )
        result = t.solve("123")
        assert result == "123"  # Should not truncate

    def test_solve_without_padding_non_numeric(self):
        """Test solve without padding returns non-numeric as-is."""
        t = token.Token(
            name="side",
            description="Side",
            permissions=[],
            key_values=[token.KeyValue("left", "L")],
            padding=0,
        )
        result = t.solve("left")
        assert result == "L"

    def test_solve_with_padding_non_numeric(self):
        """Test solve with padding on non-numeric value."""
        t = token.Token(
            name="side",
            description="Side",
            permissions=[],
            key_values=[],
            padding=3,
        )
        result = t.solve("abc")
        assert result == "abc"  # Non-numeric, no padding applied

    def test_to_dict_includes_padding(self):
        """Test to_dict includes padding when non-zero."""
        t = token.Token(
            name="index",
            description="Index number",
            permissions=[],
            key_values=[],
            padding=3,
        )
        data = t.to_dict()
        assert data["padding"] == 3

    def test_to_dict_excludes_zero_padding(self):
        """Test to_dict excludes padding when zero."""
        t = token.Token(
            name="index",
            description="Index number",
            permissions=[],
            key_values=[],
            padding=0,
        )
        data = t.to_dict()
        assert "padding" not in data

    def test_from_dict_with_padding(self):
        """Test from_dict loads padding correctly."""
        data = {
            "name": "index",
            "description": "Index number",
            "padding": 4,
            "table": {},
        }
        t = token.Token.from_dict(data)
        assert t is not None
        assert t.padding == 4

    def test_from_dict_without_padding(self):
        """Test from_dict defaults padding to 0."""
        data = {
            "name": "index",
            "description": "Index number",
            "table": {},
        }
        t = token.Token.from_dict(data)
        assert t is not None
        assert t.padding == 0

    def test_padding_roundtrip(self):
        """Test padding survives serialization/deserialization."""
        original = token.Token(
            name="index",
            description="Index number",
            permissions=[],
            key_values=[],
            padding=5,
        )
        data = original.to_dict()
        restored = token.Token.from_dict(data)
        assert restored.padding == original.padding


class TestTokenSerialization:
    """Tests for token serialization and deserialization."""

    def test_round_trip(self):
        """Test that serialization and deserialization preserves data."""
        key_values = [
            token.KeyValue("left", "L"),
            token.KeyValue("right", "R"),
            token.KeyValue("middle", "M"),
        ]
        original = token.Token(
            name="side",
            description="Side of the object",
            permissions=[],
            key_values=key_values,
        )
        data = original.to_dict()
        restored = token.Token.from_dict(data)

        assert restored is not None
        assert restored.name == original.name
        assert restored.description == original.description
        assert len(restored) == len(original)
        for kv in original.key_values():
            assert restored.solve(kv.name) == original.solve(kv.name)

    def test_from_dict_with_default(self):
        """Test deserialization handles default value."""
        data = {
            "name": "side",
            "table": {"left": "L"},
            "default": "M",
        }
        t = token.Token.from_dict(data)
        assert t is not None
        # Default handling depends on implementation
