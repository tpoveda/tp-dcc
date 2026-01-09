from __future__ import annotations

import inspect
import os
import sys
import tempfile
import unittest
from pathlib import Path

from tp.libs.naming import convention, preset, rule, token


def name_convention(add_parent: bool = False) -> convention.NamingConvention:
    """Helper function that returns naming convention using test data.

    Args:
        add_parent (bool): whether to add parent naming convention.

    Returns:
        convention.NamingConvention: naming convention instance.
    """

    root_path = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe()))
    )
    base_naming_config_path = os.path.join(root_path, "data", "base.json")

    parent_naming_convention: convention.NamingConvention | None = None
    if add_parent:
        parent_naming_config_path = os.path.join(
            root_path, "data", "parent.json"
        )
        parent_naming_convention = convention.NamingConvention.from_path(
            parent_naming_config_path
        )

    return convention.NamingConvention.from_path(
        base_naming_config_path, parent=parent_naming_convention
    )


class TestNamingRules(unittest.TestCase):
    def setUp(self) -> None:
        self.naming_convention = name_convention()

    def test_has_rules(self):
        self.assertTrue(self.naming_convention.rule_count() > 0)
        self.naming_convention.clear_rules()
        self.assertTrue(self.naming_convention.rule_count() == 0)

    def test_add_rule(self):
        self.naming_convention.clear_rules()
        new_rule = self.naming_convention.add_rule(
            "test",
            "{description}_{side}_{type}",
            {"description": "node", "side": "l", "type": "joint"},
        )
        self.assertTrue(new_rule)
        self.assertTrue(self.naming_convention.rule_count() == 1)

        return new_rule

    def test_remove_rule(self):
        new_rule = self.test_add_rule()
        result = self.naming_convention.delete_rule(new_rule)
        self.assertTrue(result)
        self.assertTrue(self.naming_convention.rule_count() == 0)
        result = self.naming_convention.delete_rule_by_name("myRule")
        self.assertFalse(result)

    def test_clear_rules(self):
        self.assertTrue(self.naming_convention.rule_count() > 0)
        self.naming_convention.clear_rules()
        self.assertTrue(self.naming_convention.rule_count() == 0)

    def test_find_rule_by_name(self):
        self.assertIsNotNone(self.naming_convention.rule("object"))
        self.assertIsNone(self.naming_convention.rule("nonExistentRule"))

    def test_rule_from_expression(self):
        _rule = self.naming_convention.rule_from_expression(
            "{area}_{section}_{side}_{type}"
        )
        self.assertIsNotNone(_rule)
        self.assertEqual(_rule, self.naming_convention.rule("object"))
        self.assertIsNone(
            self.naming_convention.rule_from_expression(
                "{non_existent_expression}"
            )
        )

    def test_resolve(self):
        resolved_name = self.naming_convention.solve(
            rule_name="object",
            **{"area": "head", "side": "L", "type": "joint"},
        )
        self.assertEqual(
            resolved_name, "head_l_jnt", "Unable to resolve with given tokens!"
        )

    def test_expression_from_string(self):
        self.assertEqual(
            self.naming_convention.expression_from_string("head_l_jnt"),
            "{area}_{section}_{side}_{type}",
        )

    def test_active_rule(self):
        new_rule = self.test_add_rule()
        self.naming_convention.set_active_rule(new_rule)
        self.assertIsNotNone(self.naming_convention.active_rule())
        self.naming_convention.set_active_rule(None)
        self.assertIsNone(self.naming_convention.active_rule())


class TestNamingTokens(unittest.TestCase):
    def setUp(self) -> None:
        self.naming_convention = name_convention()

    def test_has_tokens(self):
        self.assertTrue(self.naming_convention.token_count() > 0)
        self.naming_convention.clear_tokens()
        self.assertTrue(self.naming_convention.token_count() == 0)

    def test_add_token(self):
        self.naming_convention.add_token("newToken")
        self.assertTrue(self.naming_convention.has_token("newToken"))
        new_token = self.naming_convention.add_token(
            "newToken2", **{"myKey": "myValue"}
        )
        self.assertEqual(new_token.solve("myKey"), "myValue")
        self.assertEqual(len(new_token), 1)
        new_token = self.naming_convention.add_token(
            "newToken3", left="L", right="R", middle="M", default="M"
        )
        self.assertIsNotNone(new_token.default)

    def test_remove_token(self):
        new_token = self.naming_convention.add_token("newToken")
        self.assertTrue(self.naming_convention.has_token("newToken"))
        self.naming_convention.delete_token(new_token)
        self.assertFalse(self.naming_convention.has_token("newToken"))
        self.naming_convention.add_token("newToken2", **{"myKey": "myValue"})
        self.assertTrue(self.naming_convention.has_token("newToken2"))
        self.naming_convention.delete_token_by_name("newToken2")
        self.assertFalse(self.naming_convention.has_token("newToken2"))

    def test_has_token(self):
        self.naming_convention.add_token("newToken")
        self.assertTrue(self.naming_convention.has_token("newToken"))
        self.naming_convention.delete_token_by_name("newToken")
        self.assertFalse(self.naming_convention.has_token("newToken"))

    def test_token_solve(self):
        self.assertEqual(
            self.naming_convention.token("area").solve("arm"), "arm"
        )
        self.assertIsNone(self.naming_convention.token("area").solve("myArea"))
        self.assertEqual(
            self.naming_convention.token("area").solve(
                "myArea", "defaultValue"
            ),
            "defaultValue",
        )

    def test_add_token_key_value(self):
        self.naming_convention.add_token("newToken", **{"myKey": "myValue"})
        self.assertTrue(
            self.naming_convention.token("newToken").add("test", "testValue")
        )
        self.assertTrue(
            self.naming_convention.token("newToken").has_key("test")
        )
        self.assertEqual(
            self.naming_convention.token("newToken").solve("test"), "testValue"
        )

    def test_update_token_key_value(self):
        new_token = self.naming_convention.add_token(
            "newToken", **{"myKey": "myValue"}
        )
        new_token.key_value("myKey").value = "hello"
        self.assertEqual(new_token.key_value("myKey").value, "hello")

    def test_clear_tokens(self):
        self.assertTrue(self.naming_convention.token_count() != 0)
        self.naming_convention.add_token("newToken", **{"myKey": "myValue"})
        self.naming_convention.clear_tokens()
        self.assertTrue(self.naming_convention.token_count() == 0)


