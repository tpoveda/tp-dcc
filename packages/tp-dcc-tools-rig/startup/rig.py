from tp.core import log
from tp.preferences.interfaces import crit

logger = log.tpLogger


def startup(package_manager):
	"""
	This function is automatically called by tpDcc packages Manager when environment setup is initialized.

	:param package_manager: current tpDcc packages Manager instance.
	:return: tpDccPackagesManager
	"""

	logger.info('Loading tp-dcc-tools-rig package...')
	crit_interface = crit.crit_Interface()
	crit_interface.upgrade_preferences()
	crit_interface.upgrade_assets()


def shutdown(package_manager):
	"""
	Shutdown function that is called during tpDcc framework shutdown.
	This function is called at the end of tpDcc framework shutdown.
	"""

	logger.info('Shutting down tp-dcc-tools-rig package...')
