from __future__ import annotations

import unittest

from tp.libs.naming import api


class TestApi(unittest.TestCase):
    def test_naming_preset_manager(self):
        naming_preset_manager = api.naming_preset_manager()
        self.assertIsNotNone(naming_preset_manager)

    def test_global_naming_convention(self):
        naming_convention = api.naming_convention(check_project=False)
        self.assertIsNotNone(naming_convention)
        return naming_convention

    def test_global_project_naming_convention(self):
        naming_convention = api.naming_convention()
        self.assertIsNotNone(naming_convention)
        return naming_convention

    def test_project_cinematics_naming_convention(self):
        naming_convention = api.naming_convention(name="cinematics")
        self.assertIsNotNone(naming_convention)
        return naming_convention

    def test_active_naming_convention(self):
        api.set_active_naming_convention(None)
        self.assertIsNone(api.active_naming_convention())
        naming_convention = api.naming_convention(set_as_active=False)
        api.set_active_naming_convention(naming_convention)
        self.assertEqual(api.active_naming_convention(), naming_convention)

    def test_solve_name_explicit(self):
        naming_convention = self.test_global_project_naming_convention()
