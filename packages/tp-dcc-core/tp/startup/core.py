#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tp-dcc-core startup functionality
"""

import os
import inspect

from tp.bootstrap.core import manager, exceptions as bootstrap_exceptions
from tp.core import log
from tp.common.python import path

logger = log.tpLogger


def startup(package_manager):
	"""
	This function is automatically called by tpDcc packages Manager when environment setup is initialized.

	:param package_manager: current tpDcc packages Manager instance.
	:return: tpDccPackagesManager
	"""

	logger.info('Loading tpDcc Core package...')

	root_file_path = path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
	package = manager.get_package_from_path(root_file_path)
	if not package:
		raise bootstrap_exceptions.MissingPackage(package)

	logger.info('\n\n' + '=' * 80)
	logger.info('tpDcc Framework')
	logger.info('\n' + '=' * 80 + '\n')


def shutdown(package_manager):
	"""
	Shutdown function that is called during tpDcc framework shutdown.
	This function is called at the end of tpDcc framework shutdown.
	"""

	logger.info('Unloading tpDcc Core package...')