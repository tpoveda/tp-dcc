# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya code related with option vars
"""

import maya.cmds as cmds


def option_var(key, default=None):
	"""
	Returns the option var with given key.

	:param str key: option var key.
	:param any default: default value if option var does not exist.
	:return: option var value.
	:rtype: object
	"""

	if not cmds.optionVar(exists=key):
		return default

	return cmds.optionVar(query=key)


def set_option_var(key, value):
	"""
	Sets the given key option var with given value.

	:param str key: option var name.
	:param object value: new option var value.
	"""

	cmds.optionVar(sv=(key, value))
