#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Maya tooltips
"""

import maya.cmds as cmds


def tooltip_state():
	"""
	Returns Maya tooltip state

	:return: True if Maya tooltips are enabled; False otherwise.
	:rtype: bool
	"""

	return cmds.help(query=True, popupMode=True)


def set_tooltip_state(flag):
	"""
	Sets whether Maya tooltips should be showed.

	:param bool flag: True to enable Maya tooltips; False otherwise.
	"""

	cmds.evalDeferred(f'from maya import cmds;cmds.help(popupMode={str(int(flag))})')
