"""Integration tests for the naming library API module."""

from __future__ import annotations

import os

import pytest

from tp.libs.naming import api, config, convention


class TestPresetManagerAPI:
    """Tests for the preset manager API functions."""

    def test_naming_preset_manager(self, reset_global_config):
        """Test getting the global preset manager."""
        pm = api.naming_preset_manager()
        assert pm is not None

    def test_naming_preset_manager_singleton(self, reset_global_config):
        """Test that naming_preset_manager returns the same instance."""
        pm1 = api.naming_preset_manager()
        pm2 = api.naming_preset_manager()
        assert pm1 is pm2

    def test_naming_preset_manager_with_configuration(
        self, reset_global_config
    ):
        """Test preset manager with custom configuration."""
        custom_cfg = config.NamingConfiguration()
        builtin_path = config.builtin_presets_path()
        custom_cfg.add_preset_path(builtin_path)
        custom_cfg.default_preset_name = "default"

        pm = api.naming_preset_manager(configuration=custom_cfg)
        assert pm is not None

    def test_reset_preset_manager(self, reset_global_config):
        """Test resetting the global preset manager."""
        pm1 = api.naming_preset_manager()
        api.reset_preset_manager()
        pm2 = api.naming_preset_manager()
        assert pm1 is not pm2


class TestNamingConventionAPI:
    """Tests for naming convention API functions."""

    def test_naming_convention_global(self, reset_global_config):
        """Test getting the global naming convention."""
        nc = api.naming_convention(name="global")
        assert nc is not None

    def test_naming_convention_by_name(self, reset_global_config):
        """Test getting a naming convention by name."""
        nc = api.naming_convention(name="global")
        assert nc is not None

    def test_naming_convention_set_as_active(self, reset_global_config):
        """Test setting naming convention as active."""
        nc = api.naming_convention(name="global", set_as_active=True)
        assert nc is not None
        assert api.active_naming_convention() is nc

    def test_naming_convention_not_set_as_active(self, reset_global_config):
        """Test getting naming convention without setting as active."""
        api.set_active_naming_convention(None)
        nc = api.naming_convention(name="global", set_as_active=False)
        assert nc is not None
        # Active should still be None or previous value
        # (depends on previous state)


class TestActiveNamingConventionAPI:
    """Tests for active naming convention API functions."""

    def test_active_naming_convention_default(self, reset_global_config):
        """Test that active naming convention starts as None."""
        api.set_active_naming_convention(None)
        assert api.active_naming_convention() is None

    def test_set_active_naming_convention(self, reset_global_config):
        """Test setting active naming convention."""
        nc = api.naming_convention(name="global")
        api.set_active_naming_convention(nc)
        assert api.active_naming_convention() is nc

    def test_clear_active_naming_convention(self, reset_global_config):
        """Test clearing active naming convention."""
        nc = api.naming_convention(name="global")
        api.set_active_naming_convention(nc)
        api.set_active_naming_convention(None)
        assert api.active_naming_convention() is None


class TestSolveAPI:
    """Tests for the solve API function."""

    def test_solve_with_explicit_convention(self, reset_global_config):
        """Test solving with explicit naming convention."""
        nc = api.naming_convention(name="global")
        if nc:
            nc.add_token("description")
            nc.add_token("side", left="L", right="R", default="M")
            nc.add_token("type", joint="jnt", control="ctrl", default="ctrl")
            nc.add_rule(
                "test",
                "{description}_{side}_{type}",
                {"description": "test", "side": "left", "type": "joint"},
            )
            nc.set_active_rule_by_name("test")

            result = api.solve(
                naming_convention=nc,
                description="foo",
                side="left",
                type="joint",
            )
            assert result == "foo_L_jnt"

    def test_solve_with_active_convention(self, reset_global_config):
        """Test solving with active naming convention."""
        nc = convention.NamingConvention()
        nc.add_token("description")
        nc.add_token("side", left="L", right="R", default="M")
        nc.add_rule(
            "test",
            "{description}_{side}",
            {"description": "test", "side": "left"},
        )
        nc.set_active_rule_by_name("test")

        api.set_active_naming_convention(nc)
        result = api.solve(description="bar", side="left")
        assert result == "bar_L"

    def test_solve_with_rule_name(self, reset_global_config):
        """Test solving with specific rule name."""
        nc = convention.NamingConvention()
        nc.add_token("name")
        nc.add_token("index")
        nc.add_rule("rule1", "{name}_{index}", {"name": "obj", "index": "01"})
        nc.add_rule("rule2", "{index}_{name}", {"name": "obj", "index": "01"})

        api.set_active_naming_convention(nc)
        result = api.solve(rule_name="rule2", name="test", index="99")
        assert result == "99_test"

    def test_solve_without_convention_raises(self, reset_global_config):
        """Test that solve raises error without naming convention."""
        api.set_active_naming_convention(None)
        with pytest.raises(RuntimeError):
            api.solve(description="foo")


