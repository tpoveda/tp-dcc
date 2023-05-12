import os
import glob

from tp.common.python import jsonio
from tp.maya.api import curves

CURVE_FILE_EXTENSION = 'curve'
CURVES_ENV_VAR = 'TP_RIGTOOLKIT_CURVES_PATHS'
_PATHS_CACHE = dict()


def update_cache(force=False):
	"""
	Function that handles the update of cached curves.

	:param bool force: whether to force the update of the cache event if the cache is already initialized.
	"""

	global _PATHS_CACHE
	if _PATHS_CACHE and not force:
		return

	for root in iterate_root_paths():
		for shape_path in glob.glob(os.path.join(root, '*.{}'.format(CURVE_FILE_EXTENSION))):
			_PATHS_CACHE[os.path.splitext(os.path.basename(shape_path))[0]] = {'path': shape_path}


def clear_cache():
	"""
	Clears the cache of available curves.
	"""

	global _PATHS_CACHE
	_PATHS_CACHE.clear()


def iterate_root_paths():
	"""
	Generator function that iterates over all root locations defined by TP_RIGTOOLKIT_SHAPES_PATHS environment variable.
	"""

	for root in os.environ.get(CURVES_ENV_VAR, '').split(os.pathsep):
		if not root or not os.path.exists(root):
			continue
		yield root


def iterate_names():
	"""
	Generator function which iterates over all available curve names.

	:return: iterated curve names.
	:rtype: generator(str)
	..info:: curves are source from all the root location specified by the CURVES_ENV_VAR environment variable.
	"""

	global _PATHS_CACHE

	update_cache()
	for curve_name in _PATHS_CACHE.keys():
		yield curve_name


def names():
	"""
	List all the curve names available.

	:return:  list of curve names.
	:rtype: list(str)
	..info:: curves are source from all the root location specified by the CURVES_ENV_VAR environment variable.
	"""

	return list(iterate_names())


def load_from_lib(curve_name):
	"""
	Loads the data from the given curve name in library.

	:param str curve_name: name of the curve to load data of.
	:return: curve data.
	:rtype: dict
	:raises MissingCurveFromLibrary: if the given curve name does not exist in the library of curves.
	"""

	update_cache()

	info = _PATHS_CACHE.get(curve_name)
	if not info:
		raise MissingCurveFromLibrary('Curve name {} does not exist in the library'.format(curve_name))

	data = info.get('data')
	if not data:
		data = jsonio.read_file(info['path'])
		info['data'] = data

	return data


def load_and_create_from_lib(curve_name, parent=None):
	"""
	Loads and creates the curve from curves library. If parent is given, shape node will be parented under it.

	:param str curve_name: curve library name to load and create.
	:param OpenMaya.MObject parent: optional curve parent.
	:return: tuple with the MObject of the parent and a list representing the MObjects of the created shapes.
	:rtype: tuple(OpenMaya.MObject, list(OpenMaya.MObject))
	"""

	new_data = load_from_lib(curve_name)
	return curves.create_curve_shape(new_data, parent=parent)


class MissingCurveFromLibrary(Exception):

	pass
