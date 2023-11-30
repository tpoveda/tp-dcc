#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains class implementations related with Maya output.
"""

from tp.core import output

from tp.maya.om import output as maya_output


class MayaOutput(output.BaseOutput):

	@staticmethod
	def display_info(text: str):
		"""
		Displays info based on application.

		:param str text: info text.
		"""

		maya_output.display_info(text)

	@staticmethod
	def display_warning(text: str):
		"""
		Displays warning based on application.

		:param str text: warning text.
		"""

		maya_output.display_warning(text)


	@staticmethod
	def display_error(text: str):
		"""
		Displays error based on application.

		:param str text: error text.
		"""

		maya_output.display_error(text)
