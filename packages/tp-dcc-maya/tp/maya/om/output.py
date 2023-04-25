import maya.api.OpenMaya as OpenMaya


def display_info(text):
	"""
	Displays info based on application.

	:param str text: info text.
	"""

	OpenMaya.MGlobal.displayInfo(text)


def display_warning(text):
	"""
	Displays warning based on application.

	:param str text: warning text.
	"""

	OpenMaya.MGlobal.displayWarning(text)


def display_error(text):
	"""
	Displays error based on application.

	:param str text: error text.
	"""

	OpenMaya.MGlobal.displayError(text)
