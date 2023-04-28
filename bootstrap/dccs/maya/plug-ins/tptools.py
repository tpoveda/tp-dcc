import os
import sys
import logging
import cProfile
import traceback
from functools import wraps

from maya import cmds
from maya import OpenMaya
from maya import OpenMayaMPx

logger = logging.getLogger(__name__)
if not len(logger.handlers):
	logger.addHandler(logging.StreamHandler())
if os.environ.get('TPDCC_LOG_LEVEL', 'INFO') == 'DEBUG':
	logger.setLevel(logging.DEBUG)


def profile(fn):
	"""
	Decorator function that allows to profile a function and write that information into disk.

	:param callable fn: decorated function.
	"""

	profile_flag = int(os.environ.get('TPDCC_PROFILE', '0'))
	profile_export_path = os.path.expandvars(os.path.expanduser(os.environ.get('TPCC_PROFILE_PATH', '')))
	should_profile = True if profile_flag and profile_export_path else False

	@wraps(fn)
	def inner():
		if not should_profile:
			return fn()
		logger.debug(f'Running profile output to: {profile_export_path}')
		prof = cProfile.Profile()
		result = prof.runcall(fn)
		prof.dump_stats(profile_export_path)
		return result

	return inner


@profile
def load():
	"""
	Loads tp-dcc-tools framework

	:raises ValueError: if TPDCC_TOOLS_ROOT environment variable is not defined.
	:raises ValueError: if tp-dcc-tools Python folder does not exist.
	"""

	OpenMaya.MGlobal.displayInfo('Loading tp-dcc-tools framework, please wait...')
	logger.debug('Loading tp-dc-tools framework')

	root_path = os.path.abspath(os.environ.get('TPDCC_TOOLS_ROOT', ''))
	root_python_path = os.path.abspath(os.path.join(root_path, 'bootstrap', 'python'))
	if not root_python_path:
		raise ValueError('tp-dcc-tools framework is missing "TPDCC_TOOLS_ROOT" environment variable.')
	elif not os.path.isdir(root_python_path):
		raise ValueError('Failed to find valid tp-dcc-tools Python folder.')
	if root_python_path not in sys.path:
		sys.path.append(root_python_path)

	# import here to make sure that bootstrapping vendor paths are already included within sys.path
	from tp import bootstrap
	bootstrap.init(package_version_file='package_version_maya.config')


def load_ui():
	try:
		from tp.bootstrap.utils import env
		if env.is_mayapy() or env.is_maya_batch():
			logger.debug('Not in maya.exe, skipping tp-dcc-tools menu loading...')
		else:
			from tp.tools import toolbox
			toolbox.load(application_name='maya')
		logger.debug('Finished loading tp-dcc-tools-framework UI')
		OpenMaya.MGlobal.displayInfo('========== tp-dcc-tools-framework ============')
	except Exception as err:
		logger.error('Failed to to load tp-dcc-tools framework UI due to unknown error', exc_info=True)
		OpenMaya.MGlobal.displayError(f'Failed to start tp-dcc-tools freamework UI\n{err}')


def shutdown():
	"""
	Shutdowns tp-dcc-tools framework.
	"""

	from tp import bootstrap
	from tp.bootstrap.utils import env

	OpenMaya.MGlobal.displayInfo('Unloading tp-dcc-tools framework, please wait...')
	if env.is_maya():
		from tp.tools import toolbox
		try:
			toolbox.close()
		except Exception:
			logger.error('Failed to shutdown currently loaded tools', exc_info=True)

	bootstrap.shutdown()

	cmds.flushUndo()


def shutdown_ui():
	"""
	Necessary for shutdown_ui function. Not needed to implement because UI shutdown is handled by shutdown function.
	"""

	pass


def initializePlugin(obj):
	"""
	Maya plugin initialization function.
	"""

	mplugin = OpenMayaMPx.MFnPlugin(obj, 'Tomi Poveda', '1.0', 'Any')
	try:
		load()
		mplugin.registerUI(load_ui, shutdown_ui)
	except Exception:
		logger.error('Unhandled exception occurred during tp-dcc-tools framework startup', exc_info=True)
		OpenMaya.MGlobal.displayError(f'Unknown tp-dcc-tools framework startup failure: \n{traceback.format_exc()}')


def uninitializePlugin(obj):
	"""
	Maya plugin uninitializatzion function.
	"""

	OpenMayaMPx.MFnPlugin(obj)
	try:
		shutdown()
	except Exception:
		logger.error('Unhandled exception occurred during tp-dcc-tools framework shutdown', exc_info=True)
		OpenMaya.MGlobal.displayError(f'Unknown tp-dcc-tools framework shutdown failure: \n{traceback.format_exc()}')
