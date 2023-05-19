#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that tp-dcc-tools Core Server commands.
"""

import runpy


def is_online() -> bool:
	"""
	Returns whether DCC server is running.

	:return: True if DCC server is running; False otherwise.
	:rtype: bool
	"""

	return True


def echo_message(message: str):
	"""
	Prints message into server output.

	:param str message: message to print.
	"""

	print(message)


def run_python_script(script_path: str):
	"""
	Runs given Python script within server.

	:param str script_path: script path to run.
	"""

	runpy.run_path(script_path, init_globals=globals(), run_name='__main__')
