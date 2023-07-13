#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related to nodes selection.
"""

from __future__ import annotations

from typing import List

import maya.cmds as cmds
import maya.mel as mel


def selection_type(selection: List[str]) -> str | None:
	"""
	Returns the "object" or "component" or "uv" type depending on the first type of the given selection.

	:param List[str] selection: selected objects, components or UVs.
	:return: selected component type ("component", "object" or "uv").
	:rtype: str or None
	"""

	if not selection:
		return None

	if '.' not in selection[0]:
		return 'object'
	elif '.vtx[' in selection[0]:
		return 'component'
	elif '.e[' in selection[0]:
		return 'component'
	elif '.f[' in selection[0]:
		return 'component'
	elif '.map[' in selection[0]:
		return 'uv'

	return None


def components_type(components: List[str]) -> str | None:
	"""
	Returns the "object" or "component" or "uv" type depending on the first type of the given selection.

	:param List[str] components: selected objects, components or UVs.
	:return: selected component type ("object", "vertices", "edges", "faces" or "uvs").
	:rtype: str or None
	"""

	if not components:
		return None

	if '.' not in components[0]:
		return 'object'
	elif '.vtx[' in components[0]:
		return 'vertices'
	elif '.e[' in components[0]:
		return 'edges'
	elif '.f[' in components[0]:
		return 'faces'
	elif '.map[' in components[0]:
		return 'uvs'

	return None


def convert_selection(type_to_convert: str = 'faces') -> List[str]:
	"""
	Converts current selection to the given selection type. Supported selection types:
		"faces", "vertices", "edges", "edgeLoop", "edgeRing", "edgePerimeter", "uvs", "uvShll", "uvShellBorder"

	:param str type_to_convert: selection to convert to.
	:return: converted selection.
	:rtype: List[str]
	"""

	if type_to_convert == 'faces':
		mel.eval('ConvertSelectionToFaces;')
	elif type_to_convert == 'vertices':
		mel.eval('ConvertSelectionToVertices;')
	elif type_to_convert == 'edges':
		mel.eval('ConvertSelectionToEdges;')
	elif type_to_convert == 'uvs':
		mel.eval('ConvertSelectionToUVs;')
	elif type_to_convert == 'edgeLoop':
		mel.eval('SelectEdgeLoopSp;')
	elif type_to_convert == 'edgeRing':
		mel.eval('SelectEdgeRingSp;')
	elif type_to_convert == 'edgePerimeter':
		mel.eval('ConvertSelectionToEdgePerimeter;')
	elif type_to_convert == 'uvShell':
		mel.eval('ConvertSelectionToUVShell;')
	elif type_to_convert == 'uvShellBorder':
		mel.eval('ConvertSelectionToUVShellBorder;')
	
	return cmds.ls(selection=True)
