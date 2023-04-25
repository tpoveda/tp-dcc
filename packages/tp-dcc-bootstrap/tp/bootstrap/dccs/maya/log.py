#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Maya logger handler implementation
"""

import sys
import logging

import maya.api.OpenMaya as OpenMaya


class MayaLogHandler(logging.Handler):

	def emit(self, record):
		"""
		Overrides base emit function to show log messages using Maya API.

		:param record:
		:return:
		"""

		message = self.format(record)

		print(message)

		if record.levelname == 'WARNING':
			OpenMaya.MGlobal.displayWarning(message)
		elif record.levelname in ('ERROR', 'CRITICAL'):
			OpenMaya.MGlobal.displayError(message)
		elif record.levelname == 'DEBUG' or record.levelname == 'INFO':
			# Write all messages to sys.__stdout__, which goes to the output window. Only write debug messages here.
			# The script editor is incredibly slow and can easily hang Maya if we have a lot of debug logging on,
			# but the output window is reasonably fast.
			sys.__stdout__.write('{}\n'.format(message))