class TestParse(unittest.TestCase):
    def setUp(self) -> None:
        self.naming_convention = convention.NamingConvention()
        self.naming_convention.add_token("description")
        self.naming_convention.add_token(
            "side", left="L", right="R", middle="M", default="M"
        )
        self.naming_convention.add_token(
            "type",
            animation="anim",
            control="ctrl",
            joint="jnt",
            default="ctrl",
        )
        self.naming_convention.add_rule(
            "test1",
            "{description}_{side}_{type}",
            {"description": "test", "side": "left", "type": "joint"},
        )
        self.naming_convention.add_rule(
            "test2",
            "{side}_{description}",
            {"side": "left", "description": "test"},
        )
        self.naming_convention.add_rule(
            "test3",
            "{type}_{description}",
            {"type": "joint", "description": "test"},
        )

    def test_parsing(self):
        parsed = self.naming_convention.parse("foo_M_ctrl")
        self.assertEqual(parsed["description"], "foo")
        self.assertEqual(parsed["side"], "middle")
        self.assertEqual(parsed["type"], "control")
        self.assertEqual(len(parsed), 3)

        self.naming_convention.set_active_rule_by_name("test2")
        parsed = self.naming_convention.parse_by_active_rule("M_foo")
        self.assertEqual(parsed["description"], "foo")
        self.assertEqual(parsed["side"], "middle")
        self.assertEqual(len(parsed), 2)

        _rule = self.naming_convention.rule("test3")
        parsed = self.naming_convention.parse_by_rule(_rule, "jnt_test")
        self.assertEqual(parsed["type"], "joint")
        self.assertEqual(parsed["description"], "test")
        self.assertEqual(len(parsed), 2)


class TestSolve(unittest.TestCase):
    def setUp(self) -> None:
        self.naming_convention = convention.NamingConvention()
        self.naming_convention.add_token("description")
        self.naming_convention.add_token(
            "side", left="L", right="R", middle="M", default="M"
        )
        self.naming_convention.add_token(
            "type",
            animation="anim",
            control="ctrl",
            joint="jnt",
            default="ctrl",
        )
        self.naming_convention.add_rule_from_tokens(
            "test1", "description", "side", "type"
        )
        self.naming_convention.add_rule_from_tokens(
            "test2", "side", "description"
        )
        self.naming_convention.set_active_rule_by_name("test1")

    def test_explicit(self):
        solved = self.naming_convention.solve(
            description="foo", side="left", type="animation"
        )
        self.assertEqual(solved, "foo_L_anim")
        solved = self.naming_convention.solve(
            description="foo", side="middle", type="animation"
        )
        self.assertEqual(solved, "foo_M_anim")
        solved = self.naming_convention.solve(
            rule_name="test2", description="foo", side="left", type="animation"
        )
        self.assertEqual(solved, "L_foo")
        solved = self.naming_convention.solve(
            rule_name="test2",
            description="foo",
            side="middle",
            type="animation",
        )
        self.assertEqual(solved, "M_foo")

    def test_defaults(self):
        solved = self.naming_convention.solve(
            description="foo", type="animation"
        )
        self.assertEqual(solved, "foo_M_anim")
        solved = self.naming_convention.solve(description="foo")
        self.assertEqual(solved, "foo_M_ctrl")
        solved = self.naming_convention.solve(
            rule_name="test2", description="foo", type="animation"
        )
        self.assertEqual(solved, "M_foo")
        solved = self.naming_convention.solve(
            rule_name="test2", description="foo"
        )
        self.assertEqual(solved, "M_foo")

    def test_implicit(self):
        solved = self.naming_convention.solve("foo", type="animation")
        self.assertEqual(solved, "foo_M_anim")
        solved = self.naming_convention.solve("foo")
        self.assertEqual(solved, "foo_M_ctrl")
        solved = self.naming_convention.solve(
            "foo", rule_name="test2", type="animation"
        )
        self.assertEqual(solved, "M_foo")
        solved = self.naming_convention.solve("foo", rule_name="test2")
        self.assertEqual(solved, "M_foo")


