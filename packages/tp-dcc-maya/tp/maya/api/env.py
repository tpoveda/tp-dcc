import maya.api.OpenMaya as OpenMaya


def version():
	"""
	Returns version of the executed Maya, or 0 if not Maya version is found.

	:return: version of Maya (2022)
	:rtype: int
	"""

	return int(OpenMaya.MGlobal.mayaVersion())


def api_version():
	"""
	Returns the Maya API version.

	:return: version of Maya API (201610).
	:rtype: int
	"""

	return OpenMaya.MGlobal.apiVersion()


def version_nice_name():
	"""
	Returns Maya current active version and API (update) as an string.

	:return: Maya version nice name (2016.2)
	"""

	major_str = OpenMaya.MGlobal.mayaVersion()
	api_str = str(OpenMaya.MGlobal.apiVersion())
	api_large = float(api_str[len('{} '.format(major_str)):])
	if api_large < 1000.0:
		api_float = api_large / 1000.0  # eg 200.0 becomes 0.2 float
	else:
		api_float = api_large / 10000.0  # eg 1200 becomes 0.12 float
	nice_version = str(float(major_str) + api_float)  # eg 2018.2
	if api_large == 1000.0 or api_large == 2000.0:  # if version 10 must be .10
		nice_version = "{}0".format(nice_version)

	return nice_version


def is_mayapy():
	"""
	Returns whether current executable is mayapy.

	:return: True if current executable is mayapy; False otherwise.
	:rtype: bool
	"""

	return True if OpenMaya.MGlobal.mayaState() == OpenMaya.MGlobal.kLibraryApp else False


def is_maya_batch():
	"""
	Returns whether current executable is Maya batch.

	:return: True if current executable is Maya batch; False otherwise.
	:rtype: bool
	"""

	return True if  OpenMaya.MGlobal.mayaState() == OpenMaya.MGlobal.kBatch else False


def is_interactive():
	"""
	Returns whether Maya is being executed in interactive mode.

	:return: True if Maya is being executed in interactive mode; False otherwise.
	:rtype: bool
	"""

	return True if OpenMaya.MGlobal.mayaState() == OpenMaya.MGlobal.kInteractive else False
