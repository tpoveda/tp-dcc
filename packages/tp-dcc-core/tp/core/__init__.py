import os
import sys
import inspect


def get_root_path():
	"""
	Returns the root directory

	:return root path where this file is located
	:rtype: str
	"""

	return os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


def get_version():
	"""
	Return current Python version used
	:return: SemanticVersion, python version
	"""

	from tp.common.python import version

	py_version = sys.version_info
	current_version = version.SemanticVersion(
		major=py_version.major,
		minor=py_version.minor,
		patch=py_version.micro
	)

	return current_version


def is_python2():
	"""
	Returns whether current version is Python 2
	:return: bool
	"""

	return get_version().major == 2


def is_python3():
	"""
	Returns whether current version is Python 3
	:return: bool
	"""

	return get_version().major == 3

def register_vendors():
	"""
	Function that register vendor folder within sys.path
	"""

	vendor_path = os.path.join(get_root_path(), 'vendor')
	if os.path.isdir(vendor_path) and vendor_path not in sys.path:
		sys.path.append(vendor_path)

	py_folder = os.path.join(vendor_path, 'py2' if is_python2() else 'py3')
	if os.path.isdir(py_folder) and py_folder not in sys.path:
		sys.path.append(py_folder)


register_vendors()