class TestParentNamingRules(unittest.TestCase):
    def setUp(self) -> None:
        self.naming_convention = name_convention(add_parent=True)

    def test_parent_has_rules(self):
        self.assertTrue(len(self.naming_convention.rules()) > 0)
        self.naming_convention.clear_rules()
        self.assertTrue(
            len(self.naming_convention.rules())
            == self.naming_convention.parent.rule_count()
        )

    def test_find_parent_rule_by_name(self):
        self.assertIsNotNone(self.naming_convention.rule("parentRule"))
        self.assertIsNotNone(self.naming_convention.rule("object"))
        self.assertIsNone(self.naming_convention.rule("nonExistentRule"))

    def test_parent_rule_from_expression(self):
        rule = self.naming_convention.rule_from_expression(
            "{area}_{side}_{type}_{myToken}"
        )
        self.assertIsNotNone(rule)
        self.assertEqual(rule.name, "parentRule")
        self.assertIsNone(
            self.naming_convention.rule("{non_existent_expression}")
        )

    def test_parent_resolve(self):
        self.assertEqual(
            self.naming_convention.solve(
                rule_name="parentRule",
                **{
                    "area": "null",
                    "side": "M",
                    "type": "transform",
                    "myToken": "parent",
                },
            ),
            "null_m_srt_parentA",
        )

    # def test_parent_expression_from_string(self):
    #     expression = self.naming_convention.expression_from_string('head_l_jnt')
    #     self.assertEqual(expression, '{area}_{section}_{side}_{type}')
    #     self.assertEqual(self.naming_convention.rule_from_expression(expression).name, 'object')


class TestSerializationCase(unittest.TestCase):
    def setUp(self) -> None:
        self.naming_convention = convention.NamingConvention()

    def test_tokens(self):
        token1 = self.naming_convention.add_token(
            "side", left="L", right="R", middle="M", default="M"
        )
        token2 = token.Token.from_dict(token1.to_dict())
        self.assertEqual(token1.to_dict(), token2.to_dict())

    def test_rules(self):
        rule1 = self.naming_convention.add_rule_from_tokens(
            "test", "description", "side", "type"
        )
        rule2 = rule.Rule.from_dict(rule1.to_dict())
        self.assertEqual(rule1.to_dict(), rule2.to_dict())

    def test_validation(self):
        _token = self.naming_convention.add_token(
            "side", left="L", right="R", middle="M", default="M"
        )
        _rule = self.naming_convention.add_rule_from_tokens(
            "test", "description", "side", "type"
        )
        self.assertIsNone(rule.Rule.from_dict(_token.to_dict()))
        self.assertIsNone(token.Token.from_dict(_rule.to_dict()))

    def test_save_load_naming_convention(self):
        self.naming_convention.add_token("description")
        self.naming_convention.add_token(
            "side", left="L", right="R", middle="M", default="M"
        )
        self.naming_convention.add_token(
            "type",
            animation="anim",
            control="ctrl",
            joint="jnt",
            default="ctrl",
        )
        self.naming_convention.add_rule_from_tokens(
            "test1", "description", "side", "type"
        )
        self.naming_convention.add_rule_from_tokens(
            "test2", "side", "description"
        )
        self.naming_convention.set_active_rule_by_name("test1")

        naming_convention_file = tempfile.NamedTemporaryFile(
            suffix=".json"
        ).name
        self.naming_convention.save_to_file(naming_convention_file)
        result = self.naming_convention.save_to_file(naming_convention_file)
        self.assertTrue(result)

        self.naming_convention.clear_rules()
        self.naming_convention.clear_tokens()

        self.naming_convention.refresh(file_path=naming_convention_file)
        self.assertTrue(self.naming_convention.has_token("description"))
        self.assertTrue(self.naming_convention.has_token("side"))
        self.assertTrue(self.naming_convention.has_token("type"))
        self.assertTrue(self.naming_convention.has_rule("test1"))
        self.assertTrue(self.naming_convention.has_rule("test2"))
        self.assertEqual(self.naming_convention.active_rule().name, "test1")


class TestNamingPresets(unittest.TestCase):
    def setUp(self) -> None:
        self._preset_manager = preset.PresetsManager.from_project()

    def test_all_rules_have_valid_example_tokens(self):
        for (
            _name_convention
        ) in self._preset_manager.naming_conventions.values():
            for found_rule in _name_convention.iterate_rules(recursive=False):
                expression_tokens = found_rule.tokens()
                example_tokens = found_rule.example_tokens
                self.assertTrue(
                    all(i in example_tokens for i in expression_tokens),
                    f"Missing example_tokens for rule {found_rule.name}",
                )


if __name__ == "__main__":
    unittest.main()
