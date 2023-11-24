#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tp-dcc-maya startup functionality
"""

import os
import typing
import inspect

from tp.core import log, dcc
from tp.common.python import path
from tp.preferences.interfaces import crit
from tp.common.resources import api as resources
from tp.bootstrap.core import manager, exceptions as bootstrap_exceptions

if dcc.is_maya():
	from tp.libs.rig.crit.maya import plugin as crit_plugin

if typing.TYPE_CHECKING:
	pass


logger = log.tpLogger


def startup(package_manager):
	"""
	This function is automatically called by tpDcc packages Manager when environment setup is initialized.

	:param package_manager: current tpDcc packages Manager instance.
	:return: tpDccPackagesManager
	"""

	root_file_path = path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
	package = manager.package_from_path(root_file_path)
	if not package:
		raise bootstrap_exceptions.MissingPackage(package)

	logger.info('Loading CRIT rigging package...')

	resources_path = path.join_path(os.path.dirname(root_file_path), 'resources')
	print(resources_path)
	resources.register_resource(resources_path)

	crit_interface = crit.crit_interface()
	crit_interface.upgrade_preferences()
	crit_interface.upgrade_assets()

	if dcc.is_maya():
		crit_plugin.load()


def shutdown(package_manager):
	"""
	Shutdown function that is called during tpDcc framework shutdown.
	This function is called at the end of tpDcc framework shutdown.
	"""

	logger.info('Shutting down CRIT rigging package...')

	if dcc.is_maya():
		crit_plugin.unload()
