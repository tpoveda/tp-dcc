#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Preferences error classes
"""


class RootAlreadyExistsError(Exception):
	"""
	Exception that is raised when a root path already exists within the Preferences Manager
	"""

	pass


class RootDoesNotExistsError(Exception):
	"""
	Exception that is raised when Preferences Manager tries to retrieve a root path that does not exist.
	"""

	pass


class RootDestinationAlreadyExistsError(Exception):
	"""
	Exception that is raised when a root destination folder already exists.
	"""

	pass

