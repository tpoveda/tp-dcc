#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya manipulators
"""

import maya.cmds as cmds


def set_preserve_children(state):
	"""
	Sets all manipulator preserve children options to given state.

	:param bool state: True to preserve manipulators children; False otherwise.
	:rtype: bool
	"""

	cmds.optionVar(intValue=('trsManipsPreserveChildPosition', state))
	cmds.manipMoveContext('Move', edit=True, preserveChildPosition=state)
	cmds.manipRotateContext('Rotate', edit=True, preserveChildPosition=state)
	cmds.manipScaleContext('Scale', edit=True, preserveChildPosition=state)