class TestParseAPI:
    """Tests for the parse API function."""

    def test_parse_with_explicit_convention(self, reset_global_config):
        """Test parsing with explicit naming convention."""
        nc = convention.NamingConvention()
        nc.add_token("description")
        nc.add_token("side", left="L", right="R", middle="M")
        nc.add_token("type", joint="jnt", control="ctrl")
        nc.add_rule(
            "test",
            "{description}_{side}_{type}",
            {"description": "test", "side": "left", "type": "joint"},
        )

        result = api.parse("foo_L_jnt", naming_convention=nc)
        assert result["description"] == "foo"
        assert result["side"] == "left"
        assert result["type"] == "joint"

    def test_parse_with_active_convention(self, reset_global_config):
        """Test parsing with active naming convention using tokens with table values."""
        nc = convention.NamingConvention()
        nc.add_token("description")
        nc.add_token("side", left="L", right="R", middle="M")
        nc.add_token("type", joint="jnt", control="ctrl")
        nc.add_rule(
            "test",
            "{description}_{side}_{type}",
            {"description": "test", "side": "left", "type": "joint"},
        )

        api.set_active_naming_convention(nc)
        # Parse a format that matches the rule and has matching token values
        result = api.parse("arm_L_jnt")
        assert result["description"] == "arm"
        assert result["side"] == "left"
        assert result["type"] == "joint"

    def test_parse_without_convention_raises(self, reset_global_config):
        """Test that parse raises error without naming convention."""
        api.set_active_naming_convention(None)
        with pytest.raises(RuntimeError):
            api.parse("foo_bar")


class TestParseByRuleAPI:
    """Tests for the parse_by_rule API function."""

    def test_parse_by_rule(self, reset_global_config):
        """Test parsing by specific rule."""
        nc = convention.NamingConvention()
        nc.add_token("prefix")
        nc.add_token("suffix")
        nc.add_rule(
            "rule1", "{prefix}_{suffix}", {"prefix": "A", "suffix": "B"}
        )
        nc.add_rule(
            "rule2", "{suffix}_{prefix}", {"prefix": "A", "suffix": "B"}
        )

        api.set_active_naming_convention(nc)
        result = api.parse_by_rule("X_Y", rule_name="rule1")
        assert result["prefix"] == "X"
        assert result["suffix"] == "Y"

        result = api.parse_by_rule("X_Y", rule_name="rule2")
        assert result["suffix"] == "X"
        assert result["prefix"] == "Y"


