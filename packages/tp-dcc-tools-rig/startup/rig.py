from __future__ import annotations

from tp.core import log, dcc
from tp.preferences.interfaces import crit
from tp.bootstrap.core import exceptions, package

if dcc.is_maya():
	from tp.maya.plugins import rigloader
	from tp.libs.rig.freeform import startup as freeform_startup


logger = log.tpLogger


def startup(_: package.Package):
	"""
	This function is automatically called by tpDcc packages Manager when environment setup is initialized.
	"""

	if not dcc.is_maya():
		return

	logger.info('Loading tp-dcc-tools-rig package...')
	crit_interface = crit.crit_interface()
	crit_interface.upgrade_preferences()
	crit_interface.upgrade_assets()

	rigloader.load_all_plugins()
	freeform_startup.startup()


def shutdown(bootstrap_package: package.Package):
	"""
	Shutdown function that is called during tpDcc framework shutdown.
	This function is called at the end of tpDcc framework shutdown.

	:param Package bootstrap_package: package instance.
	"""

	if not dcc.is_maya():
		return

	if not bootstrap_package:
		raise exceptions.MissingPackage(package)

	logger.info('Shutting down tp-dcc-tools-rig package...')

	freeform_startup.shutdown()
	rigloader.unload_all_plugins()
