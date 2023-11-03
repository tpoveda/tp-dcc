#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that tp-dcc-tools Maya Server commands.
"""

from __future__ import annotations

import maya.cmds as cmds

from tp.core import dcc


def file_extensions() -> list[str]:
	"""
	Returns supported file extensions of the DCC.

	:return: list of DCC file extensions (['.mb', '.ma'], ['.max'], ...).
	:rtype: list[str]
	"""

	return dcc.file_extensions()


def make_cube() -> str:
	"""
	Creates a cube within Maya scene.

	:return: path to the created cube.
	:rtype: str
	"""

	return cmds.polyCube()


def make_sphere(name: str = 'mySphere', create_uvs: bool = True, radius: int = 3) -> str:
	"""
	Creates a new sphere within Maya scene.

	:param str name: name of the sphere.
	:param create_uvs: whether sphere should auto create UVs.
	:param radius: radius of the sphere.
	:return: path to the created cube.
	:rtype: str
	"""

	return cmds.polySphere(name=name, createUVS=create_uvs, radius=radius)


def maya_command(command: str, args: None | list[str] = None, kwargs: None | dict = None) -> str:
	"""
	Executes a raw maya.cmds command.

	import tp.core.client
	maya_client = tp.core.client.MayaClient()
	maya_client.execute('maya_command', {'command': 'cmds.polySphere', 'kwargs': {'radius": 10}})

	:param str command: name of the command to execute.
	:param list args: list of unnamed arguments.
	:param dict kwargs: dictionary with keyword arguments.
	:return: command result.
	:rtype: str
	"""

	args = args if args is not None else list()
	kwargs = kwargs if kwargs is not None else dict()
	kwargs = dict((str(k), v) for k, v in kwargs.items())
	func = eval(command)
	result = func(*args, **kwargs)

	return str(result)


def execute_python(python_script: str):
	"""
	Executes a complete Python script.

	:param str python_script: Python code to execute.
	"""

	exec(python_script)


def warning(message: str):
	"""
	Outputs warning message into Maya Output window.

	:param str message: warning message.
	"""

	cmds.warning(message)


def errors(message: str):
	"""
	Outputs error message into Maya Output window.

	:param str message: error message.
	"""

	cmds.error(message)


def new_scene(force: bool = True):
	"""
	Creates a new Maya scene.

	:param bool force: whether to force the creation of the scene.
	"""

	cmds.file(new=True, force=force)