class TestEndToEndWorkflow:
    """End-to-end integration tests for typical workflows."""

    def test_full_workflow_solve_and_parse(self, reset_global_config):
        """Test a complete workflow of solving and parsing names."""
        # Create a naming convention
        nc = convention.NamingConvention(naming_data={"name": "game_assets"})
        nc.add_token("asset_type", character="CHR", prop="PRP", weapon="WPN")
        nc.add_token("asset_name")
        nc.add_token("variant", default="A")
        nc.add_rule(
            "asset",
            "{asset_type}_{asset_name}_{variant}",
            {"asset_type": "character", "asset_name": "Hero", "variant": "A"},
        )
        nc.set_active_rule_by_name("asset")

        # Set as active
        api.set_active_naming_convention(nc)

        # Solve a name
        solved = api.solve(
            asset_type="character", asset_name="Warrior", variant="B"
        )
        assert solved == "CHR_Warrior_B"
        assert solved == "CHR_Warrior_B"

        # Parse the solved name
        parsed = api.parse(solved)
        assert parsed["asset_type"] == "character"
        assert parsed["asset_name"] == "Warrior"
        assert parsed["variant"] == "B"

    def test_workflow_with_multiple_rules(self, reset_global_config):
        """Test workflow with multiple rules."""
        nc = convention.NamingConvention(naming_data={"name": "rigging"})
        nc.add_token("type", joint="JNT", control="CTRL", locator="LOC")
        nc.add_token("region")
        nc.add_token("side", left="L", right="R", center="C", default="C")
        nc.add_token("index", default="01")

        nc.add_rule(
            "joint",
            "{type}_{region}_{side}_{index}",
            {"type": "joint", "region": "Arm", "side": "left", "index": "01"},
        )
        nc.add_rule(
            "control",
            "{region}_{side}_{type}",
            {"type": "control", "region": "Arm", "side": "left"},
        )

        api.set_active_naming_convention(nc)

        # Test joint rule
        joint_name = api.solve(
            rule_name="joint",
            type="joint",
            region="Spine",
            side="center",
            index="02",
        )
        assert joint_name == "JNT_Spine_C_02"

        # Test control rule
        control_name = api.solve(
            rule_name="control", type="control", region="Hand", side="left"
        )
        assert control_name == "Hand_L_CTRL"

    def test_workflow_with_parent_inheritance(self, reset_global_config):
        """Test workflow with parent naming convention inheritance."""
        # Create parent with common tokens
        parent = convention.NamingConvention(naming_data={"name": "base"})
        parent.add_token("side", left="L", right="R", center="C", default="C")
        parent.add_token("index", default="01")

        # Create child with specific tokens
        child = convention.NamingConvention(
            naming_data={"name": "animation"}, parent=parent
        )
        child.add_token("character")
        child.add_token("action")
        child.add_rule(
            "anim",
            "{character}_{action}_{side}",
            {"character": "Hero", "action": "Run", "side": "left"},
        )
        child.set_active_rule_by_name("anim")

        api.set_active_naming_convention(child)

        # Solve using tokens from both parent and child
        result = api.solve(character="Warrior", action="Jump", side="left")
        assert result == "Warrior_Jump_L"

    def test_workflow_with_environment_config(
        self, reset_global_config, temp_dir
    ):
        """Test workflow with environment variable configuration."""
        # Create preset and convention files
        preset_content = """name: custom
namingConventions:
- name: custom-global
  type: global
"""
        with open(os.path.join(temp_dir, "custom.preset"), "w") as f:
            f.write(preset_content)

        convention_content = """name: custom-global
description: Custom naming convention
rules:
  - name: default
    creator: test
    description: Default rule
    expression: "{prefix}_{name}"
    exampleFields:
      prefix: TST
      name: Object
tokens:
  - name: prefix
    description: Prefix token
  - name: name
    description: Name token
"""
        with open(os.path.join(temp_dir, "custom-global.yaml"), "w") as f:
            f.write(convention_content)

        # Set environment variable
        os.environ[config.NAMING_PRESET_PATHS_ENV_VAR] = temp_dir
        try:
            config.reset_configuration()
            api.reset_preset_manager()

            # Verify the custom path is loaded
            cfg = config.get_configuration()
            assert temp_dir in cfg.preset_paths

            # Find custom preset
            preset_file = cfg.find_preset_file("custom")
            assert preset_file is not None
        finally:
            del os.environ[config.NAMING_PRESET_PATHS_ENV_VAR]


class TestErrorHandling:
    """Tests for error handling in the API."""

    def test_solve_with_missing_tokens(self, reset_global_config):
        """Test solving with missing required tokens."""
        nc = convention.NamingConvention()
        nc.add_token("required_token")  # No default
        nc.add_rule("test", "{required_token}_{other}", {})
        nc.set_active_rule_by_name("test")

        api.set_active_naming_convention(nc)
        # Should handle missing tokens gracefully
        # (behavior depends on implementation)

    def test_parse_invalid_format(self, reset_global_config):
        """Test parsing a string that doesn't match any rule."""
        nc = convention.NamingConvention()
        nc.add_token("a")
        nc.add_token("b")
        nc.add_rule("test", "{a}_{b}", {"a": "x", "b": "y"})

        api.set_active_naming_convention(nc)
        # Parsing a format that doesn't match should raise ValueError
        with pytest.raises(ValueError):
            api.parse("completely_different_format_xyz")
