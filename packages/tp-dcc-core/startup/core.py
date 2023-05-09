#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script that contains tp-dcc-core startup functionality
"""

import os
import inspect

from tp.bootstrap.core import manager, exceptions as bootstrap_exceptions
from tp.core import log
from tp.common.python import path

logger = log.tpLogger


def startup(package_manager):
	"""
	This function is automatically called by tp-dcc-bootstrap packages manager when environment setup is initialized.

	:param package_manager: current tp-dcc-bootstrap packages Manager instance.
	:return: tpDccPackagesManager
	"""

	root_file_path = path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
	package = manager.package_from_path(root_file_path)
	if not package:
		raise bootstrap_exceptions.MissingPackage(package)

	logger.info('Loading tp-dcc-core package...')


def shutdown(package_manager):
	"""
	Shutdown function that is called during tp-dcc-bootstrap packages manager shutdown.
	This function is called at the end of tp-dcc-tools framework shutdown.
	"""

	logger.info('Unloading tp-dcc-core package...')
