#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for FRAG library Preference interface.
"""

from __future__ import annotations

from tp.preferences import preference


class FragInterface(preference.PreferenceInterface):

    ID = 'frag'
    _RELATIVE_PATH = 'prefs/maya/frag.pref'

    def blueprint_config(self, root: str | None = None) -> dict:
        """
        Returns the default blueprint configuration.

        :param str root: root name to search. If None, then all roots will be searched until relativePath is found.
        :return: default blueprint configuration.
        :rtype: dict
        """

        return self.settings(root=root).get('settings', {}).get('blueprint', {})
